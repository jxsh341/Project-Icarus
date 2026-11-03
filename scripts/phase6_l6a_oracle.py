"""WP-L6a - retrospective forgetting-rate certification (Phase 6 prereg section 2).

Membership-oracle analog over EXISTING artifacts (no new training sims):
  member class    : 6x ckpt_l1_gng521_feed_*  (acquired state)
  non-member class: 6x ckpt_l0_gng521_feed_*  (never learned)
  test population : 11 unlearned reps (3 dev + 8 confirmatory)
Oracle: deterministic numpy logistic regression; LOO-CV validity gate;
forgetting rate FR = fraction of the 11 unlearned reps classified non-member.
Ablation: refit without the 4 residual-edge features (dose-tail question).

Output: results/phase6/wp_l6a/oracle_report.json
Frozen by docs/PHASE_6_PREREG.md (committed before this run). Any artifact
mismatch -> loud failure, no verdict.
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
import phase5_expA_analysis as an  # noqa: E402

PREREG6 = ROOT / "docs" / "PHASE_6_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
TASKB = ROOT / "results" / "phase2" / "taskB_r1"
R1CK = TASKB / "ckpt_l1_gng521_feed_0"
OUT = ROOT / "results" / "phase6" / "wp_l6a"
CUE = [15957, 16327]
MN9_L = 10331
RESIDUAL_EDGES = [(16327, 15649), (15957, 15649), (16327, 20178), (16327, 516493)]
RANK_SHA_PREREG = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"


def grab_seeds(doc_text: str, name: str) -> list[int]:
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg6 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def fit_lr(X: np.ndarray, y: np.ndarray, l2: float = 1e-3,
           iters: int = 4000, lr: float = 0.5) -> np.ndarray:
    """Deterministic L2 logistic regression (intercept unregularized)."""
    n, d = X.shape
    Xb = np.hstack([X, np.ones((n, 1))])
    w = np.zeros(d + 1)
    reg = np.r_[np.full(d, l2), 0.0]
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(Xb @ w)))
        w -= lr * (Xb.T @ (p - y) + reg * w) / n
    return w


def predict(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    Xb = np.hstack([X, np.ones((X.shape[0], 1))])
    return (1.0 / (1.0 + np.exp(-(Xb @ w))) >= 0.5).astype(int)


def main() -> int:
    doc = PREREG6.read_text(encoding="utf-8")
    shadow = grab_seeds(doc, "P6_SHADOW_SEEDS")
    if len(shadow) != 8:
        raise an.ScopeError(f"P6_SHADOW_SEEDS: expected 8, got {len(shadow)}")
    probe_seeds = shadow[:3]

    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    pristine = matrix
    acquired, _ = an.load_final_matrix(R1CK, "R1 gng521")

    # RANK_SET: footprint vs pristine, hash-checked against the prereg doc
    d = (acquired - pristine).tocoo()
    rank_edges = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rank_sha = hashlib.sha256(json.dumps(rank_edges).encode()).hexdigest()
    doc_sha = re.search(r"sha256 of the sorted edge list\s*`([0-9a-f]{64})`", doc, re.S)
    if not doc_sha or rank_sha != doc_sha.group(1) or rank_sha != RANK_SHA_PREREG:
        raise an.ScopeError(f"RANK_SET hash mismatch: computed {rank_sha}")
    if len(rank_edges) != 25:
        raise an.ScopeError(f"footprint {len(rank_edges)} != 25")
    cue_idx = {nid[c] for c in CUE}
    carriers, unt = an.derive_carriers(pristine, acquired, cue_idx,
                                       {nid[p] for p in [13510, 18474, 12364, 14803, 14953,
                                                        66802, 516493, 524078, 555850]})

    def white_features(m: sparse.csr_matrix) -> list[float]:
        dd = (m - pristine).tocoo()
        changed = [(int(i), int(j), float(v)) for i, j, v in zip(dd.row, dd.col, dd.data) if v != 0.0]
        l1 = float(sum(abs(v) for _, _, v in changed))
        return [float(m[e]) for e in rank_edges] + [float(len(changed)), l1]

    def behavioral_sim(m: sparse.csr_matrix) -> list[float]:
        """cue-alone and cosugar (cue+sugar, L4b probe semantics) at 3 shadow
        seeds; returns [mean_alone, mean_cosugar]."""
        out = {"alone": [], "cosugar": []}
        for s in probe_seeds:
            a = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE), seed=s)
            out["alone"].append(len(a.spike_times.get(MN9_L, [])))
            c = simulate_lif(m, nodes, lif_params, 1000.0, stimulated=list(CUE),
                             stimulated2=list(sugar), r_poisson2_Hz=200.0, seed=s)
            out["cosugar"].append(len(c.spike_times.get(MN9_L, [])))
        return [float(np.mean(out["alone"])), float(np.mean(out["cosugar"]))]

    # ---- training pool: 6 member (l1) vs 6 non-member (l0) ----
    train_X, train_y, train_names = [], [], []
    for k in range(6):
        for lbl, sub in (("member", f"ckpt_l1_gng521_feed_{k}"),
                         ("nonmember", f"ckpt_l0_gng521_feed_{k}")):
            m, _ = an.load_final_matrix(TASKB / sub, sub)
            train_X.append(white_features(m) + behavioral_sim(m))
            train_y.append(1 if lbl == "member" else 0)
            train_names.append(sub)
    Xtr = np.array(train_X, dtype=float)
    ytr = np.array(train_y)
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Xtr_s = (Xtr - mu) / sd

    # LOO validity gate
    loo_pred = []
    for i in range(len(ytr)):
        idx = [j for j in range(len(ytr)) if j != i]
        w = fit_lr(Xtr_s[idx], ytr[idx])
        loo_pred.append(int(predict(Xtr_s[i:i + 1], w)[0]))
    loo_acc = float(np.mean([p == t for p, t in zip(loo_pred, ytr)]))
    w_full = fit_lr(Xtr_s, ytr)
    in_sample = predict(Xtr_s, w_full)
    member_recall = float(np.mean([p == 1 for p, t in zip(in_sample, ytr) if t == 1]))
    gate_ok = loo_acc >= 10 / 12 and member_recall == 1.0

    # ---- test population: 11 unlearned reps ----
    test_rows = []
    for r in range(3):
        test_rows.append((f"dev_r{r}", ROOT / "results/phase4/wp_l4b" / f"ckpt_r{r}",
                          ROOT / "results/phase4/wp_l4b" / "l4b_extinction.jsonl", r))
    for r in range(8):
        test_rows.append((f"conf_r{r}",
                          ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "ckpt_r0",
                          ROOT / "results/phase4/wp_l4b_confirm" / f"rep_r{r}" / "l4b_extinction.jsonl", r))
    test_X, test_names = [], []
    for name, ckpt, jsonl, r in test_rows:
        m, _ = an.load_final_matrix(ckpt, name)
        rows = an.read_jsonl(jsonl, f"{name} jsonl")
        alone25 = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "alone"]
        cosg25 = [x["mn9_hz"] for x in rows if x.get("cycle") == 25 and x.get("ptype") == "cosugar"]
        if len(alone25) != 2 or len(cosg25) != 2:
            raise an.IncompleteArtifacts(f"{name}: cycle-25 probe rows incomplete")
        beh = [float(np.mean(alone25)), float(np.mean(cosg25))]
        test_X.append(white_features(m) + beh)
        test_names.append(name)
    Xte = np.array(test_X, dtype=float)
    Xte_s = (Xte - mu) / sd
    preds = predict(Xte_s, w_full)
    fr = float(np.mean(preds == 0))

    # ---- ablation: drop the 4 residual-edge weight features ----
    resid_idx = [rank_edges.index((nid[a], nid[b])) for a, b in RESIDUAL_EDGES]
    keep = [i for i in range(Xtr_s.shape[1]) if i not in resid_idx]
    w_abl = fit_lr(Xtr_s[:, keep], ytr)
    preds_abl = predict(Xte_s[:, keep], w_abl)
    fr_abl = float(np.mean(preds_abl == 0))
    loo_abl = []
    for i in range(len(ytr)):
        idx = [j for j in range(len(ytr)) if j != i]
        w = fit_lr(Xtr_s[idx][:, keep], ytr[idx])
        loo_abl.append(int(predict(Xtr_s[i:i + 1][:, keep], w)[0]))
    loo_abl_acc = float(np.mean([p == t for p, t in zip(loo_abl, ytr)]))

    # ---- verdict (frozen three-way) ----
    if not gate_ok:
        verdict = "NEGATIVE-B"
        verdict_reason = "oracle invalid (LOO<10/12 or member recall<6/6): instrument inconclusive"
    elif fr == 1.0:
        verdict = "PASS"
        verdict_reason = "FR = 11/11 with valid oracle: all unlearned substrates indistinguishable from never-learned"
    else:
        verdict = "NEGATIVE-A"
        verdict_reason = f"FR = {fr:.3f} < 1: residual membership information is inferable"

    report = {
        "wp": "L6a", "prereg": "docs/PHASE_6_PREREG.md",
        "prereg_sha256": an.sha256_file(PREREG6),
        "rank_set_sha256": rank_sha, "rank_set_size": len(rank_edges),
        "shadow_probe_seeds": probe_seeds,
        "oracle": {"loo_accuracy": loo_acc, "loo_predictions": loo_pred,
                   "in_sample_member_recall": member_recall, "gate_ok": gate_ok,
                   "ablation_loo_accuracy": loo_abl_acc},
        "training_pool": train_names,
        "test_reps": [{"name": n, "predicted": ("member" if p else "non-member"),
                       "alone_c25_mean": float(Xte[i, -2]), "cosugar_c25_mean": float(Xte[i, -1])}
                      for i, (n, p) in enumerate(zip(test_names, preds))],
        "forgetting_rate": fr, "forgetting_rate_ablated": fr_abl,
        "residual_edge_feature_indices": resid_idx,
        "verdict": verdict, "verdict_reason": verdict_reason,
        "notes": ["Behavioral features use L4b probe semantics: 'cosugar' probe = cue+sugar; "
                  "test-rep behavioral values from existing cycle-25 JSONL rows (no new sims), "
                  "training-ckpt values from 3 shadow-seed probe sims, averaged per probe type."],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "oracle_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"LOO acc {loo_acc:.3f} (gate >=0.833), member recall {member_recall:.2f}, gate_ok={gate_ok}")
    print(f"FR = {fr:.3f} ({int(round(fr * 11))}/11 non-member) | ablated FR = {fr_abl:.3f}")
    for n, p in zip(test_names, preds):
        print(f"  {n}: {'member' if p else 'non-member'}")
    print(f"VERDICT: {verdict} - {verdict_reason}")
    print(f"report: {OUT / 'oracle_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
