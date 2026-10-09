"""WP-L3d scope-vs-rate check (review-directed 2026-10-09).

The NEGATIVE-A diagnosis said 'rate-limited (equal-eta, head-start)'.
The reviewer's alternative: SCOPE-limited - extinction touches only
11-13 edges/trial vs acquisition's 334-edge footprint. If the
touched set is a small fixed subset, eta-asymmetry (fork 1) just
erodes the same subset faster and NEVER reverses the association.

Check, from existing per-trial weight checkpoints (no new sims):
1. The identity of edges weakened per trial, across all 25 trials,
   all 3 reps: same small fixed set (scope-capped) or growing
   coverage (rate-capped)?
2. The same-edge-set comparison vs GNG521's ACQUISITION footprint
   (R1 ckpt: which edges grew during the 15 acquisition trials).
3. Cumulative coverage: |union of weakened edges| vs |acquisition
   footprint| - the number that decides the fork.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
L3D = Path("results/phase3/wp_l3d")
MN9_L = 10331


def edges_from_diff(m0, m1):
    d = (m1 - m0).tocoo()
    return {(int(r), int(c)): float(v) for r, c, v in zip(d.row, d.col, d.data) if v != 0}


def main() -> int:
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    cue_idx = [nid[c] for c in (15957, 16327)]

    # acquisition footprint: R1 ckpt weights_trial_0000 (pristine) vs 0015
    files = sorted(R1CK.glob("weights_trial_*.npz"))
    w0 = sparse.load_npz(files[0]).tocsr()
    w15 = sparse.load_npz(files[15]).tocsr()
    acq = edges_from_diff(w0, w15)
    acq_cue_incident = {k for k in acq if k[0] in cue_idx}
    print(f"acquisition footprint (t0->t15): {len(acq)} edges "
          f"({len(acq_cue_incident)} cue-incident)")

    # extinction touched edges per rep: successive weight diffs
    for rep in range(3):
        ck = L3D / f"ckpt_r{rep}"
        wf = sorted(ck.glob("weights_trial_*.npz"))
        if not wf:
            print(f"rep {rep}: no checkpoints")
            continue
        union = {}
        per_trial_n = []
        prev = sparse.load_npz(wf[0]).tocsr()
        for f in wf[1:]:
            cur = sparse.load_npz(f).tocsr()
            d = edges_from_diff(prev, cur)
            neg = {k: v for k, v in d.items() if v < 0}
            per_trial_n.append(len(neg))
            union.update(neg)
            prev = cur
        print(f"\nrep {rep}: {len(wf)-1} trials checkpointed, "
              f"neg edges/trial: {per_trial_n[:10]}...")
        print(f"  UNION of weakened edges over run: {len(union)}")
        # overlap with acquisition footprint
        inter = set(union) & set(acq)
        inter_ci = set(union) & acq_cue_incident
        print(f"  overlap with acq footprint: {len(inter)} of {len(acq)} "
              f"({100*len(inter)/len(acq):.1f}%)")
        print(f"  overlap with acq CUE-INCIDENT edges: {len(inter_ci)} "
              f"of {len(acq_cue_incident)} ({100*len(inter_ci)/len(acq_cue_incident):.1f}%)")
        # magnitude comparison
        tot_removed = sum(abs(v) for v in union.values())
        acq_mass = sum(abs(v) for v in acq.values())
        print(f"  total weakened mass: {tot_removed:.1f} vs acq mass {acq_mass:.1f} "
              f"({100*tot_removed/acq_mass:.2f}%)")
        # is the touched set FIXED? compare first-half vs second-half unions
        half = len(wf) // 2
        u1, u2 = {}, {}
        prev = sparse.load_npz(wf[0]).tocsr()
        for k, f in enumerate(wf[1:]):
            cur = sparse.load_npz(f).tocsr()
            d = edges_from_diff(prev, cur)
            neg = {kk: vv for kk, vv in d.items() if vv < 0}
            (u1 if k < half else u2).update(neg)
            prev = cur
        only_late = set(u2) - set(u1)
        print(f"  new edges recruited in 2nd half: {len(only_late)} "
              f"({'growing coverage' if len(only_late) > 3 else 'fixed small set'})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
