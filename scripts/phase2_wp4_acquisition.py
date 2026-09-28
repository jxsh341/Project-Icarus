"""FLY-LEARN-001 WP4: Task A acquisition, L0 vs L1 (pre-registered, amended).

Registry sections (2026-09-27): 'WP4 pre-registration' + 'WP4
amendment (pre-launch)'. Design:

Arms (D1 swap): arm-1 GNG521->feed / GNG380->withhold;
             arm-2 GNG521->withhold / GNG380->feed.
Seeds: 6 blocks per arm (arm-1 37000/37100/37200/37600/37700/37800;
       arm-2 37300/37400/37500/37900/38000/38100).
Schedule per run: 20 interleaved training trials (even idx: GNG521;
odd idx: GNG380), toward each cue's ASSIGNED direction:
  feed training   = cue + sugar co-presentation (cue PRIMARY @200,
                    sugar SECONDARY @200)
  withhold        = cue + bitter co-presentation (cue PRIMARY @200,
                    bitter SECONDARY @200)
Probes (is_probe) after trials 1,2,3,4,5,10,15,20; 4 per point:
  cue-A alone, cue-A cosugar, cue-B alone, cue-B cosugar
  (probe seeds base+1000+trial, distinct per probe type +offset).
L0 control: identical, plasticity=None, all 12 blocks.

PRIMARY criteria (symmetric, at theta=41.5):
  feed:    assigned cue-alone probe >= 41.5 by trial 20 (all runs)
  withhold: assigned cue+cosugar probe < 41.5 by trial 20 (all runs)
L0 must show cue-alone = 0 and cosugar >= 75 throughout.
Speed metric: trials-to-theta per cue, with across-seed spread.
Checkpointed per trial; guard live; explicit 200 Hz everywhere.
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
OUTDIR = Path("results/phase2/wp4")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
CUES = {
    "GNG521": [15957, 16327],
    "GNG380": [50843, 53901, 103327, 129624, 556072, 559464],
}
ARMS = {
    "arm1": {"assign": {"GNG521": "feed", "GNG380": "withhold"},
             "blocks": (37_000, 37_100, 37_200, 37_600, 37_700, 37_800)},
    "arm2": {"assign": {"GNG521": "withhold", "GNG380": "feed"},
             "blocks": (37_300, 37_400, 37_500, 37_900, 38_000, 38_100)},
}
PROBE_AT = (1, 2, 3, 4, 5, 10, 15, 20)


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


def out_path(arm, blk, mode):
    p = OUTDIR / f"{mode}_{arm}_blk{blk}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def seen(pp, cue, trial, ptype):
    if not pp.exists():
        return None
    for line in pp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("cue") == cue and r.get("trial") == trial and r.get("ptype") == ptype:
            return r
        if r.get("trial") == trial and r.get("ptype") == "train" and ptype == "train" and r.get("cue") == cue:
            return r
    return None


def run_block(matrix, nodes, sugar, bitter, arm, armdef, blk_i, base_seed, mode):
    pp = out_path(arm, blk_i, mode)
    plasticity = (HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
                  if mode == "l1" else None)
    run = TrainingRun(matrix, nodes, plasticity, guard(), MN9_L,
                      f"wp4_{mode}_{arm}_{blk_i}", OUTDIR / f"ckpt_{mode}_{arm}_{blk_i}",
                      lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    # order cue->direction from THIS arm's assignment
    assign = armdef["assign"]
    for t in range(20):
        cue_name = "GNG521" if t % 2 == 0 else "GNG380"
        direction = assign[cue_name]
        drive = sugar if direction == "feed" else bitter
        rec = seen(pp, cue_name, t, "train")
        if rec is None:
            s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(CUES[cue_name]),
                          drive_body_ids=tuple(drive), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            rec.update({"cue": cue_name, "ptype": "train", "direction": direction})
            with pp.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({k: rec.get(k) for k in
                                     ("cue", "trial", "ptype", "direction", "readout_hz",
                                      "total_spikes", "n_spiking", "weight_diff", "guard_fired")}) + "\n")
                fh.flush()
        else:
            # resume: replay trial index only; weight state comes from checkpoints
            pass
        if (t + 1) in PROBE_AT:
            for pi, (pcue, ptype) in enumerate([("GNG521", "alone"), ("GNG521", "cosugar"),
                                                ("GNG380", "alone"), ("GNG380", "cosugar")]):
                rec = seen(pp, pcue, t, ptype)
                if rec is None:
                    cos = ptype == "cosugar"
                    ps = TrialSpec(trial=t, seed=base_seed + 1000 + t * 10 + pi,
                                   cue_body_ids=tuple(CUES[pcue]),
                                   drive_body_ids=tuple(sugar) if cos else (),
                                   drive2_body_ids=(), r_cue_hz=200.0,
                                   r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                                   is_probe=True)
                    prec = run.run_trial(ps)
                    with pp.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"cue": pcue, "trial": t, "ptype": ptype,
                                             "readout_hz": prec["readout_hz"],
                                             "total_spikes": prec["total_spikes"],
                                             "guard_fired": prec.get("guard_fired")}) + "\n")
                        fh.flush()
    print(f"[{mode} {arm} blk{blk_i}] done", flush=True)


def main() -> int:
    matrix, nodes, sugar, bitter = load_world()
    for mode in ("l1", "l0"):
        for arm, armdef in ARMS.items():
            for blk_i, base_seed in enumerate(armdef["blocks"]):
                run_block(matrix, nodes, sugar, bitter, arm, armdef, blk_i, base_seed, mode)
    print("\nWP4 runs complete. Aggregate with wp4_report.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
