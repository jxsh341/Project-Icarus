"""Run the WP8 neural benchmark suite on the run-005 subgraph.

Three protocol pillars (FLY-BASE-001 plan section 15), n=30 seeds each:
- spontaneous: no stimulation, 1000 ms
- stimulus_response: DNge104 pair (12781, 556329) Poisson-driven, 1000 ms
- circuit_propagation: same pair, BFS hop map depth 2, 1000 ms

Outputs to benchmarks/<name>/ with a manifest per benchmark.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.benchmarks.neural import (
    benchmark_circuit_propagation,
    benchmark_spontaneous,
    benchmark_stimulus_response,
)

RUN_DIR = Path("data/processed/neuprint_snapshots/run-005")
OUT_ROOT = Path("benchmarks")
SEED_IDS = [12781, 556329]
N_TRIALS = 30
DURATION_MS = 1000.0
SEED_BASE = 1000


def main() -> int:
    matrix = sparse.load_npz(RUN_DIR / "connectivity_matrix.npz").tocsr()
    node_ids = np.load(RUN_DIR / "connectivity_nodes.npy").tolist()
    n_neurons = len(node_ids)
    n_edges = int(matrix.nnz)

    provenance = {
        "run_id": "run-005",
        "snapshot": str(RUN_DIR),
        "n_neurons": n_neurons,
        "n_edges_summed": n_edges,
        "dataset": "male-cns:v1.0",
        "note": "bidirectional closed subgraph, seeds 12781/556329",
    }

    specs = [
        (
            "spontaneous",
            lambda: benchmark_spontaneous(
                matrix, node_ids, n_trials=N_TRIALS, duration_ms=DURATION_MS,
                seed_base=SEED_BASE, subgraph_provenance=provenance,
            ),
        ),
        (
            "stimulus_response",
            lambda: benchmark_stimulus_response(
                matrix, node_ids, stimulated=SEED_IDS, n_trials=N_TRIALS,
                duration_ms=DURATION_MS, seed_base=SEED_BASE,
                subgraph_provenance=provenance,
            ),
        ),
        (
            "circuit_propagation",
            lambda: benchmark_circuit_propagation(
                matrix, node_ids, stimulated=SEED_IDS, n_trials=N_TRIALS,
                duration_ms=DURATION_MS, seed_base=SEED_BASE,
                subgraph_provenance=provenance, depth=2,
            ),
        ),
    ]

    for name, fn in specs:
        out_dir = OUT_ROOT / name
        out_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        result = fn()
        elapsed = time.time() - t0

        payload = result.to_dict()
        payload["wall_clock_seconds"] = elapsed
        payload["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        result_path = out_dir / "result.json"
        result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        manifest = {
            "benchmark": result.benchmark,
            "protocol": {
                "n_trials": result.n_trials,
                "duration_ms": result.duration_ms,
                "seeds": result.seeds,
                "stimulated": SEED_IDS if name != "spontaneous" else [],
            },
            "subgraph": provenance,
            "model": "fly.dynamics.lif (WP6-verified vs Shiu reference)",
            "outputs": ["result.json"],
            "wall_clock_seconds": elapsed,
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        s = payload.get("summary", {})
        print(f"[{name}] {result.n_trials} trials in {elapsed:.1f}s -> {result_path}")
        for key, val in list(s.items())[:6]:
            if isinstance(val, dict) and "mean" in val:
                print(f"    {key}: mean={val['mean']:.3f} std={val['std']:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
