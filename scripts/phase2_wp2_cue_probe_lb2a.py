"""WP2-blocking open item: LB2a cue probe (criteria c/d).

LB2a is the leading Task-A cue candidate after the structural census:
4 cholinergic Traced neurons, all upstream of MN9_L within 2 hops.
Remaining gates before freezing the cue pair:
  (c) probe-verified zero baseline MN9_L expression when driven alone
  (d) no suppression of the innate sugar-feed program under
      co-stimulation (the IR94e failure mode)

Arms (explicit 200 Hz via dataclasses.replace, n=5 seeds 21000-21004):
  lb2a_only       - criterion (c): MN9_L must stay silent
  lb2a_cosugar   - criterion (d): MN9_L must stay in the feed mode
                    (>= 41.5 Hz, the frozen WP9 threshold)
  (water/ir94e arms re-use the existing probe JSONL; not re-run)

PASS criteria (frozen before the run):
  c: max over seeds of lb2a_only MN9_L rate == 0 Hz
  d: min over seeds of lb2a_cosugar MN9_L rate >= 41.5 Hz
Any deviation -> LB2a is rejected and the synthetic-cue fallback
selection is triggered.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

OUT = Path("results/phase2/wp2_cue_probe_lb2a.jsonl")
MN9_L = 10331
SEEDS = [21_000 + i for i in range(5)]


def run_arm(matrix, node_ids, stim, stim2, r2, label, seed):
    done = {}
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[(rec["label"], rec["seed"])] = rec
    if (label, seed) in done:
        return done[(label, seed)]
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    t0 = time.time()
    r = simulate_lif(matrix, node_ids, params, duration_ms=1000.0,
                     stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    rec = {"label": label, "seed": seed,
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

    # LB2a population: all 4 neurons (both hemispheres) - census bodyIds
    lb2a_ids = [77868, 512913, 120770012, 919015263]
    missing = [b for b in lb2a_ids if b not in set(node_ids)]
    if missing:
        raise SystemExit(f"LB2a bodyIds not in run-007: {missing}")

    seeds = json.loads(Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    print(f"populations: LB2a n={len(lb2a_ids)} (all hemispheres), sugar n={len(sugar)}", flush=True)
    for label, stim, stim2, r2 in [
        ("lb2a_only", lb2a_ids, None, None),
        ("lb2a_cosugar", sugar, lb2a_ids, 200.0),
    ]:
        for seed in SEEDS:
            rec = run_arm(matrix, node_ids, stim, stim2, r2, label, seed)
            print(f"[{label}] seed={rec['seed']} MN9_L={rec['mn9_l_hz']} Hz "
                  f"total={rec['total_spikes']} n_spiking={rec['n_spiking']} "
                  f"({rec['wall_s']}s)", flush=True)

    recs = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    alone = [r["mn9_l_hz"] for r in recs if r["label"] == "lb2a_only"]
    co = [r["mn9_l_hz"] for r in recs if r["label"] == "lb2a_cosugar"]
    c_pass = max(alone) == 0
    d_pass = min(co) >= 41.5
    print(f"criterion (c) zero-alone-expression: MN9_L alone={alone} -> "
          f"{'PASS' if c_pass else 'FAIL'}", flush=True)
    print(f"criterion (d) no-co-suppression: MN9_L cosugar={co} -> "
          f"{'PASS' if d_pass else 'FAIL'}", flush=True)
    print("LB2a VERDICT: " + ("PASS - freeze as Task A cue" if (c_pass and d_pass) else "REJECT - trigger synthetic fallback"),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
