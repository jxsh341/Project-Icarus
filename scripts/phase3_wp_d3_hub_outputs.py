import json
from pathlib import Path
import numpy as np
from scipy import sparse

BASE = Path("C:/Users/user/fly-cognition/data/processed/neuprint_snapshots/run-007")
matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
nid = {n: i for i, n in enumerate(nodes)}
MN9_L = 10331

nt_map = {}
for f in sorted(BASE.glob("neurons_batch_*.json")):
    for rec in json.loads(f.read_text(encoding="utf-8")):
        nt_map[rec["bodyId"]] = (rec.get("consensusNt"), rec.get("type"))

for hub in (10646, 10094):
    r = nid[hub]
    row = matrix[r, :].tocoo()
    nz = sorted([(float(w), nodes[j]) for j, w in zip(row.col, row.data) if w != 0],
                key=lambda t: -abs(t[0]))
    tot = sum(abs(w) for w, _ in nz)
    print(f"{hub} ({nt_map[hub][1]}, {nt_map[hub][0]}): {len(nz)} targets, |out|={tot:.0f}")
    for w, t in nz[:12]:
        nt, ty = nt_map.get(t, (None, None))
        print(f"   -> {t} ({ty}, {nt}): {w:+.0f}")
    print()
