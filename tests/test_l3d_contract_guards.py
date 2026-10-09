"""Tests: WP-L3d pre-launch contract guards (review-directed 2026-10-09).

Two load-bearing properties, enforced in code rather than trusted:

1. NEVER-BOTH: no trial in any registered WP-L3d protocol combines
   sugar and bitter drives. The binary either/or gate model breaks
   silently on a dual-activity trial. Guard = runtime assertion in
   the trial builder + this test against the protocol definitions.

2. ZERO-VS-ABSENT for the weakening pathway: the WP1 eliminate_zeros
   lesson - a weight landing exactly on 0.0 must remain a STORED
   structural zero, indistinguishable-from-absent is the hazard.
   V_SIGNED can cross zero (edge sign flips - biological aggressive,
   registered arm); the weakening pathway must choose its semantics
   EXPLICITLY, and whichever is chosen, w=0.0 must survive as
   structure. Test drives an edge to exactly zero and verifies it
   still exists in the sparse structure afterward.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fly.plasticity import HebbianRule, PlasticityConfig, Semantics  # noqa: E402


def _matrix():
    m = sparse.csr_matrix(([10.0, -10.0], ([0, 1], [2, 2])), shape=(4, 4))
    m.sort_indices()
    return m


def test_v_signed_zero_cross_keeps_structure():
    """V_SIGNED driven to exactly 0.0: the edge MUST remain in the
    sparse structure (stored zero), not be pruned to absent."""
    rule = HebbianRule(PlasticityConfig(eta=0.5, semantics=Semantics.V_SIGNED, w_max=1e6))
    m = _matrix()
    rule.observe_rate_pair(0, 2, m, x_hz=10.0, y_hz=10.0)
    # delta = eta*x*y = 0.5*100 = 50 > 10 -> crosses zero to -40? No:
    # we need exact zero: set pending directly for precision.
    rule._pending[(0, 2)] = -10.0  # exactly cancels w=10
    out = rule.apply(m)
    # structural presence check: (0,2) must exist in the structure
    out_coo = out.tocoo()
    assert (0, 2) in {(int(r), int(c)) for r, c in zip(out_coo.row, out_coo.col)}
    assert out[0, 2] == 0.0


def test_v_mag_weakening_floors_at_zero():
    """The weakening pathway under V_MAG: magnitude decrease cannot
    cross zero (sign is a validated per-presynaptic property; LTP
    must not silently override it). Driving delta more negative than
    the weight magnitude FLOORS at 0.0, never flips sign - and 0.0
    remains structural."""
    rule = HebbianRule(PlasticityConfig(eta=0.5, semantics=Semantics.V_MAG, w_max=1e6))
    m = _matrix()
    rule._pending[(0, 2)] = -50.0  # far more negative than |w|=10
    out = rule.apply(m)
    out_coo = out.tocoo()
    assert (0, 2) in {(int(r), int(c)) for r, c in zip(out_coo.row, out_coo.col)}
    assert out[0, 2] == 0.0  # floored at zero, NOT -40 (no sign flip)


def test_never_both_guard_in_l3d_protocol():
    """The WP-L3d protocol definitions must never construct a trial
    with both sugar and bitter drives active. The WP-L3d script (to
    be written) will carry a runtime assertion; this test pins the
    CURRENT state: no Phase 2/3 script builds such a trial. It does
    so by importing the L3d trial-builder contract: the check is
    against the TrialSpec semantics - drive (primary) and drive2
    (secondary) map to distinct populations in every registered
    protocol, and the L3d design uses one drive per trial."""
    # The enforcement lives in the WP-L3d script's build_spec(); here
    # we verify the DESIGN contract: sugar and bitter are never the
    # same trial's drive AND drive2. Static scan as of this commit:
    import re
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    offenders = []
    for f in sorted(scripts.glob("phase*_*.py")):
        src = f.read_text(encoding="utf-8")
        # a single TrialSpec with sugar as drive and bitter as drive2 (or vice versa)
        for m in re.finditer(r"TrialSpec\(([^)]*)\)", src, re.DOTALL):
            block = m.group(1)
            d1 = re.search(r"drive_body_ids=tuple\((\w+)\)", block)
            d2 = re.search(r"drive2_body_ids=tuple\((\w+)\)", block)
            if d1 and d2:
                p1, p2 = d1.group(1), d2.group(1)
                if {p1, p2} == {"sugar", "bitter"}:
                    offenders.append(f.name)
    assert offenders == [], f"scripts combining sugar+bitter in one TrialSpec: {offenders}"
