"""WP8 v2: neural benchmarks on the SIGNED connectome (post-WP6b/6c).

Supersedes the run-005 unsigned benchmarks:
- run-005 was 1-hop truncated (circuit_propagation INVALIDATED there)
  and unsigned (spike counts epileptiform-inflated ~16x).
- run-006 (male-cns:v0.9, depth-2, DNge104-seeded) is the canonical
  substrate for the three plan pillars: spontaneous, stimulus_response,
  circuit_propagation - directly comparable to the WP6b-validated
  protocol (same seed pair 12781/556329).
- run-007 (GRN-seeded closure) adds an excitatory recruitment
  benchmark: sugar-GRN drive, the WP6c-validated excitatory pathway.

All runs use run_benchmark_checkpointed (per-trial JSONL resume) -
standing standard since the WP6c orphan incident.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.benchmarks.neural import run_benchmark_checkpointed

RUN_006 = Path("data/processed/neuprint_snapshots/run-006")
RUN_007 = Path("data/processed/neuprint_snapshots/run-007")
OUT_ROOT = Path("benchmarks_v2")
SEED_IDS = [12781, 556329]  # DNge104 pair (WP6b protocol)
N_TRIALS = 30
DURATION_MS = 1000.0
SEED_BASE = 1000


def load_run(run_dir: Path):
    matrix = sparse.load_npz(run_dir / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(run_dir / "connectivity_nodes.npy").tolist()
    return matrix, node_ids


def save_benchmark(name: str, result, provenance: dict, stimulated, t0: float):
    out_dir = OUT_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()
    payload["wall_clock_seconds"] = time.time() - t0
    payload["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2) + "\n",
                                         encoding="utf-8")
    manifest = {
        "benchmark": result.benchmark,
        "protocol": {
            "n_trials": result.n_trials,
            "duration_ms": result.duration_ms,
            "seeds": result.seeds,
            "stimulated": stimulated,
        },
        "subgraph": provenance,
        "model": "fly.dynamics.lif (WP6b-verified vs Shiu reference, signed graph)",
        "matrix": "connectivity_matrix_signed.npz (NT-signed)",
        "outputs": ["result.json", "trials.jsonl"],
        "wall_clock_seconds": time.time() - t0,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                           encoding="utf-8")
    s = payload.get("summary", {})
    print(f"[{name}] {result.n_trials} trials in {time.time()-t0:.1f}s")
    for key, val in s.items():
        if isinstance(val, dict) and "mean" in val:
            print(f"    {key}: mean={val['mean']:.3f} std={val['std']:.3f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmarks", nargs="+",
                    default=["spontaneous", "stimulus_response",
                             "circuit_propagation", "sugar_recruitment"],
                    help="which benchmarks to run")
    args = ap.parse_args()

    t0 = time.time()
    matrix6, nodes6 = load_run(RUN_006)

    prov6 = {
        "run_id": "run-006",
        "snapshot": str(RUN_006),
        "matrix": "connectivity_matrix_signed.npz",
        "dataset": "male-cns:v0.9",
        "note": "DNge104-seeded depth-2 closure, NT-signed (WP6b)",
    }

    if "spontaneous" in args.benchmarks:
        t = time.time()
        r = run_benchmark_checkpointed(
            "benchmark_spontaneous", matrix6, nodes6,
            n_trials=N_TRIALS, duration_ms=DURATION_MS, seed_base=SEED_BASE,
            checkpoint=OUT_ROOT / "spontaneous" / "trials.jsonl",
            dataset="male-cns:v0.9", subgraph_provenance=prov6,
        )
        save_benchmark("spontaneous", r, prov6, [], t)

    if "stimulus_response" in args.benchmarks:
        t = time.time()
        r = run_benchmark_checkpointed(
            "benchmark_stimulus_response", matrix6, nodes6,
            stimulated=SEED_IDS,
            n_trials=N_TRIALS, duration_ms=DURATION_MS, seed_base=SEED_BASE,
            checkpoint=OUT_ROOT / "stimulus_response" / "trials.jsonl",
            dataset="male-cns:v0.9", subgraph_provenance=prov6,
        )
        save_benchmark("stimulus_response", r, prov6, SEED_IDS, t)

    if "circuit_propagation" in args.benchmarks:
        t = time.time()
        r = run_benchmark_checkpointed(
            "benchmark_circuit_propagation", matrix6, nodes6,
            stimulated=SEED_IDS,
            n_trials=N_TRIALS, duration_ms=DURATION_MS, seed_base=SEED_BASE,
            checkpoint=OUT_ROOT / "circuit_propagation" / "trials.jsonl",
            dataset="male-cns:v0.9", subgraph_provenance=prov6, depth=2,
        )
        save_benchmark("circuit_propagation", r, prov6, SEED_IDS, t)

    if "sugar_recruitment" in args.benchmarks:
        t = time.time()
        matrix7, nodes7 = load_run(RUN_007)
        seeds = json.loads(
            (Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json"))
            .read_text(encoding="utf-8"))
        sugar_ids = [r["bodyId"] for r in seeds["sugar_R"]]
        prov7 = {
            "run_id": "run-007",
            "snapshot": str(RUN_007),
            "matrix": "connectivity_matrix_signed.npz",
            "dataset": "male-cns:v0.9",
            "note": "GRN-seeded depth-2 closure, NT-signed (WP6c substrate)",
        }
        r = run_benchmark_checkpointed(
            "benchmark_stimulus_response", matrix7, nodes7,
            stimulated=sugar_ids,
            n_trials=N_TRIALS, duration_ms=DURATION_MS, seed_base=SEED_BASE,
            checkpoint=OUT_ROOT / "sugar_recruitment" / "trials.jsonl",
            dataset="male-cns:v0.9", subgraph_provenance=prov7,
        )
        save_benchmark("sugar_recruitment", r, prov7, sugar_ids, t)

    print(f"\nwall clock total: {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
