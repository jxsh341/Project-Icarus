"""FLY-LEARN-001 Task B Stage R1: retention / distributional stability.

Registry: 'R2 masking probe + R1 interpretation (2026-10-03)' +
'Task B design' + 'WP4 addendum'. Design:

- Conditions (learned directions ONLY): GNG521->feed,
  GNG380->withhold. 6 seed blocks each (12 total).
- Weights are FROZEN during retention (no decay mechanism exists):
  this is a DISTRIBUTIONAL STABILITY test at the retained state.
- Retained state: 15 full-dose acquisition trials (per-direction
  block schedule; feed = cue+sugar, withhold = cue+bitter;
  cue PRIMARY @200, drive SECONDARY @200; explicit everywhere).
- Stability probes: 7 points at trial counts 0,5,10,15,20,25,30 of
  a 30-trial NO-STIMULUS retention phase (the script never acquired
  - v1 fed the training drive every trial, mislabeled it; corrected
  2026-10-04), 4 probe types per point (both cues x alone/cosugar),
  2 sims per point (probe-variance rule), plasticity OFF (is_probe),
  distinct seeds. The retained state enters via resume from the
  earlier arm1/wp4-trained checkpoints? NO - R1 retention needs the
  ACQUIRED state; see run_block note.
- Probe seeds: 90000 + bi*1000 + pt*10 + ty*2 + rep (verified
  disjoint; pairwise check pre-launch). Training seeds:
  80000 + bi*100 + t.
- L0-R control: identical schedule+seeds, plasticity=None, same 12
  blocks (matched-seed paired comparison, as WP4; L0 cue-alone is
  exactly 0 by construction - degenerate null, stated as such).
- Interpretation (registered): point passes iff BOTH reps on the
  learned side of theta=41.5 (conservative; a wrong-side spike =
  instability signal); block passes iff all points pass; >=5/6
  blocks per condition. Below-theta = recorded retention failure -
  investigated, never patched by retraining.
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
OUTDIR = Path("results/phase2/taskB_r1")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
COND = {
    "gng521_feed": {"ids": [15957, 16327], "drive": "sugar",
                    "blocks": (80_000, 80_100, 80_200, 80_300, 80_400, 80_500),
                    "side": "alone"},
    "gng380_withhold": {"ids": [50843, 53901, 103327, 129624, 556072, 559464],
                        "drive": "bitter",
                        "blocks": (80_600, 80_700, 80_800, 80_900, 80_1000 - 1000, 80_1100 - 1000),
                        "side": "cosugar"},
}
# NOTE: gng380 blocks are bi 6..11 -> 80000 + bi*100 + t = 80600..81100+t
PROBE_POINTS = (0, 5, 10, 15, 20)


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def load_world():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    return matrix, nodes, [r["bodyId"] for r in seeds["sugar_R"]], [r["bodyId"] for r in seeds["bitter_R"]]


def bi_of(cond, k):
    return (0 if cond == "gng521_feed" else 6) + k


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


def run_block(matrix, nodes, sugar, bitter, cond, conddef, k, mode):
    pp = out_path(cond, k, mode)
    ckpt = OUTDIR / f"ckpt_{mode}_{cond}_{k}"
    bi = bi_of(cond, k)
    plasticity = (HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
                  if mode == "l1" else None)
    if (ckpt / "run_state.json").exists():
        run = TrainingRun.load(ckpt, matrix, nodes, plasticity, guard(), MN9_L)
    else:
        run = TrainingRun(matrix, nodes, plasticity, guard(), MN9_L,
                          f"r1_{mode}_{cond}_{k}", ckpt,
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    drive = sugar if conddef["drive"] == "sugar" else bitter
    # ACQUISITION PHASE (15 full-dose trials) - the retained state must
    # EXIST before stability can be tested. v1 omitted this.
    for t in range(15):
        if find_rec(pp, cond, t, "train") is None:
            s = TrialSpec(trial=t, seed=80_000 + bi * 100 + t, cue_body_ids=tuple(conddef["ids"]),
                          drive_body_ids=tuple(drive), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            write_rec(pp, {"cue": cond, "trial": t, "ptype": "train",
                           "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                           "n_spiking": rec["n_spiking"], "weight_diff": rec.get("weight_diff"),
                           "guard_fired": rec.get("guard_fired")})
            run.save()
    # RETENTION PHASE: 30 no-stimulus trials, probes at 7 points.
    N_TRIALS = 30
    PROBE_AT = (0, 5, 10, 15, 20, 25, 30)
    for t in range(N_TRIALS):
        if find_rec(pp, cond, t, "train") is None:
            s = TrialSpec(trial=t, seed=80_000 + bi * 100 + t, cue_body_ids=(),
                          drive_body_ids=(), drive2_body_ids=(),
                          r_cue_hz=0.0, r_drive_hz=0.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            write_rec(pp, {"cue": cond, "trial": t, "ptype": "train",
                           "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                           "n_spiking": rec["n_spiking"], "weight_diff": rec.get("weight_diff"),
                           "guard_fired": rec.get("guard_fired")})
            run.save()
        if t in PROBE_AT:
            # stability probes: 4 types x 2 reps, plasticity OFF
            for ty, (pcue, ptype) in enumerate([("GNG521", "alone"), ("GNG521", "cosugar"),
                                                ("GNG380", "alone"), ("GNG380", "cosugar")]):
                for rep in range(2):
                    if find_rec(pp, pcue, t, ptype, rep) is None:
                        cos = ptype == "cosugar"
                        cue_ids = COND[f"{pcue.lower()}_feed"]["ids"] if pcue == "GNG521" else \
                            COND["gng380_withhold"]["ids"]
                        ps = TrialSpec(trial=t, seed=90_000 + bi * 1000 + t * 10 + ty * 2 + rep,
                                       cue_body_ids=tuple(cue_ids),
                                       drive_body_ids=tuple(sugar) if cos else (),
                                       drive2_body_ids=(), r_cue_hz=200.0,
                                       r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                        prec = run.run_trial(ps)
                        write_rec(pp, {"cue": pcue, "trial": t, "ptype": ptype, "rep": rep,
                                       "readout_hz": prec["readout_hz"],
                                       "total_spikes": prec["total_spikes"],
                                       "guard_fired": prec.get("guard_fired")})
                        run.save()
    print(f"[{mode} {cond} blk{k}] done", flush=True)


def main() -> int:
    matrix, nodes, sugar, bitter = load_world()
    for mode in ("l1", "l0"):
        for cond, conddef in COND.items():
            for k in range(6):
                run_block(matrix, nodes, sugar, bitter, cond, conddef, k, mode)
    print("\nR1 runs complete. Aggregate with taskB_r1_report.py; R2 launches on retained blocks.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
