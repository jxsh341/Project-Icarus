"""FLY-LEARN-001 WP4: Task A acquisition, L0 vs L1 (v2: fixed harness).

Registry: 'WP4 pre-registration' + 'WP4 amendment (pre-launch)' +
'WP4 v2 relaunch' (seed scheme + weight checkpointing). Changes from
the discarded v0 run (wp4_discarded_v0):
  - weight state IS checkpointed now: run.save() after EVERY
    simulation (training + probe), TrainingRun.load() at block start
    with hash verification - a mid-block resume continues from the
    correct potentiated matrix instead of silently replaying from
    pristine weights (the v0 defect: save() never called, so resume
    would have stitched records from two weight trajectories);
  - new seed scheme: training seeds 40000 + bi*100 + t, probe seeds
    50000 + bi*1000 + t*10 + pi (bi = global block index 0-23) -
    verified disjoint from ALL prior stages and internally (the v0
    audit found 4 train-seed overlaps with onset probes and 16
    probe/train collisions).

Arms (D1 swap): arm-1 GNG521->feed / GNG380->withhold;
             arm-2 GNG521->withhold / GNG380->feed.
Schedule per run: 20 interleaved training trials (even idx: GNG521;
odd: GNG380) toward each cue's ASSIGNED direction:
  feed training   = cue + sugar co-presentation (cue PRIMARY @200,
                    sugar SECONDARY @200)
  withhold        = cue + bitter co-presentation (cue PRIMARY @200,
                    bitter SECONDARY @200)
Probes (is_probe) after trials 1,2,3,4,5,10,15,20; 4 per point:
  cue-A alone, cue-A cosugar, cue-B alone, cue-B cosugar.
PRIMARY criteria (symmetric, at theta=41.5):
  feed: assigned cue-alone probe >= 41.5 by trial 20
  withhold: assigned cue+cosugar probe < 41.5 by trial 20
L0 control: identical, plasticity=None.
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
             "blocks": (40_000, 40_100, 40_200, 40_600, 40_700, 40_800)},
    "arm2": {"assign": {"GNG521": "withhold", "GNG380": "feed"},
             "blocks": (40_300, 40_400, 40_500, 40_900, 41_000, 41_100)},
}
PROBE_AT = (1, 2, 3, 4, 5, 10, 15, 20)
# global block index: l1 arm1 0-5, l1 arm2 6-11, l0 arm1 12-17, l0 arm2 18-23
BLOCK_INDEX = {}
_bi = 0
for _mode in ("l1", "l0"):
    for _arm in ARMS:
        for _k in range(6):
            BLOCK_INDEX[(_mode, _arm, _k)] = _bi
            _bi += 1


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


def out_path(arm, blk_i, mode):
    p = OUTDIR / f"{mode}_{arm}_blk{blk_i}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def find_rec(pp, cue, trial, ptype):
    if not pp.exists():
        return None
    for line in pp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("cue") == cue and r.get("trial") == trial and r.get("ptype") == ptype:
            return r
    return None


def write_rec(pp, rec):
    with pp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def run_block(matrix, nodes, sugar, bitter, arm, armdef, blk_i, base_seed, mode):
    pp = out_path(arm, blk_i, mode)
    ckpt = OUTDIR / f"ckpt_{mode}_{arm}_{blk_i}"
    plasticity = (HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
                  if mode == "l1" else None)
    # resume: weight state restored from checkpoint when present
    if (ckpt / "run_state.json").exists():
        run = TrainingRun.load(ckpt, matrix, nodes, plasticity, guard(), MN9_L)
    else:
        run = TrainingRun(matrix, nodes, plasticity, guard(), MN9_L,
                          f"wp4_{mode}_{arm}_{blk_i}", ckpt,
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    bi = BLOCK_INDEX[(mode, arm, blk_i)]
    assign = armdef["assign"]
    for t in range(20):
        cue_name = "GNG521" if t % 2 == 0 else "GNG380"
        direction = assign[cue_name]
        drive = sugar if direction == "feed" else bitter
        if find_rec(pp, cue_name, t, "train") is None:
            s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(CUES[cue_name]),
                          drive_body_ids=tuple(drive), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            write_rec(pp, {"cue": cue_name, "trial": t, "ptype": "train",
                           "direction": direction, "readout_hz": rec["readout_hz"],
                           "total_spikes": rec["total_spikes"], "n_spiking": rec["n_spiking"],
                           "weight_diff": rec.get("weight_diff"),
                           "guard_fired": rec.get("guard_fired")})
            run.save()  # per-simulation weight checkpoint
        if (t + 1) in PROBE_AT:
            for pi, (pcue, ptype) in enumerate([("GNG521", "alone"), ("GNG521", "cosugar"),
                                                ("GNG380", "alone"), ("GNG380", "cosugar")]):
                if find_rec(pp, pcue, t, ptype) is None:
                    cos = ptype == "cosugar"
                    ps = TrialSpec(trial=t, seed=50_000 + bi * 1000 + t * 10 + pi,
                                   cue_body_ids=tuple(CUES[pcue]),
                                   drive_body_ids=tuple(sugar) if cos else (),
                                   drive2_body_ids=(), r_cue_hz=200.0,
                                   r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                                   is_probe=True)
                    prec = run.run_trial(ps)
                    write_rec(pp, {"cue": pcue, "trial": t, "ptype": ptype,
                                   "readout_hz": prec["readout_hz"],
                                   "total_spikes": prec["total_spikes"],
                                   "guard_fired": prec.get("guard_fired")})
                    run.save()
    print(f"[{mode} {arm} blk{blk_i}] done", flush=True)


def main() -> int:
    matrix, nodes, sugar, bitter = load_world()
    for mode in ("l1", "l0"):
        for arm, armdef in ARMS.items():
            for blk_i, base_seed in enumerate(armdef["blocks"]):
                run_block(matrix, nodes, sugar, bitter, arm, armdef, blk_i, base_seed, mode)
    print("\nWP4 v2 runs complete. Aggregate with wp4_report.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
