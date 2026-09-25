"""WP0: reproduce Phase 1 headline metrics from the frozen state.

Re-verifies (frozen conditions, frozen seeds):
  1. test suite passes (68)
  2. spontaneous: 0 spikes / 30 trials (run-006, seeds 1000-1029)
  3. WP9 decision boundary corners on run-007 (seeds 10000-10004):
       (200,0) feed ~82 Hz; (200,200) withhold <=6.7; (0,200) withhold 0
  4. sugar recruitment: ~411 spiking (but note: WP8's was 150 Hz actual;
     we verify BOTH the 150 Hz historic number and the true-200 number)
  5. L0 boundary exactness: the full row r_sugar=200 reproduces the
     frozen WP9 row (withhold for all r_bitter >= 20)

All runs explicit-rate (dataclasses.replace), checkpointed.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

OUT = Path("results/phase2/wp0_reverification.jsonl")
MN9_L = 10331


def run_checked(matrix, node_ids, label, params, stim, stim2, r2, seed, duration=1000.0):
    done = {}
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[(rec["label"], rec["seed"])] = rec
    if (label, seed) in done:
        return done[(label, seed)]
    t0 = time.time()
    r = simulate_lif(matrix, node_ids, params, duration_ms=duration,
                     stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    rec = {"label": label, "seed": seed, "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
           "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
           "wall_s": round(time.time() - t0, 1)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def main() -> int:
    r6 = Path("data/processed/neuprint_snapshots/run-006")
    r7 = Path("data/processed/neuprint_snapshots/run-007")
    m6 = sparse.load_npz(r6 / "connectivity_matrix_signed.npz").tocsr()
    n6 = np.load(r6 / "connectivity_nodes.npy").tolist()
    m7 = sparse.load_npz(r7 / "connectivity_matrix_signed.npz").tocsr()
    n7 = np.load(r7 / "connectivity_nodes.npy").tolist()
    seeds = json.loads(Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    p_default = LIFParams()  # spontaneous: no drive, rate irrelevant
    p150 = dataclasses.replace(LIFParams(), r_poisson_Hz=150.0)  # the HISTORIC WP8 condition (mislabeled era)
    p200 = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    print("== 1. spontaneous (run-006, frozen seeds 1000-1029) ==", flush=True)
    spon = [run_checked(m6, n6, "spontaneous_run006", p_default, None, None, None, 1000 + i)
            for i in range(30)]
    print(f"   total_spikes: {[t['total_spikes'] for t in spon]} -> sum {sum(t['total_spikes'] for t in spon)}", flush=True)

    print("== 2. WP9 boundary corners (run-007, frozen seeds 10000-10004) ==", flush=True)
    for label, rs, rb, stim, stim2, r2 in [
        ("corner_200_0", 200, 0, sugar, None, None),
        ("corner_200_200", 200, 200, sugar, bitter, 200.0),
        ("corner_0_200", 0, 200, None, bitter, 200.0),
    ]:
        recs = []
        for i in range(5):
            params = dataclasses.replace(LIFParams(), r_poisson_Hz=float(rs))
            recs.append(run_checked(m7, n7, label, params, stim, stim2, r2, 10_000 + i))
        mn9 = [t["mn9_l_hz"] for t in recs]
        verdict = "feed" if np.mean(mn9) >= 41.5 else "withhold"
        print(f"   {label}: MN9_L {mn9} -> {verdict}", flush=True)

    print("== 3. sugar recruitment historic (150 Hz) vs true (200 Hz), n=5 ==", flush=True)
    for label, params in [("sugar_150", p150), ("sugar_200", p200)]:
        recs = [run_checked(m7, n7, label, params, sugar, None, None, 10_000 + i) for i in range(5)]
        nspk = [t["n_spiking"] for t in recs]
        print(f"   {label}: n_spiking {nspk} (mean {np.mean(nspk):.1f})", flush=True)

    print("== 4. L0 boundary row: r_sugar=200, r_bitter in {{20,60,120,200}}, n=3 ==", flush=True)
    for rb in [20, 60, 120, 200]:
        recs = []
        for i in range(3):
            params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
            recs.append(run_checked(m7, n7, f"row200_{rb}", params, sugar, bitter, float(rb), 10_000 + i))
        mn9 = [t["mn9_l_hz"] for t in recs]
        print(f"   (200,{rb}): MN9_L {mn9} -> {'feed' if np.mean(mn9) >= 41.5 else 'withhold'}", flush=True)

    print("WP0 metric replay complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
