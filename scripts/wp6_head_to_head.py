"""WP6 head-to-head: our LIF implementation vs the authors' Brian2 model.

Runs the reference reproduction chain on the run-005 biological subgraph:
- arm 'reference': unmodified shiu_model.py (Brian2), brian2.seed(42+i) per trial
- arm 'ours':      fly.dynamics.lif.simulate_lif, numpy seed 42+i per trial

Same inputs, same stimulation protocol (DNge104 pair 12781/556329
Poisson-driven), same duration. Checkpoints every trial to a JSONL file so
partial results survive interruption; final stats are computed from whatever
trials are on disk.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RUN_DIR = Path("data/processed/neuprint_snapshots/run-005")
REF_INPUTS = RUN_DIR / "reference_inputs"
SEED_IDS = [12781, 556329]
SEED_BASE = 42


def _load_shiu():
    spec = importlib.util.spec_from_file_location(
        "shiu_model", Path("data/raw/reference/shiu_model.py")
    )
    shiu = importlib.util.module_from_spec(spec)
    sys.modules["shiu_model"] = shiu
    spec.loader.exec_module(shiu)
    return shiu


def run_reference_trial(shiu, comp_csv, con_parquet, i2flyid, flyid2i, duration_ms, seed):
    import brian2 as b2

    b2.seed(seed)
    params = dict(shiu.default_params)
    from brian2 import ms

    params["t_run"] = duration_ms * ms
    params["n_run"] = 1
    spk_trn = shiu.run_trial(
        exc=[flyid2i[n] for n in SEED_IDS],
        exc2=[],
        slnc=[],
        path_comp=str(comp_csv),
        path_con=str(con_parquet),
        params=params,
    )
    return {int(i2flyid[i]): len(v) for i, v in spk_trn.items() if len(v)}


def run_ours_trial(matrix, node_ids, duration_ms, seed):
    from fly.dynamics.lif import LIFParams, simulate_lif

    result = simulate_lif(
        matrix, node_ids, LIFParams(),
        duration_ms=duration_ms,
        stimulated=SEED_IDS,
        seed=seed,
    )
    return {int(nid): len(v) for nid, v in result.spike_times.items()}


def record_line(line: dict, jsonl_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")
        fh.flush()


def summarize(jsonl_path: Path, n_neurons: int, node_ids: list[int]) -> dict:
    records = {}
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        records[(rec["arm"], rec["trial"])] = rec

    summary: dict = {"n_neurons": n_neurons, "trials": {}}
    mean_counts: dict[str, np.ndarray] = {}

    for arm in ("reference", "ours"):
        arm_recs = [r for (a, _), r in sorted(records.items()) if a == arm]
        if not arm_recs:
            continue
        totals = np.array([r["total_spikes"] for r in arm_recs], dtype=float)
        n_spiking = np.array([r["n_spiking"] for r in arm_recs], dtype=float)
        seed_a = np.array([r["seed_rates"]["12781"] for r in arm_recs], dtype=float)
        seed_b = np.array([r["seed_rates"]["556329"] for r in arm_recs], dtype=float)

        counts = np.zeros(len(node_ids))
        index_of = {nid: k for k, nid in enumerate(node_ids)}
        for rec in arm_recs:
            for nid, c in rec["counts"].items():
                counts[index_of[int(nid)]] += c
        mean_counts[arm] = counts / len(arm_recs)

        majority_active = {
            int(nid)
            for k, nid in enumerate(node_ids)
            if sum(1 for r in arm_recs if int(nid) in r["counts"]) > len(arm_recs) / 2
        }

        summary["trials"][arm] = {
            "n_trials": len(arm_recs),
            "total_spikes": {
                "mean": float(totals.mean()),
                "std": float(totals.std(ddof=1)) if len(arm_recs) > 1 else None,
            },
            "n_spiking": {
                "mean": float(n_spiking.mean()),
                "std": float(n_spiking.std(ddof=1)) if len(arm_recs) > 1 else None,
            },
            "recruitment_fraction": {
                "mean": float((n_spiking / n_neurons).mean()),
                "std": float((n_spiking / n_neurons).std(ddof=1)) if len(arm_recs) > 1 else None,
            },
            "seed_rate_12781_Hz": {
                "mean": float(seed_a.mean()),
                "std": float(seed_a.std(ddof=1)) if len(arm_recs) > 1 else None,
            },
            "seed_rate_556329_Hz": {
                "mean": float(seed_b.mean()),
                "std": float(seed_b.std(ddof=1)) if len(arm_recs) > 1 else None,
            },
            "majority_active_neurons": len(majority_active),
        }
        summary.setdefault("_majority_sets", {})[arm] = sorted(majority_active)

    if {"reference", "ours"}.issubset(mean_counts):
        from scipy import stats

        rho, pval = stats.spearmanr(mean_counts["ours"], mean_counts["reference"])
        ref_totals = np.array(
            [r["total_spikes"] for (a, _), r in records.items() if a == "reference"], dtype=float
        )
        our_totals = np.array(
            [r["total_spikes"] for (a, _), r in records.items() if a == "ours"], dtype=float
        )
        t_stat, t_p = stats.ttest_ind(our_totals, ref_totals, equal_var=False)

        set_a = set(summary["_majority_sets"]["ours"])
        set_b = set(summary["_majority_sets"]["reference"])
        jaccard = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 1.0

        summary["comparison"] = {
            "spearman_rho_per_neuron_mean_counts": float(rho),
            "spearman_p_value": float(pval),
            "welch_t_total_spikes": {
                "t_statistic": float(t_stat),
                "p_value": float(t_p),
                "ours_mean": float(our_totals.mean()),
                "reference_mean": float(ref_totals.mean()),
            },
            "jaccard_majority_active_sets": float(jaccard),
        }
    summary.pop("_majority_sets", None)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", choices=["both", "reference", "ours"], default="both")
    parser.add_argument("--n-trials", type=int, default=30)
    parser.add_argument("--start-trial", type=int, default=0)
    parser.add_argument("--duration-ms", type=float, default=1000.0)
    parser.add_argument("--out-dir", type=Path, default=Path("results/wp6_headtohead"))
    args = parser.parse_args()

    comp_csv = REF_INPUTS / "completeness.csv"
    con_parquet = REF_INPUTS / "connectivity.parquet"

    df_comp = pd.read_csv(comp_csv, index_col=0)
    node_ids = [int(v) for v in df_comp.index]
    flyid2i = {jid: i for i, jid in enumerate(df_comp.index)}
    i2flyid = {i: j for j, i in flyid2i.items()}
    n_neurons = len(node_ids)

    from scipy import sparse as sp

    matrix = sp.load_npz(RUN_DIR / "connectivity_matrix.npz").tocsr()

    shiu = None
    if args.arms in ("both", "reference"):
        shiu = _load_shiu()

    jsonl_path = args.out_dir / "trials.jsonl"
    for trial in range(args.start_trial, args.n_trials):
        seed = SEED_BASE + trial

        if args.arms in ("both", "reference"):
            t0 = time.time()
            counts = run_reference_trial(shiu, comp_csv, con_parquet, i2flyid, flyid2i,
                                          args.duration_ms, seed)
            line = {
                "arm": "reference", "trial": trial, "seed": seed,
                "duration_ms": args.duration_ms,
                "total_spikes": int(sum(counts.values())),
                "n_spiking": len(counts),
                "seed_rates": {str(s): counts.get(s, 0) for s in SEED_IDS},
                "counts": {str(k): v for k, v in counts.items()},
            }
            record_line(line, jsonl_path)
            print(f"[reference] trial {trial + 1}/{args.n_trials} seed={seed} "
                  f"total={line['total_spikes']} n_spiking={line['n_spiking']} "
                  f"({time.time() - t0:.1f}s)", flush=True)

        if args.arms in ("both", "ours"):
            t0 = time.time()
            counts = run_ours_trial(matrix, node_ids, args.duration_ms, seed)
            line = {
                "arm": "ours", "trial": trial, "seed": seed,
                "duration_ms": args.duration_ms,
                "total_spikes": int(sum(counts.values())),
                "n_spiking": len(counts),
                "seed_rates": {str(s): counts.get(s, 0) for s in SEED_IDS},
                "counts": {str(k): v for k, v in counts.items()},
            }
            record_line(line, jsonl_path)
            print(f"[ours] trial {trial + 1}/{args.n_trials} seed={seed} "
                  f"total={line['total_spikes']} n_spiking={line['n_spiking']} "
                  f"({time.time() - t0:.1f}s)", flush=True)

    summary = summarize(jsonl_path, n_neurons, node_ids)
    summary_path = args.out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if args.arms == "both" and args.n_trials == 30 and args.start_trial == 0:
        val_path = Path("validation/reference/wp6_head_to_head.json")
        val_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
