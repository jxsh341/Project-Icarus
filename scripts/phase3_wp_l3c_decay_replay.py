"""WP-L3c decisive replay: DecayHebbianRule on the GNG380 reversal trajectory.

Tests the D-4 prediction + the split criteria (registered):
- PASS (consolidated reversal): crossed theta, then held at t24.
- NEGATIVE-1 (acquisition strangled): never crossed.
- NEGATIVE-2 (crossed but regressed): decay insufficient at band value.

Arms: lam in (0.75 band center, 0.807 band edge, 0.70 band edge) +
L1 control (lam=1.0 equivalent - the frozen rule, for reference).
Replay: same retained entry state (R1 blk0 checkpoint), same
training seeds as Task B blk0 (85600+t), 25 trials, probes every 5
(2 reps, gate OFF during probes, plasticity OFF for probes).
Prediction on record: NEGATIVE-1 for GNG380 at 0.75.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase3_decay_rule import DecayHebbianRule  # noqa: E402

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0")
OUT = Path("results/phase3/wp_l3c")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
CUE = [50843, 53901, 103327, 129624, 556072, 559464]
INTER = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
LAMS = (0.75, 0.807, 0.70)
N_TRIALS = 25
PROBE_AT = (5, 10, 15, 20, 25)
TRAIN_SEED_BASE = 85_600
PROBE_SEED_BASE = 153_000


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def run_arm(matrix, nodes, sugar, lam, out, lif_params):
    tag = f"lam{lam}" if lam < 1.0 else "l1_control"
    rule = (DecayHebbianRule(HebbianRule(PlasticityConfig(
                eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX)), lam=lam)
            if lam < 1.0 else
            HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX)))
    retained = TrainingRun.load(R1CK, matrix, nodes, rule, guard(), MN9_L)
    run = TrainingRun(retained.matrix, nodes, rule, guard(), MN9_L,
                      f"l3c_{tag}", OUT / f"ckpt_{tag}", lif_params=lif_params)
    arc = []
    for t in range(N_TRIALS):
        spec = TrialSpec(trial=t, seed=TRAIN_SEED_BASE + t,
                         cue_body_ids=tuple(CUE), drive_body_ids=tuple(sugar),
                         drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0,
                         r_drive2_hz=0.0)
        rec = run.run_trial(spec)
        run.save()
        arc.append(rec["readout_hz"])
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"lam": lam, "trial": t, "ptype": "train",
                                 "readout_hz": rec["readout_hz"],
                                 "guard_fired": rec.get("guard_fired")}) + "\n")
        if (t + 1) in PROBE_AT:
            for rep in range(2):
                pseed = PROBE_SEED_BASE + t * 10 + rep
                lif = simulate_lif(run.matrix, nodes, lif_params, 1000.0,
                                   stimulated=list(CUE), stimulated2=list(sugar),
                                   r_poisson2_Hz=200.0, seed=pseed)
                inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER}
                mn9 = len(lif.spike_times.get(MN9_L, []))
                with out.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"lam": lam, "trial": t, "ptype": "probe",
                                         "rep": rep, "intermediates": inter,
                                         "mn9_hz": mn9}) + "\n")
    print(f"  {tag}: arc {arc}", flush=True)
    return arc


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "l3c_decay_replay.jsonl"

    print("== WP-L3c: decay-eligible replay of GNG380 reversal ==", flush=True)
    arcs = {}
    arcs["l1"] = run_arm(matrix, nodes, sugar, 1.0, out, lif_params)
    for lam in LAMS:
        arcs[lam] = run_arm(matrix, nodes, sugar, lam, out, lif_params)

    # verdict per the SPLIT criteria
    print("\n== verdict (split criteria, registered) ==")
    for tag, arc in arcs.items():
        crossed = any(v >= THETA for v in arc[:20])
        held = arc[24] >= THETA
        if crossed and held:
            v = "PASS (consolidated reversal)"
        elif not crossed:
            v = "NEGATIVE-1 (acquisition strangled - never crossed)"
        else:
            v = "NEGATIVE-2 (crossed but regressed)"
        peak = max(arc)
        print(f"  {tag}: peak={peak}, final={arc[24]}, crossed={crossed} -> {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
