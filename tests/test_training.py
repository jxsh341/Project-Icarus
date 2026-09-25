"""Tests for the WP2 training-loop driver (fly/training.py).

Cue-agnostic driver semantics that must hold regardless of which cue
population is eventually frozen:
  1. L0 identity: plasticity=None reproduces Phase 1 dynamics exactly
     (same seeds -> same readout as bare simulate_lif).
  2. L1 changes weights only via observed coincidences; probe trials
     never touch weights.
  3. Guard firing halts the run and the stop reason survives resume.
  4. Checkpoint/resume is lossless: a resumed run reproduces the
     original run's per-trial readouts bit-for-bit.
  5. The coincidence observation is structural-gated (existing edges
     only), matching HebbianRule's contract.

Runs on a small synthetic matrix to keep tests fast (real-closure
integration is covered by the probe scripts, not unit tests).
"""

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec, weight_matrix_hash

# 6-neuron toy circuit: 0,1 driven; 2,3 interneurons; 4 readout; 5 unconnected
# edges: 0->2 (+), 1->3 (+), 2->4 (+), 3->4 (-), 0->1 (+), 4->5 (+)
_ROWS = [0, 1, 2, 3, 0, 4]
_COLS = [2, 3, 4, 4, 1, 5]
_DATA = [20.0, 20.0, 20.0, -20.0, 10.0, 10.0]
N_NODES = 6
READOUT = 4


def _matrix():
    m = sparse.csr_matrix((_DATA, (_ROWS, _COLS)), shape=(N_NODES, N_NODES))
    m.sort_indices()
    return m


def _guard(permissive=True):
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=10_000_000 if permissive else 10,
        spontaneous_rate_hz=10_000_000.0,
        inh_weight_drift_frac=1_000_000.0,
    ))


def _run(tmp_path, plasticity, guard=None, matrix=None, lif_params=None):
    return TrainingRun(
        matrix=matrix if matrix is not None else _matrix(),
        node_ids=list(range(N_NODES)),
        plasticity=plasticity,
        guard=guard if guard is not None else _guard(),
        readout_body_id=READOUT,
        run_id="test-run",
        checkpoint_path=tmp_path / "ckpt",
        lif_params=lif_params,
    )


def _spec(trial=0, seed=100, cue=(0,), drive=(1,), r_drive=150.0, probe=False):
    return TrialSpec(trial=trial, seed=seed, cue_body_ids=tuple(cue),
                     drive_body_ids=tuple(drive), drive2_body_ids=(),
                     r_cue_hz=200.0, r_drive_hz=r_drive, r_drive2_hz=0.0,
                     is_probe=probe)


# ---- L0 identity -----------------------------------------------------------

def test_l0_identity_matches_bare_simulation(tmp_path) -> None:
    """plasticity=None must reproduce bare simulate_lif exactly."""
    m = _matrix()
    nodes = list(range(N_NODES))
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    run = _run(tmp_path, plasticity=None, lif_params=params)
    for i in range(3):
        spec = _spec(trial=i, seed=100 + i)
        rec = run.run_trial(spec)
        bare = simulate_lif(m, nodes, params, duration_ms=1000.0,
                            stimulated=list(spec.cue_body_ids),
                            stimulated2=list(spec.drive_body_ids),
                            r_poisson2_Hz=spec.r_drive_hz, seed=spec.seed)
        assert rec["readout_hz"] == len(bare.spike_times.get(READOUT, []))
        assert rec["total_spikes"] == bare.n_spikes
        assert rec["weight_hash"] == weight_matrix_hash(m)  # never changes


# ---- L1: coincidences drive change; probes never touch weights ------------------

def test_l1_changes_weights_via_coincidences(tmp_path) -> None:
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    h0 = weight_matrix_hash(run.matrix)
    spec = _spec(trial=0, seed=100)
    rec = run.run_trial(spec)
    assert rec["weight_diff"]["n_edges_changed"] > 0
    assert weight_matrix_hash(run.matrix) != h0


def test_probe_trials_do_not_apply_plasticity(tmp_path) -> None:
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    h0 = weight_matrix_hash(run.matrix)
    rec = run.run_trial(_spec(trial=0, seed=100, probe=True))
    assert "weight_diff" not in rec
    assert weight_matrix_hash(run.matrix) == h0
    # guard must still watch probe trials
    tight = PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=5, spontaneous_rate_hz=1e9, inh_weight_drift_frac=1e9))
    run2 = _run(tmp_path, plasticity=HebbianRule(cfg), guard=tight)
    run2.run_trial(_spec(trial=0, seed=100, probe=True))
    assert run2.stopped_reason is not None


# ---- guard halt + resume ---------------------------------------------------

def test_guard_halts_and_reason_survives_resume(tmp_path) -> None:
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    tight = PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=5, spontaneous_rate_hz=1e9, inh_weight_drift_frac=1e9))
    run = _run(tmp_path, plasticity=HebbianRule(cfg), guard=tight)
    run.run_trial(_spec(trial=0, seed=100))
    assert run.stopped_reason is not None
    run.save()
    loaded = TrainingRun.load(tmp_path / "ckpt", _matrix(), list(range(N_NODES)),
                              HebbianRule(cfg), _guard(), READOUT)
    assert loaded.stopped_reason == run.stopped_reason


def test_checkpoint_resume_is_lossless(tmp_path) -> None:
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    nodes = list(range(N_NODES))
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    recs = [run.run_trial(_spec(trial=i, seed=100 + i)) for i in range(3)]
    run.save()

    loaded = TrainingRun.load(tmp_path / "ckpt", _matrix(), nodes,
                              HebbianRule(cfg), _guard(), READOUT)
    assert loaded.trial_index == 3
    assert [r["readout_hz"] for r in loaded.history] == [r["readout_hz"] for r in recs]
    assert weight_matrix_hash(loaded.matrix) == weight_matrix_hash(run.matrix)
    # continuing after resume reproduces the un-resumed continuation
    rec_loaded = loaded.run_trial(_spec(trial=3, seed=103))
    run.run_trial(_spec(trial=3, seed=103))
    assert rec_loaded["readout_hz"] == run.history[-1]["readout_hz"]


# ---- structural gating --------------------------------------------------------

def test_coincidence_observation_is_structural(tmp_path) -> None:
    """A coincidence between neurons with NO structural edge must not
    create one."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    spec = _spec(trial=0, seed=100, cue=(0,), drive=(5,))  # 0->5 has no edge
    rec = run.run_trial(spec)
    # cue neuron 0's 1-hop targets are {2, 1}; nothing else may change
    d = (run.matrix - _matrix()).tocoo()
    for r, c in zip(d.row, d.col):
        if d.data[list(zip(d.row, d.col)).index((r, c))] != 0:
            assert (r, c) in {(0, 2), (0, 1), (2, 4), (4, 5)}


def test_rates_are_per_trial_and_cue_gated(tmp_path) -> None:
    """No coincidence is observed when the cue population is silent."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    h0 = weight_matrix_hash(run.matrix)
    # drive 150 Hz hits neuron 1, but cue neuron 0 is NOT driven in this spec
    spec = TrialSpec(trial=0, seed=100, cue_body_ids=(0,), drive_body_ids=(1,),
                    drive2_body_ids=(), r_cue_hz=0.0, r_drive_hz=150.0, r_drive2_hz=0.0)
    rec = run.run_trial(spec)
    assert rec.get("weight_diff", {}).get("n_edges_changed", 0) == 0
    assert weight_matrix_hash(run.matrix) == h0


# ---- state persistence across trials (Stage B v1 bug class) ----------------

def test_state_persists_across_trials(tmp_path) -> None:
    """Constructing the run inside the trial loop (the v1 bug) resets all
    accumulation. A single run across 3 trials must accumulate: the
    weight hash changes every trial and the cue-incident edge grows."""
    cfg = PlasticityConfig(eta=0.1, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    hashes = [weight_matrix_hash(run.matrix)]
    w_edge = [run.matrix[0, 2]]
    for t in range(3):
        run.run_trial(_spec(trial=t, seed=100 + t))
        hashes.append(weight_matrix_hash(run.matrix))
        w_edge.append(run.matrix[0, 2])
    assert len(set(hashes)) == 4          # every trial leaves a trace
    assert all(b > a for a, b in zip(w_edge, w_edge[1:]))  # monotone growth


# ---- 2-hop observation window (mechanism experiment support) ----------------

def test_window_1_default_leaves_second_leg_alone(tmp_path) -> None:
    """Frozen L1 semantics: only cue-incident (1-hop) edges potentiate.
    The chain edge 2->4 must NOT change when only the cue is the
    plasticity source, even though 2 and 4 both fire."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    w24_before = run.matrix[2, 4]
    # cue=(0,) driven; drive=(4,) driven directly -> 2 fires via 0->2
    run.run_trial(_spec(trial=0, seed=100, cue=(0,), drive=(4,)))
    assert run.matrix[0, 2] > 10.0        # first leg potentiated
    assert run.matrix[2, 4] == w24_before  # second leg untouched (window=1)


def test_window_2_potentiates_second_leg(tmp_path) -> None:
    """window_hops=2 adds cue-gated leg-2 eligibility: edge (m->n) where
    m is a cue's 1-hop target and n is m's 1-hop target potentiates by
    eta * x_cue * y_n when cue and n co-fire."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    run = _run(tmp_path, plasticity=HebbianRule(cfg))
    w24_before = run.matrix[2, 4]
    spec = dataclasses.replace(_spec(trial=0, seed=100, cue=(0,), drive=(4,)),
                               window_hops=2)
    run.run_trial(spec)
    assert run.matrix[0, 2] > 10.0        # first leg still potentiated
    assert run.matrix[2, 4] > w24_before  # second leg NOW potentiated
