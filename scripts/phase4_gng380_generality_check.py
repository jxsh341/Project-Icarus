"""GNG380 generality check (close-out precondition, review-directed).

Is 'the substrate can unlearn' extensible to GNG380's association,
or is it GNG521-specific? The L4b mechanism worked because:
sugar drives the previously-unreachable partners -> sugar-phase
opens their coincidence -> eligibility accumulates -> bitter-phase
sign erodes it.

GNG380's learned association is the WITHHOLD direction (cue+bitter
built suppressive connectivity onto the readout). The analogous
erosion protocol needs:
1. GNG380's acquisition footprint (R1 ckpt diff, withhold direction);
2. its partners' input structure: does the AVERSIVE-side
   recruitment have the mirror-image reachability structure - i.e.,
   are the footprint partners driven by whatever drive would
   re-open their coincidence in an erosion protocol (bitter, since
   bitter built the association)?
3. the sign problem: eroding a SUPPRESSIVE association needs
   POSITIVE deltas (the update that would RE-strengthen excitatory
   readout tone) - the reverse of L4b's sign arrangement.

Structural census only - no sims. This determines whether the
close-out states GNG380-unlearning as TESTABLE-BY-THE-SAME-DESIGN
or as a GENUINELY OPEN MECHANISM QUESTION.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0")
CUE = [50843, 53901, 103327, 129624, 556072, 559464]


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    # footprint
    files = sorted(R1CK.glob("weights_trial_*.npz"))
    w0 = sparse.load_npz(files[0]).tocsr()
    w15 = sparse.load_npz(files[15]).tocsr()
    d = (w15 - w0).tocoo()
    fp = {(int(r), int(c)): float(v) for r, c, v in zip(d.row, d.col, d.data) if v != 0}
    cue_idx = [nid[c] for c in CUE]
    fp_ci = {k: v for k, v in fp.items() if k[0] in cue_idx}
    print(f"GNG380 withhold acquisition footprint: {len(fp)} edges "
          f"({len(fp_ci)} cue-incident)")
    partners = sorted({k[1] for k in fp_ci})
    print(f"partners ({len(partners)}): {[nodes[x] for x in partners][:12]}")

    # per-partner: bitter drive? (the drive that BUILT the association)
    print("\n== partner input from bitter GRNs (the recruiting drive) ==")
    driven = 0
    for x in partners:
        X = nodes[x]
        bit_w = sum(float(matrix[nid[b], x]) for b in bitter)
        col = matrix[:, x].tocoo()
        n_in = int((col.data != 0).sum())
        tot_in = float(abs(col.data).sum())
        if bit_w != 0:
            driven += 1
        print(f"  {X}: bitter-in {bit_w:+.1f} of |total in| {tot_in:.0f} ({n_in} inputs)")
    print(f"\nbitter-driven partners: {driven}/{len(partners)}")

    # the sign question: what did acquisition DO to these edges?
    grew = [k for k, v in fp_ci.items() if v > 0]
    shr = [k for k, v in fp_ci.items() if v < 0]
    print(f"\nfootprint edge signs: {len(grew)} grew, {len(shr)} shrank")
    for k in list(fp_ci)[:8]:
        w_i = float(w0[k]); w_f = float(w15[k])
        print(f"  {nodes[k[0]]}->{nodes[k[1]]}: {w_i:.1f} -> {w_f:.1f} (d={fp_ci[k]:+.1f})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
