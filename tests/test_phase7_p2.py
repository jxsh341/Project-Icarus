"""Phase 7 WP-P2 analysis: frozen verdict-logic contract tests (synthetic reps)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7_p2_analysis as p7  # noqa: E402


def _crit(c1=True, c2=True, c3=True, c4=True, c5=True, c6=True):
    return {"c1_recovery": c1, "c2_band_c25": c2, "c3_innate_intact": c3,
            "c4_guard_silent": c4, "c5_floors": c5, "c6_structure": c6}


def _branch(c):
    neg_a = not (c["c1_recovery"] and c["c2_band_c25"] and c["c5_floors"] and c["c6_structure"])
    neg_b = not (c["c3_innate_intact"] and c["c4_guard_silent"])
    if neg_a and neg_b:
        return "NEGATIVE-A+NEGATIVE-B"
    if neg_a:
        return "NEGATIVE-A"
    if neg_b:
        return "NEGATIVE-B"
    return "PASS"


def test_all_pass_aggregates_pass():
    assert all(_branch(_crit()) == "PASS" for _ in range(8))
    assert p7.aggregate(["PASS"] * 8) == "PASS"


def test_target_side_failure_is_negative_a():
    assert _branch(_crit(c5=False)) == "NEGATIVE-A"
    assert _branch(_crit(c1=False)) == "NEGATIVE-A"
    assert p7.aggregate(["PASS"] * 7 + ["NEGATIVE-A"]) == "MIXED"


def test_collateral_side_failure_is_negative_b():
    assert _branch(_crit(c4=False)) == "NEGATIVE-B"
    assert _branch(_crit(c3=False)) == "NEGATIVE-B"
    assert p7.aggregate(["NEGATIVE-B"] * 8) == "NEGATIVE-B"


def test_mixed_is_non_aggregating():
    assert p7.aggregate(["PASS"] * 6 + ["NEGATIVE-A", "NEGATIVE-B"]) == "MIXED"
    assert p7.aggregate(["NEGATIVE-A", "NEGATIVE-A+NEGATIVE-B"]) == "MIXED"


def test_reproduce_draw_matches_prereg():
    p7.reproduce_draw()  # raises ScopeError if anchors do not reproduce
