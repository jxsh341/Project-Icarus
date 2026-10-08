"""FLY-LEARN-001 WP2: training-loop driver.

A training *run* = a sequence of trials under one plasticity config.
Each trial:
  1. build the stimulus schedule (cue population + innate drive
     co-presentation window, per the frozen task protocol)
  2. simulate one trial on the CURRENT weight matrix
  3. observe coincidences for the plasticity rule (rate-form Hebbian
     over the cue's downstream 1-hop neighborhood)
  4. apply the rule -> new weight matrix (carried across trials)
  5. checkpoint the full run state (config, trial index, weight
     matrix hash + diff summary, readout, guard status)

The driver is cue-agnostic: populations arrive as bodyId lists.
The run stops early if the PlasticityGuard fires (D6 thresholds).

L0 (plasticity disabled) is the identity: a run with plasticity=None
must produce trial sequences identical to Phase 1 dynamics.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, StabilityThresholds


@dataclasses.dataclass(frozen=True)
class TrialSpec:
    """One trial's full stimulus specification (explicit, no defaults)."""

    trial: int
    seed: int
    cue_body_ids: tuple[int, ...]        # the learned-cue population
    drive_body_ids: tuple[int, ...]       # innate drive co-present (e.g. sugar)
    drive2_body_ids: tuple[int, ...]      # second innate drive (e.g. bitter), if any
    r_cue_hz: float                       # cue drive rate
    r_drive_hz: float                      # primary drive rate
    r_drive2_hz: float                    # second drive rate (0 = absent)
    gate_body_ids: tuple[int, ...] = ()   # L3 gate population (e.g. gate-DA)
    r_gate_hz: float = 0.0                 # gate drive rate (0 = absent)
    window_hops: int = 1                  # L1 observation window (frozen=1)
    duration_ms: float = 1000.0
    is_probe: bool = False                # probe trials: no plasticity applied


@dataclasses.dataclass(frozen=True)
class RunState:
    """Everything needed to resume or audit a training run."""

    run_id: str
    trial_index: int
    n_trials: int
    config_hash: str
    weight_hash: str
    history: tuple  # of per-trial dicts (readout + guard + diff summary)


def weight_matrix_hash(w: sparse.csr_matrix) -> str:
    m = w.tocsr()
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(m.indptr).tobytes())
    h.update(np.ascontiguousarray(m.indices).tobytes())
    h.update(np.ascontiguousarray(m.data).tobytes())
    return h.hexdigest()[:16]


class TrainingRun:
    """Checkpointed, guard-protected sequence of trials under plasticity."""

    def __init__(
        self,
        matrix: sparse.csr_matrix,
        node_ids: Sequence[int],
        plasticity: Optional[HebbianRule],
        guard: PlasticityGuard,
        readout_body_id: int,
        run_id: str,
        checkpoint_path: Path,
        lif_params: Optional[LIFParams] = None,
    ) -> None:
        self.matrix = matrix.tocsr()
        self.node_ids = list(node_ids)
        self.plasticity = plasticity
        # window_hops lives ONLY on TrialSpec (explicit-everything
        # discipline): every trial declares its own observation window.
        self.guard = guard
        self.readout_body_id = readout_body_id
        self.run_id = run_id
        self.checkpoint_path = checkpoint_path
        self.lif_params = lif_params if lif_params is not None else LIFParams()
        self.trial_index = 0
        self.history: list[dict] = []
        self.stopped_reason: Optional[str] = None

    # -- one trial ------------------------------------------------------------

    def run_trial(self, spec: TrialSpec) -> dict:
        # Stimulus wiring, EXPLICIT per skill rule: the PRIMARY Poisson
        # drive (r_poisson_Hz) goes to the cue; the SECOND population
        # (stimulated2 / r_poisson2_Hz) is the innate drive (sugar).
        # r_cue_hz=0 or r_drive_hz=0 disables the respective population.
        # THIRD population (stimulated3): the L3 gate (e.g. gate-DA),
        # default-off (empty ids / rate 0 = no-op, bit-identical).
        params = dataclasses.replace(self.lif_params, r_poisson_Hz=spec.r_cue_hz)
        t0 = time.time()
        result = simulate_lif(
            self.matrix, self.node_ids, params,
            duration_ms=spec.duration_ms,
            stimulated=list(spec.cue_body_ids) if spec.r_cue_hz > 0 else None,
            stimulated2=(list(spec.drive_body_ids) if spec.r_drive_hz > 0
                         and spec.drive_body_ids else None),
            r_poisson2_Hz=spec.r_drive_hz if spec.r_drive_hz > 0 else None,
            stimulated3=(list(spec.gate_body_ids) if spec.r_gate_hz > 0
                         and spec.gate_body_ids else None),
            r_poisson3_Hz=spec.r_gate_hz if spec.r_gate_hz > 0 else None,
            seed=spec.seed,
        )
        readout_hz = len(result.spike_times.get(self.readout_body_id, []))
        rec = {
            "run_id": self.run_id,
            "trial": spec.trial,
            "seed": spec.seed,
            "readout_hz": readout_hz,
            "total_spikes": result.n_spikes,
            "n_spiking": len(result.spike_times),
            "wall_s": round(time.time() - t0, 1),
            "weight_hash": weight_matrix_hash(self.matrix),
            "is_probe": spec.is_probe,
        }

        if self.plasticity is not None and not spec.is_probe:
            # rate-form Hebbian observation, then apply. window_hops=1 is
            # the FROZEN L1 definition (cue-incident edges only).
            # window_hops=2 is the registered mechanism-experiment arm:
            # it ADDS cue-gated leg-2 eligibility (postsynaptic neuron
            # must itself be a cue 1-hop target - not open-ended 2-hop
            # eligibility) while leaving leg-1 semantics unchanged.
            self._observe_coincidences(spec, result)
            new_matrix = self.plasticity.apply(self.matrix)
            rec["weight_diff"] = self._diff_summary(self.matrix, new_matrix)
            self.matrix = new_matrix

        # stability guard
        fired = self.guard.check(trial_spikes=result.n_spikes)
        if fired is not None:
            self.stopped_reason = fired
            rec["guard_fired"] = fired
        self.history.append(rec)
        self.trial_index = spec.trial + 1
        return rec

    def _observe_coincidences(self, spec: TrialSpec, result) -> None:
        """Observe (cue neuron -> its 1-hop targets) coincidences.

        Rate-form Hebbian: for each cue neuron that spiked, for each of
        its 1-hop targets that spiked, observe eta * x * y with x, y
        the per-trial firing rates (Hz) of pre and post.
        """
        idx_of = {n: i for i, n in enumerate(self.node_ids)}
        rates = {n: len(ts) for n, ts in result.spike_times.items()}
        window = spec.window_hops if spec.window_hops in (1, 2) else 1
        for cue_id in spec.cue_body_ids:
            if cue_id not in idx_of:
                continue
            ci = idx_of[cue_id]
            x_hz = rates.get(cue_id, 0)
            if x_hz == 0:
                continue
            row = self.matrix.getrow(ci)
            leg1_targets = set(row.indices.tolist())
            # leg-1: cue -> its 1-hop targets
            for tgt_idx in leg1_targets:
                tgt = self.node_ids[tgt_idx]
                y_hz = rates.get(tgt, 0)
                if y_hz == 0:
                    continue
                self.plasticity.observe_rate_pair(ci, tgt_idx, self.matrix,
                                                  x_hz=x_hz, y_hz=y_hz)
            # leg-2 (window_hops=2, mechanism-experiment arm only):
            # edge (m -> n) with m a cue 1-hop target and n a 1-hop
            # target of m; potentiation gate is cue activity x_m's own
            # co-firing with n (cue-gated leg-2, NOT open eligibility)
            if window == 2:
                for m_idx in leg1_targets:
                    m_row = self.matrix.getrow(m_idx)
                    for n_idx in m_row.indices:
                        n = self.node_ids[n_idx]
                        y_hz = rates.get(n, 0)
                        if y_hz == 0:
                            continue
                        # pre rate for leg-2 is the CUE's rate (the
                        # eligibility source), post rate is n's rate
                        self.plasticity.observe_rate_pair(
                            m_idx, n_idx, self.matrix,
                            x_hz=x_hz, y_hz=y_hz)

    def _diff_summary(self, old: sparse.csr_matrix, new: sparse.csr_matrix) -> dict:
        if old.shape != new.shape:
            return {"shape_changed": True}
        d = (new - old).tocoo()
        n_changed = int(np.count_nonzero(d.data))
        return {
            "n_edges_changed": n_changed,
            "max_abs_delta": float(np.max(np.abs(d.data))) if n_changed else 0.0,
            "total_delta": float(d.data.sum()) if n_changed else 0.0,
        }

    # -- checkpointing ----------------------------------------------------------

    def save(self) -> None:
        blob = {
            "run_id": self.run_id,
            "trial_index": self.trial_index,
            "n_history": len(self.history),
            "config_hash": (self.plasticity.config.content_hash()
                           if self.plasticity else None),
            "weight_hash": weight_matrix_hash(self.matrix),
            "stopped_reason": self.stopped_reason,
        }
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)
        (self.checkpoint_path / "run_state.json").write_text(
            json.dumps(blob, indent=2), encoding="utf-8")
        # full history JSONL append
        hist_path = self.checkpoint_path / "history.jsonl"
        if not hist_path.exists():
            hist_path.write_text("", encoding="utf-8")
        seen = sum(1 for _ in hist_path.open(encoding="utf-8"))
        for rec in self.history[seen:]:
            with hist_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        # weight matrix snapshot (only when plasticity active)
        if self.plasticity is not None:
            wpath = self.checkpoint_path / f"weights_trial_{self.trial_index:04d}.npz"
            sparse.save_npz(wpath, self.matrix)

    @classmethod
    def load(cls, checkpoint_path: Path, matrix: sparse.csr_matrix,
             node_ids: Sequence[int], plasticity: Optional[HebbianRule],
             guard: PlasticityGuard, readout_body_id: int) -> "TrainingRun":
        blob = json.loads((checkpoint_path / "run_state.json").read_text(encoding="utf-8"))
        hist_lines = (checkpoint_path / "history.jsonl").read_text(encoding="utf-8").splitlines()
        history = [json.loads(l) for l in hist_lines if l.strip()]
        run = cls(matrix, node_ids, plasticity, guard, readout_body_id,
                  blob["run_id"], checkpoint_path)
        run.trial_index = blob["trial_index"]
        run.history = history
        run.stopped_reason = blob.get("stopped_reason")
        if plasticity is not None and blob.get("weight_hash"):
            wfiles = sorted(checkpoint_path.glob("weights_trial_*.npz"))
            if wfiles:
                run.matrix = sparse.load_npz(wfiles[-1]).tocsr()
                actual = weight_matrix_hash(run.matrix)
                if actual != blob["weight_hash"]:
                    raise RuntimeError(
                        f"checkpoint weight hash mismatch: {actual} != {blob['weight_hash']}"
                    )
        return run
