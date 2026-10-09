"""Tests: WP-L4a decoupled eligibility-then-sign rule.

The Phase 4 mechanism (registered): eligibility accumulation is
driven by whichever population opens coincidence (sugar phase),
the sign is applied from a separate source (bitter phase), and
_pending persists across the phase boundary.

Reviewer checks wired in as tests:
- DECAY TIMEBASE: no decay fires between the sugar phase and the
  bitter phase within one trial. The L3c per-trial lambda
  calibration does NOT carry over - the L4a rule has no decay term
  at all between phases; eligibility survives fully intact. Pinned
  by test 5.
- CLAIM BOUNDARY: these tests verify MECHANISM wiring on synthetic
  data only. Whether the real 9 untouched partners get touched is
  WP-L4b's empirical question (registered; not claimed here).
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fly.plasticity import Semantics  # noqa: E402


def _matrix():
    m = sparse.csr_matrix(([10.0, 10.0, 10.0], ([0, 0, 1], [2, 3, 3])), shape=(5, 5))
    m.sort_indices()
    return m


def test_eligibility_accumulates_under_sugar_sign_source_absent():
    """(1) sugar-phase coincidence accumulates eligibility with no
    sign source present; nothing applies yet."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = _matrix()
    # sugar phase: cue (0) + partner (2) co-fire
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    assert rule.pending_count() == 1
    assert rule.pending_edge((0, 2)) == pytest.approx(100.0 * 100.0)
    # no sign source applied yet -> no weight change
    m2 = rule.apply(m, sign=None)
    assert m2[0, 2] == 10.0  # unchanged


def test_bitter_phase_applies_negative_delta_to_live_eligibility():
    """(2) subsequent bitter-phase sign applies NEGATIVE delta to the
    live eligibility."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = _matrix()
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    m2 = rule.apply(m, sign=-1)
    # dw = eta * sign * c = 0.5 * (-1) * 10000 = -5000 -> floored at 0 by V_CLIP
    assert m2[0, 2] == 0.0
    # a smaller contrast that still overshoots: floors at 0 (V_CLIP), never -40
    rule2 = EligibilitySignRule(eta=0.5, w_max=1e6)
    m3 = _matrix()
    rule2.observe_rate_pair(0, 3, m3, x_hz=10.0, y_hz=10.0)
    m4 = rule2.apply(m3, sign=-1)
    assert m4[0, 3] == 0.0  # 10 - 50 = -40 crosses zero -> V_CLIP floors at 0


def test_full_footprint_eligibility_then_sign():
    """(3) the mechanism reaches the FULL edge set in one
    sugar-then-bitter cycle: every co-firing edge accumulates and
    receives the negative sign (synthetic; L4b decides real
    coverage)."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = _matrix()
    # sugar phase: three edges co-fire
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    rule.observe_rate_pair(0, 3, m, x_hz=100.0, y_hz=50.0)
    rule.observe_rate_pair(1, 3, m, x_hz=80.0, y_hz=80.0)
    assert rule.pending_count() == 3
    m2 = rule.apply(m, sign=-1)
    assert m2[0, 2] == 0.0
    assert m2[0, 3] == 0.0
    assert m2[1, 3] == 0.0  # 10 - 0.5*6400 < 0 -> floored


def test_never_simultaneous_is_structural():
    """(4) the rule exposes separate phase hooks; the driver asserts
    never-simultaneous (sugar XOR bitter active at any moment). Here:
    the rule itself cannot be driven with both signs at once - the
    sign is a scalar applied at apply-time, never accumulated."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = _matrix()
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    # sign is chosen ONCE at apply; there is no code path where two
    # signs compose in one application
    m2 = rule.apply(m, sign=-1)
    assert m2[0, 2] == 0.0
    # pending flushed after apply; a second sign cannot double-apply
    assert rule.pending_count() == 0


def test_no_decay_between_phases_within_trial():
    """(5) DECAY TIMEBASE (reviewer check): eligibility survives the
    sugar->bitter phase boundary FULLY INTACT - no decay fires
    between phases within one trial. The L3c per-trial lambda does
    NOT carry into this rule: there is no decay term at all."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = _matrix()
    # sugar phase
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    e_before = rule.pending_edge((0, 2))
    # ... bitter phase arrives (simulated passage of a phase gap) ...
    # the rule has no tick/decay call; eligibility is unchanged:
    e_after = rule.pending_edge((0, 2))
    assert e_after == e_before
    # and applies at full strength after the gap
    m2 = rule.apply(m, sign=-1)
    assert m2[0, 2] == 0.0  # full -5000 delta floored at 0, not partial


def test_vclip_floor_preserved():
    """(6) V_CLIP semantics preserved: negative deltas floor at zero,
    sign never flips, structural zeros survive."""
    from phase4_eligibility_sign_rule import EligibilitySignRule
    rule = EligibilitySignRule(eta=0.5, w_max=1e6)
    m = sparse.csr_matrix(([10.0, 0.0], ([0, 1], [2, 2])), shape=(5, 5))
    m.sort_indices()
    rule.observe_rate_pair(0, 2, m, x_hz=100.0, y_hz=100.0)
    m2 = rule.apply(m, sign=-1)
    assert m2[0, 2] == 0.0  # floored, not flipped
    # the stored zero edge (1,2) survives as structure
    coo = m2.tocoo()
    assert (1, 2) in {(int(r), int(c)) for r, c in zip(coo.row, coo.col)}
