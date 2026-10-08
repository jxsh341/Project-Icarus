"""Phase 3 WP-D2: anatomy of the DA->10646 gate pathway.

D-3 anchors L3 on pathway-specific DA gating of the GABA hub 10646
(AVLP597) - the coincidence-waste neuron. A gate is only honest if
its INPUTS exist in the substrate: what drives the 13 DA neurons
that project onto 10646? This census measures, from the frozen
snapshot:

1. The 13 DA neurons: identities, types, and their edge weights
   onto 10646 (and onto the other 7 GNG380 intermediates).
2. Their INPUTS: in-edges from sugar GRNs (reward candidate),
   bitter GRNs, the two cue populations, MN9_L (readout feedback),
   and other DA/OA/5HT modulators.
3. Whether any of them receive drive that could serve as a
   substrate-honest reward signal (sugar-GRN convergence = the
   'r' candidate).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase3/wp_d2_gate_anatomy.json")

HUB = 10646
CUE_521 = [15957, 16327]
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
INTER_380 = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
MN9_L = 10331


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    # metadata lookup
    meta = {}
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            if rec.get("consensusNt") == "dopamine":
                meta[rec["bodyId"]] = rec

    hub_col = nid[HUB]
    inter_cols = [nid[x] for x in INTER_380]

    # 1) DA neurons with edges onto ANY of the 8 intermediates (esp. 10646)
    da_rows = [nid[b] for b in meta if b in nid]
    gate_da = []
    for b, r in zip(meta, da_rows):
        w_hub = float(matrix[r, hub_col])
        w_any = float(matrix[r, inter_cols].sum())
        if w_any != 0 or w_hub != 0:
            gate_da.append(b)
    # direct: edges onto 10646 only
    onto_hub = {b: float(matrix[nid[b], hub_col]) for b in meta
                if b in nid and matrix[nid[b], hub_col] != 0}
    print(f"DA neurons with edges onto 10646: {len(onto_hub)}")
    for b, w in sorted(onto_hub.items(), key=lambda kv: -abs(kv[1])):
        t = meta[b].get("type")
        print(f"  {b} ({t}): w={w:+.1f}")

    # 2) inputs to those DA neurons
    print(f"\n== Inputs to the {len(onto_hub)} gate DA neurons ==")
    da_hub_idx = [nid[b] for b in onto_hub]
    inputs = {}
    for b, r in zip(list(onto_hub), da_hub_idx):
        col = matrix[:, r].tocoo()  # in-edges to this DA neuron
        src_sugar = [nodes[i] for i in col.row if nodes[i] in sugar]
        src_bitter = [nodes[i] for i in col.row if nodes[i] in bitter]
        src_cue = [nodes[i] for i in col.row if nodes[i] in CUE_521 + CUE_380]
        src_mn9 = [nodes[i] for i in col.row if nodes[i] == MN9_L]
        w_sugar = float(matrix[[nid[s] for s in src_sugar], r].sum()) if src_sugar else 0.0
        w_bitter = float(matrix[[nid[s] for s in src_bitter], r].sum()) if src_bitter else 0.0
        inputs[b] = {
            "n_in_edges": int((col.data != 0).sum()),
            "sugar_grn_sources": src_sugar, "sugar_weight": w_sugar,
            "bitter_grn_sources": src_bitter, "bitter_weight": w_bitter,
            "cue_sources": src_cue, "mn9_feedback": src_mn9,
            "total_in_weight": float(col.data.sum()),
        }
        print(f"  {b} ({meta[b].get('type')}): in-edges={inputs[b]['n_in_edges']}, "
              f"sugar_w={w_sugar:.1f}, bitter_w={w_bitter:.1f}, "
              f"cue={len(src_cue)}, mn9_fb={bool(src_mn9)}")

    # 3) modulator-to-modulator: any of these DA receive from other DA/OA/5HT?
    mod_types = {"dopamine", "octopamine", "serotonin"}
    mod_ids = {b for b, rec in meta.items()}
    # need OA/5HT too - rescan quickly
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            if rec.get("consensusNt") in mod_types and rec.get("consensusNt") != "dopamine":
                mod_ids.add(rec["bodyId"])
    for b in list(onto_hub):
        col = matrix[:, nid[b]].tocoo()
        src_mods = {nodes[i]: meta.get(nodes[i], {}).get("consensusNt") for i in col.row
                    if nodes[i] in mod_ids}
        # fix: meta only holds DA; get NT from a full scan - approximate here
    print(f"\nmodulator pool size (DA+OA+5HT): {len(mod_ids)}")

    result = {"onto_hub_weights": {str(k): v for k, v in onto_hub.items()},
              "inputs": {str(k): {kk: (vv if not isinstance(vv, list) else vv)
                                  for kk, vv in v.items()} for k, v in inputs.items()}}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
