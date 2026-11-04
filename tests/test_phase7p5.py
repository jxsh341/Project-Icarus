"""Phase 7 P5: frozen-logic contract tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7p5_analysis as p5  # noqa: E402


def test_reproduce_draw_matches_prereg():
    p5.reproduce_draw()


def test_probe_space_sized():
    assert len(p5.probe_space(3_200_000)) == 12


def test_arm_map():
    assert p5.ARM_OF == {0: "true", 1: "true", 2: "thresh4", 3: "thresh4", 4: "hop1", 5: "hop1"}
