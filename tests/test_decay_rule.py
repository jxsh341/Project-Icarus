"""Tests: DecayHebbianRule (WP-L3c) - eligibility-decay variant of the frozen L1 rule.

D-4: consolidation re-scoped to the rule - per-trial eligibility decay
lambda (CALIBRATED band [0.70, 0.807], gamma pinned = 1). The variant
multiplies each edge's update by its accumulated decaying trace
instead of the raw per-trial contrast:

    e <- lambda * e + c_t          (per-edge trace; c_t = this trial's contrast)
    dw  = eta * e                  (update from the TRACE, not the raw contrast)

vs frozen L1's dw = eta * c_t. This changes the learning-rate
profile over trials (early trials count most; the trace plateaus at
c/(1-lambda)) WITHOUT changing single-trial semantics at e=0 - the
first trial's update is identical to L1's.

Pinned here:
1. First-trial equivalence: with e=0, one trial produces the SAME
   weight change as the frozen L1 rule (same eta, same contrast).
2. Decay: repeated identical trials produce sub-linear accumulated
   growth approaching the c/(1-lambda) plateau (not linear growth).
3. gamma is NOT a parameter of this rule (pinned = 1 by registry).
"""

import dataclasses
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec


_N = 6
_ROWS = [0, 1, 2, 3, 4]
_COLS = [5, 5, 5, 5, 5]
_DATA = [10.0, 10.0, 10.0, -10.0, 10.0]
READOUT = 105


def _matrix():
    m = sparse.csr_matrix((_DATA, (_ROWS, _COLS)), shape=(_N, _N))
    m.sort_indices()
    return m


def _nodes():
    return list(range(100, 100 + _N))


def _rule():
    return HebbianRule(PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6))


def _guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=10_000_000, spontaneous_rate_hz=10_000_000.0,
        inh_weight_drift_frac=10_000_000.0))


def _spec(trial=0, seed=100):
    return TrialSpec(trial=trial, seed=seed, cue_body_ids=(100,), drive_body_ids=(101,),
                    drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=150.0, r_drive2_hz=0.0)


def test_first_trial_equivalence_with_l1(tmp_path):
    """e=0 start: the decay rule's first update == frozen L1's."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from phase3_decay_rule import DecayHebbianRule

    a = TrainingRun(_matrix(), _nodes(), _rule(), _guard(), READOUT,
                    "a", Path(tmp_path) / "a", lif_params=LIFParams())
    b = TrainingRun(_matrix(), _nodes(), DecayHebbianRule(_rule(), lam=0.75),
                    _guard(), READOUT, "b", Path(tmp_path) / "b", lif_params=LIFParams())
    ra = a.run_trial(_spec())
    rb = b.run_trial(_spec())
    assert ra["weight_diff"] == rb["weight_diff"]


def test_decay_sublinear_accumulation(tmp_path):
    """Sub-linearity pinned directly on the rule: identical contrasts
    c applied for T trials -> cumulative dw = eta*c*(1-lam^T)/(1-lam),
    strictly less than T * eta * c (the L1 growth), with increments
    converging to the plateau. Uses the rule API directly - the toy
    circuit's weights run away under feedback and confound rates."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from phase3_decay_rule import DecayHebbianRule
    from scipy import sparse as sp

    lam = 0.5
    eta = 1e-4
    cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=1e9)
    rule = DecayHebbianRule(HebbianRule(cfg), lam=lam)
    m = sp.csr_matrix(([10.0], ([0], [1])), shape=(4, 4))
    m.sort_indices()

    increments = []
    for t in range(8):
        before = m[0, 1]
        rule.observe_rate_pair(0, 1, m, x_hz=100.0, y_hz=100.0)
        m = rule.apply(m)
        increments.append(m[0, 1] - before)

    c = 100.0 * 100.0
    expected_total = eta * c * (1 - lam**8) / (1 - lam)
    total = sum(increments)
    # sub-linear: strictly less than L1's 8 * eta * c
    assert total < 8 * eta * c
    assert abs(total - expected_total) < 1e-6  # exact geometric closed form
    # per-trial increments are AGE-DISCOUNTED contrasts: eta * lam^(n-1) * c
    for n_1, got in enumerate(increments):
        exp = eta * (lam ** n_1) * c
        assert abs(got - exp) < 1e-6
