import json
from pathlib import Path
import numpy as np
from scipy import sparse

from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun

root = Path("C:/Users/user/fly-cognition")
BASE = root/"data/processed/neuprint_snapshots/run-007"
MN9_L = 10331

# CLAIM AUDIT 1: probe ranges as stated in the close-out
rows = [json.loads(l) for l in
        (root/"results/phase4/wp_l4b/l4b_extinction.jsonl"
         ).read_text(encoding="utf-8").splitlines() if l.strip()]
cos = [r["mn9_hz"] for r in rows if r.get("ptype") == "cosugar"]
alone_c5 = [r["mn9_hz"] for r in rows if r.get("ptype") == "alone" and r["cycle"] == 5]
alone_c10 = [r["mn9_hz"] for r in rows if r.get("ptype") == "alone" and r["cycle"] == 10]
print(f"cosugar: min={min(cos)}, max={max(cos)}  (close-out claims 78-92)")
print(f"alone c5: min={min(alone_c5)}, max={max(alone_c5)}  (claims 68-84)")
print(f"alone c10: min={min(alone_c10)}, max={max(alone_c10)}  (claims 26-72)")

# CLAIM AUDIT 2: "byte-identical edge outcomes across reps" at float precision
guard = PlasticityGuard(StabilityThresholds(
    max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0, inh_weight_drift_frac=0.20))
rule = HebbianRule(PlasticityConfig(eta=1e-4, w_max=766.0, semantics=Semantics.V_CLIP))
finals = []
for rep in range(3):
    run = TrainingRun.load(root/f"results/phase4/wp_l4b/ckpt_r{rep}",
                           sparse.load_npz(BASE/"connectivity_matrix_signed.npz").tocsr(),
                           np.load(BASE/"connectivity_nodes.npy").tolist(),
                           rule, guard, MN9_L)
    finals.append(run.matrix)
m0, m1, m2 = finals
d01 = (m0 - m1).tocoo()
d02 = (m0 - m2).tocoo()
n01 = int(np.count_nonzero(d01.data)) if d01.data.size else 0
n02 = int(np.count_nonzero(d02.data)) if d02.data.size else 0
print(f"\nfloat-exact final-matrix comparison across reps:")
print(f"  rep0 vs rep1: {n01} differing entries (of {m0.nnz})")
print(f"  rep0 vs rep2: {n02} differing entries (of {m0.nnz})")
if n01 == 0 and n02 == 0:
    print("  -> EXACTLY identical: claim holds")
else:
    print("  -> NOT identical: close-out over-claims; inspect below")
    diffs = sorted(set(zip(d01.row[d01.data != 0], d01.col[d01.data != 0])) |
                   set(zip(d02.row[d02.data != 0], d02.col[d02.data != 0])))
    nodes = np.load(BASE/"connectivity_nodes.npy").tolist()
    for r, c in diffs[:10]:
        print(f"    {nodes[r]}->{nodes[c]}: rep0={m0[r,c]:.6f} rep1={m1[r,c]:.6f} rep2={m2[r,c]:.6f}")
