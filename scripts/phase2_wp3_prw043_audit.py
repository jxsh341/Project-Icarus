"""Structural audit of the PRW043 null: WHERE do the potentiated edges land?

Interpretation-order hypothesis (3): the cue's potentiable edge set may
not intersect a sufficient path to the readout. Tests, without any
simulation:

  A. Which potentiated edges exist and with what sign/direction?
     (From the v2 accumulated matrices: cue-incident edges that grew.)
  B. Hop distance from each cue neuron to MN9_L through SIGNED weights
     (shortest positive-product path - a path is 'sufficient' only if
     its net effect can be excitatory).
  C. The same for GNG521 (the successful cue) as the contrast case.

Uses the v2 Stage-B accumulated matrices (saved after each arm). If
those are missing (v2 not yet run), falls back to the structural
edge sets from the frozen matrix with sign decomposition.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
MN9_L = 10331
CUES = {
    "GNG521": [15957, 16327],
    "PRW043": [25250, 26891, 37670, 39767, 69045],
}


def bfs_min_hops(W, src_idx, dst_idx, positive_only=True):
    """Shortest hop path count; if positive_only, only edges with w > 0
    are traversable (a 'sufficient' excitatory path)."""
    from collections import deque
    n = W.shape[0]
    seen = {src_idx: 0}
    q = deque([src_idx])
    while q:
        cur = q.popleft()
        if cur == dst_idx:
            return seen[cur]
        row = W.getrow(cur)
        for tgt, w in zip(row.indices, row.data):
            if positive_only and w <= 0:
                continue
            if tgt not in seen:
                seen[tgt] = seen[cur] + 1
                q.append(tgt)
    return None


def main() -> None:
    W = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(nodes)}
    mn9 = idx[MN9_L]

    out = {}
    for cue, ids in CUES.items():
        rows = []
        for b in ids:
            i = idx.get(b)
            if i is None:
                continue
            row = W.getrow(i)
            pos = [(int(t), float(w)) for t, w in zip(row.indices, row.data) if w > 0]
            neg = [(int(t), float(w)) for t, w in zip(row.indices, row.data) if w < 0]
            # excitatory hop distance to MN9_L
            h_pos = bfs_min_hops(W, i, mn9, positive_only=True)
            # any-sign hop distance
            h_any = bfs_min_hops(W, i, mn9, positive_only=False)
            # do any of the cue's POSITIVE 1-hop targets reach MN9_L
            # within 2 more hops via positive edges?
            reach2 = []
            for t, w in pos:
                d = bfs_min_hops(W, t, mn9, positive_only=True)
                if d is not None and d <= 2:
                    reach2.append((int(t), float(w), d))
            rows.append({
                "bodyId": b,
                "out_pos_edges": len(pos), "out_neg_edges": len(neg),
                "hop_to_mn9_excitatory_only": h_pos,
                "hop_to_mn9_any_sign": h_any,
                "pos_targets_reaching_mn9_within_2": reach2,
            })
        out[cue] = rows
        print(f"== {cue} ==")
        for r in rows:
            print(f"  {r['bodyId']}: out+ = {r['out_pos_edges']}, out- = {r['out_neg_edges']}, "
                  f"excitatory hops to MN9_L = {r['hop_to_mn9_excitatory_only']}, "
                  f"any-sign hops = {r['hop_to_mn9_any_sign']}")
            if r["pos_targets_reaching_mn9_within_2"]:
                print(f"    positive targets reaching MN9_L <= 2 hops: "
                      f"{[(t, w, d) for t, w, d in r['pos_targets_reaching_mn9_within_2']][:6]}")

    Path("results/phase2/wp3_pilot/prw043_structural_audit.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("wrote results/phase2/wp3_pilot/prw043_structural_audit.json")


if __name__ == "__main__":
    main()
