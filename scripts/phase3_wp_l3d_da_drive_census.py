"""WP-L3d pre-registration checks (review-directed, 2026-10-09):

Three questions BEFORE the weakening test launches:

Q1. What defines 'gate on'? A threshold would be a relocated free
    parameter. Check: measure the gate-DA population's rates under
    sugar-present vs sugar-absent vs bitter-present conditions; see
    whether a graded (threshold-free) gate definition is derivable
    from the substrate's own separation.

Q2. Does bitter route through a DIFFERENT DA population than sugar
    (PAM-appetitive / PPL-aversive dichotomy)? Check: traced sims
    with sugar-only and bitter-only drives; measure ALL 1,449 DA
    neurons' rates; compare which fire under each. Also: PAM/PPL
    composition of the 9 gate-DA cells.

Q3. Gate-off eligibility semantics (freeze vs decay vs zero):
    design decision informed by Q1/Q2 results - whether a negative
    delta has anything to act on during reversal.

Frozen dynamics, no plasticity. Seeds 154000+ (disjoint).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase3/wp_l3d_checks")
MN9_L = 10331
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
SEED_BASE = 154_000
REPS = 3


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    # full DA list + type classification
    da = {}
    for f in sorted(BASE.glob("neurons_batch_*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            if rec.get("consensusNt") == "dopamine":
                da[rec["bodyId"]] = rec.get("type") or "?"
    print(f"DA neurons: {len(da)}")

    def cluster_of(t: str) -> str:
        if t.startswith("PAM"):
            return "PAM"
        if t.startswith("PPL"):
            return "PPL"
        if t.startswith("PPM"):
            return "PPM"
        return "other"

    print("\n== Q2a: the 9 gate-DA cells by cluster ==")
    for b in GATE_DA:
        print(f"  {b}: {da.get(b)} -> {cluster_of(da.get(b, '?'))}")
    from collections import Counter
    print(f"  clusters: {dict(Counter(cluster_of(da.get(b, '?')) for b in GATE_DA))}")
    print(f"  full-closure DA clusters: "
          f"{dict(Counter(cluster_of(t) for t in da.values()))}")

    # traced sims: sugar-only, bitter-only, cue-only (no drive), 3 reps each
    conds = {
        "sugar_only": (sugar, None),
        "bitter_only": (bitter, None),
        "cue_only": (list(GATE_DA), None),  # n/a - use no-stim baseline instead
        "baseline": ([], None),
    }
    # run each condition by stimulating the given population as PRIMARY
    results = {}
    for name, (stim, _) in conds.items():
        if name == "cue_only":
            continue
        rates = {b: [] for b in da if b in nid}
        for rep in range(REPS):
            seed = SEED_BASE + rep
            if stim:
                p = dataclasses.replace(lif_params, r_poisson_Hz=200.0)
                lif = simulate_lif(matrix, nodes, p, 1000.0,
                                   stimulated=list(stim), seed=seed)
            else:
                p = dataclasses.replace(lif_params, r_poisson_Hz=0.0)
                lif = simulate_lif(matrix, nodes, p, 1000.0,
                                   stimulated=[], seed=seed)
            for b in rates:
                rates[b].append(len(lif.spike_times.get(b, [])))
        results[name] = rates

    # which DA neurons fire under each condition?
    print("\n== Q2b: DA neurons firing (>5 Hz in >=2/3 reps) under each drive ==")
    for name in ("baseline", "sugar_only", "bitter_only"):
        active = [b for b, rs in results[name].items()
                  if sum(1 for r in rs if r >= 5) >= 2]
        clusters = Counter(cluster_of(da.get(b, "?")) for b in active)
        print(f"  {name}: {len(active)} active; clusters={dict(clusters)}")
        if len(active) <= 25:
            for b in sorted(active):
                print(f"    {b} ({da.get(b)}): {results[name][b]}")

    sugar_set = {b for b, rs in results["sugar_only"].items()
                 if sum(1 for r in rs if r >= 5) >= 2}
    bitter_set = {b for b, rs in results["bitter_only"].items()
                  if sum(1 for r in rs if r >= 5) >= 2}
    print(f"\n  overlap sugar^bitter: {len(sugar_set & bitter_set)} "
          f"{sorted(sugar_set & bitter_set)}")
    print(f"  sugar-only active: {len(sugar_set - bitter_set)}")
    print(f"  bitter-only active: {len(bitter_set - sugar_set)}")

    # gate-DA population rates per condition (Q1)
    print("\n== Q1: gate-DA population rates per condition (3 reps) ==")
    for name in ("baseline", "sugar_only", "bitter_only"):
        per_cell = {b: results[name].get(b, [0]*REPS) for b in GATE_DA}
        means = {b: float(np.mean(v)) for b, v in per_cell.items()}
        pop_mean = float(np.mean([np.mean(v) for v in per_cell.values()]))
        print(f"  {name}: population mean {pop_mean:.1f} Hz; cells: "
              + " ".join(f"{b}:{m:.0f}" for b, m in means.items()))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "da_drive_census.json").write_text(json.dumps({
        "gate_da_clusters": {str(b): [da.get(b), cluster_of(da.get(b, "?"))] for b in GATE_DA},
        "sugar_active": sorted(sugar_set), "bitter_active": sorted(bitter_set),
        "overlap": sorted(sugar_set & bitter_set),
        "gate_da_rates": {n: {str(b): results[n].get(b, [0]*REPS) for b in GATE_DA}
                          for n in ("baseline", "sugar_only", "bitter_only")},
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT / 'da_drive_census.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
