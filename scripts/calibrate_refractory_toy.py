"""Empirical calibration: our LIF vs Brian2 on the 2-neuron continuous-drive toy.

Scenario (same as tests/test_lif.py::test_refractory_freezes_v_and_g_during_refractory):
- neuron 10 -> neuron 20, 50 synapses
- neuron 10 Poisson-driven at 1000 Hz (w_syn * f_poi = 68.75 mV, rfc=0 for it)
- 2000 ms trial

Runs the unmodified shiu reference (Brian2) and our implementation with the
same protocol, multiple seeds, and prints target spike counts side by side.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from fly.data.reference_format import build_reference_inputs
from fly.dynamics.lif import LIFParams, simulate_lif

import dataclasses


def _load_shiu():
    spec = importlib.util.spec_from_file_location(
        "shiu_model", Path("data/raw/reference/shiu_model.py")
    )
    shiu = importlib.util.module_from_spec(spec)
    sys.modules["shiu_model"] = shiu
    spec.loader.exec_module(shiu)
    return shiu


def main() -> int:
    shiu = _load_shiu()
    from brian2 import Hz, ms

    node_ids = [10, 20]
    matrix = sparse.csr_matrix(
        (np.array([50.0]), (np.array([0]), np.array([1]))), shape=(2, 2)
    )
    matrix.sum_duplicates()

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        nodes_path = td_path / "nodes.npy"
        matrix_path = td_path / "matrix.npz"
        np.save(nodes_path, np.array(node_ids))
        sparse.save_npz(matrix_path, matrix)
        comp_csv, con_parquet = build_reference_inputs(
            nodes_path, matrix_path, td_path, comp_name="comp.csv", con_name="con.parquet"
        )
        df_comp = pd.read_csv(comp_csv, index_col=0)
        flyid2i = {jid: i for i, jid in enumerate(df_comp.index)}
        i2flyid = {i: j for j, i in flyid2i.items()}

        ref_counts = []
        for seed in range(5):
            import brian2 as b2

            b2.seed(seed)
            params = dict(shiu.default_params)
            params["t_run"] = 2000 * ms
            params["n_run"] = 1
            params["r_poi"] = 1000 * Hz
            spk = shiu.run_trial(
                exc=[flyid2i[10]],
                exc2=[],
                slnc=[],
                path_comp=str(comp_csv),
                path_con=str(con_parquet),
                params=params,
            )
            ref_counts.append(len(spk[flyid2i[20]]))

    ours_counts = []
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=1000.0)
    for seed in range(5):
        r = simulate_lif(matrix, node_ids, params, duration_ms=2000.0, stimulated=[10], seed=seed)
        ours_counts.append(len(r.spike_times.get(20, [])))

    report = {
        "scenario": "10->20, 50 synapses, drive 1000 Hz, 2000 ms",
        "brian2_reference_target_spikes": ref_counts,
        "ours_target_spikes": ours_counts,
        "brian2_mean": float(np.mean(ref_counts)),
        "ours_mean": float(np.mean(ours_counts)),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
