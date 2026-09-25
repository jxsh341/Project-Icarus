"""Tests for the Phase 2 PlasticityRule API (FLY-LEARN-001 WP1).

Protocol WP1 requirements: clean interface, deterministic unit tests,
numerical stability. Registry decisions baked in:
- D3: three named signed-weight semantics (V-mag default, V-signed,
  V-clip), each separately tested;
- D5: no read-side parameter defaults - a PlasticityConfig with any
  required field unset must raise;
- D6: stability thresholds pre-registered (enforced by a guard that
  halts a run when thresholds are crossed);
- checkpoint(): the rule's full state must round-trip losslessly.
"""

import dataclasses

import numpy as np
import pytest
from scipy import sparse

from fly.plasticity import (
    PlasticityConfig,
    HebbianRule,
    PlasticityGuard,
    Semantics,
    StabilityThresholds,
)


def _toy_matrix():
    # 2x2: A->B weight +5 (exc), C->D weight -5 (inh); indices 0..3
    rows, cols, data = [0, 2], [1, 3], [5.0, -5.0]
    m = sparse.csr_matrix((data, (rows, cols)), shape=(4, 4))
    m.sort_indices()
    return m


# ---- D5: config discipline -------------------------------------------------

def test_config_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        PlasticityConfig()  # every field unset -> must raise


def test_config_explicit_construction_and_hash() -> None:
    cfg = PlasticityConfig(eta=1e-3, semantics=Semantics.V_MAG,
                           w_max=100.0)
    assert cfg.eta == 1e-3
    assert cfg.semantics is Semantics.V_MAG
    h1 = cfg.content_hash()
    h2 = dataclasses.replace(cfg, eta=1e-3).content_hash()
    assert h1 == h2
    h3 = dataclasses.replace(cfg, eta=1e-2).content_hash()
    assert h1 != h3


# ---- D3: three named semantics ----------------------------------------------

def test_v_mag_preserves_sign_and_grows_magnitude() -> None:
    rule = HebbianRule(PlasticityConfig(eta=0.1, semantics=Semantics.V_MAG,
                                        w_max=1e6))
    w = sparse.csr_matrix(([5.0, -5.0], ([0, 2], [1, 3])), shape=(4, 4))
    rule.observe(pre=0, post=1, weight=w)
    rule.observe(pre=2, post=3, weight=w)  # inhibitory pair coincides too
    w2 = rule.apply(w)
    assert w2[0, 1] == pytest.approx(5.1)      # exc grew
    assert w2[2, 3] == pytest.approx(-5.1)     # inh magnitude grew, sign kept


def test_v_signed_can_cross_zero() -> None:
    rule = HebbianRule(PlasticityConfig(eta=1.0, semantics=Semantics.V_SIGNED,
                                        w_max=1e6))
    w = sparse.csr_matrix(([-5.0], ([2], [3])), shape=(4, 4))
    rule.observe(pre=2, post=3, weight=w)  # one potentiation event of eta*x*y=1
    w2 = rule.apply(w)
    # V-signed: w <- w + eta*x*y with x=y=1 -> -4.0 (no flip at small eta)
    assert w2[2, 3] == pytest.approx(-4.0)
    for _ in range(6):
        rule.observe(pre=2, post=3, weight=w2)
        w2 = rule.apply(w2)
    assert w2[2, 3] > 0  # crossed zero after repeated events


def test_v_clip_frozen_at_zero_crossing() -> None:
    rule = HebbianRule(PlasticityConfig(eta=1.0, semantics=Semantics.V_CLIP,
                                        w_max=1e6))
    w = sparse.csr_matrix(([-5.0], ([2], [3])), shape=(4, 4))
    for _ in range(10):
        rule.observe(pre=2, post=3, weight=w)
        w = rule.apply(w)
    assert w[2, 3] == 0.0  # approached zero and froze there, never crossed


def test_weights_bounded_w_max() -> None:
    rule = HebbianRule(PlasticityConfig(eta=10.0, semantics=Semantics.V_MAG,
                                        w_max=7.0))
    w = sparse.csr_matrix(([6.9], ([0], [1])), shape=(4, 4))
    rule.observe(pre=0, post=1, weight=w)
    w2 = rule.apply(w)
    assert w2[0, 1] == pytest.approx(7.0)  # clipped at bound


# ---- determinism + checkpoint ------------------------------------------------

def test_checkpoint_round_trip_restores_behavior() -> None:
    cfg = PlasticityConfig(eta=0.1, semantics=Semantics.V_MAG,
                           w_max=100.0)
    r1 = HebbianRule(cfg)
    w = _toy_matrix()
    r1.observe(pre=0, post=1, weight=w)
    r1.observe(pre=2, post=3, weight=w)
    state = r1.checkpoint()

    r2 = HebbianRule.from_checkpoint(state)
    assert r2.checkpoint() == state  # lossless round trip
    w_a = r1.apply(w)
    w_b = r2.apply(_toy_matrix())
    assert abs(w_a[0, 1] - w_b[0, 1]) < 1e-12  # identical behavior


def test_identical_observation_streams_identical_results() -> None:
    cfg = PlasticityConfig(eta=0.1, semantics=Semantics.V_MAG,
                           w_max=100.0)
    w = _toy_matrix()
    outs = []
    for _ in range(2):
        r = HebbianRule(cfg)
        for _ in range(5):
            r.observe(pre=0, post=1, weight=w)
        outs.append(r.apply(w)[0, 1])
    assert outs[0] == outs[1]  # deterministic: no hidden RNG


# ---- D6: stability guard ------------------------------------------------------

def test_guard_fires_on_spike_ceiling() -> None:
    g = PlasticityGuard(StabilityThresholds(max_spikes_per_trial=150_000,
                                             spontaneous_rate_hz=5.0,
                                             inh_weight_drift_frac=0.20))
    assert g.check(trial_spikes=149_999) is None
    fired = g.check(trial_spikes=150_001)
    assert fired is not None and "max_spikes_per_trial" in fired


def test_guard_fires_on_spontaneous_rate_and_drift() -> None:
    g = PlasticityGuard(StabilityThresholds(max_spikes_per_trial=150_000,
                                             spontaneous_rate_hz=5.0,
                                             inh_weight_drift_frac=0.20))
    a = g.check(trial_spikes=100, spontaneous_rate_hz=6.0)
    assert a is not None and "spontaneous_rate_hz" in a
    b = g.check(trial_spikes=100, inh_weight_drift_frac=0.25)
    assert b is not None and "inh_weight_drift_frac" in b
    assert g.check(trial_spikes=100) is None  # quiet trial passes


# ---- numerical stability -------------------------------------------------------

def test_zero_weight_edge_stays_zero_v_mag() -> None:
    # a zero weight (structural edge that lost all synapses) must not
    # resurrect from a potentiation event under V-mag/|w| semantics
    rule = HebbianRule(PlasticityConfig(eta=0.1, semantics=Semantics.V_MAG,
                                        w_max=100.0))
    w = sparse.csr_matrix(([0.0], ([0], [1])), shape=(4, 4))
    rule.observe(pre=0, post=1, weight=w)
    w2 = rule.apply(w)
    assert w2[0, 1] == 0.0


def test_tiny_eta_no_overflow_over_many_events() -> None:
    rule = HebbianRule(PlasticityConfig(eta=1e-4, semantics=Semantics.V_MAG,
                                        w_max=50.0))
    w = _toy_matrix()
    for _ in range(1000):
        rule.observe(pre=0, post=1, weight=w)
        w = rule.apply(w)
    assert np.isfinite(w[0, 1]) and w[0, 1] <= 50.0
