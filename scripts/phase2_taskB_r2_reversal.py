"""FLY-LEARN-001 Task B Stage R2: reversal (per direction, from retained state).

Registry: 'R2 masking probe + R1 interpretation (2026-10-03)' +
'R2 criteria fix (2026-10-03)' + docs/TASK_B_DESIGN.md (S3).
Registered before any R2 data exists:

- Conditions (reversal, per direction, from the R1 RETAINED state):
    gng521_rev : R1 gng521_feed state  -> train WITHHOLD (cue+bitter), 25 trials
    gng380_rev : R1 gng380_withhold state -> train FEED (cue+sugar), 25 trials
  Per-direction runs (NOT interleaved) - the dose rule: interleaving
  silently halves per-cue dose (the WP4 arm2 artifact).
- Dose: 25 reversal trials each (dose table: GNG380-feed needs 15-20;
  GNG521-withhold unknown -> room above 10).
- R2 gate: R1 retention must have passed for that block (final-point
  probes on the learned side of theta, BOTH reps, conservative). A
  block failing retention is N/A-with-reason for R2 - the retained
  state is the required input.
- Probes: 4 types (both cues x alone/cosugar) x 2 reps, at trials
  1,2,3,5,10,15 during training + a FINAL set after trial 25
  (7 point-slots: pt 0-6). >=2 sims/point (probe-variance rule).
- MASKING TEST (load-bearing): GNG521-reversed -> cue-ALONE at the
  final points; alone >= theta = MASKED (old pathway intact), alone
  < theta = GENUINE REORGANIZATION. GNG380-reversed -> cue+COSUGAR at
  the final points; cosugar < theta STILL = old suppression intact
  (NOT unlearned), cosugar >= theta = GENUINE REORGANIZATION.
  Claim entitlement: 'reversed' requires the masking test passed;
  otherwise the finding is 'masked by a second, competing
  association' (two-association coexistence - a different result).
- CORRECTED unlearning criteria (self-caught 2026-10-03): unlearning
  = OLD response gone WITHOUT the competing drive (GNG521: cue-alone
  < theta; GNG380: cosugar >= theta). Relearning: GNG521 cosugar <
  theta; GNG380 cue-alone >= theta.
- L0-R: identical schedule+seeds from the SAME retained state,
  plasticity=None (isolates the effect of plasticity during
  reversal; L0 cue-alone = 0 by construction - degenerate null).
- Seeds: training 85000 + bi*100 + t (max 86124); probes 120000 +
  bi*2000 + pt*10 + ty*2 + rep (max within registered 142047;
  verified disjoint - separate ranges from R1's 80000/90000).
- Per-simulation weight checkpoints; probe purity test-verified;
  guard live; per-record JSONL appends.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1DIR = Path("results/phase2/taskB_r1")
OUTDIR = Path("results/phase2/taskB_r2")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
N_REV = 25
PROBE_AT = (1, 2, 3, 5, 10, 15)          # pt 0-5
FINAL_PT = 6                              # probe set after trial 25
CUES = {
    "GNG521": [15957, 16327],
    "GNG380": [50843, 53901, 103327, 129624, 556072, 559464],
}
R2_COND = {
    "gng521_rev": {"r1_cond": "gng521_feed", "cue": "GNG521", "direction": "withhold",
                   "bi": 0},
    "gng380_rev": {"r1_cond": "gng380_withhold", "cue": "GNG380", "direction": "feed",
                   "bi": 6},
}


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def load_world():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    return matrix, nodes, sugar, bitter


def out_path(cond, k, mode):
    p = OUTDIR / f"{mode}_{cond}_blk{k}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def find_rec(pp, cue, trial, ptype, rep=None):
    if not pp.exists():
        return None
    for line in pp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("cue") == cue and r.get("trial") == trial and r.get("ptype") == ptype:
            if rep is None or r.get("rep") == rep:
                return r
    return None


def write_rec(pp, rec):
    with pp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def r1_retained(cdef, k):
    """True iff the R1 block retained: FINAL-point probes (t=25 - the
    last point that actually fired in R1's as-run 30-trial schedule;
    0/5/10 are acquisition-phase, 15/20/25 retention-phase) on the
    learned side of theta for BOTH reps. Pre-launch audit 2026-10-08:
    was reading trial==10 (acquisition-phase point - wrong). Cue
    filter was already fixed 2026-10-03 (see inline note)."""
    f = R1DIR / f"l1_{cdef['r1_cond']}_blk{k}.jsonl"
    if not f.exists():
        return False, []
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    ptype = "alone" if cdef["r1_cond"] == "gng521_feed" else "cosugar"
    # FILTER BY THE TRAINED CUE: the probe set records BOTH cues at every
    # point (cross-direction leakage by design); mixing the untrained
    # cue's values (0 by construction) into the criterion made every
    # block read FAIL. Bug caught 2026-10-03 before any R2 data ran.
    vals = [r["readout_hz"] for r in rows
            if r["trial"] == 25 and r["ptype"] == ptype and r["cue"] == cdef["cue"]]
    if not vals:
        return False, []
    if ptype == "alone":
        return all(v >= THETA for v in vals), vals
    return all(v < THETA for v in vals), vals


def run_block(matrix, nodes, sugar, bitter, cond, cdef, k, mode):
    pp = out_path(cond, k, mode)
    bi = cdef["bi"] + k
    r1ckpt = R1DIR / f"ckpt_l1_{cdef['r1_cond']}_{k}"
    ckpt = OUTDIR / f"ckpt_{mode}_{cond}_{k}"
    cue = cdef["cue"]
    drive = sugar if cdef["direction"] == "feed" else bitter
    plasticity = (HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
                  if mode == "l1" else None)
    if (ckpt / "run_state.json").exists():
        run = TrainingRun.load(ckpt, matrix, nodes, plasticity, guard(), MN9_L)
    else:
        # start from the R1 retained state (same input for L1 and L0-R)
        if r1ckpt.exists() and (r1ckpt / "run_state.json").exists():
            # RESTORE WITH PLASTICITY ACTIVE even for the L0 arm: load()
            # skips weight restoration when plasticity is None (silent
            # pristine-matrix trap), so the retained matrix is restored
            # under the L1 rule and then handed to the L0 runner.
            restore_rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG,
                                                        w_max=W_MAX))
            r1run = TrainingRun.load(r1ckpt, matrix, nodes, restore_rule, guard(), MN9_L)
            start_matrix = r1run.matrix
        else:
            print(f"[{mode} {cond} blk{k}] R1 checkpoint missing - N/A", flush=True)
            return
        run = TrainingRun(start_matrix, nodes, plasticity, guard(), MN9_L,
                          f"r2_{mode}_{cond}_{k}", ckpt,
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    for t in range(N_REV):
        if find_rec(pp, cue, t, "train") is None:
            s = TrialSpec(trial=t, seed=85_000 + bi * 100 + t, cue_body_ids=tuple(CUES[cue]),
                          drive_body_ids=tuple(drive), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            write_rec(pp, {"cue": cue, "trial": t, "ptype": "train", "direction": cdef["direction"],
                           "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                           "n_spiking": rec["n_spiking"], "weight_diff": rec.get("weight_diff"),
                           "guard_fired": rec.get("guard_fired")})
            run.save()
        if (t + 1) in PROBE_AT:
            pt = PROBE_AT.index(t + 1)
            probe_point(pp, run, bi, pt, t, sugar)
    # FINAL probe set after trial 25 (the masking-test points)
    probe_point(pp, run, bi, FINAL_PT, N_REV - 1, sugar)
    print(f"[{mode} {cond} blk{k}] done", flush=True)


def probe_point(pp, run, bi, pt, trial, sugar):
    for ty, (pcue, ptype) in enumerate([("GNG521", "alone"), ("GNG521", "cosugar"),
                                        ("GNG380", "alone"), ("GNG380", "cosugar")]):
        for rep in range(2):
            if find_rec(pp, pcue, trial, ptype, rep) is None:
                cos = ptype == "cosugar"
                ps = TrialSpec(trial=trial, seed=120_000 + bi * 2000 + pt * 10 + ty * 2 + rep,
                               cue_body_ids=tuple(CUES[pcue]),
                               drive_body_ids=tuple(sugar) if cos else (),
                               drive2_body_ids=(), r_cue_hz=200.0,
                               r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                               is_probe=True)
                prec = run.run_trial(ps)
                write_rec(pp, {"cue": pcue, "trial": trial, "ptype": ptype, "rep": rep,
                               "pt": pt, "readout_hz": prec["readout_hz"],
                               "total_spikes": prec["total_spikes"],
                               "guard_fired": prec.get("guard_fired")})
                run.save()


def main() -> int:
    matrix, nodes, sugar, bitter = load_world()
    for cond, cdef in R2_COND.items():
        for k in range(6):
            ok, vals = r1_retained(cdef, k)
            if not ok:
                na = OUTDIR / f"R2_NA_{cond}_blk{k}.json"
                na.parent.mkdir(parents=True, exist_ok=True)
                na.write_text(json.dumps({
                    "reason": "R1 retention gate FAIL - retained state not established",
                    "r1_cond": cdef["r1_cond"], "final_point_vals": vals,
                    "note": "N/A-with-reason (standing convention)"}), encoding="utf-8")
                print(f"[{cond} blk{k}] R1 retention FAIL - R2 N/A-with-reason", flush=True)
                continue
            for mode in ("l1", "l0"):
                run_block(matrix, nodes, sugar, bitter, cond, cdef, k, mode)
    print("\nR2 complete. Criteria + masking-test classification in the report.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
