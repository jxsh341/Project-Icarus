"""Deterministic-drive parity check between our LIF and Brian2.

Two parts:
1. Fixed inline reimplementation (rfc=0 for driven neuron this time) with
   the same deterministic 1 ms drive as the Brian2 probe. If the dynamics
   match, our target spike count must equal Brian2's 249 with identical
   ISI structure (8.0 ms).
2. Poisson-driven comparison (10 seeds): driven-neuron spike counts per arm.
   If driven counts match but target counts differ, the gap is in the
   dynamics; if driven counts differ, it's in the Poisson process itself.
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

spec = importlib.util.spec_from_file_location("shiu_model", Path("data/raw/reference/shiu_model.py"))
shiu = importlib.util.module_from_spec(spec)
sys.modules["shiu_model"] = shiu
spec.loader.exec_module(shiu)
from brian2 import Hz, ms
import brian2 as b2

p_v0, p_vth, p_vrst = -52.0, -45.0, -52.0
t_mbr, tau_s, t_rfc, t_dly, w_syn = 20.0, 5.0, 2.2, 1.8, 0.275
dt = 0.1
kick = 68.75
w_edge = 50 * w_syn

e_m = np.exp(-dt / t_mbr)
e_s = np.exp(-dt / tau_s)
c_gain = tau_s / (t_mbr - tau_s)

# ---------- Part 1: deterministic drive, inline loop (rfc=0 for driven) ----------
n_steps = int(2000.0 / dt)
v = np.array([p_v0, p_v0])
g = np.array([0.0, 0.0])
last = np.array([-np.inf, -np.inf])
pending: list[tuple[float, int, float]] = []
spikes = [[], []]

for step in range(n_steps):
    t = step * dt
    # deterministic drive at t = 1, 2, ... (kick BEFORE state update)
    if round(t, 6) == round(t) and 1 <= round(t) < 2000:
        v[0] += kick
    frozen = (t - last) < (t_rfc - 1e-9)
    frozen[0] = False  # rfc = 0 for the driven neuron (reference poi())
    new_pending = []
    for (tt, tgt, amt) in pending:
        if tt <= t + 1e-9:
            if not frozen[tgt]:
                g[tgt] += amt
        else:
            new_pending.append((tt, tgt, amt))
    pending = new_pending
    g_next = g * e_s
    u = v - p_v0
    u_next = e_m * u + c_gain * (e_m - e_s) * g
    g = np.where(frozen, g, g_next)
    v = np.where(frozen, p_v0 + u, p_v0 + u_next)
    can = (v > p_vth) & ~frozen
    for i in np.flatnonzero(can):
        spikes[i].append(round(t, 2))
        last[i] = t
        v[i] = p_vrst
        g[i] = 0.0
        pending.append((t + t_dly, 1, w_edge))

print("PART 1 - deterministic drive (rfc=0 for driven):")
print("  driven spikes:", len(spikes[0]), "first:", spikes[0][:5])
print("  target spikes:", len(spikes[1]), " first:", spikes[1][:5])
isi = [round(b - a, 2) for a, b in zip(spikes[1], spikes[1][1:])]
print("  target ISIs (first 12):", isi[:12])
print("  (brian2 reference: 249 target spikes, ISI 8.0)")

# ---------- Part 2: Poisson drive, 10 seeds, driven counts both arms ----------
node_ids = [10, 20]
matrix = sparse.csr_matrix((np.array([50.0]), (np.array([0]), np.array([1]))), shape=(2, 2))
matrix.sum_duplicates()

ref_driven, ref_target = [], []
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
    df_comp = pd.read_csv(comp_csv, index_col=0)
    flyid2i = {jid: i for i, jid in enumerate(df_comp.index)}
    for seed in range(10):
        b2.seed(seed)
        params = dict(shiu.default_params)
        params["t_run"] = 2000 * ms
        params["n_run"] = 1
        params["r_poi"] = 1000 * Hz
        spk = shiu.run_trial(
            exc=[flyid2i[10]], exc2=[], slnc=[],
            path_comp=str(comp_csv), path_con=str(con_parquet), params=params,
        )
        ref_driven.append(len(spk.get(flyid2i[10], [])))
        ref_target.append(len(spk.get(flyid2i[20], [])))

import dataclasses
from fly.dynamics.lif import LIFParams, simulate_lif

p = dataclasses.replace(LIFParams(), r_poisson_Hz=1000.0)
our_driven, our_target = [], []
for seed in range(10):
    r = simulate_lif(matrix, node_ids, p, duration_ms=2000.0, stimulated=[10], seed=seed)
    our_driven.append(len(r.spike_times.get(10, [])))
    our_target.append(len(r.spike_times.get(20, [])))

print("\nPART 2 - Poisson drive 1000 Hz, 10 seeds:")
print("  driven ref:  ", ref_driven, "mean", np.mean(ref_driven))
print("  driven ours: ", our_driven, "mean", np.mean(our_driven))
print("  target ref:  ", ref_target, "mean", np.mean(ref_target))
print("  target ours: ", our_target, "mean", np.mean(our_target))
print("  target ratio ours/ref:", np.mean(our_target) / np.mean(ref_target))
print("  driven ratio ours/ref:", np.mean(our_driven) / np.mean(ref_driven))
