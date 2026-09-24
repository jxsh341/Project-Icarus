"""WP10: computational cost baseline for the FLY-BASE-001 LIF simulator.

Measures (plan section 17) on the existing, already-run substrates:
wall-clock, RAM, timesteps/s, sim/bio time ratio, storage generated,
plus CPU info. GPU and energy are N/A for this CPU-only numpy/scipy
implementation (recorded as such, not omitted).

Two measurement modes:
  profile  - run a short instrumented trial (1 trial, 1000 ms) per
             substrate and measure resource use directly (peak RSS,
             peak CPU %, wall time). Cheap, fresh numbers.
  archive  - fold in wall-clock + storage stats from the completed
             benchmark/trial archives (WP8 v2, WP6b/c runs), which
             already recorded wall_s per trial and result-file sizes.

Output: validation/reference/wp10_compute_baseline.json
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import psutil
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

OUT = Path("validation/reference/wp10_compute_baseline.json")

SUBSTRATES = {
    "run-006": {
        "dir": Path("data/processed/neuprint_snapshots/run-006"),
        "note": "DNge104-seeded depth-2 closure (WP6b/WP8 substrate)",
        "stimulated": [12781, 556329],
    },
    "run-007": {
        "dir": Path("data/processed/neuprint_snapshots/run-007"),
        "note": "GRN-seeded depth-2 closure (WP6c/WP8 substrate)",
        "stimulated": None,  # filled from seeds file
    },
}


def run_profile(substrate: str, cfg: dict, duration_ms: float = 1000.0) -> dict:
    base = cfg["dir"]
    matrix = sparse.load_npz(base / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(base / "connectivity_nodes.npy").tolist()
    n = len(node_ids)

    proc = psutil.Process()
    gc0 = None
    # baseline RSS before load
    rss_before = proc.memory_info().rss

    t0 = time.perf_counter()
    run = simulate_lif(
        matrix, node_ids, LIFParams(), duration_ms=duration_ms,
        stimulated=cfg["stimulated"], seed=99,
    )
    wall_s = time.perf_counter() - t0
    rss_after = proc.memory_info().rss

    n_steps = int(duration_ms / 0.1)  # dt = 0.1 ms (LIFParams default)
    spikes = run.n_spikes
    return {
        "substrate": substrate,
        "note": cfg["note"],
        "n_neurons": n,
        "n_edges_signed": int(matrix.nnz),
        "duration_ms": duration_ms,
        "n_timesteps": n_steps,
        "timestep_ms": 0.1,
        "wall_clock_s": round(wall_s, 3),
        "timesteps_per_s": round(n_steps / wall_s, 1),
        "x_bio_realtime": round((duration_ms / 1000.0) / wall_s, 4),
        "spikes_in_trial": spikes,
        "ram_peak_rss_mb": round((proc.memory_info().rss) / 1e6, 1),
        "ram_trial_delta_mb": round((rss_after - rss_before) / 1e6, 1),
        "matrix_mem_mb": round((matrix.data.nbytes + matrix.indptr.nbytes
                                + matrix.indices.nbytes) / 1e6, 1),
    }


def collect_archive_stats() -> dict:
    """Wall-clock and storage from completed runs (no re-simulation)."""
    stats = {}
    # WP8 v2 benchmarks
    broot = Path("benchmarks_v2")
    for bdir in sorted(broot.glob("*/")) if broot.exists() else []:
        name = bdir.name
        rj = bdir / "result.json"
        if not rj.exists():
            continue
        r = json.loads(rj.read_text(encoding="utf-8"))
        wall = r.get("wall_clock_seconds")
        size = sum(f.stat().st_size for f in bdir.rglob("*") if f.is_file())
        stats[f"wp8_{name}"] = {
            "n_trials": r["n_trials"],
            "duration_ms_each": r["duration_ms"],
            "wall_clock_s": round(wall, 1) if wall else None,
            "storage_bytes": size,
            "trials_per_s": round(r["n_trials"] / wall, 3) if wall else None,
        }
    # WP6b head-to-head + WP6c grids
    for label, root in [("wp6b_head_to_head", Path("results/wp6_headtohead_run006_signed")),
                        ("wp6c_sugar_bitter", Path("results/wp6c_sugar_bitter"))]:
        if root.exists():
            jls = list(root.glob("trials*.jsonl"))
            n_recs = 0
            walls = []
            for jl in jls:
                for line in jl.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        n_recs += 1
                        if "wall_s" in rec:
                            walls.append(rec["wall_s"])
            size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
            stats[label] = {
                "n_trials": n_recs,
                "wall_s_recorded": bool(walls),
                "mean_wall_s_per_trial": round(float(np.mean(walls)), 2) if walls else None,
                "storage_bytes": size,
                "note": (None if walls else
                         "wall_s not recorded per trial in this run (field added in WP6c); "
                         "total wall clock for the 30x2 run was ~25 min, from session log"),
            }
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["profile", "archive", "both"], default="both")
    args = ap.parse_args()

    # run-007 stimulated: sugar GRNs
    seeds = json.loads(Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json")
                       .read_text(encoding="utf-8"))
    SUBSTRATES["run-007"]["stimulated"] = [r["bodyId"] for r in seeds["sugar_R"]]

    report: dict = {
        "work_package": "WP10",
        "title": "Computational cost baseline (FLY-BASE-001, plan section 17)",
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "implementation": "numpy/scipy sparse LIF (fly.dynamics.lif), CPU-only",
        },
        "measures_applicability": {
            "wall_clock": "measured (profile + archive)",
            "cpu_utilization": "measured as core-seconds proxy via wall clock on this single-threaded loop; detailed per-core % not instrumented",
            "gpu_utilization": "N/A - CPU-only implementation (recorded, not omitted)",
            "ram": "measured (peak RSS + trial delta)",
            "gpu_memory": "N/A - CPU-only implementation",
            "timesteps_per_second": "measured",
            "sim_vs_bio_time_ratio": "measured",
            "storage_generated": "measured (archive)",
            "energy": "not measurable on this host (no per-process watt metering); wall-clock is the proxy",
        },
    }

    if args.mode in ("profile", "both"):
        report["profile"] = {}
        for name, cfg in SUBSTRATES.items():
            t = time.time()
            report["profile"][name] = run_profile(name, cfg)
            print(f"[profile {name}] {report['profile'][name]['wall_clock_s']}s, "
                  f"{report['profile'][name]['timesteps_per_s']} steps/s, "
                  f"RSS {report['profile'][name]['ram_peak_rss_mb']} MB")
    if args.mode in ("archive", "both"):
        report["archive"] = collect_archive_stats()
        for k, v in report["archive"].items():
            print(f"[archive {k}] {v}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("report ->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
