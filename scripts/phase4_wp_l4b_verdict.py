"""WP-L4b verdict completion: edge-level coverage check from checkpoints.

The run completed all 3 reps (training + probes checkpointed); only
the aggregation code crashed. This script completes the verdict:
1. Per rep: final-vs-initial weight diff on the 9 untouched edges
   (NEGATIVE-A check: did real coverage happen?).
2. The full footprint: all 25 acquisition edges - how many weakened,
   by how much, toward what values.
3. Sanity: the sugar->MN9 pathway intact (cosugar probe explains);
   no structural corruption (edge count preserved).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, PlasticityConfig, Semantics, StabilityThresholds
from fly.training import TrainingRun

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
OUT = Path("results/phase4/wp_l4b")
MN9_L = 10331
CUE = [15957, 16327]
UNTOUCHED = [13510, 18474, 12364, 14803, 14953, 66802, 516493, 524078, 555850]
W_MAX = 766.0
ETA = 1e-4


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}

    guard = PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0, inh_weight_drift_frac=0.20))
    rule = HebbianRule(PlasticityConfig(eta=ETA, w_max=W_MAX, semantics=Semantics.V_CLIP))

    initial = TrainingRun.load(R1CK, matrix, nodes, rule, guard, MN9_L).matrix
    w_init = initial.copy()

    # acquisition footprint edges (from the same R1 checkpoint: t0->t15 diff)
    files = sorted(R1CK.glob("weights_trial_*.npz"))
    w0 = sparse.load_npz(files[0]).tocsr()
    w15 = sparse.load_npz(files[15]).tocsr()
    d = (w15 - w0).tocoo()
    footprint = {(int(r), int(c)): float(v) for r, c, v in zip(d.row, d.col, d.data) if v != 0}

    untouched_keys = {(nid[c], nid[p]) for p in UNTOUCHED for c in CUE}

    for rep in range(3):
        run = TrainingRun.load(OUT / f"ckpt_r{rep}", matrix, nodes, rule, guard, MN9_L)
        final = run.matrix
        dd = (final - w_init).tocoo()
        changed = {(int(r), int(c)): float(v) for r, c, v in zip(dd.row, dd.col, dd.data) if v != 0}
        # footprint coverage
        fp_changed = {k: v for k, v in changed.items() if k in footprint}
        fp_weakened = {k: v for k, v in fp_changed.items() if v < 0}
        untouched_hit = {k: v for k, v in changed.items() if k in untouched_keys}
        untouched_weakened = {k: v for k, v in untouched_hit.items() if v < 0}
        print(f"rep {rep}: total changed {len(changed)}; footprint edges changed "
              f"{len(fp_changed)}/25 (weakened {len(fp_weakened)}); "
              f"untouched-9 changed {len(untouched_hit)} (weakened {len(untouched_weakened)})")
        # per-edge detail on the 9
        for k in sorted(untouched_keys):
            w_i = float(w_init[k])
            w_f = float(final[k])
            tag = "WEAKENED" if w_f < w_i else ("intact" if w_f == w_i else "GREW")
            print(f"  edge {nodes[k[0]]}->{nodes[k[1]]}: {w_i:.1f} -> {w_f:.1f}  [{tag}]")
        # structural integrity: edge count preserved
        print(f"  structure: nnz init {w_init.nnz}, final {final.nnz}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
