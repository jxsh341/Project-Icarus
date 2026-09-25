"""Synthetic-cue candidate screen + screen validation against measured cases.

Triggered by: LB2a probe REJECT on frozen criteria (c) and (d)
(results/phase2/wp2_cue_probe_lb2a.jsonl).

The LB2a failure mode - cholinergic, upstream of MN9_L <=2 hops, yet
co-drive suppresses the sugar feed program (82 -> 9-54 Hz) - suggests
multi-hop influence through inhibitory intermediates can dominate a
candidate's own excitatory direct path. This screen computes, for every
neuron in the run-007 closure, a linear path-influence decomposition to
the MN9_L readout:

  P1[i] = W[i, mn9]                    (direct edge weight)
  P2[i] = sum_m W[i,m] * W[m, mn9]     (2-hop path-product sum)
  P3[i] = W @ P2                       (3-hop path-product sum)

P2/P3 signs are first-order predictors of net excitatory vs
inhibitory influence. The screen is VALIDATED against the four
already-measured probe cases before it is allowed to rank anything:

  sugar_R   -> feeds alone (82 Hz)        expect net influence >> 0
  bitter_R  -> co-suppresses at >=20 Hz   expect net influence << 0
  ir94e     -> co-suppresses (82 -> 5)    expect net influence < 0
  lb2a      -> co-suppresses (82 -> 24)   expect net influence < 0

If all four signs match measurement, the screen ranks synthetic-cue
candidates by the frozen criterion set (cholinergic, <=3-hop path,
net-positive multi-hop influence, low GABA-intermediate fraction among
readout-upstream targets, modest out-degree, non-sensory/motor type)
and emits matched pairs (in/out-degree within 20%, disjoint targets).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

base = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase2/wp2_synthetic_cue_screen.json")

W = sparse.load_npz(base / "connectivity_matrix_signed.npz").tocsr()
node_ids = np.load(base / "connectivity_nodes.npy").tolist()
idx = {n: i for i, n in enumerate(node_ids)}
MN9_L = 10331
mn9 = idx[MN9_L]

meta: dict[int, dict] = {}
for p in sorted(base.glob("neurons_batch_*.json")):
    for r in json.loads(p.read_text(encoding="utf-8")):
        meta[r["bodyId"]] = r

# --- path-influence decomposition (two sparse matvecs) -----------------------
P1 = np.asarray(W[:, mn9].todense()).ravel()
P2 = np.asarray(W @ P1).ravel()
P3 = np.asarray(W @ P2).ravel()
NET = P1 + P2 + P3

U1 = set(W[:, mn9].nonzero()[0])  # 1-hop upstream of readout

seeds = json.loads(Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text(encoding="utf-8"))
sugar_ids = [r["bodyId"] for r in seeds["sugar_R"]]
bitter_ids = [r["bodyId"] for r in seeds["bitter_R"]]

CALIBRATION = {
    "sugar_R": sugar_ids,
    "bitter_R": bitter_ids,
    "ir94e_LB1e_R": [r["bodyId"] for r in meta.values()
                     if r.get("type") == "LB1e" and r.get("rootSide") == "R"],
    "water_LB3a_R": [r["bodyId"] for r in meta.values()
                     if r.get("type") == "LB3a" and r.get("rootSide") == "R"],
    "lb2a_all": [77868, 512913, 120770012, 919015263],
}


def gaba_intermediate_frac(body_id: int) -> tuple[float, int, int]:
    """Among the candidate's 1-hop targets that are upstream of MN9_L,
    the fraction that are GABAergic (the LB2a suppression signature)."""
    i = idx[body_id]
    targets = set(W[i, :].nonzero()[1].tolist())
    bridge = targets & U1
    if not bridge:
        return 0.0, 0, len(targets)
    n_gaba = sum(1 for t in bridge
                 if meta.get(node_ids[t], {}).get("predictedNt") in ("gaba", "glutamate"))
    return n_gaba / len(bridge), len(bridge), len(targets)


def summarize(body_ids: list[int]) -> dict:
    rows = []
    for b in body_ids:
        i = idx[b]
        frac, n_bridge, out_deg = gaba_intermediate_frac(b)
        rows.append({
            "bodyId": b, "type": meta.get(b, {}).get("type"),
            "nt": meta.get(b, {}).get("predictedNt"),
            "P1": float(P1[i]), "P2": float(P2[i]), "P3": float(P3[i]),
            "net": float(NET[i]),
            "gaba_bridge_frac": round(frac, 3), "bridge_n": n_bridge,
            "out_deg": out_deg,
            "in_deg": int(W[:, i].nnz),
        })
    agg = {
        "n": len(rows),
        "net_mean": float(np.mean([r["net"] for r in rows])),
        "net_range": [float(min(r["net"] for r in rows)), float(max(r["net"] for r in rows))],
        "gaba_bridge_frac_mean": float(np.mean([r["gaba_bridge_frac"] for r in rows])),
        "per_neuron": rows,
    }
    return agg


# --- validate the screen against measured behavior ---------------------------
print("== screen validation vs measured probe cases ==", flush=True)
validation = {}
expectations = {"sugar_R": "positive (feeds alone, 82 Hz)",
                "bitter_R": "negative (co-suppresses >=20 Hz)",
                "ir94e_LB1e_R": "negative (co-suppresses 82->5)",
                "water_LB3a_R": "unmeasured co-drive; alone-silent (any sign OK)",
                "lb2a_all": "negative (co-suppresses 82->24; REJECTED)"}
for name, ids in CALIBRATION.items():
    agg = summarize(ids)
    validation[name] = agg
    print(f"{name:14s} net_mean={agg['net_mean']:+9.1f}  range=[{agg['net_range'][0]:+9.1f},"
          f"{agg['net_range'][1]:+9.1f}]  gaba_bridge={agg['gaba_bridge_frac_mean']:.2f}"
          f"  expect: {expectations[name]}", flush=True)

sign_ok = (validation["sugar_R"]["net_mean"] > 0
           and validation["bitter_R"]["net_mean"] < 0
           and validation["ir94e_LB1e_R"]["net_mean"] < 0
           and validation["lb2a_all"]["net_mean"] < 0)
print(f"screen sign validation: {'PASS - all four measured cases predicted' if sign_ok else 'FAIL - do not trust rankings'}",
      flush=True)

# --- candidate ranking (only if the screen validates) -----------------------
candidates = []
if sign_ok:
    excluded_prefix = ("LB", "Gr", "Ir", "ppk", "MN", "DN", "CG", "og", "ES")
    for b, r in meta.items():
        if b not in idx:
            continue
        i = idx[b]
        nt = r.get("predictedNt")
        if nt != "acetylcholine":
            continue
        t = r.get("type") or ""
        if any(t.startswith(p) for p in excluded_prefix):
            continue
        out_deg = W[i, :].nnz
        in_deg = W[:, i].nnz
        if not (5 <= in_deg <= 400 and 10 <= out_deg <= 150):
            continue
        if NET[i] <= 0:  # need net-positive influence for a feed-learnable cue
            continue
        frac, n_bridge, _ = gaba_intermediate_frac(b)
        if frac > 0.4:
            continue
        candidates.append({
            "bodyId": b, "type": t, "instance": r.get("instance"),
            "side": r.get("rootSide"),
            "net": float(NET[i]), "P2": float(P2[i]), "P3": float(P3[i]),
            "gaba_bridge_frac": round(frac, 3), "in_deg": in_deg, "out_deg": out_deg,
        })
    candidates.sort(key=lambda c: (c["gaba_bridge_frac"], c["out_deg"]))
    print(f"\ncandidates passing filters: {len(candidates)}", flush=True)

    # matched pairs: in/out-degree within 20%, disjoint targets, net>0 both
    pairs = []
    for a in range(len(candidates)):
        ca = candidates[a]
        ta = set(W[idx[ca["bodyId"]], :].nonzero()[1].tolist())
        for b_ in range(a + 1, len(candidates)):
            cb = candidates[b_]
            if ca["side"] == cb["side"] and ca["side"] is not None:
                continue  # prefer cross-hemisphere for symmetry
            if abs(ca["in_deg"] - cb["in_deg"]) > 0.2 * max(ca["in_deg"], cb["in_deg"]):
                continue
            if abs(ca["out_deg"] - cb["out_deg"]) > 0.2 * max(ca["out_deg"], cb["out_deg"]):
                continue
            tb = set(W[idx[cb["bodyId"]], :].nonzero()[1].tolist())
            jac = len(ta & tb) / max(1, len(ta | tb))
            if jac > 0.2:
                continue
            pairs.append({"a": ca, "b": cb, "target_jaccard": round(jac, 3)})
            if len(pairs) >= 25:
                break
        if len(pairs) >= 25:
            break
    print(f"matched pairs emitted: {len(pairs)}", flush=True)
    for k, pr in enumerate(pairs[:5]):
        print(f"  pair {k}: a={pr['a']['bodyId']} ({pr['a']['type']}, {pr['a']['side']}, "
              f"in={pr['a']['in_deg']} out={pr['a']['out_deg']} net={pr['a']['net']:+.1f}) | "
              f"b={pr['b']['bodyId']} ({pr['b']['type']}, {pr['b']['side']}, "
              f"in={pr['b']['in_deg']} out={pr['b']['out_deg']} net={pr['b']['net']:+.1f}) "
              f"jac={pr['target_jaccard']}", flush=True)
else:
    pairs = []

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "validation": validation, "screen_sign_pass": bool(sign_ok),
    "candidates": candidates[:200], "pairs": pairs,
}, indent=2), encoding="utf-8")
print(f"\nwrote {OUT}", flush=True)
