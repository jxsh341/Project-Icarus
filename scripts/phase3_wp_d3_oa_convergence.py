"""Phase 3 WP-D3: OA-relay convergence census (data check before L3 design).

The OA relay (10120 OA-VPM4, 11608/12109 OA-VUMa2) is the single
convergence point for reward en route to the DA gate. This census
measures, from the frozen snapshot:

1. INPUT budget of each OA relay neuron: total in-weight, weight
   share from sugar GRNs, from bitter GRNs, from modulators, and
   the top non-sugar drivers (who ELSE talks to the reward relay?).
2. VALENCE TEST: does bitter reach the relay with meaningful
   weight? If yes, the relay is not a pure reward channel.
3. OUTPUT budget of the 9 gate-DA cells: besides the hub 10646,
   what do they reach (is the gate pathway-specific or does it
   fan out)?
4. The gate-DA cells' total output onto the FULL GNG380
   intermediate set vs everything else (specificity ratio).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase3/wp_d3_oa_convergence.json")

OA = [10120, 11608, 12109]
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
HUB = 10646
INTER_380 = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
MN9_L = 10331


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    nt_map = {}
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            nt_map[rec["bodyId"]] = rec.get("consensusNt")

    print("== 1) OA relay input budgets ==")
    relay_stats = {}
    for b in OA:
        r = nid[b]
        col = matrix[:, r].tocoo()
        nz = [(nodes[i], float(w)) for i, w in zip(col.row, col.data) if w != 0]
        tot_w = sum(abs(w) for _, w in nz)
        sug_w = sum(abs(w) for s, w in nz if s in sugar)
        bit_w = sum(abs(w) for s, w in nz if s in bitter)
        pos_w = sum(w for _, w in nz if w > 0)
        neg_w = sum(-w for _, w in nz if w < 0)
        top = sorted(nz, key=lambda t: -abs(t[1]))[:8]
        relay_stats[b] = {
            "n_inputs": len(nz), "total_abs_weight": tot_w,
            "sugar_abs_weight": sug_w, "bitter_abs_weight": bit_w,
            "sugar_share": sug_w / tot_w if tot_w else 0,
            "excitatory_weight": pos_w, "inhibitory_weight": neg_w,
            "top_inputs": {str(s): w for s, w in top},
        }
        print(f"  {b}: {len(nz)} inputs, |w|={tot_w:.0f} (exc {pos_w:.0f} / inh {neg_w:.0f}), "
              f"sugar|w|={sug_w:.0f} ({100*sug_w/tot_w:.1f}%), bitter|w|={bit_w:.0f} ({100*bit_w/tot_w:.1f}%)")
        print(f"    top: " + ", ".join(f"{s}({nt_map.get(s,'?')[:4]}):{w:+.0f}" for s, w in top))

    print("\n== 2) bitter paths to relay (any depth, weight-ordered) ==")
    for b in OA:
        r = nid[b]
        # 1-hop
        col = matrix[:, r].tocoo()
        b1 = [(nodes[i], float(w)) for i, w in zip(col.row, col.data)
              if nodes[i] in bitter and w != 0]
        # 2-hop through top interneurons
        two_hop = []
        col_nz = [(nodes[i], float(w)) for i, w in zip(col.row, col.data) if w != 0]
        for mid, w2 in col_nz:
            m = nid[mid]
            row = matrix[m, :].tocoo()
            for j, w1 in zip(row.col, row.data):
                if nodes[j] in bitter and w1 != 0 and w1 * w2 > 0:  # same-sign path
                    two_hop.append((b, mid, nodes[j], w1, w2, w1 * w2))
        two_hop.sort(key=lambda t: -t[5])
        print(f"  {b}: 1-hop bitter={b1}, 2-hop same-sign paths (top 5): "
              f"{[(m, s, w1, w2) for _, m, s, w1, w2, _ in two_hop[:5]]}")

    print("\n== 3) gate-DA output budgets (besides the hub) ==")
    gate_stats = {}
    inter_idx = [nid[x] for x in INTER_380]
    for b in GATE_DA:
        r = nid[b]
        row = matrix[r, :].tocoo()
        nz = [(nodes[j], float(w)) for j, w in zip(row.col, row.data) if w != 0]
        tot = sum(abs(w) for _, w in nz)
        hub_w = float(matrix[r, nid[HUB]])
        inter_w = sum(abs(float(matrix[r, c])) for c in inter_idx)
        mn9_w = float(matrix[r, nid[MN9_L]])
        gate_stats[b] = {
            "n_targets": len(nz), "total_abs_out": tot,
            "onto_hub": hub_w, "onto_8_intermediates": inter_w,
            "onto_MN9L": mn9_w,
            "specificity": inter_w / tot if tot else 0,
            "targets": {str(s): w for s, w in sorted(nz, key=lambda t: -abs(t[1]))[:10]},
        }
        print(f"  {b}: {len(nz)} targets, |out|={tot:.0f}; hub={hub_w:+.0f}, "
              f"8-inter={inter_w:.0f} ({100*inter_w/tot:.0f}% of output), MN9={mn9_w:+.0f}")
        for s, w in sorted(nz, key=lambda t: -abs(t[1]))[:6]:
            print(f"     -> {s} ({nt_map.get(s, '?')}): {w:+.0f}")

    result = {"relay": {str(k): v for k, v in relay_stats.items()},
              "gate_da": {str(k): v for k, v in gate_stats.items()}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
