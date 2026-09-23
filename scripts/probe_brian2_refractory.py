"""Probe Brian2's exact refractory/synapse semantics on the 2-neuron toy.

Deterministic drive (SpikeGeneratorGroup, no Poisson) so traces are exact.
Questions this answers:
1. Does on_pre 'g += w' add to g while the target is refractory?
2. What does '(unless refractory)' freeze in practice (v only? g too)?
3. What is the 'w' that the reset string 'v = v_rst; w = 0; g = 0' touches?
4. What is the target's post-spike trajectory (ISI structure)?
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
    import brian2 as b2
    from brian2 import Hz, mV, ms

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

        from fly.data.reference_format import build_reference_inputs

        comp_csv, con_parquet = build_reference_inputs(
            nodes_path, matrix_path, td_path, comp_name="comp.csv", con_name="con.parquet"
        )

        params = dict(shiu.default_params)
        params["t_run"] = 2000 * ms
        params["n_run"] = 1

        neu, syn, spk_mon = shiu.create_model(str(comp_csv), str(con_parquet), params)

        print("neuron variables:", sorted(neu.variables.keys()))
        print("synapse variables:", sorted(syn.variables.keys()))

        # Deterministic drive: neuron 0 kicked to v every 1.0 ms.
        drive_times = np.arange(1.0, 2000.0, 1.0) * ms
        gen = b2.SpikeGeneratorGroup(1, np.zeros(len(drive_times), dtype=int), drive_times)
        drive_syn = b2.Synapses(
            gen, neu, "w_dr : volt", on_pre="v += w_dr", delay=0 * ms
        )
        drive_syn.connect(i=0, j=0)
        drive_syn.w_dr = params["w_syn"] * params["f_poi"]  # 68.75 mV
        neu[0].rfc = 0 * ms  # mirror poi(): no refractory for driven neuron

        mon = b2.StateMonitor(neu, ["v", "g"], record=[0, 1], dt=0.1 * ms)
        net = b2.Network(neu, syn, spk_mon, gen, drive_syn, mon)
        b2.seed(0)
        net.run(params["t_run"])

        t1 = np.asarray(spk_mon.spike_trains()[1] / ms)
        isi = np.diff(t1)
        print(f"\ndrive neuron spikes: {len(spk_mon.spike_trains()[0])}")
        print(f"target spikes: {len(t1)}  mean ISI: {isi.mean():.2f} ms")
        print("first 12 target spike times:", np.round(t1[:12], 2).tolist())
        print("first 12 ISIs:", np.round(isi[:12], 2).tolist())

        # Trace dump around the first few target spikes: does g step up during
        # the refractory window (last_spike .. last_spike + 2.2 ms)?
        tv = np.asarray(mon.t / ms)
        v1 = np.asarray(mon[1].v / mV)
        g1 = np.asarray(mon[1].g / mV)

        report = {"first_spikes": t1[:12].tolist(), "first_isis": isi[:12].tolist()}
        for k in range(min(3, len(t1) - 1)):
            t0 = t1[k]
            lo = int(np.searchsorted(tv, t0 - 0.3))
            hi = int(np.searchsorted(tv, t0 + 3.0))
            print(f"\n--- around target spike #{k} at t={t0:.1f} ms "
                  f"(refractory until {t0 + 2.2:.1f} ms)")
            for row in range(lo, hi, 5):  # every 0.5 ms
                rfc = "RFC" if tv[row] < t0 + 2.2 else "   "
                print(f"  t={tv[row]:6.2f} {rfc} v={v1[row]:8.3f} g={g1[row]:8.3f}")
        report["n_target_spikes"] = int(len(t1))

        out = Path("results/probe_brian2_refractory.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nreport -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
