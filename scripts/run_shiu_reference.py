"""WP6 head-to-head: run the authors' Brian2 model on FLY-BASE inputs.

Uses the *unmodified* reference implementation from
data/raw/reference/shiu_model.py (Shiu et al. 2024) against the run-005
subgraph, with the same stimulation protocol as our NumPy probe:
DNge104 seed pair (12781, 556329) Poisson-driven, 1 s trial.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Load the authors' model.py as-is from its pinned location.
_spec = importlib.util.spec_from_file_location(
    "shiu_model", Path("data/raw/reference/shiu_model.py")
)
shiu = importlib.util.module_from_spec(_spec)
sys.modules["shiu_model"] = shiu
_spec.loader.exec_module(shiu)

from brian2 import mV, ms, Hz  # noqa: E402


def main() -> int:
    base = Path("data/processed/neuprint_snapshots/run-005")
    ref_dir = base / "reference_inputs"
    comp_csv = ref_dir / "completeness.csv"
    con_parquet = ref_dir / "connectivity.parquet"

    params = dict(shiu.default_params)
    params["t_run"] = 1000 * ms
    params["n_run"] = 1

    # Poisson-drive the DNge104 seed pair (same protocol as our probe).
    neu_exc = [12781, 556329]

    spk_trn = shiu.run_trial(
        exc=[],  # filled below via index mapping, not names: see run_exp
        exc2=[],
        slnc=[],
        path_comp=str(comp_csv),
        path_con=str(con_parquet),
        params=params,
    ) if False else None

    # run_trial needs *indices*, not IDs; do the mapping the way run_exp does.
    import pandas as pd

    df_comp = pd.read_csv(comp_csv, index_col=0)
    flyid2i = {jid: i for i, jid in enumerate(df_comp.index)}
    exc_idx = [flyid2i[n] for n in neu_exc]

    spk_trn = shiu.run_trial(
        exc=exc_idx,
        exc2=[],
        slnc=[],
        path_comp=str(comp_csv),
        path_con=str(con_parquet),
        params=params,
    )

    i2flyid = {i: j for j, i in flyid2i.items()}
    n_spikes = sum(len(v) for v in spk_trn.values())
    spiking_ids = sorted({i2flyid[i] for i in spk_trn})

    seed_counts = {}
    for seed in neu_exc:
        seed_counts[str(seed)] = len(spk_trn.get(flyid2i[seed], []))

    out = {
        "implementation": "shiu reference (brian2, unmodified)",
        "n_neurons": int(len(df_comp)),
        "n_seeds_stimulated": len(neu_exc),
        "n_spiking_neurons": len(spiking_ids),
        "total_spikes": int(n_spikes),
        "seed_spikes": seed_counts,
        "seed_rates_Hz": {k: v for k, v in seed_counts.items()},
        "spiking_ids": spiking_ids,
        "duration_ms": 1000.0,
        "params_note": "shiu default_params; t_run=1000ms; n_run=1",
    }
    out_path = ref_dir / "shiu_reference_run.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "spiking_ids"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
