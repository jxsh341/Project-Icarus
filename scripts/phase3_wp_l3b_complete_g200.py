"""WP-L3b completion: resume the 200 Hz arm (died at trial 18).

The main run (proc_4b6bb366f7a6) was lost at trial 18 of the final
arm. The JSONL holds 4 complete arms (0/50/100/150) + the 200 arm's
trials 0-18 and probes after t=4,9,14. The checkpoint
ckpt_g200/run_state.json + weights_trial_0019.npz are intact.

This script resumes ONLY the missing piece: training trials 19-24
plus probes after t=19 and t=24 (seeds identical to the main run's
scheme: train 85600+t, probes 152000 + t*10 + rep), appending to the
same JSONL. TrainingRun.load restores the potentiated matrix with
hash verification (the bit-for-bit resume rule).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
CKPT = Path("results/phase3/wp_l3b/ckpt_g200")
OUT = Path("results/phase3/wp_l3b/l3b_gate_trained.jsonl")
MN9_L = 10331
W_MAX = 766.0
ETA = 1e-4
GATE_RATE = 200.0
CUE = [50843, 53901, 103327, 129624, 556072, 559464]
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
INTER = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
PROBE_AT = (5, 10, 15, 20, 25)   # fires when (t+1) in PROBE_AT
TRAIN_SEED_BASE = 85_600
PROBE_SEED_BASE = 152_000


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def rec_exists(pp, ptype, trial, rep=None):
    for line in pp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if (r.get("gate_rate") == GATE_RATE and r.get("ptype") == ptype
                and r.get("trial") == trial
                and (rep is None or r.get("rep") == rep)):
            return True
    return False


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
    run = TrainingRun.load(CKPT, matrix, nodes, rule, guard(), MN9_L)
    print(f"resumed from checkpoint: trial_index={run.trial_index}", flush=True)

    for t in range(19, 25):
        if not rec_exists(OUT, "train", t):
            spec = TrialSpec(trial=t, seed=TRAIN_SEED_BASE + t,
                             cue_body_ids=tuple(CUE), drive_body_ids=tuple(sugar),
                             drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0,
                             r_drive2_hz=0.0,
                             gate_body_ids=tuple(GATE_DA), r_gate_hz=GATE_RATE)
            rec = run.run_trial(spec)
            run.save()
            with OUT.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"gate_rate": GATE_RATE, "trial": t, "ptype": "train",
                                     "readout_hz": rec["readout_hz"],
                                     "weight_diff": rec.get("weight_diff"),
                                     "guard_fired": rec.get("guard_fired")}) + "\n")
        if (t + 1) in PROBE_AT:
            for rep in range(2):
                if not rec_exists(OUT, "probe", t, rep):
                    pseed = PROBE_SEED_BASE + t * 10 + rep
                    lif = simulate_lif(run.matrix, nodes, lif_params, 1000.0,
                                       stimulated=list(CUE), stimulated2=list(sugar),
                                       r_poisson2_Hz=200.0, seed=pseed)
                    inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER}
                    mn9 = len(lif.spike_times.get(MN9_L, []))
                    with OUT.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"gate_rate": GATE_RATE,
                                             "trial": t, "ptype": "probe", "rep": rep,
                                             "intermediates": inter,
                                             "mn9_hz": mn9}) + "\n")
    print("200 Hz arm complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
