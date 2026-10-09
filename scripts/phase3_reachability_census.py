"""Reachability census: the untouched 40% (WP-L3d follow-up, Phase 3 closer).

Q-A (protocol-family) and Q-B (closure-wide), per the registered
scope distinction. Pure structural analysis on the frozen matrix -
NO simulations.

Inputs (all from existing checkpoints):
- GNG521 acquisition footprint: R1 ckpt t0->t15 diff (25 edges).
- Extinction touched sets: L3d ckpt per-trial diffs, union per rep
  (15-18 edges). Untouched = footprint - union (rep 0, the widest).
For each untouched cue->X edge's postsynaptic partner X:
- Q-A: what drives X under cue+bitter presentations? X's in-edges
  from the bitter GRN set, the PPL trio, and the cue itself;
  PLUS X's 1-hop-in neighbors that are themselves driven (would X
  fire under the extinction protocol's reachable activity?).
  Answered structurally: sum of possible excitatory input X can
  receive from populations present in the protocol.
- Q-B: X's FULL in-edge list from the closure - every identifiable
  input source, weighted, with NT/type labels. If X has strong
  inputs from any population, a differently-designed protocol
  could in principle recruit them.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
L3D = Path("results/phase3/wp_l3d")
OUT = Path("results/phase3/wp_l3d/reachability_census.json")
CUE = [15957, 16327]
MN9_L = 10331


def edges_from_diff(m0, m1):
    d = (m1 - m0).tocoo()
    return {(int(r), int(c)): float(v) for r, c, v in zip(d.row, d.col, d.data) if v != 0}


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    PPL_TRIO = [11618, 11900, 529516]

    # metadata
    meta = {}
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            meta[rec["bodyId"]] = rec

    # footprint + touched sets
    files = sorted(R1CK.glob("weights_trial_*.npz"))
    w0 = sparse.load_npz(files[0]).tocsr()
    w15 = sparse.load_npz(files[15]).tocsr()
    acq = edges_from_diff(w0, w15)
    union = {}
    wf = sorted((L3D / "ckpt_r0").glob("weights_trial_*.npz"))
    prev = sparse.load_npz(wf[0]).tocsr()
    for f in wf[1:]:
        cur = sparse.load_npz(f).tocsr()
        d = edges_from_diff(prev, cur)
        union.update({k: v for k, v in d.items() if v < 0})
        prev = cur
    untouched = {k: acq[k] for k in acq if k not in union}
    print(f"footprint {len(acq)}, touched {len(union)}, untouched {len(untouched)}")
    print(f"untouched edges (cue -> partner): "
          f"{[(nodes[k[0]], nodes[k[1]], round(v,1)) for k, v in untouched.items()]}")

    # why each untouched partner was missed: X's in-edges
    report = {}
    for (ci, xi), w_acq in untouched.items():
        X = nodes[xi]
        col = matrix[:, xi].tocoo()
        in_edges = sorted([(float(w), nodes[i]) for i, w in zip(col.row, col.data) if w != 0],
                          key=lambda t: -abs(t[0]))
        # Q-A classification
        q_a_sources = {"cue": 0.0, "bitter_grn": 0.0, "ppl_trio": 0.0, "sugar_grn": 0.0}
        for w, src in in_edges:
            if src in CUE:
                q_a_sources["cue"] += w
            elif src in bitter:
                q_a_sources["bitter_grn"] += w
            elif src in PPL_TRIO:
                q_a_sources["ppl_trio"] += w
            elif src in sugar:
                q_a_sources["sugar_grn"] += w
        # Q-B: full in-edge structure
        q_b = [{"src": src, "w": round(w, 1),
                "nt": meta.get(src, {}).get("consensusNt"),
                "type": meta.get(src, {}).get("type")} for w, src in in_edges[:10]]
        report[X] = {"acq_weight": round(w_acq, 1), "q_a_sources": q_a_sources,
                     "q_b_top_inputs": q_b, "n_inputs": len(in_edges),
                     "X_type": meta.get(X, {}).get("type"),
                     "X_nt": meta.get(X, {}).get("consensusNt")}
        print(f"\n{X} ({report[X]['X_type']}, {report[X]['X_nt']}): "
              f"acq weight {w_acq:.0f}, {len(in_edges)} inputs")
        print(f"  Q-A: {q_a_sources}")
        for e in q_b[:5]:
            print(f"  Q-B in: {e['src']} ({e['type']}, {e['nt']}): {e['w']}")

    OUT.write_text(json.dumps({str(k): v for k, v in report.items()}, indent=2),
                   encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
