"""Task B R2 mechanism probe: leg-2 intermediate saturation check.

Review-directed (2026-10-08): the GNG380 reversal transient (crosses
theta at trial 15, regresses to 27 by trial 25) needs a WHY before
the Task B close-out scopes Phase 3's consolidation mechanism.

Weight evidence first (from checkpoint diff, t1->t25):
- ZERO edges into MN9_L changed - all growth is on cue->intermediate
  (leg-1) edges;
- the grown cue->intermediate deltas are ENORMOUS (+738 on
  556072->12256, +733 53901->12256, ... vs w_max=766) - the cue's
  inputs to its leg-2 intermediates are saturating the weight cap.

This probe: replay ONE reversal block (same seeds, same retained
entry state) with per-neuron spike tracing on the intermediates that
received the largest grown cue edges (12256, 10646, 15014, 15207,
14642, 14793, 12583, 63701) plus MN9_L, recording each trial:
intermediate firing rates + MN9_L readout, to distinguish:
  (a) refractory saturation of intermediates (their rates RISE then
      FALL while input weights keep growing) -> consolidation = a
      stopping rule keyed to intermediate saturation;
  (b) interference via shared intermediates;
  (c) readout-side ceiling (MN9_L ceiling-then-decline under drive).

Deterministic replay: identical seeds to the original block 0
(training seeds 85000 + bi*100 + t, bi=6 -> 85600+t).
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
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0")
OUT = Path("results/phase2/taskB_r2/mechanism_saturation_probe.json")
MN9_L = 10331
W_MAX = 766.0
ETA = 1e-4
CUE = [50843, 53901, 103327, 129624, 556072, 559464]
INTERMEDIATES = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
BLOCK_BI = 6  # gng380_rev blk0 -> train seeds 85000 + 600 + t


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
    guard = PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0, inh_weight_drift_frac=0.20))
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    # restore the R1 retained (bit-identical to end-of-acquisition) state
    retained = TrainingRun.load(R1CK, matrix, nodes, rule, guard, MN9_L)
    run = TrainingRun(retained.matrix, nodes, rule, guard, MN9_L,
                      "saturation_probe", Path("results/phase2/taskB_r2/ckpt_satprobe"),
                      lif_params=lif_params)

    records = []
    for t in range(25):
        s = TrialSpec(trial=t, seed=85_000 + BLOCK_BI * 100 + t,
                      cue_body_ids=tuple(CUE), drive_body_ids=tuple(sugar),
                      drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0,
                      r_drive2_hz=0.0)
        # traced sim on the CURRENT matrix (pre-update state of trial t),
        # identical wiring to TrainingRun.run_trial (verified against
        # fly/training.py L112-119: stimulated=cue, stimulated2=drive).
        # THEN apply the training update via the same path - the update
        # follows the sim, so the trace reflects trial t's pre-update
        # matrix exactly as in the original run.
        params = dataclasses.replace(lif_params, r_poisson_Hz=s.r_cue_hz)
        lif = simulate_lif(
            run.matrix, nodes, params, duration_ms=s.duration_ms,
            stimulated=list(s.cue_body_ids),
            stimulated2=list(s.drive_body_ids),
            r_poisson2_Hz=s.r_drive_hz,
            seed=s.seed,
        )
        rec = run.run_trial(s)  # applies plasticity, updates weights
        run.save()

        rates = {}
        for n in INTERMEDIATES:
            rates[n] = len(lif.spike_times.get(n, []))
        mn9 = len(lif.spike_times.get(MN9_L, []))
        # cue->intermediate weight sums (input drive to each intermediate)
        nid = {n: i for i, n in enumerate(nodes)}
        cue_rows = np.array([nid[c] for c in CUE])
        w_in = {}
        for n in INTERMEDIATES:
            col = nid[n]
            w_in[n] = round(float(run.matrix[cue_rows, col].sum()), 1)
        records.append({
            "trial": t, "seed": s.seed,
            "readout_mn9_hz": rec["readout_hz"], "trace_mn9_hz": mn9,
            "intermediate_rates_hz": rates,
            "cue_weight_sum_into_intermediates": w_in,
            "n_spiking": rec["n_spiking"], "total_spikes": rec["total_spikes"],
        })
        print(f"t={t:>2} MN9={mn9:>3} | " +
              " ".join(f"{n}:{rates[n]:>3}(w{w_in[n]:>5.0f})" for n in INTERMEDIATES),
              flush=True)

    OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
