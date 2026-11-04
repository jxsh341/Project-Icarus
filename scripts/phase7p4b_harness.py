"""Phase 7 P4b harness - P4 Amendment B1: same protocol, 20 acq trials (GNG521 vs GNG491).

Frozen by docs/PHASE_7P4_PREREG.md. Stage via env PHASE7P4B_STAGE = acq|unlearn.
Globals OUT/ACQ_BASE/UNL_BASE injected in memory only by phase7p4_launcher.py
(harness sha256 pinned in prereg, guard G1).

acq:    load frozen R1CK (GNG521 already acquired, 25-edge footprint sha-pinned),
        run 20 trials cueB(GNG491)+sugar feed (seeds ACQ_BASE+1..20), then
        acquisition probes aloneA/aloneB (2 seeds each, ACQ_BASE+100+s).
        Saves combined matrix to OUT/combined.npz + footprint dumps.
unlearn: from OUT/combined.npz, rank-decay cue-A's 25 solo edges (tau=1.0,
        25 cycles, analytic fast decay as in P3 - sim-independent, validated
        there), probes at cycles (5,15,25): ptypes aloneA/aloneB/cosA/cosB
        x 2 seeds (UNL_BASE+1000+100c+10p+s). Dumps rank_final_weights (A
        edges) and B-edge weights before/after.
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
from fly.plasticity import (HebbianRule, PlasticityConfig, PlasticityGuard,
                            Semantics, StabilityThresholds)
from fly.training import TrainingRun, TrialSpec, weight_matrix_hash

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
CUE_A = [15957, 16327]      # GNG521
CUE_B = [14094]             # GNG491 (held-out, acquired in P1)
MN9_L = 10331
DRIVE_HZ = 200.0
ETA = 1e-4
W_MAX = 766.0
W_EPS = 1e-9
TAU = 1.0
N_ACQ_TRIALS = 20
N_CYCLES = 25
PROBE_AT = (5, 15, 25)
PTYPES = ("aloneA", "aloneB", "cosA", "cosB")
RANK_A_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"

# injected by launcher
OUT = Path("results/phase7p4b/unset")
ACQ_BASE = 0
UNL_BASE = 0


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


def load_base(matrix, nodes):
    rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
    return TrainingRun.load(R1CK, matrix, nodes, rule, guard(), MN9_L).matrix.copy()


def edges_of(m, ref):
    d = (m - ref).tocoo()
    return sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)


def decay_to(matrix, rank, cycles, tau=TAU):
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


def probe(matrix, nodes, params, sugar, cue, pseed, ptype):
    cosugar = ptype.startswith("cos")
    res = simulate_lif(matrix, nodes, params, 1000.0,
                       stimulated=list(cue),
                       stimulated2=(list(sugar) if cosugar else None),
                       r_poisson2_Hz=(DRIVE_HZ if cosugar else None),
                       seed=pseed)
    return {"mn9_hz": float(len(res.spike_times.get(MN9_L, []))), "n_spikes": int(res.n_spikes)}


def stage_acq() -> int:
    pristine, nodes, sugar, params = world()
    base_m = load_base(pristine, nodes)
    rank_a = edges_of(base_m, pristine)
    if hashlib.sha256(json.dumps(rank_a).encode()).hexdigest() != RANK_A_SHA256:
        raise RuntimeError("RANK_A sha mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "acq.jsonl"
    g = guard()
    rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
    run = TrainingRun(base_m.copy(), nodes, rule, g, MN9_L, "p4_acq",
                      OUT / "ckpt", lif_params=params)
    for t in range(1, N_ACQ_TRIALS + 1):
        spec = TrialSpec(trial=t, seed=ACQ_BASE + t, cue_body_ids=tuple(CUE_B),
                         drive_body_ids=tuple(sugar), drive2_body_ids=(),
                         r_cue_hz=DRIVE_HZ, r_drive_hz=DRIVE_HZ, r_drive2_hz=0.0)
        rec = run.run_trial(spec)
        run.save()
        log(jout, {"stage": "acq", "trial": t, "seed": ACQ_BASE + t,
                   "readout_hz": rec["readout_hz"], "guard_fired": rec.get("guard_fired"),
                   "weight_hash": weight_matrix_hash(run.matrix)})
    combined = run.matrix.copy()
    sparse.save_npz(OUT / "combined.npz", combined)
    for ptype, cue in (("aloneA", CUE_A), ("aloneB", CUE_B)):
        for s in (0, 1):
            pseed = ACQ_BASE + 100 + s
            r = probe(combined, nodes, params, sugar, cue, pseed, ptype)
            log(jout, {"stage": "acq_probe", "ptype": ptype, "seed": pseed, "mn9_hz": r["mn9_hz"]})
    fp_comb = edges_of(combined, pristine)
    fp_b = edges_of(combined, base_m)
    (OUT / "footprints.json").write_text(json.dumps({
        "rank_a_n": len(rank_a), "rank_a_sha256": RANK_A_SHA256,
        "combined_vs_pristine_n": len(fp_comb),
        "combined_vs_pristine_sha256": hashlib.sha256(json.dumps(fp_comb).encode()).hexdigest(),
        "b_added_n": len(fp_b),
        "b_added_sha256": hashlib.sha256(json.dumps(fp_b).encode()).hexdigest(),
        "overlap_a_b": len(set(rank_a) & set(fp_b)),
        "combined_hash": weight_matrix_hash(combined)}, indent=1), encoding="utf-8")
    print("acq done", flush=True)
    return 0


def stage_unlearn() -> int:
    pristine, nodes, sugar, params = world()
    base_m = load_base(pristine, nodes)
    rank_a = edges_of(base_m, pristine)
    combined = sparse.load_npz(OUT / "combined.npz").tocsr()
    fp_b = edges_of(combined, base_m)
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "unl.jsonl"
    g = guard()
    log(jout, {"stage": "unl_cfg", "unl_base": UNL_BASE, "tau": TAU,
               "combined_hash": weight_matrix_hash(combined), "rank_a_n": len(rank_a)})
    b_before = {f"{i},{j}": float(combined[i, j]) for i, j in fp_b}
    for cyc in PROBE_AT:
        m = decay_to(combined, rank_a, cyc)
        for p, ptype in enumerate(PTYPES):
            cue = CUE_A if ptype.endswith("A") else CUE_B
            for s in (0, 1):
                pseed = UNL_BASE + 1000 + 100 * cyc + 10 * p + s
                r = probe(m, nodes, params, sugar, cue, pseed, ptype)
                fired = g.check(trial_spikes=r["n_spikes"])
                log(jout, {"stage": "probe", "ptype": ptype, "cycle": cyc, "seed": pseed,
                           "mn9_hz": r["mn9_hz"], "weight_hash": weight_matrix_hash(m),
                           **({"guard_fired": fired} if fired else {})})
    m25 = decay_to(combined, rank_a, N_CYCLES)
    (OUT / "final.json").write_text(json.dumps({
        "rank_a_final_weights": {f"{i},{j}": float(m25[i, j]) for i, j in rank_a},
        "b_after": {f"{i},{j}": float(m25[i, j]) for i, j in fp_b},
        "b_unchanged": all(float(m25[i, j]) == v for (i, j), v in
                           ((tuple(map(int, k.split(","))), v) for k, v in b_before.items())),
        "final_hash": weight_matrix_hash(m25)}, indent=1), encoding="utf-8")
    print("unlearn done", flush=True)
    return 0


def main() -> int:
    stage = os.environ["PHASE7P4B_STAGE"]
    if stage == "acq":
        return stage_acq()
    if stage == "unlearn":
        return stage_unlearn()
    raise RuntimeError(f"unknown stage {stage}")


if __name__ == "__main__":
    raise SystemExit(main())
