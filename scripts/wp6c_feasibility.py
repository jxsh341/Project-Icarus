"""WP6c feasibility: are the driven GRN populations + MN9 in run-006, and reachable?"""
import json
from pathlib import Path

import numpy as np
from scipy import sparse

base = Path("data/processed/neuprint_snapshots/run-006")
matrix = sparse.load_npz(base / "connectivity_matrix_signed.npz").tocsr()
node_ids = np.load(base / "connectivity_nodes.npy").tolist()
index_of = {n: i for i, n in enumerate(node_ids)}

sugar_types, bitter_types = {"LB3b", "LB3c"}, {"LB1a", "LB1b", "LB1c", "LB1d"}
sugar, bitter = [], []
for p in sorted(base.glob("neurons_batch_*.json")):
    for r in json.loads(p.read_text(encoding="utf-8")):
        t = r.get("type")
        if t in sugar_types:
            sugar.append((r["bodyId"], t, r.get("rootSide")))
        elif t in bitter_types:
            bitter.append((r["bodyId"], t, r.get("rootSide")))

sugar_r = [b for b, t, s in sugar if s == "R"]
bitter_r = [b for b, t, s in bitter if s == "R"]
print(f"sugar GRNs in run-006: {len(sugar)} ({len(sugar_r)} right): {sorted(sugar_r)}")
print(f"bitter GRNs in run-006: {len(bitter)} ({len(bitter_r)} right)")
print("Shiu drove: 21 sugar / 20 bitter (right hemisphere)")

mn9 = [b for b in (10331, 16949) if b in index_of]
print(f"MN9 present in run-006: {mn9}")

if mn9 and sugar_r:
    src = [index_of[b] for b in sugar_r if b in index_of]
    tgt = {index_of[b] for b in mn9}
    dist = {i: 0 for i in src}
    frontier = list(src)
    reached = False
    for h in range(1, 9):
        if not frontier:
            break
        nxt = set()
        for i in frontier:
            nxt.update(matrix.getrow(i).nonzero()[1])
        nxt -= dist.keys()
        for j in nxt:
            dist[j] = h
        if tgt & set(dist):
            print(f"MN9 first reached at hop {h}")
            reached = True
            break
        frontier = list(nxt)
    if not reached:
        print("MN9 NOT reachable within 8 hops from sugar GRNs in run-006")
