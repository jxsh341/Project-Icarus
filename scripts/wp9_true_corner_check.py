"""Verify the TRUE (200,200) and (200,0) corners with explicit sugar rate.

The WP6c/WP8 'sugar 200 Hz' labels were actually driven at the LIFParams
default 150 Hz (r_poisson_Hz never overridden for the sugar population).
This probe sets r_poisson_Hz=200 explicitly. n=5 seeds each, checkpointed.
"""
import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

OUT = Path("results/wp9/true_corner_check.jsonl")


def main() -> int:
    base = Path('data/processed/neuprint_snapshots/run-007')
    matrix = sparse.load_npz(base / 'connectivity_matrix_signed.npz').tocsr()
    node_ids = np.load(base / 'connectivity_nodes.npy').tolist()
    seeds = json.loads(Path('data/processed/neuprint_snapshots/wp6c_grn_seeds.json').read_text(encoding='utf-8'))
    sugar = [r['bodyId'] for r in seeds['sugar_R']]
    bitter = [r['bodyId'] for r in seeds['bitter_R']]

    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding='utf-8').splitlines():
            if line.strip():
                rec = json.loads(line)
                done.add((rec['condition'], rec['seed']))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    p200 = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    with OUT.open('a', encoding='utf-8') as fh:
        for cond, stim2, r2 in [("200,0", None, None), ("200,200", bitter, 200.0)]:
            for s in range(5):
                seed = 9100 + s
                if (cond, seed) in done:
                    continue
                t0 = time.time()
                r = simulate_lif(matrix, node_ids, p200, duration_ms=1000.0,
                                  stimulated=sugar, stimulated2=stim2,
                                  r_poisson2_Hz=r2, seed=seed)
                rec = {"condition": cond, "seed": seed,
                       "mn9_l_hz": len(r.spike_times.get(10331, [])),
                       "mn9_r_hz": len(r.spike_times.get(16949, [])),
                       "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
                       "wall_s": round(time.time() - t0, 1)}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print(f"[{cond}] seed={seed} MN9_L={rec['mn9_l_hz']} Hz total={rec['total_spikes']} ({rec['wall_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
