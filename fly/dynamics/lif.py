"""Reference leaky integrate-and-fire model (WP5).

Equations, parameters, and semantics are traced to the Shiu et al. reference
implementation (data/raw/reference/shiu_model.py, fetched 2026-09-23):

    dv/dt = (v_0 - v + g) / t_mbr    (unless refractory)
    dg/dt = -g / tau                 (unless refractory)
    threshold: v > v_th
    reset:    v = v_rst; g = 0
    synapse:  on_pre  g += w,  delay = t_dly
    Poisson:  target v, weight = w_syn * f_poi, refractory disabled for targets

Brian2's ``method='linear'`` integrates the coupled linear ODEs exactly; we
replicate that with the closed-form coupled update below rather than naive
Euler steps, so a single synaptic kick produces the same trajectory Brian2
would.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class LIFParams:
    """LIF constants, all values from shiu_model.py default_params."""

    v0_mV: float = -52.0            # resting potential (Kakaria & de Bivort 2017)
    v_reset_mV: float = -52.0      # reset potential after spike
    v_thresh_mV: float = -45.0     # spike threshold
    tau_mbr_ms: float = 20.0       # membrane time constant
    tau_syn_ms: float = 5.0        # synaptic decay constant (Jürgensen et al.)
    t_refractory_ms: float = 2.2   # refractory period (Lazar et al.)
    t_delay_ms: float = 1.8        # synaptic delay (Paul et al. 2015)
    w_syn_mV: float = 0.275        # weight per synapse (free parameter)
    r_poisson_Hz: float = 150.0    # Poisson stimulation rate
    f_poisson: float = 250.0       # Poisson kick scaling factor
    dt_ms: float = 0.1             # Brian2 default clock step


@dataclass(frozen=True)
class LIFRun:
    """Results of one LIF simulation trial."""

    node_ids: list[int]
    spike_times: dict[int, list[float]]  # node id -> sorted spike times (ms)
    v_final_mV: np.ndarray
    n_spikes: int
    duration_ms: float
    params: LIFParams = field(repr=False, default_factory=LIFParams)


def _check_ids(node_ids: list[int], ids: list[int], what: str) -> list[int]:
    known = set(node_ids)
    for value in ids:
        if value not in known:
            raise ValueError(f"{what} id {value!r} not in node_ids")
    return list(ids)


def simulate_lif(
    connectivity: sparse.csr_matrix,
    node_ids: list[int],
    params: LIFParams,
    duration_ms: float,
    stimulated: list[int] | None = None,
    silenced: list[int] | None = None,
    init_v_mV: float | None = None,
    seed: int = 0,
) -> LIFRun:
    """Run one LIF trial on a weighted connectivity matrix.

    connectivity[i, j] is the synapse count from node_ids[i] to node_ids[j];
    the per-edge voltage kick is count * w_syn (shiu model.py: syn.w =
    'Excitatory x Connectivity' * w_syn, on_pre g += w, delayed by t_dly).
    Neurons in ``stimulated`` receive direct Poisson kicks to v of
    w_syn * f_poi at rate r_poisson, with refractory disabled (poi() in the
    reference sets rfc = 0 for Poisson targets). Neurons in ``silenced``
    have all outgoing weights zeroed (silence() in the reference).

    Deterministic for a given seed.
    """
    n = len(node_ids)
    if connectivity.shape != (n, n):
        raise ValueError(
            f"connectivity shape {connectivity.shape} does not match {n} node ids"
        )
    stimulated = _check_ids(node_ids, stimulated or [], "stimulated")
    silenced = _check_ids(node_ids, silenced or [], "silenced")

    dt = params.dt_ms
    n_steps = int(round(duration_ms / dt))
    delay_steps = int(round(params.t_delay_ms / dt))

    index_of = {node_id: i for i, node_id in enumerate(node_ids)}
    stimulated_idx = [index_of[v] for v in stimulated]
    silenced_mask = np.zeros(n, dtype=bool)
    for v in silenced:
        silenced_mask[index_of[v]] = True

    # Outgoing edge weights in mV: synapse count * w_syn; silenced rows zeroed.
    weights = connectivity.tocsr(copy=True).astype(float) * params.w_syn_mV
    if silenced_mask.any():
        weights[silenced_mask.nonzero()[0], :] = 0.0

    # Precomputed decay terms of the exact coupled linear solution.
    # x' = A x with x = [u, g], A = [[-1/tau_m, 1/tau_m], [0, -1/tau_s]].
    # exp(A dt) = [[e_m, c_gain*(e_m - e_s)], [0, e_s]]
    #   with c_gain = tau_s / (tau_m - tau_s)   (upper-triangular exact step)
    e_m = np.exp(-dt / params.tau_mbr_ms)             # membrane decay
    e_s = np.exp(-dt / params.tau_syn_ms)             # synapse decay
    denom = params.tau_mbr_ms - params.tau_syn_ms      # 20 - 5 = 15
    if abs(denom) < 1e-12:                             # tau == tau_mbr edge case
        c_gain = dt / params.tau_mbr_ms * np.exp(-dt / (2 * params.tau_mbr_ms))
    else:
        c_gain = params.tau_syn_ms / denom             # coupling coefficient

    v = np.full(n, params.v0_mV if init_v_mV is None else float(init_v_mV))
    g = np.zeros(n)
    last_spike = np.full(n, -np.inf)
    refractory_steps = int(round(params.t_refractory_ms / dt))

    # Delayed-kick ring buffer: kicks scheduled at step s land at (s + delay).
    ring_len = delay_steps + 1
    ring = np.zeros((ring_len, n))
    ring_targets = [np.empty(0, dtype=int) for _ in range(ring_len)]

    stim_set = np.array(stimulated_idx, dtype=int)
    stim_refractory = np.zeros(n, dtype=bool)
    stim_refractory[stim_set] = True   # Poisson targets: rfc = 0 (reference poi())
    poisson_p = params.r_poisson_Hz * dt / 1000.0
    poisson_kick = params.w_syn_mV * params.f_poisson

    rng = np.random.default_rng(seed)
    spike_times: dict[int, list[float]] = {node_id: [] for node_id in node_ids}
    weights_csr = weights.tocsr()

    for step in range(n_steps):
        slot = step % ring_len
        t = step * dt

        # Refractory mask: neurons whose refractory window is still open.
        # Stimulated neurons have rfc = 0 (reference poi()) so never freeze.
        if refractory_steps:
            frozen = (t - last_spike) < (params.t_refractory_ms - 1e-9)
            frozen &= ~stim_refractory
        else:
            frozen = np.zeros(n, dtype=bool)

        # Exact coupled linear update (Brian2 method='linear' equivalent),
        # applied only to non-frozen neurons: dv/dt and dg/dt both carry
        # '(unless refractory)' in the reference equations. This is the
        # 'groups' slot of the Brian2 schedule: it runs BEFORE the
        # threshold check and before any kicks are delivered this step.
        g_next = g * e_s
        u = v - params.v0_mV
        u_next = e_m * u + c_gain * (e_m - e_s) * g
        g = np.where(frozen, g, g_next)
        v = params.v0_mV + np.where(frozen, u, u_next)

        # Spike check ('thresholds' slot): evaluated before this step's
        # kick delivery, so a kick can first cause a spike one step later.
        can_spike = (v > params.v_thresh_mV) & ~frozen
        spiking = np.flatnonzero(can_spike)

        # Synaptic kick delivery ('synapses' slot: after thresholds, before
        # resets). Measured reference semantics
        # (scripts/probe_brian2_refractory.py): a kick landing on a
        # refractory target is DROPPED - g stays pinned at its reset value
        # (0) for the whole refractory window, and accumulation restarts
        # from zero when the window closes.
        if ring_targets[slot].size:
            idx = ring_targets[slot]
            live = idx[~frozen[idx]]
            if live.size:
                np.add.at(g, live, ring[slot][live])
            ring[slot] = 0.0
            ring_targets[slot] = np.empty(0, dtype=int)

        # Poisson kicks for stimulated neurons (PoissonInput also runs in
        # the 'synapses' slot; measured in
        # scripts/probe_poisson_input_census.py): an event spikes the
        # target one step later, and an event drawn in a step where the
        # neuron already spiked is destroyed by the reset below. At
        # 1000 Hz this makes the effective drive ~0.9x nominal, matching
        # the reference's observed ~907 Hz driven rate.
        if stim_set.size and n_steps:
            fires = rng.random(stim_set.size) < poisson_p
            if fires.any():
                v[stim_set[fires]] += poisson_kick

        # Reset ('resets' slot): runs AFTER kick delivery, destroying any
        # kick that landed on a spiking neuron this step.
        if spiking.size:
            for i in spiking:
                spike_times[node_ids[i]].append(t)
                last_spike[i] = t
            v[spiking] = params.v_reset_mV
            g[spiking] = 0.0
            # Schedule delayed kicks to postsynaptic targets.
            for i in spiking:
                row = weights_csr.getrow(i)
                targets = row.nonzero()[1]
                if targets.size:
                    slot_next = (step + delay_steps) % ring_len
                    np.add.at(ring[slot_next], targets, row.toarray().ravel()[targets])
                    existing = ring_targets[slot_next]
                    ring_targets[slot_next] = np.union1d(existing, targets)

    return LIFRun(
        node_ids=node_ids,
        spike_times={k: vals for k, vals in spike_times.items() if vals},
        v_final_mV=v,
        n_spikes=sum(len(vals) for vals in spike_times.values()),
        duration_ms=duration_ms,
        params=params,
    )
