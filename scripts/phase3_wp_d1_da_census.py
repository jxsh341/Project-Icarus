"""Phase 3 opening move: dopaminergic projection census (WP-D1).

The re-anchoring obligation (Phase 1 freeze): NT->sign mapping is
SCOPE-LIMITED to gustatory/motor (WP6c-anchored); dopamine-pathway
signs must be re-anchored BEFORE L3 exists. This census answers the
structural question the Cadence audit posed: does MaleCNS's actual
dopaminergic wiring support a single broadcast scalar, or is it
pathway-specific?

Method (data-first, from the frozen run-007 snapshot only):
1. Identify DA neurons: consensusNt == 'DA' (fallback predictedNt
   where consensus missing, confidence recorded).
2. Build the DA->target edge list from the connectivity matrix.
3. Broadcast test: what fraction of ALL edges from DA neurons land
   on (a) our readout MN9_L, (b) our cue populations' leg-2
   intermediates, (c) SEZ motor circuitry broadly, vs (d) MB/other?
   A broadcast signal should reach broadly; a pathway-specific
   anatomy concentrates on distinct targets.
4. Concentration metrics: out-degree distribution of DA neurons;
   top targets; DA-target overlap with our trained circuits
   (cue members, the 8 intermediates from the coincidence probe,
   MN9_L itself, sugar/bitter GRNs).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase3/wp_d1_da_census.json")

CUE_521 = [15957, 16327]
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
INTER_380 = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
INTER_521 = [12807, 12364, 567143]
MN9_L = 10331


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}

    # 1) DA neurons from per-neuron metadata (VOCABULARY CHECKED: snapshot
    # uses lowercase 'dopamine' for consensusNt/predictedNt - the first run's
    # 'DA' matched 0 records, a string-vocabulary error caught by the
    # empty-scope guard this time)
    da_ids, da_meta = [], []
    n_consensus = n_pred = 0
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            nt = rec.get("consensusNt")
            if nt == "dopamine":
                da_ids.append(rec["bodyId"]); n_consensus += 1
                da_meta.append({"bodyId": rec["bodyId"], "type": rec.get("type"),
                               "source": "consensus", "pre": rec.get("pre")})
            elif nt is None and rec.get("predictedNt") == "dopamine":
                conf = rec.get("predictedNtConfidence", 0)
                if conf and conf >= 0.75:
                    da_ids.append(rec["bodyId"]); n_pred += 1
                    da_meta.append({"bodyId": rec["bodyId"], "type": rec.get("type"),
                                   "source": f"predicted@{conf}", "pre": rec.get("pre")})
    da_set = set(da_ids)
    print(f"DA neurons: {len(da_set)} (consensus {n_consensus}, predicted>=0.75 {n_pred})")

    da_idx = sorted(nid[b] for b in da_set if b in nid)
    missing = len(da_set - set(nodes))
    # EMPTY-SCOPE GUARD (standing rule: a verification must fail loudly
    # when its scope is empty)
    if not da_idx:
        raise RuntimeError("DA neuron set is empty - census scope is empty; "
                           "refusing to emit a vacuous result")
    print(f"  in matrix: {len(da_idx)} (missing from snapshot: {missing})")

    # 2) DA out-edges from the matrix
    rows = np.array(da_idx)
    sub = matrix[rows, :].tocoo()
    total_da_edges = int((sub.data != 0).sum())
    print(f"DA out-edges in closure: {total_da_edges}")

    # 3) Target overlap with our trained circuits
    trained = set(CUE_521) | set(CUE_380) | set(INTER_380) | set(INTER_521) | {MN9_L}
    overlap_counts = {}
    for name, ids in [("cue_GNG521", CUE_521), ("cue_GNG380", CUE_380),
                      ("intermediates_380", INTER_380), ("intermediates_521", INTER_521),
                      ("readout_MN9_L", [MN9_L])]:
        tgts = set(ids)
        hits = [b for b in da_set if matrix[nid[b], [nid[t] for t in tgts if t in nid]].count_nonzero() > 0]
        overlap_counts[name] = {"da_neurons_projecting": len(hits), "targets": len(tgts)}
        print(f"  {name}: {len(hits)} DA neurons project onto it")

    # 4) Concentration: DA per-neuron out-degree; top targets overall
    out_deg = np.asarray((matrix[rows, :] != 0).sum(axis=1)).ravel()
    tgt_deg = np.asarray((matrix[rows, :] != 0).sum(axis=0)).ravel()
    top_t = np.argsort(-tgt_deg)[:15]
    print(f"\nDA out-degree: median={np.median(out_deg)}, max={out_deg.max()}, "
          f"n_with_out_edges={(out_deg > 0).sum()}/{len(rows)}")
    print("Top DA targets (bodyId, in-edges from DA):")
    for t in top_t:
        print(f"  {nodes[t]}: {tgt_deg[t]}")

    # 5) Broadcast test: fraction of DA edges reaching the trained circuit
    trained_idx = [nid[t] for t in trained if t in nid]
    mask = np.isin(sub.col, trained_idx)
    frac_trained = float(sub.data[mask].sum() / sub.data.sum()) if sub.data.size else 0.0
    n_targets = len(set(sub.col.tolist()))
    print(f"\nDA distinct targets: {n_targets}")
    print(f"Fraction of DA out-weight onto trained circuit "
          f"({len(trained_idx)} nodes): {frac_trained:.4f}")

    result = {
        "n_da": len(da_set), "n_consensus": n_consensus, "n_predicted": n_pred,
        "n_in_matrix": len(da_idx), "missing_from_snapshot": missing,
        "total_da_edges": total_da_edges,
        "distinct_targets": n_targets,
        "out_degree": {"median": float(np.median(out_deg)), "max": int(out_deg.max()),
                        "n_with_out_edges": int((out_deg > 0).sum())},
        "trained_circuit_overlap": overlap_counts,
        "frac_da_weight_onto_trained": frac_trained,
        "top_targets": {str(nodes[t]): int(tgt_deg[t]) for t in top_t},
        "da_meta": da_meta,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
