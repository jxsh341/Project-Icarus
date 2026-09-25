"""Batch cue probe: 15 sampled candidates, cue-alone + cue-cosugar, 5 seeds.

Candidates: results/phase2/wp2_cue_probe_batch_candidates.json (every-69th
by bodyId from 1026 filter-passing cholinergic non-sensory/motor neurons
<=2 hops upstream of MN9_L; sampling rule frozen before the run).

Frozen criteria (unchanged from the registry):
  (c) cue-alone: MN9_L == 0 Hz, all 5 seeds
  (d) cue-cosugar: MN9_L >= 41.5 Hz, all 5 seeds
Checkpointed per trial; resumable; explicit 200 Hz everywhere.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

OUT = Path("results/phase2/wp2_cue_probe_batch.jsonl")
MN9_L = 10331
SEEDS = [22_000 + i for i in range(5)]
THRESH = 41.5


def run_trial(matrix, node_ids, stim, stim2, r2, label, body_id, seed):
    done = {}
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[(rec["label"], rec["body_id"], rec["seed"])] = rec
    key = (label, body_id, seed)
    if key in done:
        return done[key]
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    t0 = time.time()
    r = simulate_lif(matrix, node_ids, params, duration_ms=1000.0,
                     stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    rec = {"label": label, "body_id": body_id, "seed": seed,
           "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
           "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
           "wall_s": round(time.time() - t0, 1)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
    return rec


def main() -> int:
    base = Path("data/processed/neuprint_snapshots/run-007")
    matrix = sparse.load_npz(base / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(base / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(node_ids)}

    cands = json.loads(Path("results/phase2/wp2_cue_probe_batch_candidates.json").read_text(encoding="utf-8"))
    seeds = json.loads(Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    for c in cands:
        b = c["bodyId"]
        if b not in idx:
            print(f"SKIP {b} ({c['type']}): not in closure", flush=True)
            continue
        for label, stim, stim2, r2 in [
            ("cue_alone", [b], None, None),
            ("cue_cosugar", sugar, [b], 200.0),
        ]:
            for seed in SEEDS:
                rec = run_trial(matrix, node_ids, stim, stim2, r2, label, b, seed)
                print(f"[{c['type']}/{b}] {label} seed={rec['seed']} "
                      f"MN9_L={rec['mn9_l_hz']} Hz total={rec['total_spikes']} "
                      f"n_spiking={rec['n_spiking']} ({rec['wall_s']}s)", flush=True)

    # aggregate + verdict
    recs = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== batch verdict (frozen criteria) ==", flush=True)
    survivors = []
    for c in cands:
        b = c["bodyId"]
        alone = [r["mn9_l_hz"] for r in recs if r["body_id"] == b and r["label"] == "cue_alone"]
        co = [r["mn9_l_hz"] for r in recs if r["body_id"] == b and r["label"] == "cue_cosugar"]
        if not alone or not co:
            continue
        c_ok = max(alone) == 0
        d_ok = min(co) >= THRESH
        verdict = "PASS" if (c_ok and d_ok) else ("c-only" if c_ok else "reject")
        if c_ok and d_ok:
            survivors.append({**c, "alone": alone, "cosugar": co})
        print(f"{c['type']:<16s} {b:>9d}: alone={alone} cosugar={co} -> {verdict}", flush=True)
    print(f"\nsurvivors: {len(survivors)}/{len(cands)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
