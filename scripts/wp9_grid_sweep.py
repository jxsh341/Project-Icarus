"""WP9: 11x11 sugar/bitter decision-boundary grid sweep.

Sweeps r_sugar and r_bitter in {0,20,...,200} Hz (the paper's own Fig 3a
grid), n=10 seeds per cell, on the run-007 signed closure. Every trial
sets BOTH rates explicitly via dataclasses.replace (the mislabel fix:
WP6c/WP8's 'sugar 200' cells were actually 150 Hz because LIFParams()
default was never overridden).

Readout per trial: MN9_L (10331) rate - the paper's readout, WP6c/WP8-
validated. Decision rule (frozen BEFORE this sweep, see
results/wp9/theta_calibration.json): feed if MN9_L rate >= 41.5 Hz.

Checkpointed per trial to results/wp9/grid_trials.jsonl (resumable).
Full sweep: 121 cells x 10 seeds = 1,210 trials. Expected wall clock at
~30-90 s/trial: 10-30 h. Run in background; poll with process_manage.

Output: results/wp9/grid_trials.jsonl (raw), wp9_report.py consumes it.
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
SEEDS_FILE = Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json")
OUT = Path("results/wp9/grid_trials.jsonl")
MN9_L = 10331

RATES = list(range(0, 201, 20))  # 0..200 in 20 Hz steps (11 values)
N_TRIALS = 10
SEED_BASE = 10_000
DURATION_MS = 1000.0


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done.add((rec["r_sugar"], rec["r_bitter"], rec["seed"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"resuming: {len(done)} trials already checkpointed", flush=True)

    t_start = time.time()
    n_done = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for r_sugar in RATES:
            for r_bitter in RATES:
                # optimization: cell (0,0) is the spontaneous control - verified 0/30
                for i in range(N_TRIALS):
                    seed = SEED_BASE + i
                    if (r_sugar, r_bitter, seed) in done:
                        continue
                    params = dataclasses.replace(LIFParams(), r_poisson_Hz=float(r_sugar))
                    t0 = time.time()
                    run = simulate_lif(
                        matrix, node_ids, params,
                        duration_ms=DURATION_MS,
                        stimulated=sugar if r_sugar > 0 else None,
                        stimulated2=bitter if r_bitter > 0 else None,
                        r_poisson2_Hz=float(r_bitter) if r_bitter > 0 else None,
                        seed=seed,
                    )
                    rec = {
                        "r_sugar": r_sugar, "r_bitter": r_bitter, "seed": seed,
                        "mn9_l_hz": len(run.spike_times.get(MN9_L, [])),
                        "mn9_r_hz": len(run.spike_times.get(16949, [])),
                        "total_spikes": run.n_spikes,
                        "n_spiking": len(run.spike_times),
                        "wall_s": round(time.time() - t0, 1),
                    }
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    n_done += 1
                    if n_done % 10 == 0:
                        rate = n_done / (time.time() - t_start)
                        eta_h = (1210 - len(done) - n_done) / rate / 3600 if rate > 0 else -1
                        print(f"({r_sugar},{r_bitter}) seed {seed}: MN9_L={rec['mn9_l_hz']} Hz "
                              f"| {len(done)+n_done}/1210 | {rate:.2f} trials/s | ETA {eta_h:.1f} h",
                              flush=True)
    print(f"grid complete: {len(done)+n_done} trials in {(time.time()-t_start)/3600:.2f} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
