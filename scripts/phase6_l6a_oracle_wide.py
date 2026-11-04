"""WP-L6a-A3 - widened membership oracle (Phase 6 prereg Amendment A3, frozen
2026-11-04 before this run). Same artifacts and gates as A2, widened features:
F1 rank-set weights (25), F2 changed-edge stats (6), F3 top-8 |dw| (8),
F4 trial-quantile L1 trajectory (6), F5 per-seed + held-out behavior (4).
Output: results/phase6/wp_l6a/oracle_report_wide_A3.json
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fly.dynamics.lif import LIFParams, simulate_lif  # noqa: E402
from fly.training import weight_matrix_hash  # noqa: E402
import phase5_expA_analysis as an  # noqa: E402
from phase6_l6a_oracle import (  # noqa: E402
    CUE, MN9_L, PRISTINE_HASH, RANK_SHA_PREREG, RESIDUAL_EDGES,
    class_weights, fit_lr, grab_seeds, predict,
)

PREREG6 = ROOT / "docs" / "PHASE_6_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
TASKB = ROOT / "results/phase2/taskB_r1"
OUT = ROOT / "results/phase6/wp_l6a"
QUANT = [0.05, 0.2, 0.4, 0.6, 0.8, 1.0]


def load_trial(path: Path, i: int):
    return sparse.load_npz(path / f"weights_trial_{i:04d}.npz").tocsr()


def trajectory(m_final, ckpt: Path | None, pristine):
    """L1(dw) at trial quantiles normalized by final L1; zeros if no snapshots."""
    final_l1 = float(abs((m_final - pristine)).sum())
    if ckpt is None or final_l1 == 0.0:
        return [0.0] * len(QUANT)
    trials = sorted(int(f.stem.split("_")[-1]) for f in ckpt.glob("weights_trial_*.npz"))
    if not trials:
        return [0.0] * len(QUANT)
    out = []
    for q in QUANT:
        i = trials[min(int(q * len(trials)), len(trials) - 1)]
        out.append(float(abs((load_trial(ckpt, i) - pristine)).sum()) / final_l1)
    return out


def wide_features(m, ckpt, pristine, rank_edges, beh_row):
    dd = (m - pristine).tocoo()
    ch = [(float(v)) for v in dd.data if v != 0.0]
    n = len(ch)
    l1 = float(sum(abs(v) for v in ch))
    f2 = [float(n), l1, float(np.sqrt(sum(v * v for v in ch))),
          float(np.std(ch)) if n > 1 else 0.0,
          float(max((abs(v) for v in ch), default=0.0)),
          float(sum(1 for v in ch if v > 0) / n) if n else 0.0]
    top8 = sorted((abs(v) for v in ch), reverse=True)[:8]
    top8 += [0.0] * (8 - len(top8))
    f1 = [float(m[e]) for e in rank_edges]
    f4 = trajectory(m, ckpt, pristine)
    return f1 + f2 + top8 + f4 + list(beh_row)


def beh(m, nodes, lif_params, sugar, seed):
    a = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE), seed=seed)
    c = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE),
                     stimulated2=list(sugar), r_poisson2_Hz=200.0, seed=seed)
    return (float(len(a.spike_times.get(MN9_L, []))),
            float(len(c.spike_times.get(MN9_L, []))))


def main() -> int:
    doc = PREREG6.read_text(encoding="utf-8")
    shadow = grab_seeds(doc, "P6_SHADOW_SEEDS")
    assert "Amendment A3" in doc, "A3 not frozen in prereg"
    if len(shadow) != 8:
        raise an.ScopeError("P6_SHADOW_SEEDS size wrong")

    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    pristine = matrix
    if weight_matrix_hash(pristine) != PRISTINE_HASH:
        raise an.ScopeError("pristine hash mismatch")

    acquired, _ = an.load_final_matrix(TASKB / "ckpt_l1_gng521_feed_0", "R1 gng521")
    d = (acquired - pristine).tocoo()
    rank_edges = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rank_sha = hashlib.sha256(json.dumps(rank_edges).encode()).hexdigest()
    if rank_sha != RANK_SHA_PREREG or len(rank_edges) != 25:
        raise an.ScopeError(f"RANK_SET mismatch: {rank_sha} n={len(rank_edges)}")

    held = shadow[4:]
    held_cache = {}

    def beh_row(m, ckpt, seed):
        a, c = beh(m, nodes, lif_params, sugar, seed)
        key = id(m)
        if key not in held_cache:
            ha = np.mean([beh(m, nodes, lif_params, sugar, s)[0] for s in held])
            hc = np.mean([beh(m, nodes, lif_params, sugar, s)[1] for s in held])
            held_cache[key] = (float(ha), float(hc))
        return (a, c, *held_cache[key])

    # training pool (identical to A2): 6 l1 ckpts x shadow[:4], pristine x 8
    X, y, names = [], [], []
    for k in range(6):
        ck = TASKB / f"ckpt_l1_gng521_feed_{k}"
        m, _ = an.load_final_matrix(ck, f"l1_{k}")
        for s in shadow[:4]:
            X.append(wide_features(m, ck, pristine, rank_edges, beh_row(m, ck, s)))
            y.append(1)
            names.append(f"l1_{k}_s{s}")
    for s in shadow:
        X.append(wide_features(pristine, None, pristine, rank_edges, beh_row(pristine, None, s)))
        y.append(0)
        names.append(f"pristine_s{s}")
    Xtr = np.array(X, float)
    ytr = np.array(y)
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Xtr_s = (Xtr - mu) / sd
    cw = class_weights(ytr)

    loo_pred = []
    for i in range(len(ytr)):
        idx = [j for j in range(len(ytr)) if j != i]
        v = fit_lr(Xtr_s[idx], ytr[idx], w=cw[idx])
        loo_pred.append(int(predict(Xtr_s[i:i + 1], v)[0]))
    loo_acc = float(np.mean([p == t for p, t in zip(loo_pred, ytr)]))
    v_full = fit_lr(Xtr_s, ytr, w=cw)
    member_recall = float(np.mean([p == 1 for p, t in zip(predict(Xtr_s, v_full), ytr) if t == 1]))
    gate_ok = loo_acc >= 0.80 and member_recall == 1.0

    # test: 11 unlearned reps x shadow[:4]
    test_rows = [(f"dev_r{r}", ROOT / "results/phase4/wp_l4b" / f"ckpt_r{r}", r, True)
                 for r in range(3)]
    test_rows += [(f"conf_r{r}", ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "ckpt_r0", r, False)
                  for r in range(8)]
    Xte, te_names, te_rep = [], [], []
    for name, ckpt, r, shared in test_rows:
        m, _ = an.load_final_matrix(ckpt, name)
        rows = an.read_jsonl(
            (ROOT / "results/phase4/wp_l4b" / "l4b_extinction.jsonl") if shared
            else (ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "l4b_extinction.jsonl"),
            name)
        if shared:
            rows = [x for x in rows if x.get("rep") == r]
        c25a = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "alone"]
        c25c = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "cosugar"]
        if len(c25a) != 2 or len(c25c) != 2:
            raise an.IncompleteArtifacts(f"{name}: cycle-25 rows incomplete")
        for s in shadow[:4]:
            a, c = beh(m, nodes, lif_params, sugar, s)
            key = name
            if key not in held_cache:
                held_cache[key] = (float(np.mean([beh(m, nodes, lif_params, sugar, s2)[0] for s2 in held])),
                                   float(np.mean([beh(m, nodes, lif_params, sugar, s2)[1] for s2 in held])))
            Xte.append(wide_features(m, ckpt, pristine, rank_edges, (a, c, *held_cache[key])))
            te_names.append(f"{name}_s{s}")
            te_rep.append(name)
    Xte = np.array(Xte, float)
    preds = predict((Xte - mu) / sd, v_full)
    fr = float(np.mean(preds == 0))
    per_rep = {}
    for n, p, r in zip(te_names, preds, te_rep):
        per_rep.setdefault(r, []).append(int(p == 0))
    per_rep_fr = {r: float(np.mean(v)) for r, v in per_rep.items()}

    # ablation: drop the 4 residual-edge features
    resid_idx = [rank_edges.index((nid[a], nid[b])) for a, b in RESIDUAL_EDGES]
    keep = [i for i in range(Xtr_s.shape[1]) if i not in resid_idx]
    v_abl = fit_lr(Xtr_s[:, keep], ytr, w=cw)
    fr_abl = float(np.mean(predict(((Xte - mu) / sd)[:, keep], v_abl) == 0))
    loo_abl = []
    for i in range(len(ytr)):
        idx = [j for j in range(len(ytr)) if j != i]
        v = fit_lr(Xtr_s[idx][:, keep], ytr[idx], w=cw[idx])
        loo_abl.append(int(predict(Xtr_s[i:i + 1][:, keep], v)[0]))
    loo_abl_acc = float(np.mean([p == t for p, t in zip(loo_abl, ytr)]))

    if not gate_ok:
        verdict, why = "NEGATIVE-B", "wide oracle invalid: instrument inconclusive"
    elif fr == 1.0:
        verdict, why = "PASS", f"FR = {int(round(fr * len(preds)))}/{len(preds)} rows with valid wide oracle (LOO {loo_acc:.3f})"
    else:
        verdict, why = "NEGATIVE-A", f"FR = {fr:.3f} < 1: membership inferable from widened features"

    report = {
        "wp": "L6a-A3", "amendment": "A3 (wide feature set, frozen before run)",
        "prereg": "docs/PHASE_6_PREREG.md", "prereg_sha256": an.sha256_file(PREREG6),
        "n_features": int(Xtr_s.shape[1]), "feature_blocks": {"F1_rank": 25, "F2_stats": 6, "F3_top8": 8, "F4_traj": 6, "F5_beh": 4},
        "rank_set_sha256": rank_sha, "pristine_hash": PRISTINE_HASH,
        "oracle": {"n_rows": len(ytr), "loo_accuracy": loo_acc,
                   "in_sample_member_recall": member_recall, "gate_ok": gate_ok,
                   "ablation_loo_accuracy": loo_abl_acc},
        "test_rows": [{"name": n, "rep": r, "predicted": ("member" if p else "non-member")}
                      for n, r, p in zip(te_names, te_rep, preds)],
        "forgetting_rate_rows": fr, "forgetting_rate_per_rep": per_rep_fr,
        "forgetting_rate_ablated": fr_abl,
        "verdict": verdict, "verdict_reason": why,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "oracle_report_wide_A3.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"features={Xtr_s.shape[1]} rows={len(ytr)} LOO={loo_acc:.3f} member_recall={member_recall:.2f} gate_ok={gate_ok}")
    print(f"FR rows = {int(round(fr * len(preds)))}/{len(preds)} | ablated FR = {fr_abl:.3f} (LOO {loo_abl_acc:.3f})")
    print("per-rep FR:", {r: round(v, 2) for r, v in per_rep_fr.items()})
    print(f"VERDICT: {verdict} - {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
