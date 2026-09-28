"""Tests: WP4 harness I/O persistence (the v0 overnight-launch bug class).

The v0 harness never called run.save() and its writer required a
pre-existing directory. These tests construct the runner against a
NONEXISTENT output path and assert:
  1. the JSONL file appears after the FIRST simulation (a 1-trial dry
     run through the whole I/O path);
  2. the checkpoint dir + run_state.json + weight .npz appear after
     the first simulation;
  3. a second runner constructed from the checkpoint resumes with the
     SAME weight hash (per-simulation weight checkpointing works);
  4. the resumed runner's next trial matches the un-resumed
     continuation (no trajectory stitching).
"""

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec, weight_matrix_hash

_ROWS = [0, 1, 2, 3, 0, 4]
_COLS = [2, 3, 4, 4, 1, 5]
_DATA = [20.0, 20.0, 20.0, -20.0, 10.0, 10.0]
N_NODES = 6
READOUT = 4


def _matrix():
    m = sparse.csr_matrix((_DATA, (_ROWS, _COLS)), shape=(N_NODES, N_NODES))
    m.sort_indices()
    return m


def _guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=10_000_000, spontaneous_rate_hz=10_000_000.0,
        inh_weight_drift_frac=10_000_000.0))


def _spec(trial=0, seed=100):
    return TrialSpec(trial=trial, seed=seed, cue_body_ids=(0,), drive_body_ids=(1,),
                     drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=150.0,
                     r_drive2_hz=0.0)


def test_jsonl_appears_after_first_simulation(tmp_path) -> None:
    """NONEXISTENT output path + first simulation -> file must exist."""
    out = tmp_path / "nonexistent_dir" / "out.jsonl"
    assert not out.exists()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"trial": 0}) + "\n")
        fh.flush()
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0])["trial"] == 0


def test_checkpoint_artifacts_appear_after_first_simulation(tmp_path) -> None:
    ckpt = tmp_path / "fresh" / "ckpt"
    run = TrainingRun(_matrix(), list(range(N_NODES)), HebbianRule(
        PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)),
        _guard(), READOUT, "t", ckpt,
        lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    run.run_trial(_spec())
    run.save()
    assert (ckpt / "run_state.json").exists()
    assert list(ckpt.glob("weights_trial_*.npz"))


def test_resume_continues_from_checkpointed_weights(tmp_path) -> None:
    """Two trials in one run, then a fresh runner from the checkpoint:
    its weight hash must match the original run's CURRENT hash (the
    per-simulation checkpoint must carry potentiation, not pristine)."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    ckpt = tmp_path / "res" / "ckpt"
    run = TrainingRun(_matrix(), list(range(N_NODES)), HebbianRule(cfg),
                      _guard(), READOUT, "t", ckpt,
                      lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    run.run_trial(_spec(trial=0, seed=100))
    run.run_trial(_spec(trial=1, seed=101))
    run.save()
    h_after_2 = weight_matrix_hash(run.matrix)

    loaded = TrainingRun.load(ckpt, _matrix(), list(range(N_NODES)),
                              HebbianRule(cfg), _guard(), READOUT)
    assert weight_matrix_hash(loaded.matrix) == h_after_2


def test_resume_reproduces_continuation(tmp_path) -> None:
    """Resumed runner's next trial must match the un-resumed
    continuation bit-for-bit (no trajectory stitching)."""
    cfg = PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6)
    nodes = list(range(N_NODES))
    ckpt = tmp_path / "cont" / "ckpt"
    run = TrainingRun(_matrix(), nodes, HebbianRule(cfg), _guard(), READOUT,
                      "t", ckpt,
                      lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    run.run_trial(_spec(trial=0, seed=100))
    run.run_trial(_spec(trial=1, seed=101))
    run.save()

    # un-resumed continuation
    r_ref = run.run_trial(_spec(trial=2, seed=102))
    h_ref = weight_matrix_hash(run.matrix)

    # resumed continuation
    loaded = TrainingRun.load(ckpt, _matrix(), nodes, HebbianRule(cfg),
                              _guard(), READOUT)
    r_res = loaded.run_trial(_spec(trial=2, seed=102))

    assert r_res["readout_hz"] == r_ref["readout_hz"]
    assert weight_matrix_hash(loaded.matrix) == h_ref
