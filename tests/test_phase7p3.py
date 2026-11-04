"""Phase 7 P3: frozen-logic + fast==full validation tests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7p3_analysis as p3  # noqa: E402


def test_reproduce_draw_matches_prereg():
    p3.reproduce_draw()


def test_probe_space_sized():
    assert len(p3.probe_space(3_000_000)) == 8


def test_tau_assignment():
    assert [p3.TAU_LEVELS[r % 4] for r in range(16)] == [0.5, 1.0, 2.0, 4.0] * 4


def test_fast_equals_full_bit_identical(tmp_path):
    """fast (analytic decay between probe cycles) must equal full
    (per-cycle sim+decay) on probe mn9 and weight hashes."""
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location(
        "p3h_val", ROOT / "scripts/phase7p3_harness.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["p3h_val"] = mod
    spec.loader.exec_module(mod)
    mod.N_CYCLES = 5            # validation-only shrink (globals are runtime-read)
    mod.ALONE_AT = (2, 5)
    mod.COSUGAR_AT = (5,)
    base = 3_500_000  # validation-only seed base, outside all prereg spaces
    rows = {}
    for mode in ("fast", "full"):
        mod.OUT = tmp_path / mode
        mod.PROBE_BASE = base
        mod.TAU = 1.0
        mod.MODE = mode
        os.environ["PHASE7P3_MODE"] = mode
        mod.main()
        import phase5_expA_analysis as an
        rows[mode] = an.read_jsonl(mod.OUT / "p3.jsonl", mode)
    fp = [x for x in rows["fast"] if x.get("phase") == "probe"]
    fl = [x for x in rows["full"] if x.get("phase") == "probe"]
    assert len(fp) == len(fl) == 6  # 2 alone cycles x2 + cosugar x2 at shrunk config
    for a, b in zip(fp, fl):
        assert a["seed"] == b["seed"] and a["ptype"] == b["ptype"] and a["cycle"] == b["cycle"]
        assert a["mn9_hz"] == b["mn9_hz"], (a, b)
        assert a["weight_hash"] == b["weight_hash"], (a, b)
