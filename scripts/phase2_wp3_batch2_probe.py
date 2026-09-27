"""Batch probe of the two-feature-screened pool (143 types, ranked by
pre-declared rule). Batch 1 = top 15. Group-level, cue-alone +
cue-cosugar, n=10 seeds (34000-34009), explicit 200 Hz, cue PRIMARY.

Freeze-grade criteria: (c) max(alone)==0 AND (d) min(cosugar)>=41.5.
Also logs cosugar-vs-sugar-only n_spiking for each type (a (d)-adjacent
diagnostic: does the cue perturb the feed program's recruitment?).
Checkpointed per trial to results/phase2/wp3_pilot/batch2_probe.jsonl.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase2/wp3_pilot/batch2_probe.jsonl")
MN9_L = 10331
THRESH = 41.5
SEEDS = range(34_000, 34_010)


def run_arm(W, nodes, stim, stim2, r2, label, typ, seed, out):
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("label") == label and r.get("type") == typ and r.get("seed") == seed:
                return r
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    t0 = time.time()
    res = simulate_lif(W, nodes, params, duration_ms=1000.0,
                       stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    rec = {"label": label, "type": typ, "seed": seed,
           "mn9_l_hz": len(res.spike_times.get(MN9_L, [])),
           "total_spikes": res.n_spikes, "n_spiking": len(res.spike_times),
           "wall_s": round(time.time() - t0, 1)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
    return rec


def main() -> int:
    W = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    meta = {}
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            meta[r["bodyId"]] = r

    ranked = json.loads(Path("results/phase2/wp3_pilot/batch_probe_ranking.json").read_text(encoding="utf-8"))
    batch = ranked[:15]

    print("== batch 1: top 15 of 143 (group-level probes, n=10) ==", flush=True)
    survivors = []
    for t in batch:
        ids = [b for b, r in meta.items() if r.get("type") == t and b in idx]
        if not ids:
            print(f"  {t}: no members in closure - SKIP", flush=True)
            continue
        alone, co = [], []
        nspk_alone, nspk_co = [], []
        for seed in SEEDS:
            r = run_arm(W, nodes, ids, None, None, "cue_alone", t, seed, OUT)
            alone.append(r["mn9_l_hz"])
            nspk_alone.append(r["n_spiking"])
            r = run_arm(W, nodes, sugar, ids, 200.0, "cue_cosugar", t, seed, OUT)
            co.append(r["mn9_l_hz"])
            nspk_co.append(r["n_spiking"])
        c_ok, d_ok = max(alone) == 0, min(co) >= THRESH
        ok = c_ok and d_ok
        if ok:
            survivors.append(t)
        print(f"  {t:<14s} n={len(ids):<3d}: alone={alone} cosugar_min={min(co)} "
              f"-> {'PASS' if ok else 'FAIL(' + ('c' if not c_ok else '') + ('d' if not d_ok else '') + ')'}",
              flush=True)

    print(f"\nbatch-1 survivors: {len(survivors)}: {survivors}", flush=True)
    # sugar-only reference n_spiking for the (d)-adjacent diagnostic
    print("(sugar-only reference n_spiking ~440 from WP0 replay)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
