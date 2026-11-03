"""WP-L6a - retrospective forgetting-rate certification (Phase 6 prereg section 2,
Amendment A2 pool).

Membership-oracle analog over EXISTING artifacts (no new training sims):
  member rows    : 6x ckpt_l1_gng521_feed_* x 4 shadow seeds  (24 (matrix,seed) rows)
  non-member rows: pristine matrix x 8 shadow seeds            (8 rows; the l0
                   ckpts carry no weight snapshots - their run_state hash equals
                   the pristine hash, so pristine IS the never-learned substrate)
  test population: 11 unlearned reps (3 dev + 8 confirmatory), behavior from
                   existing cycle-25 JSONL rows.
Oracle: class-balanced numpy logistic regression; LOO gate >= 0.80 and
in-sample member recall == 1.0; FR = fraction of 11 reps classified non-member.
Ablation: refit without the 4 residual-edge features.

Output: results/phase6/wp_l6a/oracle_report.json
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

PREREG6 = ROOT / "docs" / "PHASE_6_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
TASKB = ROOT / "results/phase2/taskB_r1"
R1CK = TASKB / "ckpt_l1_gng521_feed_0"
OUT = ROOT / "results/phase6/wp_l6a"
CUE = [15957, 16327]
MN9_L = 10331
RESIDUAL_EDGES = [(16327, 15649), (15957, 15649), (16327, 20178), (16327, 516493)]
RANK_SHA_PREREG = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"
PRISTINE_HASH = "384406e9278ae0c0"


def grab_seeds(doc_text: str, name: str) -> list[int]:
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg6 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def fit_lr(X, y, w=None, l2=1e-3, iters=4000, lr=0.5):
    """Deterministic (optionally weighted) L2 logistic regression."""
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    if w is None:
        w = np.ones(n)
    w = np.asarray(w, float)
    reg = np.r_[np.full(d, l2), 0.0]
    v = np.zeros(d + 1)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(Xb @ v)))
        v -= lr * ((Xb.T @ ((p - y) * w)) / w.sum() + reg * v / n)
    return v


def predict(X, v):
    Xb = np.hstack([X, np.ones((X.shape[0], 1))])
    return (1.0 / (1.0 + np.exp(-(Xb @ v))) >= 0.5).astype(int)


def class_weights(y):
    n = len(y)
    return np.where(y == 1, n / (2.0 * max(y.sum(), 1)), n / (2.0 * max((1 - y).sum(), 1)))


def beh(m, nodes, lif_params, sugar, seeds):
    """Per-seed behavioral rows: [alone, cosugar] mn9 spike counts."""
    out = []
    for s in seeds:
        a = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE), seed=s)
        c = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE),
                         stimulated2=list(sugar), r_poisson2_Hz=200.0, seed=s)
        out.append((s, float(len(a.spike_times.get(MN9_L, []))),
                    float(len(c.spike_times.get(MN9_L, [])))))
    return out


def main() -> int:
    doc = PREREG6.read_text(encoding="utf-8")
    shadow = grab_seeds(doc, "P6_SHADOW_SEEDS")
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
        raise an.ScopeError("pristine hash != Amendment A2 evidence hash")

    acquired, _ = an.load_final_matrix(R1CK, "R1 gng521")
    d = (acquired - pristine).tocoo()
    rank_edges = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rank_sha = hashlib.sha256(json.dumps(rank_edges).encode()).hexdigest()
    if rank_sha != RANK_SHA_PREREG or len(rank_edges) != 25:
        raise an.ScopeError(f"RANK_SET hash/size mismatch: {rank_sha} n={len(rank_edges)}")
    cue_idx = {nid[c] for c in CUE}
    an.derive_carriers(pristine, acquired, cue_idx,
                       {nid[p] for p in [13510, 18474, 12364, 14803, 14953,
                                         66802, 516493, 524078, 555850]})

    def white_features(m):
        dd = (m - pristine).tocoo()
        changed = [(int(i), int(j), float(v)) for i, j, v in zip(dd.row, dd.col, dd.data) if v != 0.0]
        return [float(m[e]) for e in rank_edges] + [float(len(changed)),
                                                    float(sum(abs(v) for _, _, v in changed))]

    # ---- training pool (Amendment A2): rows = (matrix, seed) ----
    rows_X, rows_y, rows_names = [], [], []
    for k in range(6):
        m, _ = an.load_final_matrix(TASKB / f"ckpt_l1_gng521_feed_{k}", f"l1_{k}")
        wf = white_features(m)
        for s, alone, cosg in beh(m, nodes, lif_params, sugar, shadow[:4]):
            rows_X.append(wf + [alone, cosg])
            rows_y.append(1)
            rows_names.append(f"l1_{k}_s{s}")
    wf0 = white_features(pristine)
    for s, alone, cosg in beh(pristine, nodes, lif_params, sugar, shadow):
        rows_X.append(wf0 + [alone, cosg])
        rows_y.append(0)
        rows_names.append(f"pristine_s{s}")
    Xtr = np.array(rows_X, float)
    ytr = np.array(rows_y)
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
    in_sample = predict(Xtr_s, v_full)
    member_recall = float(np.mean([p == 1 for p, t in zip(in_sample, ytr) if t == 1]))
    gate_ok = loo_acc >= 0.80 and member_recall == 1.0

    # ---- test population: 11 unlearned reps (behavior from cycle-25 JSONL) ----
    test_rows = [(f"dev_r{r}", ROOT / "results/phase4/wp_l4b" / f"ckpt_r{r}",
                  ROOT / "results/phase4/wp_l4b" / "l4b_extinction.jsonl")
                 for r in range(3)]
    test_rows += [(f"conf_r{r}", ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "ckpt_r0",
                   ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "l4b_extinction.jsonl")
                  for r in range(8)]
    test_X, test_names = [], []
    for name, ckpt, jsonl in test_rows:
        m, _ = an.load_final_matrix(ckpt, name)
        rows = an.read_jsonl(jsonl, f"{name} jsonl")
        alone25 = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "alone"]
        cosg25 = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "cosugar"]
        if len(alone25) != 2 or len(cosg25) != 2:
            raise an.IncompleteArtifacts(f"{name}: cycle-25 probe rows incomplete")
        test_X.append(white_features(m) + [float(np.mean(alone25)), float(np.mean(cosg25))])
        test_names.append(name)
    Xte = np.array(test_X, float)
    Xte_s = (Xte - mu) / sd
    preds = predict(Xte_s, v_full)
    fr = float(np.mean(preds == 0))

    # ---- ablation: drop the 4 residual-edge weight features ----
    resid_idx = [rank_edges.index((nid[a], nid[b])) for a, b in RESIDUAL_EDGES]
    keep = [i for i in range(Xtr_s.shape[1]) if i not in resid_idx]
    v_abl = fit_lr(Xtr_s[:, keep], ytr, w=cw)
    preds_abl = predict(Xte_s[:, keep], v_abl)
    fr_abl = float(np.mean(preds_abl == 0))
    loo_abl = []
    for i in range(len(ytr)):
        idx = [j for j in range(len(ytr)) if j != i]
        v = fit_lr(Xtr_s[idx][:, keep], ytr[idx], w=cw[idx])
        loo_abl.append(int(predict(Xtr_s[i:i + 1][:, keep], v)[0]))
    loo_abl_acc = float(np.mean([p == t for p, t in zip(loo_abl, ytr)]))

    if not gate_ok:
        verdict, why = "NEGATIVE-B", "oracle invalid (LOO<0.80 or member recall<1.0): instrument inconclusive"
    elif fr == 1.0:
        verdict, why = "PASS", "FR = 11/11 with valid oracle: all unlearned substrates indistinguishable from never-learned"
    else:
        verdict, why = "NEGATIVE-A", f"FR = {fr:.3f} < 1: residual membership information is inferable"

    report = {
        "wp": "L6a", "prereg": "docs/PHASE_6_PREREG.md", "prereg_sha256": an.sha256_file(PREREG6),
        "amendment": "A2 (pristine = never-learned substrate; l0 ckpts have no weight snapshots)",
        "rank_set_sha256": rank_sha, "pristine_hash": PRISTINE_HASH,
        "shadow_seeds": shadow,
        "oracle": {"n_rows": len(ytr), "n_member_rows": int(ytr.sum()),
                   "loo_accuracy": loo_acc, "in_sample_member_recall": member_recall,
                   "gate_ok": gate_ok, "ablation_loo_accuracy": loo_abl_acc},
        "training_rows": rows_names,
        "test_reps": [{"name": n, "predicted": ("member" if p else "non-member")}
                      for n, p in zip(test_names, preds)],
        "forgetting_rate": fr, "forgetting_rate_ablated": fr_abl,
        "residual_edge_feature_indices": resid_idx,
        "verdict": verdict, "verdict_reason": why,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "oracle_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"rows={len(ytr)} (member {int(ytr.sum())}) LOO={loo_acc:.3f} member_recall={member_recall:.2f} gate_ok={gate_ok}")
    print(f"FR = {fr:.3f} ({int(round(fr * 11))}/11 non-member) | ablated FR = {fr_abl:.3f} (LOO {loo_abl_acc:.3f})")
    for n, p in zip(test_names, preds):
        print(f"  {n}: {'member' if p else 'non-member'}")
    print(f"VERDICT: {verdict} - {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
