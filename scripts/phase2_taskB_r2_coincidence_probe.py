import json
from pathlib import Path
import numpy as np
from scipy import sparse
import dataclasses
from fly.dynamics.lif import LIFParams, simulate_lif

root = Path("C:/Users/user/fly-cognition")
ck = root/"results/phase2/taskB_r2/ckpt_satprobe"
nodes = np.load(root/"data/processed/neuprint_snapshots/run-007/connectivity_nodes.npy").tolist()
seeds = json.loads((root/"data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text(encoding="utf-8"))
sugar = [r["bodyId"] for r in seeds["sugar_R"]]
CUE = [50843, 53901, 103327, 129624, 556072, 559464]
lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

for t, f in [(14, "weights_trial_0014.npz"), (24, "weights_trial_0024.npz")]:
    M = sparse.load_npz(ck/f).tocsr()
    lif = simulate_lif(M, nodes, lif_params, duration_ms=1000.0,
                       stimulated=CUE, stimulated2=sugar,
                       r_poisson2_Hz=200.0, seed=85_000 + 600 + t)
    nid = {n: i for i, n in enumerate(nodes)}
    MN9 = 10331
    col = nid[MN9]
    pre = M[:, col].tocoo()
    partners = [nodes[r] for r in pre.row]
    arrivals = []
    for p in set(partners):
        arrivals.extend(lif.spike_times.get(p, []))
    arrivals = np.sort(np.array(arrivals))
    if len(arrivals) > 1:
        iv = np.diff(arrivals)
        clustered = float((iv < 2.0).mean())
        print(f"trial {t}: MN9 spikes={len(lif.spike_times.get(MN9, []))}, "
              f"partners={len(partners)}, arrivals={len(arrivals)}, "
              f"median_iv={np.median(iv):.2f}ms, frac_iv_lt_2ms={clustered:.3f}")
    else:
        print(f"trial {t}: no arrivals")
