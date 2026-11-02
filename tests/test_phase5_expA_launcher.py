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


# ---------- G4 (A2): known-artifacts-only output root ----------

def test_g4_allows_missing_root(tmp_path):
    L.guard_output_root(tmp_path / "does_not_exist")  # must not raise


def test_g4_allows_known_artifacts(tmp_path):
    d = tmp_path / "conf"
    (d / "rep_r0").mkdir(parents=True)
    (d / "launcher_manifest.json").write_text("{}", encoding="utf-8")
    L.guard_output_root(d)  # manifest + rep dirs are known - must not raise


def test_g4_refuses_unknown_file(tmp_path):
    d = tmp_path / "conf"
    d.mkdir()
    (d / "stranger.txt").write_text("?", encoding="utf-8")
    with pytest.raises(L.GuardViolation, match="G4 unknown artifacts"):
        L.guard_output_root(d)


def test_g4_refuses_unknown_subdir(tmp_path):
    d = tmp_path / "conf"
    (d / "old_attempt").mkdir(parents=True)
    with pytest.raises(L.GuardViolation, match="G4 unknown artifacts"):
        L.guard_output_root(d)


# ---------- A2: artifact-level completion criterion ----------

def _complete_rep_dir(tmp_path, base: int) -> Path:
    import json as _json
    from scipy import sparse
    from fly.training import weight_matrix_hash
    d = tmp_path / "rep_x"
    (d / "ckpt_r0").mkdir(parents=True)
    hist = [{"run_id": "l4b_r0", "trial": c * 2 + ph, "seed": base + c * 2 + ph,
             "readout_hz": 80, "total_spikes": 1200, "n_spiking": 40,
             "wall_s": 4.0, "weight_hash": "wh", "is_probe": False,
             "weight_diff": {}} for c in range(1, 26) for ph in (0, 1)]
    (d / "ckpt_r0" / "history.jsonl").write_text(
        "\n".join(_json.dumps(x) for x in hist) + "\n", encoding="utf-8")
    rows = [{"rep": 0, "cycle": c, "sugar_readout": 80, "bitter_readout": 0,
             "pending_after_sugar": 0, "guard_fired": None} for c in range(1, 26)]
    for c in (5, 10, 15, 20, 25):
        for pt in ("alone", "cosugar"):
            for r2 in (0, 1):
                rows.append({"rep": 0, "cycle": c, "ptype": pt, "rep2": r2,
                             "mn9_hz": 0})
    (d / "l4b_extinction.jsonl").write_text(
        "\n".join(_json.dumps(x) for x in rows) + "\n", encoding="utf-8")
    mat = sparse.eye(3, format="csr")
    sparse.save_npz(d / "ckpt_r0" / "weights_trial_0052.npz", mat)
    (d / "ckpt_r0" / "run_state.json").write_text(_json.dumps(
        {"run_id": "l4b_r0", "trial_index": 52, "n_history": 50,
         "config_hash": "x", "weight_hash": weight_matrix_hash(mat),
         "stopped_reason": None}))
    return d


def test_a2_complete_rep_accepted(tmp_path):
    d = _complete_rep_dir(tmp_path, TRAIN[0])
    ok, why = L.rep_artifacts_complete(d, TRAIN[0])
    assert ok and why == "complete"


def test_a2_truncated_history_rejected(tmp_path):
    d = _complete_rep_dir(tmp_path, TRAIN[0])
    hp = d / "ckpt_r0" / "history.jsonl"
    hp.write_text("\n".join(hp.read_text(encoding="utf-8").splitlines()[:-5])
                  + "\n", encoding="utf-8")
    ok, why = L.rep_artifacts_complete(d, TRAIN[0])
    assert not ok and "history rows" in why


def test_a2_wrong_base_seeds_rejected(tmp_path):
    d = _complete_rep_dir(tmp_path, TRAIN[0])
    ok, why = L.rep_artifacts_complete(d, TRAIN[1])  # seeds belong to rep 0's base
    assert not ok and "seeds" in why


# ---------- G5/G7 wiring ----------

def test_g5_confirm_root_is_not_dev_root():
    assert an.CONF_ROOT != an.DEV_OUT
    assert "wp_l4b_confirm" in str(an.CONF_ROOT)


def test_inject_keys_are_exactly_the_documented_four():
    assert L.INJECT_KEYS == {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT"}
