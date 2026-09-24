"""WP9 scoping probe: what motor population does bitter-only drive recruit?

If bitter GRNs drive a motor set DISJOINT from the sugar-driven feeding
set (MN9_L, MN11D_R, MN4b_R...), the substrate supports action selection
between competing drives - the smallest meaningful behavioral baseline.
Records per-neuron motor recruitment, not just MN9.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
SEEDS_FILE = Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json")
OUT = Path("results/wp9_scoping")
N_TRIALS = 5
DURATION_MS = 1000.0


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    meta = {}
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            meta[r["bodyId"]] = r

    ckpt = OUT / "trials_bitter_only.jsonl"
    done = set()
    if ckpt.exists():
        for line in ckpt.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["seed"])

    with ckpt.open("a", encoding="utf-8") as fh:
        for i in range(N_TRIALS):
            seed = 8000 + i
            if seed in done:
                continue
            t0 = time.time()
            r = simulate_lif(matrix, node_ids, LIFParams(),
                             duration_ms=DURATION_MS,
                             stimulated=bitter, seed=seed)
            # recruited neurons: rate > 0
            recruited = {str(k): len(v) for k, v in r.spike_times.items()}
            motor_recruited = {
                k: v for k, v in recruited.items()
                if int(k) in meta and (
                    (meta[int(k)].get("superclass") or "") == "cb_motor"
                    or "motor" in (meta[int(k)].get("subclass") or "")
                )
            }
            rec = {
                "seed": seed, "total_spikes": r.n_spikes,
                "n_spiking": len(r.spike_times),
                "motor_recruited": motor_recruited,
                "wall_s": round(time.time() - t0, 1),
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[bitter-only seed={seed}] total={rec['total_spikes']} "
                  f"n_spiking={rec['n_spiking']} motor={len(motor_recruited)} "
                  f"({rec['wall_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
