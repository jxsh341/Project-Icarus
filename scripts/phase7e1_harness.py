"""Phase 7 E1 harness - closed-loop conditioning on the embodiment scaffold.

Frozen by docs/PHASE_7E1_PREREG.md. Arm via env PHASE7E1_ARM (learn|control).
Module globals OUT/REPS/TASTE_BASE/PROBE_BASE injected in memory only by
phase7e1_launcher.py (harness sha256 pinned in prereg, guard G1).

Per rep:
  taste: 8 episodes x 3 steps. Episode starts proboscis EXTENDED (ext=1.0),
  cue_on, sugar_present -> sugar transduced (contact). Each 1 s step runs
  the frozen simulate_lif via the embodiment ports; in the learn arm the
  frozen window-1 leg-1 Hebbian observation (cue -> 1-hop targets, rate
  form) is applied per step with the same HebbianRule/guard as phase 2.
  control arm: identical steps/seeds, plasticity disabled (probe-only).
  probes (after tasting, proboscis retracted ext=0):
    alone:    cue_on, no sugar, 2 steps x 2 seeds
    closed:   cue_on + sugar_present, 3 steps x 2 seeds (does the loop
              close autonomously: cue -> MN9 -> extension -> contact ->
              sugar_detected?)
    sugonly:  sugar_present, no cue, 2 steps x 1 seed
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.embodiment.body_graph import (CUE_GRNS, DRIVE_HZ, MN9_L, BodyState,
                                       default_body_graph)
from fly.plasticity import (HebbianRule, PlasticityConfig, PlasticityGuard,
                            Semantics, StabilityThresholds)
from fly.training import weight_matrix_hash

BASE = Path("data/processed/neuprint_snapshots/run-007")
ETA = 1e-4
W_MAX = 766.0
MN9_FIRE_HZ = 41.5
N_TASTE_EP = 8
N_TASTE_STEPS = 3
N_ALONE_SEEDS = 2
N_ALONE_STEPS = 2
N_CLOSED_SEEDS = 2
N_CLOSED_STEPS = 3
N_PROBE = N_ALONE_SEEDS * N_ALONE_STEPS + N_CLOSED_SEEDS * N_CLOSED_STEPS + 2  # 12

# injected by launcher
OUT = Path("results/phase7e1/unset")
REPS = 1
TASTE_BASE = 0
PROBE_BASE = 0


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
    bitter = [r["bodyId"] for r in grn["bitter_R"]]
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=DRIVE_HZ)
    return matrix, nodes, sugar, bitter, params


def step_once(matrix, nodes, params, body, state, seed):
    """One 1 s embodied step, identical wiring to SensorimotorLoop.step."""
    rates = body.sensor_rates(state)
    res = simulate_lif(
        matrix, nodes, params, 1000.0,
        stimulated=CUE_GRNS if rates["cue"] > 0 else None,
        stimulated2=body.sensors["sugar"].neuron_ids if rates["sugar"] > 0 else None,
        r_poisson2_Hz=rates["sugar"] if rates["sugar"] > 0 else None,
        stimulated3=body.sensors["bitter"].neuron_ids if rates["bitter"] > 0 else None,
        r_poisson3_Hz=rates["bitter"] if rates["bitter"] > 0 else None,
        seed=seed,
    )
    mn9_hz = float(len(res.spike_times.get(MN9_L, [])))
    body.apply_actuators(state, {MN9_L: mn9_hz})
    rec = {"seed": seed, "cue_on": state.cue_on, "sugar_present": state.sugar_present,
           "mn9_hz": mn9_hz, "proboscis_extension": round(state.proboscis_extension, 6),
           "sugar_detected": state.sugar_detected,
           "n_spikes": int(res.n_spikes), "weight_hash": weight_matrix_hash(matrix)}
    return rec, res


def observe_leg1(rule, matrix, nodes, res):
    """Frozen window-1 leg-1 rate-form Hebbian observation (phase-2 L1)."""
    idx_of = {n: i for i, n in enumerate(nodes)}
    rates = {n: len(ts) for n, ts in res.spike_times.items()}
    for cue_id in CUE_GRNS:
        ci = idx_of[cue_id]
        x_hz = rates.get(cue_id, 0)
        if x_hz == 0:
            continue
        row = matrix.getrow(ci)
        for tgt_idx in row.indices.tolist():
            y_hz = rates.get(nodes[tgt_idx], 0)
            if y_hz == 0:
                continue
            rule.observe_rate_pair(ci, tgt_idx, matrix, x_hz=x_hz, y_hz=y_hz)


def main() -> int:
    arm = os.environ["PHASE7E1_ARM"]
    assert arm in ("learn", "control")
    matrix0, nodes, sugar, bitter, params = world()
    body = default_body_graph()
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / f"{arm}.jsonl"
    for rep in range(REPS):
        matrix = matrix0.copy()
        rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX)) if arm == "learn" else None
        g = guard()
        # --- taste episodes ---
        for ep in range(1, N_TASTE_EP + 1):
            state = BodyState(cue_on=True, sugar_present=True, proboscis_extension=1.0)
            for k in range(N_TASTE_STEPS):
                seed = TASTE_BASE + (ep - 1) * N_TASTE_STEPS + k + 1
                rec, res = step_once(matrix, nodes, params, body, state, seed)
                rec.update({"rep": rep, "phase": "taste", "episode": ep, "step": k})
                if rule is not None:
                    observe_leg1(rule, matrix, nodes, res)
                    matrix = rule.apply(matrix)
                    rec["weight_hash"] = weight_matrix_hash(matrix)
                fired = g.check(trial_spikes=res.n_spikes)
                if fired is not None:
                    rec["guard_fired"] = fired
                log(jout, rec)
        log(jout, {"rep": rep, "phase": "post_taste", "weight_hash": weight_matrix_hash(matrix),
                   "arm": arm, "train_base": TASTE_BASE, "probe_base": PROBE_BASE})
        d = (matrix - matrix0).tocoo()
        fp = sorted([int(i), int(j)] for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
        (OUT / f"footprint_r{rep}.json").write_text(json.dumps(
            {"rep": rep, "arm": arm, "n_edges": len(fp), "edges": fp,
             "sha256": hashlib.sha256(json.dumps(fp).encode()).hexdigest()}), encoding="utf-8")
        # --- probes ---
        p = PROBE_BASE + 1000
        def run_probe(ptype, cue_on, sugar_present, n_seeds, n_steps):
            for s in range(n_seeds):
                state = BodyState(cue_on=cue_on, sugar_present=sugar_present, proboscis_extension=0.0)
                for k in range(n_steps):
                    seed = p + s * 10 + k
                    rec, res = step_once(matrix, nodes, params, body, state, seed)
                    rec.update({"rep": rep, "phase": "probe", "ptype": ptype, "pseeds": s, "step": k})
                    fired = g.check(trial_spikes=res.n_spikes)
                    if fired is not None:
                        rec["guard_fired"] = fired
                    log(jout, rec)
            return p + n_seeds * 10
        p = run_probe("alone", True, False, N_ALONE_SEEDS, N_ALONE_STEPS)
        p = run_probe("closed", True, True, N_CLOSED_SEEDS, N_CLOSED_STEPS)
        run_probe("sugonly", False, True, 1, 2)
        print(f"{arm} rep {rep} done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
