"""Phase 7 P3 harness - graded unlearning (dose sweep) on GNG521, fast-decay.

Frozen by docs/PHASE_7P3_PREREG.md. Env PHASE7P3_MODE = fast | full.
Globals OUT/REPS/PROBE_BASE/TAU injected in memory only by
phase7p3_launcher.py (harness sha256 pinned in prereg, guard G1).

Rank-targeted decay is deterministic and sim-independent (observe_rate_pair
is a no-op; apply is w <- w*e^(-1/TAU) with W_EPS snap on rank edges), so:
  fast mode: between probe cycles, apply the exact multiplicative decay
             analytically (one factor e^(-dc/TAU) on rank edges, snap), and
             sim ONLY at probe cycles.
  full mode: sim every cycle (guard each), then decay per cycle - the
             phase-6 semantics; used by the validation test to prove fast
             == full bit-identically.
Probe cycles: alone at (5,15,25) x 2 seeds; cosugar at (25,) x 2 seeds.
Base matrix: frozen R1CK; rank set = ckpt - pristine nonzero (sha256 pinned).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.embodiment.body_graph import CUE_GRNS, DRIVE_HZ, MN9_L
from fly.plasticity import PlasticityGuard, StabilityThresholds
from fly.training import TrainingRun, weight_matrix_hash
from fly.plasticity import HebbianRule, PlasticityConfig, Semantics

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
W_EPS = 1e-9
N_CYCLES = 25
ALONE_AT = (5, 15, 25)
COSUGAR_AT = (25,)
RANK_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"

# injected by launcher / test
OUT = Path("results/phase7p3/unset")
REPS = 1
PROBE_BASE = 0
TAU = 1.0
MODE = "fast"


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def log(path: Path, rec: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def world():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=DRIVE_HZ)
    return matrix, nodes, sugar, params


def load_acquired(matrix, nodes):
    base_rule = HebbianRule(PlasticityConfig(eta=1e-4, semantics=Semantics.V_CLIP, w_max=766.0))
    retained = TrainingRun.load(R1CK, matrix, nodes, base_rule, guard(), MN9_L)
    return retained.matrix.copy()


def rank_edges(acquired, pristine):
    d = (acquired - pristine).tocoo()
    rank = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    sha = hashlib.sha256(json.dumps(rank).encode()).hexdigest()
    if sha != RANK_SHA256:
        raise RuntimeError(f"RANK_SET sha {sha} != pinned {RANK_SHA256}")
    return rank


def decay_to(matrix, rank, cycles, tau):
    """Exact rank decay after `cycles` cycles: w <- w * e^(-cycles/tau), snap."""
    coo = matrix.tocoo()
    idx = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(coo.row, coo.col))}
    f = math.exp(-cycles / tau)
    data = coo.data.copy()
    for e in rank:
        k = idx.get(e)
        if k is None:
            continue
        v = float(data[k]) * f
        data[k] = 0.0 if v < W_EPS else v
    out = sparse.coo_matrix((data, (coo.row, coo.col)), shape=coo.shape).tocsr()
    out.sum_duplicates()
    return out


def probe(matrix, nodes, params, sugar, pseed, ptype):
    res = simulate_lif(matrix, nodes, params, 1000.0,
                       stimulated=list(CUE_GRNS),
                       stimulated2=(list(sugar) if ptype == "cosugar" else None),
                       r_poisson2_Hz=(DRIVE_HZ if ptype == "cosugar" else None),
                       seed=pseed)
    return {"mn9_hz": float(len(res.spike_times.get(MN9_L, []))),
            "n_spikes": int(res.n_spikes)}


def main() -> int:
    mode = os.environ.get("PHASE7P3_MODE", MODE)
    assert mode in ("fast", "full")
    pristine, nodes, sugar, params = world()
    acquired = load_acquired(pristine, nodes)
    rank = rank_edges(acquired, pristine)
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "p3.jsonl"
    g = guard()
    log(jout, {"phase": "config", "mode": mode, "tau": TAU, "probe_base": PROBE_BASE,
               "rank_n": len(rank), "acquired_hash": weight_matrix_hash(acquired),
               "pristine_hash": weight_matrix_hash(pristine)})
    if mode == "full":
        # phase-6 semantics: sim + guard EVERY cycle, then decay one cycle.
        # Guard-sim seeds live at PROBE_BASE + 100000 + cyc (outside all
        # preregistered spaces; full mode is used only by the validation test).
        matrix = acquired.copy()
        for cyc in range(1, N_CYCLES + 1):
            matrix = decay_to(matrix, rank, 1, TAU)  # decay first: cycle c sees e^(-c/tau)
            r = probe(matrix, nodes, params, sugar, PROBE_BASE + 100000 + cyc, "alone")
            fired = g.check(trial_spikes=r["n_spikes"])
            log(jout, {"phase": "cycle", "cycle": cyc, "seed": PROBE_BASE + 100000 + cyc,
                       "mn9_hz": r["mn9_hz"], "weight_hash": weight_matrix_hash(matrix),
                       **({"guard_fired": fired} if fired else {})})
    # probes from analytically decayed matrices (identical in both modes)
    for cyc in ALONE_AT:
        m = decay_to(acquired, rank, cyc, TAU)
        for s in (0, 1):
            pseed = PROBE_BASE + 100 * cyc + s
            r = probe(m, nodes, params, sugar, pseed, "alone")
            fired = g.check(trial_spikes=r["n_spikes"])
            log(jout, {"phase": "probe", "ptype": "alone", "cycle": cyc, "seed": pseed,
                       "mn9_hz": r["mn9_hz"], "weight_hash": weight_matrix_hash(m),
                       **({"guard_fired": fired} if fired else {})})
    m25 = decay_to(acquired, rank, N_CYCLES, TAU)
    for s in (0, 1):
        pseed = PROBE_BASE + 1000 + s
        r = probe(m25, nodes, params, sugar, pseed, "cosugar")
        fired = g.check(trial_spikes=r["n_spikes"])
        log(jout, {"phase": "probe", "ptype": "cosugar", "cycle": N_CYCLES, "seed": pseed,
                   "mn9_hz": r["mn9_hz"], "weight_hash": weight_matrix_hash(m25),
                   **({"guard_fired": fired} if fired else {})})
    d = (m25 - pristine).tocoo()
    fp = sorted([int(i), int(j)] for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rw = {f"{i},{j}": float(m25[i, j]) for i, j in rank}  # rank-edge final weights (c5 metric)
    (OUT / "footprint_final.json").write_text(json.dumps(
        {"tau": TAU, "n_edges": len(fp), "edges": fp, "rank_final_weights": rw,
         "sha256": hashlib.sha256(json.dumps(fp).encode()).hexdigest()}), encoding="utf-8")
    print(f"p3 done mode={mode} tau={TAU} probe_base={PROBE_BASE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
