import json
from pathlib import Path
import numpy as np
from scipy import sparse

BASE = Path("C:/Users/user/fly-cognition/data/processed/neuprint_snapshots/run-007")
matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
nid = {n: i for i, n in enumerate(nodes)}

nt_map = {}
for f in sorted(BASE.glob("neurons_batch_*.json")):
    for rec in json.loads(f.read_text(encoding="utf-8")):
        nt_map[rec["bodyId"]] = (rec.get("consensusNt"), rec.get("type"))

gate_da = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
print("== full input lists for the 9 gate DA neurons ==")
for b in gate_da:
    r = nid[b]
    col = matrix[:, r].tocoo()
    srcs = []
    for i, w in zip(col.row, col.data):
        if w != 0:
            s = nodes[i]
            nt, ty = nt_map.get(s, (None, None))
            srcs.append((s, ty, nt, float(w)))
    print(f"\n{b} ({nt_map.get(b, (None, None))[1]}):")
    for s, ty, nt, w in srcs:
        print(f"   {s} ({ty}, {nt}): {w:+.0f}")

# and: what are the DA sources' OWN drivers, one level up, for the strongest (10898, 12588)?
print("\n== one level up: drivers of the strongest gate-DA sources ==")
for b in (10898, 12588):
    r = nid[b]
    col = matrix[:, r].tocoo()
    upstream = [(nodes[i], nt_map.get(nodes[i], (None, None))[1],
                 nt_map.get(nodes[i], (None, None))[0], float(w))
                for i, w in zip(col.row, col.data) if w != 0]
    print(f"  {b} upstream ({len(upstream)}):")
    for s, ty, nt, w in upstream[:12]:
        print(f"     {s} ({ty}, {nt}): {w:+.0f}")
