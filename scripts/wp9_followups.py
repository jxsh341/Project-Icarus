"""WP9 follow-ups: staggered-onset latency + generalization probe.

Staggered onset: sugar 200 Hz from t=0, bitter 200 Hz from t=200 ms
(the delayed-drive capability built for this). Records full MN9_L
spike-time lists so suppression latency (bitter onset -> last MN9_L
spike) is measurable per trial.

Generalization probe: off-grid drive ratios (170,0), (170,120),
(90,180) plus on-grid (200,200) re-run, all with LEFT-OUT seeds
(12000-12009) - fresh RNG streams the grid never used.

Checkpointed per trial; resumable.
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
STAG_OUT = Path("results/wp9/staggered_trials.jsonl")
GEN_OUT = Path("results/wp9/generalization_trials.jsonl")
MN9_L, MN9_R = 10331, 16949
DURATION_MS = 1000.0
BITTER_ONSET_MS = 200.0


def load_setup():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    return matrix, node_ids, [r["bodyId"] for r in seeds["sugar_R"]], [r["bodyId"] for r in seeds["bitter_R"]]


def done_keys(path: Path, keyfields: tuple):
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done.add(tuple(rec[k] for k in keyfields))
    return done


def staggered(matrix, node_ids, sugar, bitter) -> int:
    done = done_keys(STAG_OUT, ("seed",))
    STAG_OUT.parent.mkdir(parents=True, exist_ok=True)
    p200 = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    with STAG_OUT.open("a", encoding="utf-8") as fh:
        for i in range(10):
            seed = 11_000 + i
            if (seed,) in done:
                continue
            t0 = time.time()
            r = simulate_lif(matrix, node_ids, p200, duration_ms=DURATION_MS,
                             stimulated=sugar, stimulated2=bitter,
                             r_poisson2_Hz=200.0, stim2_start_ms=BITTER_ONSET_MS,
                             seed=seed)
            rec = {
                "seed": seed,
                "mn9_l_spike_times_ms": [round(t, 2) for t in r.spike_times.get(MN9_L, [])],
                "mn9_l_total": len(r.spike_times.get(MN9_L, [])),
                "pre_onset_spikes": sum(1 for t in r.spike_times.get(MN9_L, []) if t < BITTER_ONSET_MS),
                "total_spikes": r.n_spikes,
                "wall_s": round(time.time() - t0, 1),
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[staggered] seed={seed} MN9_L spikes={rec['mn9_l_total']} "
                  f"(pre-onset {rec['pre_onset_spikes']}) {rec['wall_s']}s", flush=True)
    return 0


def generalization(matrix, node_ids, sugar, bitter) -> int:
    cells = [(170, 0), (170, 120), (90, 180), (200, 200)]  # last = on-grid, left-out seeds
    done = done_keys(GEN_OUT, ("r_sugar", "r_bitter", "seed"))
    GEN_OUT.parent.mkdir(parents=True, exist_ok=True)
    with GEN_OUT.open("a", encoding="utf-8") as fh:
        for r_sugar, r_bitter in cells:
            params = dataclasses.replace(LIFParams(), r_poisson_Hz=float(r_sugar))
            for i in range(10):
                seed = 12_000 + i
                if (r_sugar, r_bitter, seed) in done:
                    continue
                t0 = time.time()
                r = simulate_lif(matrix, node_ids, params, duration_ms=DURATION_MS,
                                 stimulated=sugar if r_sugar > 0 else None,
                                 stimulated2=bitter if r_bitter > 0 else None,
                                 r_poisson2_Hz=float(r_bitter) if r_bitter > 0 else None,
                                 seed=seed)
                rec = {"r_sugar": r_sugar, "r_bitter": r_bitter, "seed": seed,
                       "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
                       "mn9_r_hz": len(r.spike_times.get(MN9_R, [])),
                       "total_spikes": r.n_spikes,
                       "wall_s": round(time.time() - t0, 1)}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print(f"[gen ({r_sugar},{r_bitter})] seed={seed} MN9_L={rec['mn9_l_hz']} Hz", flush=True)
    return 0


def main() -> int:
    matrix, node_ids, sugar, bitter = load_setup()
    staggered(matrix, node_ids, sugar, bitter)
    generalization(matrix, node_ids, sugar, bitter)
    print("follow-ups complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
