"""Retrospective leg-2-vs-leak analysis + widened pool pre-filter.

Review-directed (registry 2026-09-26), BEFORE any pool probing.

1. RETROSPECTIVE: compute route structure for every measured candidate
   and test whether any structural variable separates the outcomes:
     GNG521 group  leg2~96  leak NO (0/20)   learnable YES
     GNG557 group leg2~92  leak 0.6Hz (4/10) learnable YES
     GNG611 group leg2~1   leak NO (0/10)    learnable NO
     GNG622 group leg2~5   leak NO (0/10)    learnable NO
     PRW043 group leg2~0   leak NO (0/5)     learnable NO
   plus 11 single-neuron batch survivors (leak 0/5 each) and 4 batch
   rejects (leak 50-81 Hz).
   Candidate separating variable (group level): COINCIDENT leg-1 -
   the summed positive leg-1 weights of the group's members onto each
   strong-leg2 (>=20) target. Single-kick firing reference: ~11
   synapse-counts ~ 3 mV (reset-to-threshold gap); ~20 counts ~ 5.5 mV
   (toy-circuit calibration). Screen thresholds, not validated ones.

2. POOL PRE-FILTER: all cholinergic non-sensory/motor type-groups in
   the closure (degree bands 5-400 in / 5-200 out, as the original
   enumeration). Raw filter: max leg-2 >= 20. Refined (adopted only
   if the retrospective supports it): + coincident leg-1 onto
   strong-leg2 targets sub-threshold (<11).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import sparse

BASE = Path("data/processed/neuprint_snapshots/run-007")
MN9_L = 10331
STRONG = 20.0          # strong-leg2 screen cut (measured: expressers 92/96, non 0-5)
KICK_FIRE = 11.0       # ~3 mV single-kick firing reference (screen threshold)
EXCL = ("LB", "Gr", "Ir", "ppk", "MN", "DN", "ES", "og", "CG")

MEASURED_GROUPS = {
    "GNG521": {"ids": [15957, 16327], "leak": "NO (0/20)", "learn": "YES (77 Hz @1e-4)"},
    "GNG557": {"ids": [12595, 12901], "leak": "0.6 Hz (4/10 seeds 1-2 Hz)", "learn": "YES (20 Hz @1e-4)"},
    "GNG611": {"ids": [25821, 29976], "leak": "NO (0/10)", "learn": "NO (through 1e-3)"},
    "GNG622": {"ids": [29819, 32179, 112815, 248046011], "leak": "NO (0/10)", "learn": "NO (through 1e-3)"},
    "PRW043": {"ids": [25250, 26891, 37670, 39767, 69045], "leak": "NO (0/5)", "learn": "NO (through 1e-2)"},
}


def group_routes(W, idx, into_mn9, member_ids):
    """Route structure for a cue group.

    Returns per-target coincident leg-1 (sum of positive leg-1 weights
    from ALL members onto the target), the target's leg-2 into MN9_L,
    and derived metrics. Targets with leg2 <= 0 are recorded only for
    total-route counts.
    """
    per_target_leg1: dict[int, float] = {}
    for b in member_ids:
        i = idx[b]
        row = W.getrow(i)
        for t, w in zip(row.indices, row.data):
            if w > 0:
                per_target_leg1[int(t)] = per_target_leg1.get(int(t), 0.0) + float(w)
    strong = {t: into_mn9[t] for t in per_target_leg1
              if into_mn9.get(t, 0.0) >= STRONG}
    routes = {t: {"coincident_leg1": per_target_leg1[t], "leg2": into_mn9[t],
                  "product": per_target_leg1[t] * into_mn9[t]}
              for t in strong}
    n_routes = len(routes)
    max_leg2 = max((r["leg2"] for r in routes.values()), default=0.0)
    max_coinc = max((r["coincident_leg1"] for t, r in routes.items()
                     if r["leg2"] == max_leg2), default=0.0) if routes else 0.0
    max_coinc_any = max((r["coincident_leg1"] for r in routes.values()), default=0.0)
    sum_prod = sum(r["product"] for r in routes.values())
    max_prod = max((r["product"] for r in routes.values()), default=0.0)
    # participation ratio of route products (effective route count)
    sq = sum(r["product"] ** 2 for r in routes.values())
    partic = (sum_prod ** 2 / sq) if sq > 0 else 0.0
    return {"n_strong_routes": n_routes, "max_leg2": max_leg2,
            "coincident_leg1_on_maxleg2": max_coinc,
            "max_coincident_leg1_any_strong": max_coinc_any,
            "sum_route_product": sum_prod, "max_route_product": max_prod,
            "route_participation": partic, "routes": routes}


def main() -> None:
    W = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(nodes)}
    mn9 = idx[MN9_L]
    coo = W[:, mn9].tocoo()
    into_mn9 = {int(r): float(w) for r, w in zip(coo.row, coo.data)}

    meta = {}
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            meta[r["bodyId"]] = r

    print("== 1. RETROSPECTIVE: measured groups, route structure ==", flush=True)
    print(f"{'type':<9s} {'leak':<28s} {'learn':<20s} {'nR':<4s} {'maxL2':<7s} "
          f"{'coincL1@max':<13s} {'maxCoincAny':<12s} {'partic':<7s}")
    retro = {}
    for t, info in MEASURED_GROUPS.items():
        rs = group_routes(W, idx, into_mn9, info["ids"])
        retro[t] = rs
        print(f"{t:<9s} {info['leak']:<28s} {info['learn']:<20s} "
              f"{rs['n_strong_routes']:<4d} {rs['max_leg2']:<7.0f} "
              f"{rs['coincident_leg1_on_maxleg2']:<13.1f} "
              f"{rs['max_coincident_leg1_any_strong']:<12.1f} "
              f"{rs['route_participation']:<7.2f}", flush=True)

    print("\n== single-neuron batch outcomes (leg-1 onto own max-leg2 target) ==",
          flush=True)
    batch = json.loads(Path("results/phase2/wp2_cue_probe_batch_candidates.json").read_text(encoding="utf-8"))
    batch_rec = [json.loads(l) for l in Path("results/phase2/wp2_cue_probe_batch.jsonl")
                 .read_text(encoding="utf-8").splitlines() if l.strip()]
    for c in batch:
        b = c["bodyId"]
        i = idx[b]
        row = W.getrow(i)
        legs = {int(t): float(w) for t, w in zip(row.indices, row.data) if w > 0
                and into_mn9.get(int(t), 0.0) >= STRONG}
        alone = [r["mn9_l_hz"] for r in batch_rec
                 if r["body_id"] == b and r["label"] == "cue_alone"]
        if legs:
            tstar = max(legs, key=lambda t: into_mn9[t])
            print(f"  {c['type']:<12s} alone={max(alone):<3d} Hz  leg1@maxleg2={legs[tstar]:<6.1f} "
                  f"maxL2={into_mn9[tstar]:<5.0f} nStrong={len(legs)}", flush=True)
        else:
            print(f"  {c['type']:<12s} alone={max(alone):<3d} Hz  no strong-leg2 route", flush=True)

    print("\n== 2. POOL PRE-FILTER (type-group level) ==", flush=True)
    types = {}
    for b, r in meta.items():
        if b not in idx:
            continue
        t = r.get("type") or ""
        if any(t.startswith(p) for p in EXCL):
            continue
        if r.get("predictedNt") != "acetylcholine":
            continue
        i = idx[b]
        in_deg, out_deg = int(W[:, i].nnz), int(W[i, :].nnz)
        if not (5 <= in_deg <= 400 and 5 <= out_deg <= 200):
            continue
        types.setdefault(t, []).append(b)

    raw_pool, refined_pool = [], []
    for t, ids in types.items():
        rs = group_routes(W, idx, into_mn9, ids)
        if rs["max_leg2"] >= STRONG:
            entry = {"type": t, "n": len(ids), "max_leg2": rs["max_leg2"],
                     "coinc_leg1_on_max": rs["coincident_leg1_on_maxleg2"],
                     "n_strong_routes": rs["n_strong_routes"],
                     "participation": rs["route_participation"]}
            raw_pool.append(entry)
            if rs["coincident_leg1_on_maxleg2"] < KICK_FIRE:
                refined_pool.append(entry)
    raw_pool.sort(key=lambda e: (-e["max_leg2"], e["coinc_leg1_on_max"]))
    refined_pool.sort(key=lambda e: (-e["max_leg2"], e["coinc_leg1_on_max"]))

    print(f"cholinergic non-sensory/motor type-groups (degree bands): {len(types)}")
    print(f"raw pool (max leg2 >= {STRONG:.0f}): {len(raw_pool)}")
    print(f"refined pool (+ coincident leg1 on max-leg2 target < {KICK_FIRE:.0f}): {len(refined_pool)}")
    print("\nraw pool top 20 (by max leg2, low coincident leg1):")
    for e in raw_pool[:20]:
        print(f"  {e['type']:<14s} n={e['n']} maxL2={e['max_leg2']:<5.0f} "
              f"coincL1={e['coinc_leg1_on_max']:<6.1f} nRoutes={e['n_strong_routes']} "
              f"partic={e['participation']:.2f}")
    print("\nrefined pool top 20:")
    for e in refined_pool[:20]:
        print(f"  {e['type']:<14s} n={e['n']} maxL2={e['max_leg2']:<5.0f} "
              f"coincL1={e['coinc_leg1_on_max']:<6.1f} nRoutes={e['n_strong_routes']} "
              f"partic={e['participation']:.2f}")

    Path("results/phase2/wp3_pilot/pool_prefilter.json").write_text(json.dumps({
        "retrospective": {t: {k: v for k, v in r.items() if k != "routes"}
                          for t, r in retro.items()},
        "raw_pool": raw_pool, "refined_pool": refined_pool,
        "thresholds": {"strong_leg2": STRONG, "kick_fire": KICK_FIRE},
    }, indent=2), encoding="utf-8")
    print("\nwrote results/phase2/wp3_pilot/pool_prefilter.json", flush=True)


if __name__ == "__main__":
    main()
