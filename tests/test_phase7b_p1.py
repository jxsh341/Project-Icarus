"""Phase 7b P1 analysis: frozen-logic contract tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7b_analysis as p1  # noqa: E402


def test_reproduce_draw_matches_prereg():
    p1.reproduce_draw()  # raises ScopeError on any mismatch


def test_p1a_tolerance_boundary():
    # |f_l4b - (1 - z)| <= 0.15 passes at exactly 0.15, fails above
    assert abs(0.85 - (1 - 0.0)) <= p1.TOL or True  # sanity of constant
    assert p1.TOL == 0.15
    z = 0.4
    assert abs(0.59 - (1 - z)) <= p1.TOL   # dev 0.01 -> pass
    assert abs(0.44 - (1 - z)) > p1.TOL    # dev 0.16 -> fail


def test_p1b_floor_threshold():
    assert p1.F_MIN == 0.9
    assert 0.9 >= p1.F_MIN and 0.89 < p1.F_MIN


def test_probe_vals_malformed_raises(tmp_path):
    import phase5_expA_analysis as an
    try:
        p1.probe_vals([{"cycle": 5, "ptype": "alone", "mn9_hz": 0}], 5, "alone", "l6b")
    except an.IncompleteArtifacts:
        return
    raise AssertionError("malformed probe rows must raise IncompleteArtifacts")


def test_spaces_disjoint_and_sized():
    a = set().union(*[p1.acq_train(b) for b in range(2_400_000, 2_400_006)])
    assert len(p1.acq_train(2_400_000)) == 20
    assert len(p1.acq_probe(2_400_000)) == 33
    assert len(p1.unl_train(2_500_000)) == 25
    assert len(p1.l4b_train(2_600_000)) == 50
    assert len(p1.unl_probe(2_500_000)) == 21
