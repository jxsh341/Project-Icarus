"""Phase 5 Experiment A launcher guards: TDD'd tamper tests.

Each guard must REFUSE (raise GuardViolation) when its condition is
violated and pass on the real frozen configuration. These are the
runtime raises that protect the confirmatory run from silently
altered frozen parameters, a modified harness, a stale output
directory, or a contaminated seed space.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


an = _load("phase5_expA_analysis", "scripts/phase5_expA_analysis.py")
L = _load("phase5_expA_launcher", "scripts/phase5_expA_launcher.py")

TRAIN, PROBE = an.parse_prereg_seeds()


# ---------- G1: frozen harness ----------

def test_g1_passes_on_frozen_harness():
    L.guard_harness_sha(an.HARNESS, an.FROZEN_HARNESS_SHA)  # must not raise


def test_g1_refuses_modified_harness(tmp_path):
    fake = tmp_path / "phase4_wp_l4b_extinction.py"
    fake.write_text("# tampered: ETA = 1e-2\n", encoding="utf-8")
    with pytest.raises(L.GuardViolation, match="G1"):
        L.guard_harness_sha(fake, an.FROZEN_HARNESS_SHA)


# ---------- G2: injection confined to the four keys ----------

def test_g2_allows_the_four_injections():
    before = {"ETA": 1e-4, "THETA": 41.5, "REPS": 3, "OUT": Path("dev"),
              "TRAIN_SEED_BASE": 160_000, "PROBE_SEED_BASE": 162_000}
    after = dict(before, REPS=1, OUT=Path("confirm"),
                 TRAIN_SEED_BASE=TRAIN[0], PROBE_SEED_BASE=PROBE[0])
    L.guard_injection_keys(before, after, L.INJECT_KEYS)  # must not raise


def test_g2_catches_frozen_constant_tamper():
    before = {"ETA": 1e-4, "THETA": 41.5, "REPS": 3, "OUT": Path("dev"),
              "TRAIN_SEED_BASE": 160_000, "PROBE_SEED_BASE": 162_000}
    after = dict(before, REPS=1, ETA=1e-2)  # a frozen constant moved
    with pytest.raises(L.GuardViolation, match="ETA"):
        L.guard_injection_keys(before, after, L.INJECT_KEYS)


def test_g2_catches_silent_extra_change():
    before = {"CUE": [15957, 16327], "REPS": 3}
    after = {"CUE": [15957], "REPS": 1}
    with pytest.raises(L.GuardViolation, match="CUE"):
        L.guard_injection_keys(before, after, L.INJECT_KEYS)


# ---------- G3: seed space ----------

def test_g3_real_anchors_are_clean():
    union = L.guard_seed_space(TRAIN, PROBE, 8)
    assert len(union) == 8 * 50 + 8 * 20 + 8          # 50 train + 20 probe + 1 sanity per rep
    assert min(union) > 193_000                       # strictly above dev space
    assert not (union & an.dev_seed_space())


def test_g3_catches_collisions():
    dup = [TRAIN[0]] * 8
    with pytest.raises(L.GuardViolation, match="COLLISION"):
        L.guard_seed_space(dup, PROBE, 8)


def test_g3_catches_dev_overlap():
    contaminated = [160_100, 160_200, 160_300, 160_400,
                    160_500, 160_600, 160_700, 160_800]
    with pytest.raises(L.GuardViolation, match="G3"):
        L.guard_seed_space(contaminated, PROBE, 8)


# ---------- G4: fresh output root ----------

def test_g4_allows_missing_root(tmp_path):
    L.guard_fresh_out(tmp_path / "does_not_exist")  # must not raise


def test_g4_allows_empty_root(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    L.guard_fresh_out(d)  # must not raise


def test_g4_refuses_stale_root(tmp_path):
    d = tmp_path / "stale"
    (d / "rep_r0").mkdir(parents=True)
    (d / "rep_r0" / "l4b_extinction.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(L.GuardViolation, match="G4"):
        L.guard_fresh_out(d)


# ---------- G5/G7 wiring ----------

def test_g5_confirm_root_is_not_dev_root():
    assert an.CONF_ROOT != an.DEV_OUT
    assert "wp_l4b_confirm" in str(an.CONF_ROOT)


def test_inject_keys_are_exactly_the_documented_four():
    assert L.INJECT_KEYS == {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT"}
