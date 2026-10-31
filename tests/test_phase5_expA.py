"""Phase 5 Experiment A: analysis-script tests against synthetic fixtures.

Covers the preregistered criteria end-to-end on tiny synthetic run
trees: PASS, NEGATIVE-A, NEGATIVE-B (cosugar / guard / sign-flip
variants), MIXED, and malformed/incomplete inputs (which must fail
LOUDLY with no verdict emitted). Also pins the aggregate rule
(all-PASS -> PASS; identical branch -> that branch; any split ->
MIXED) and the prereg seed draw reproduction.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fly.training import weight_matrix_hash  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # required before exec_module: @dataclass resolution
    spec.loader.exec_module(mod)
    return mod


an = _load("phase5_expA_analysis", "scripts/phase5_expA_analysis.py")

# --- fixture geometry (tiny stand-in for run-007) ---
N = 30
CUE = (0, 1)
POSTS = list(range(2, 27))            # 25 partner posts
UNTOUCHED = tuple(range(18, 27))      # 9 of them
CARRIERS = [(0, p) for p in POSTS]    # all 25 from cue 0
NID = {i: i for i in range(N)}
PROBE_AT = (5, 10, 15, 20, 25)
TRAIN_BASES, PROBE_BASES = an.parse_prereg_seeds(
    an.PREREG.read_text(encoding="utf-8"))


def _mat(d: dict) -> sparse.csr_matrix:
    m = sparse.lil_matrix((N, N))
    for (i, j), v in d.items():
        m[i, j] = v
    return m.tocsr()


def _pristine() -> sparse.csr_matrix:
    return _mat({(5, 6): 3.0, (7, 8): 2.0, (9, 10): 1.0})


def _acquired() -> sparse.csr_matrix:
    d = {(5, 6): 3.0, (7, 8): 2.0, (9, 10): 1.0}
    d.update({c: 10.0 for c in CARRIERS})
    return _mat(d)


def _final(acq: sparse.csr_matrix, *, zero_carriers=True, mutate=None) -> sparse.csr_matrix:
    m = acq.tolil()
    if zero_carriers:
        for (i, j) in CARRIERS:
            m[i, j] = 0.0
    if mutate:
        for (i, j), v in mutate.items():
            m[i, j] = v
    return m.tocsr()


def _history(base: int, wh: str, *, total_spikes=1200) -> list[dict]:
    rows = []
    for c in range(1, 26):
        for ph in (0, 1):
            rows.append({"run_id": "l4b_r0", "trial": c * 2 + ph,
                         "seed": base + c * 2 + ph, "readout_hz": 80,
                         "total_spikes": total_spikes, "n_spiking": 40,
                         "wall_s": 4.0, "weight_hash": wh, "is_probe": False,
                         "weight_diff": {"n_edges_changed": 0, "max_abs_delta": 0.0,
                                         "total_delta": 0.0}})
    return rows


def _jsonl_rows(*, alone=None, cosugar=None, guard=None) -> list[dict]:
    alone = alone or {5: 70, 10: 25, 15: 0, 20: 0, 25: 0}
    cosugar = cosugar or {5: 82, 10: 84, 15: 85, 20: 83, 25: 84}
    rows = []
    for c in range(1, 26):
        rows.append({"rep": 0, "cycle": c, "sugar_readout": 85, "bitter_readout": 0,
                     "pending_after_sugar": 12, "guard_fired": guard})
    for c in PROBE_AT:
        for r2 in (0, 1):
            rows.append({"rep": 0, "cycle": c, "ptype": "alone", "rep2": r2,
                         "mn9_hz": alone[c]})
            rows.append({"rep": 0, "cycle": c, "ptype": "cosugar", "rep2": r2,
                         "mn9_hz": cosugar[c]})
    return rows


def _build_tree(tmp: Path, *, per_rep_mutate=None, alone=None, cosugar=None,
                alone_by_rep=None, cosugar_by_rep=None,
                guard=None, total_spikes=1200, drop_rep=None,
                drop_probe_row=False, corrupt_line=False, seed_tamper_rep=None,
                final_mutate=None, n_carriers=25) -> Path:
    root = tmp / "wp_l4b_confirm"
    pristine, acq = _pristine(), _acquired()
    if n_carriers != 25:  # scope-surprise fixture: one carrier never grew
        d = {(5, 6): 3.0, (7, 8): 2.0, (9, 10): 1.0}
        d.update({c: 10.0 for c in CARRIERS[:n_carriers]})
        acq = _mat(d)
    sparse.save_npz(tmp / "pristine.npz", pristine)
    acq_dir = tmp / "r1ck"
    acq_dir.mkdir(parents=True)
    sparse.save_npz(acq_dir / "weights_trial_0030.npz", acq)
    (acq_dir / "run_state.json").write_text(json.dumps(
        {"run_id": "r1_l1", "trial_index": 30, "n_history": 78,
         "config_hash": "x", "weight_hash": weight_matrix_hash(acq),
         "stopped_reason": None}))

    reps = []
    for r in range(8):
        rep_dir = root / f"rep_r{r}"
        base = TRAIN_BASES[r]
        reps.append({"rep": r, "out_dir": str(rep_dir), "train_base": base,
                     "probe_base": PROBE_BASES[r],
                     "expected_train_seeds": sorted(an.expected_train_seeds(base)),
                     "expected_probe_seeds": sorted(an.expected_probe_seeds(PROBE_BASES[r]))})
        if drop_rep == r:
            continue  # simulate a crashed rep: manifest entry exists, dir does not
        (rep_dir / "ckpt_r0").mkdir(parents=True)
        rows = _jsonl_rows(alone=(alone_by_rep or {}).get(r, alone),
                           cosugar=(cosugar_by_rep or {}).get(r, cosugar),
                           guard=guard)
        if drop_probe_row and r == 3:
            rows = [x for x in rows
                    if not (x.get("ptype") == "alone" and x["cycle"] == 25 and x["rep2"] == 1)]
        if corrupt_line and r == 3:
            (rep_dir / "l4b_extinction.jsonl").write_text(
                "\n".join(json.dumps(x) for x in rows[:-1]) + "\n{broken\n",
                encoding="utf-8")
        else:
            (rep_dir / "l4b_extinction.jsonl").write_text(
                "\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
        hist = _history(base, "wh", total_spikes=total_spikes)
        if seed_tamper_rep == r:
            hist[10]["seed"] += 1
        (rep_dir / "ckpt_r0" / "history.jsonl").write_text(
            "\n".join(json.dumps(x) for x in hist) + "\n", encoding="utf-8")
        fin = _final(acq, mutate=(final_mutate or {}).get(r))
        sparse.save_npz(rep_dir / "ckpt_r0" / "weights_trial_0052.npz", fin)
        (rep_dir / "ckpt_r0" / "run_state.json").write_text(json.dumps(
            {"run_id": f"l4b_r0_rep{r}", "trial_index": 52, "n_history": 50,
             "config_hash": "x", "weight_hash": weight_matrix_hash(fin),
             "stopped_reason": None}))
    (root / "launcher_manifest.json").write_text(json.dumps(
        {"reps": reps, "harness_sha256": an.FROZEN_HARNESS_SHA,
         "prereg_sha256": an.sha256_file(an.PREREG), "git_head": "test"}))
    return root


def _cfg(root: Path) -> an.AnalysisConfig:
    return an.AnalysisConfig(
        conf_root=root, pristine_path=root.parent / "pristine.npz",
        r1ck_dir=root.parent / "r1ck", dev_jsonl=an.DEV_JSONL,
        manifest_path=root / "launcher_manifest.json",
        nid=NID, cue=CUE, untouched=UNTOUCHED)


# ---------- aggregate rule (pure) ----------

def test_aggregate_rule():
    assert an.aggregate_verdict(["PASS"] * 8) == "PASS"
    assert an.aggregate_verdict(["NEGATIVE-A"] * 8) == "NEGATIVE-A"
    assert an.aggregate_verdict(["NEGATIVE-B"] * 8) == "NEGATIVE-B"
    assert an.aggregate_verdict(["PASS"] * 7 + ["NEGATIVE-A"]) == "MIXED"
    assert an.aggregate_verdict(["NEGATIVE-A", "NEGATIVE-B"]) == "MIXED"
    assert an.aggregate_verdict(["PASS", "NEGATIVE-A+B"]) == "MIXED"


# ---------- seed provenance ----------

def test_prereg_draw_reproduces():
    t, p = an.parse_prereg_seeds()
    an.reproduce_draw(t, p)  # must not raise
    assert len(t) == 8 and len(p) == 15
    assert all(860001 <= s <= 860999 for s in t)
    assert all(970001 <= s <= 970999 for s in p)
    assert p == sorted(p)  # documented as the sorted sample


def test_dev_space_disjoint_from_confirm():
    dev = an.dev_seed_space()
    t, p = an.parse_prereg_seeds()
    conf = set().union(*[an.expected_train_seeds(b) for b in t],
                       *[an.expected_probe_seeds(b) for b in p[:8]],
                       {an.sanity_seed(b) for b in p[:8]})
    assert not (conf & dev)
    assert min(conf) > 193_000


# ---------- end-to-end verdict fixtures ----------

def test_pass_all_reps(tmp_path):
    root = _build_tree(tmp_path)
    rep = an.evaluate_run(_cfg(root))
    assert rep["overall"] == "PASS"
    assert all(b == "PASS" for b in rep["branches"])
    assert rep["trials_to_zero_distribution"] == {"15": 8}
    assert all(x["carriers_at_floor"] == 25 and x["untouched_at_floor"] == 9
               for x in rep["per_rep"])
    assert all(x["cosugar_min"] >= 78 and x["cosugar_max"] <= 88 for x in rep["per_rep"])
    assert all(x["collateral_count"] == 0 for x in rep["per_rep"])


def test_negative_a_one_rep_gives_mixed(tmp_path):
    root = _build_tree(tmp_path, alone_by_rep={3: {5: 70, 10: 25, 15: 3, 20: 3, 25: 3}})
    rep = an.evaluate_run(_cfg(root))
    assert rep["per_rep"][3]["branch"] == "NEGATIVE-A"
    assert rep["per_rep"][3]["cycles_to_zero"] is None
    assert rep["overall"] == "MIXED"          # 7 PASS + 1 NEGATIVE-A -> MIXED
    assert rep["criteria_verdicts"]["c1_zero_by_15"][3] is False


def test_negative_b_cosugar_band(tmp_path):
    root = _build_tree(tmp_path, cosugar_by_rep={0: {5: 82, 10: 60, 15: 85, 20: 83, 25: 84}})
    rep = an.evaluate_run(_cfg(root))
    assert rep["per_rep"][0]["branch"] == "NEGATIVE-B"
    assert rep["per_rep"][0]["cosugar_below_band"] == [60, 60]  # both sims
    assert rep["overall"] == "MIXED"


def test_negative_b_guard_fired(tmp_path):
    root = _build_tree(tmp_path, guard=True)
    rep = an.evaluate_run(_cfg(root))
    assert all(x["branch"] == "NEGATIVE-B" for x in rep["per_rep"])
    assert rep["overall"] == "NEGATIVE-B"     # identical branch across all reps


def test_negative_b_sign_flip(tmp_path):
    root = _build_tree(tmp_path, final_mutate={2: {(7, 8): -2.0}})
    rep = an.evaluate_run(_cfg(root))
    assert rep["per_rep"][2]["branch"] == "NEGATIVE-B"
    assert rep["per_rep"][2]["sign_flips"] == [(7, 8, 2.0, -2.0)]
    assert rep["overall"] == "MIXED"


def test_spike_threshold_violation_is_negative_b(tmp_path):
    root = _build_tree(tmp_path, total_spikes=200_000)
    rep = an.evaluate_run(_cfg(root))
    assert all(x["spike_threshold_violations"] == 50 for x in rep["per_rep"])
    assert rep["overall"] == "NEGATIVE-B"


def test_collateral_reported_not_verdict(tmp_path):
    root = _build_tree(tmp_path, final_mutate={1: {(5, 6): 3.3}})
    rep = an.evaluate_run(_cfg(root))
    assert rep["per_rep"][1]["collateral_count"] == 1
    assert abs(rep["per_rep"][1]["collateral_max_abs_delta"] - 0.3) < 1e-9
    assert rep["per_rep"][1]["branch"] == "PASS"   # descriptive, not criterion


# ---------- malformed / incomplete: fail loudly, no verdict ----------

def _no_verdict(root: Path):
    assert not (root / "CONFIRMATORY_VERDICT.json").exists()


def test_missing_rep_dir_fails_loudly(tmp_path):
    root = _build_tree(tmp_path, drop_rep=4)
    with pytest.raises(an.IncompleteArtifacts, match="rep 4"):
        an.evaluate_run(_cfg(root))
    _no_verdict(root)


def test_missing_probe_row_fails_loudly(tmp_path):
    root = _build_tree(tmp_path, drop_probe_row=True)
    with pytest.raises(an.IncompleteArtifacts, match="probe rows"):
        an.evaluate_run(_cfg(root))
    _no_verdict(root)


def test_corrupt_jsonl_fails_loudly(tmp_path):
    root = _build_tree(tmp_path, corrupt_line=True)
    with pytest.raises(an.IncompleteArtifacts, match="malformed JSON"):
        an.evaluate_run(_cfg(root))
    _no_verdict(root)


def test_seed_mismatch_fails_loudly(tmp_path):
    root = _build_tree(tmp_path, seed_tamper_rep=6)
    with pytest.raises(an.IncompleteArtifacts, match="seeds diverge"):
        an.evaluate_run(_cfg(root))
    _no_verdict(root)


def test_carrier_scope_surprise_fails_loudly(tmp_path):
    root = _build_tree(tmp_path, n_carriers=24)
    with pytest.raises(an.ScopeError, match="carrier footprint is 24"):
        an.evaluate_run(_cfg(root))
    _no_verdict(root)


def test_harness_tamper_fails_loudly(tmp_path, monkeypatch):
    root = _build_tree(tmp_path)
    cfg = _cfg(root)
    monkeypatch.setattr(an, "FROZEN_HARNESS_SHA", "0" * 64)
    with pytest.raises(an.ScopeError, match="harness sha"):
        an.evaluate_run(cfg)
    _no_verdict(root)
