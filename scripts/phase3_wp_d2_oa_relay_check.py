import json
from pathlib import Path
import numpy as np
from scipy import sparse

BASE = Path("C:/Users/user/fly-cognition/data/processed/neuprint_snapshots/run-007")
matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
nid = {n: i for i, n in enumerate(nodes)}
seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
sugar = [r["bodyId"] for r in seeds["sugar_R"]]
bitter = [r["bodyId"] for r in seeds["bitter_R"]]

# OA relay neurons driving the gate-DA cells
oa = [10120, 11608, 12109]
print("== do sugar/bitter GRNs reach the OA relay neurons? ==")
for b in oa:
    r = nid[b]
    col = matrix[:, r].tocoo()
    src_sugar = [(nodes[i], float(w)) for i, w in zip(col.row, col.data)
                 if nodes[i] in sugar and w != 0]
    src_bitter = [(nodes[i], float(w)) for i, w in zip(col.row, col.data)
                  if nodes[i] in bitter and w != 0]
    print(f"\n{b}: sugar inputs={src_sugar}, bitter inputs={src_bitter}")
    # full input list, top 10 by |w|
    srcs = sorted([(float(w), nodes[i]) for i, w in zip(col.row, col.data) if w != 0],
                  key=lambda t: -abs(t[0]))
    print(f"  top inputs by |w| ({len(srcs)} total):")
    for w, s in srcs[:10]:
        print(f"    {s}: {w:+.0f}")

# two-hop: sugar -> X -> OA
print("\n== two-hop sugar->X->OA relay paths ==")
for b in oa:
    r = nid[b]
    col = matrix[:, r].tocoo()
    mids = {nodes[i] for i, w in zip(col.row, col.data) if w != 0}
    for s in sugar:
        sidx = nid[s]
        row = matrix[sidx, :].tocoo()
        hits = [(nodes[j], float(row.data[k]), float(col.data[col.row == j][0]) if (col.row == j).any() else 0)
                for k, j in enumerate(row.col)]
        hits = [(m, w1, w2) for m, w1, w2 in hits if m in mids and w1 != 0]
        if hits:
            print(f"  sugar {s} -> {b}: {hits[:4]}")
