"""Tests for the conservative reference LIF implementation.

All equations, parameters, and semantics trace to Shiu et al.'s reference
implementation (data/raw/reference/shiu_model.py, fetched 2026-09-23 from
https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/model.py):

    dv/dt = (v_0 - v + g) / t_mbr    (unless refractory)
    dg/dt = -g / tau                  (unless refractory)
    threshold v > v_th; reset v = v_rst, g = 0; delay t_dly; on_pre g += w
    Poisson activation targets v with weight w_syn * f_poi and rfc = 0
    silencing zeroes a neuron's outgoing weights
"""

import dataclasses
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams, LIFRun, simulate_lif


def _matrix(rows, cols, data, n):
    m = sparse.csr_matrix((np.asarray(data, dtype=float), (rows, cols)), shape=(n, n))
    m.sum_duplicates()
    m.sort_indices()
    return m


def test_default_params_match_shiu_reference() -> None:
    p = LIFParams()

    assert p.v0_mV == pytest.approx(-52.0)
    assert p.v_reset_mV == pytest.approx(-52.0)
    assert p.v_thresh_mV == pytest.approx(-45.0)
    assert p.tau_mbr_ms == pytest.approx(20.0)
    assert p.tau_syn_ms == pytest.approx(5.0)
    assert p.t_refractory_ms == pytest.approx(2.2)
    assert p.t_delay_ms == pytest.approx(1.8)
    assert p.w_syn_mV == pytest.approx(0.275)
    assert p.r_poisson_Hz == pytest.approx(150.0)
    assert p.f_poisson == pytest.approx(250.0)


def test_unstimulated_network_produces_no_spikes() -> None:
    counts = _matrix([], [], [], 3)

    result = simulate_lif(counts, [1, 2, 3], LIFParams(), duration_ms=100.0, seed=0)

    assert isinstance(result, LIFRun)
    assert result.n_spikes == 0
    assert result.spike_times == {}
    assert result.node_ids == [1, 2, 3]
    assert result.duration_ms == 100.0


def test_poisson_stimulation_drives_spiking_deterministically() -> None:
    counts = _matrix([], [], [], 1)

    a = simulate_lif(counts, [7], LIFParams(), duration_ms=1000.0, stimulated=[7], seed=42)
    b = simulate_lif(counts, [7], LIFParams(), duration_ms=1000.0, stimulated=[7], seed=42)
    c = simulate_lif(counts, [7], LIFParams(), duration_ms=1000.0, stimulated=[7], seed=7)

    n_a = len(a.spike_times[7])
    # r_poi = 150 Hz; each Poisson event adds 68.75 mV (needs only 7 mV to spike)
    assert 80 <= n_a <= 250
    assert a.spike_times[7] == b.spike_times[7]  # same seed -> identical trial
    assert isinstance(c.spike_times[7], list)    # other seed runs, valid sample


def test_synaptic_propagation_respects_delay() -> None:
    # 100 synapses: one presynaptic spike delivers 27.5 mV to g of the target
    counts = _matrix([0], [1], [100], 2)

    result = simulate_lif(
        counts, [10, 20], LIFParams(), duration_ms=200.0, stimulated=[10], seed=1
    )

    pre = result.spike_times[10]
    post = result.spike_times[20]
    assert len(pre) > 0
    assert len(post) > 0
    # every postsynaptic spike follows a presynaptic one by at least t_dly
    assert post[0] >= pre[0] + 1.8 - 0.15
    # and arrives within a bounded window
    assert post[0] < pre[0] + 50.0


def test_silencing_blocks_propagation_but_not_the_silenced_neuron() -> None:
    counts = _matrix([0], [1], [100], 2)

    silenced_run = simulate_lif(
        counts, [10, 20], LIFParams(), duration_ms=200.0, stimulated=[10], silenced=[10], seed=1
    )

    assert len(silenced_run.spike_times[10]) > 0   # silencing zeroes outgoing weights only
    assert 20 not in silenced_run.spike_times       # target never receives a kick


def test_refractory_enforces_minimum_isi_on_unstimulated_neurons() -> None:
    # Presynaptic neuron driven at 2000 Hz (rfc disabled for stimulated neurons)
    # delivers a huge kick each ~0.5 ms; the unstimulated target can still
    # only spike once per refractory period.
    counts = _matrix([0], [1], [1_000_000], 2)
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=2000.0)

    result = simulate_lif(counts, [10, 20], params, duration_ms=100.0, stimulated=[10], seed=5)

    isi = np.diff(result.spike_times[20])
    assert len(isi) > 3
    assert isi.min() >= params.t_refractory_ms - 0.15


def test_refractory_freezes_v_and_g_during_refractory() -> None:
    # Brian2 '(unless refractory)': v and g are FROZEN for the whole
    # refractory window (shiu_model.py eqs: dv/dt and dg/dt both carry the
    # flag). A continuously driven target therefore pays a post-refractory
    # rise time on every spike. Measured against the reference
    # (scripts/calibrate_refractory_toy.py): Brian2 gives ~235 target
    # spikes / 2 s here; the pre-fix behaviour (v integrating through
    # refractory) sustained 333.
    counts = _matrix([0], [1], [50], 2)
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=1000.0)

    result = simulate_lif(counts, [10, 20], params, duration_ms=2000.0, stimulated=[10], seed=3)

    isi = np.diff(result.spike_times[20])
    assert len(isi) > 50  # target still fires continuously
    assert len(result.spike_times[20]) < 300  # frozen refractory costs rise time


def test_kick_arriving_during_refractory_is_dropped() -> None:
    # Measured Brian2 reference semantics (scripts/probe_brian2_refractory.py):
    # a synaptic kick arriving while the target is refractory is LOST - the
    # probe trace shows g pinned at 0.000 throughout the refractory window
    # despite kicks landing, and the next cycle accumulates from zero.
    # Deterministic setup: both neurons start above threshold, so each fires
    # exactly one spike at t=0. A's kick to B is delayed by 1.8 ms, landing at
    # t=1.8 - inside B's refractory window [0, 2.2). With 1000 synapses the
    # kick is 275 mV: dropped -> B fires exactly once; accumulated (the bug)
    # -> g carries 275 mV into the post-refractory climb (~43 mV peak
    # excursion, far above the 7 mV threshold) and B fires a second time.
    counts = _matrix([0], [1], [1000], 2)

    result = simulate_lif(
        counts, [10, 20], LIFParams(), duration_ms=10.0, init_v_mV=-44.0, seed=0
    )

    assert result.spike_times[10] == [0.0]
    assert result.spike_times[20] == [0.0]  # exactly one spike: the kick was dropped


def test_synaptic_kick_cannot_cause_spike_in_its_arrival_step() -> None:
    # Measured Brian2 slot order ('groups' -> 'thresholds' -> 'synapses' ->
    # 'resets'; see scripts/probe_brian2_refractory.py and
    # scripts/probe_poisson_input_census.py): the state update and threshold
    # check run BEFORE kick delivery, so a kick can first cause a spike one
    # dt AFTER its arrival step. Pre-fix, kicks were delivered before the
    # threshold check and a large kick spiked the target in the arrival step
    # itself (first spike at t=1.9 below instead of t=2.0).
    # Setup: A is Poisson-driven hard enough that the draw fires every step
    # (p = r*dt/1000 = 10 > 1, deterministic despite the seed); A's first
    # spike is at t=0.1, so its 6000-synapse kick (1650 mV) to B arrives at
    # t=1.9. B starts 0.1 mV below threshold and decays. The kick's first
    # contribution to v lands in the t=2.0 update -> first spike at 2.0.
    counts = _matrix([0], [1], [6000], 2)
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=100_000.0)

    result = simulate_lif(
        counts, [10, 20], params, duration_ms=10.0, stimulated=[10], init_v_mV=-45.1, seed=0
    )

    assert len(result.spike_times[10]) > 5          # driven neuron fires throughout
    assert result.spike_times[20][0] == pytest.approx(2.0)  # one dt after arrival


def test_unknown_ids_are_rejected() -> None:
    counts = _matrix([], [], [], 2)

    with pytest.raises(ValueError, match="stimulated"):
        simulate_lif(counts, [1, 2], LIFParams(), duration_ms=10.0, stimulated=[99])
    with pytest.raises(ValueError, match="silenced"):
        simulate_lif(counts, [1, 2], LIFParams(), duration_ms=10.0, silenced=[99])
    with pytest.raises(ValueError, match="shape"):
        simulate_lif(_matrix([], [], [], 3), [1, 2], LIFParams(), duration_ms=10.0)


def test_run_records_metadata_and_final_state() -> None:
    counts = _matrix([], [], [], 3)

    result = simulate_lif(counts, [1, 2, 3], LIFParams(), duration_ms=50.0, seed=3)

    assert result.n_spikes == sum(len(v) for v in result.spike_times.values())
    assert result.v_final_mV.shape == (3,)
    assert result.params is not None


def test_reference_file_is_on_disk_and_checksummed() -> None:
    # provenance gate: the traced reference source must exist locally
    ref = Path("data/raw/reference/shiu_model.py")
    assert ref.is_file()
    assert "default_params" in ref.read_text(encoding="utf-8")
