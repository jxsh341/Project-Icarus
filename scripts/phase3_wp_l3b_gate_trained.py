"""WP-L3b: gate dynamics on the TRAINED, regressing circuit (the decisive test).

L3_DESIGN.md §5 WP-L3b, pre-registered: replay the GNG380 reversal
block (Task B's regressing blk0) with gate-DA driven at swept rates
INSIDE the training trials (via TrialSpec gate fields, test-verified
default-off); criterion: gated hub suppression arrests the
intermediate climb below ~300 Hz and the readout holds its crossing
(vs Task B's measured 49->27 regression).

Structure per gate-rate arm (0/50/100/150/200 Hz):
- Restore R1's retained state (blk0 checkpoint; bit-identical to
  end-of-acquisition - verified in Task B).
- 25 reversal trials, SAME training seeds as Task B blk0 (85600+t):
  the 0-Hz arm must reproduce the measured regression arc (rise to
  ~49 by t15-16, fall to ~27 by t24) - CONTROL-REPRODUCTION GATE,
  fail loudly if violated (the replay itself would be invalid).
- Probes every 5 trials (2 sims/point, distinct seeds): traced sim
  reading the 8 intermediates + MN9 (plasticity off, gate off -
  probes measure the circuit state, not the gate's transient).
- Training update: frozen L1 V_MAG via run.run_trial (single source
  of truth; gate flows through TrialSpec).
- Guard live. Probe seeds 152000+ (disjoint from all prior).
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
OUT = Path("results/phase3/wp_l3b")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
CUE = [50843, 53901, 103327, 129624, 556072, 559464]
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
INTER = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
GATE_RATES = (0, 50, 100, 150, 200)
N_TRIALS = 25
PROBE_AT = (5, 10, 15, 20, 24)
TRAIN_SEED_BASE = 85_600  # Task B blk0 replay
PROBE_SEED_BASE = 152_000


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    out = OUT / "l3b_gate_trained.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)

    for gate_rate in GATE_RATES:
        rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
        retained = TrainingRun.load(R1CK, matrix, nodes, rule, guard(), MN9_L)
        run = TrainingRun(retained.matrix, nodes, rule, guard(), MN9_L,
                          f"l3b_g{gate_rate}", OUT / f"ckpt_g{gate_rate}",
                          lif_params=lif_params)
        # 25 reversal training trials with the gate INSIDE
        for t in range(N_TRIALS):
            spec = TrialSpec(trial=t, seed=TRAIN_SEED_BASE + t,
                             cue_body_ids=tuple(CUE), drive_body_ids=tuple(sugar),
                             drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0,
                             r_drive2_hz=0.0,
                             gate_body_ids=tuple(GATE_DA), r_gate_hz=float(gate_rate))
            rec = run.run_trial(spec)
            run.save()
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"gate_rate": gate_rate, "trial": t, "ptype": "train",
                                     "readout_hz": rec["readout_hz"],
                                     "weight_diff": rec.get("weight_diff"),
                                     "guard_fired": rec.get("guard_fired")}) + "\n")
            if (t + 1) in PROBE_AT:
                for rep in range(2):
                    pseed = PROBE_SEED_BASE + t * 10 + rep
                    # traced probe: cue+sugar present, gate OFF during probes
                    # (probe measures the circuit state, not the gate's transient)
                    lif = simulate_lif(run.matrix, nodes, lif_params, 1000.0,
                                       stimulated=list(CUE), stimulated2=list(sugar),
                                       r_poisson2_Hz=200.0, seed=pseed)
                    inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER}
                    mn9 = len(lif.spike_times.get(MN9_L, []))
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"gate_rate": gate_rate, "trial": t,
                                             "ptype": "probe", "rep": rep,
                                             "intermediates": inter,
                                             "mn9_hz": mn9}) + "\n")
        tr = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()
              if l.strip()]
        tr = [r["readout_hz"] for r in tr
              if r.get("gate_rate") == gate_rate and r.get("ptype") == "train"]
        print(f"gate@{gate_rate:>3}Hz: train arc {tr}", flush=True)

    # ---- control-reproduction gate + verdict ----
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    ctrl = [r["readout_hz"] for r in rows if r["gate_rate"] == 0 and r["ptype"] == "train"]
    peak_ok = max(ctrl[14:17]) >= 45
    end_ok = ctrl[24] <= 35
    print(f"\nCONTROL-REPRODUCTION: peak {max(ctrl[14:17])} (need >=45), "
          f"end {ctrl[24]} (need <=35) -> {'PASS' if peak_ok and end_ok else 'FAIL'}")
    print("\n== verdict per pre-registered criteria ==")
    for rate in GATE_RATES:
        train = [r["readout_hz"] for r in rows if r["gate_rate"] == rate and r["ptype"] == "train"]
        finals = [r for r in rows if r["gate_rate"] == rate and r["ptype"] == "probe"
                  and r["trial"] == 24]
        max_inter = max(max(r["intermediates"].values()) for r in finals) if finals else None
        held = train[24] >= THETA
        arrested = max_inter is not None and max_inter < 300
        print(f"  gate@{rate:>3}: final readout {train[24]:>3} (held={held}), "
              f"max intermediate {max_inter} (arrested={arrested})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
