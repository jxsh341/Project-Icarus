import json
from pathlib import Path
import numpy as np
from scipy import sparse

BASE = Path("C:/Users/user/fly-cognition/data/processed/neuprint_snapshots/run-007")
matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
nid = {n: i for i, n in enumerate(nodes)}

HUBS = [10646, 10094]
INTER = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
MN9_L = 10331
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]

print("== hub -> GNG380 intermediates edges (the load-bearing connectivity check) ==")
for h in HUBS:
    r = nid[h]
    row = matrix[r, :].tocoo()
    for x in INTER:
        w = float(matrix[r, nid[x]])
        print(f"  {h} -> {x}: {w:+.1f}")

print("\n== hub -> MN9_L, hub -> gate-DA (feedback), gate-DA -> intermediates (direct) ==")
for h in HUBS:
    print(f"  {h} -> MN9_L: {float(matrix[nid[h], nid[MN9_L]]):+.1f}")
for h in HUBS:
    for g in GATE_DA:
        w = float(matrix[nid[h], nid[g]])
        if w != 0:
            print(f"  {h} -> gateDA {g}: {w:+.1f}")
for g in GATE_DA:
    for x in INTER:
        w = float(matrix[nid[g], nid[x]])
        if w != 0:
            print(f"  gateDA {g} -> inter {x}: {w:+.1f}")

# who DO the hubs' strong targets connect to? 2-hop: hub -> top targets -> intermediates?
print("\n== 2-hop hub influence: hub -> top-10 targets -> intermediates ==")
for h in HUBS:
    r = nid[h]
    row = matrix[r, :].tocoo()
    nz = sorted([(abs(float(w)), nodes[j]) for j, w in zip(row.col, row.data) if w != 0],
                key=lambda t: -t[0])[:10]
    print(f"  {h}:")
    for aw, t in nz:
        tr = nid[t]
        trow = matrix[tr, :].tocoo()
        hits = [(nodes[j], float(w)) for j, w in zip(trow.col, trow.data)
                if nodes[j] in INTER and w != 0]
        print(f"    {t} (|w|={aw:.0f}) -> intermediates: {hits}")
