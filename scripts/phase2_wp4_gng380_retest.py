"""FLY-LEARN-001: GNG380-feed re-test (registry 2026-10-01).

Resolves the reviewer's arm2-vs-pilot discrepancy: was arm2's
GNG380-feed failure (3-9 Hz at trial 20) pure trial BUDGET (the
interleaved schedule delivers only 10 feed trials by the probe
point; the pilot's ramp crosses theta between feed-trials 15-20),
or does the interleaved bitter-alternating context SUPPRESS
GNG380's excitatory path (reviewer option 2)?

Arm A (budget): 20 consecutive GNG380-feed trials x 3 seeds.
Arm B (interleave): 40 interleaved trials (GNG380-feed odd,
GNG521-withhold even) x 3 seeds - 20 feed trials, alternating.
Probes (no plasticity): alone + cosugar after feed-trials
5/10/15/20 in both arms. Frozen L1, eta*=1e-4, guard live,
per-simulation checkpoints, explicit 200 Hz.
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
OUTDIR = Path("results/phase2/wp4_retest")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
GNG380 = [50843, 53901, 103327, 129624, 556072, 559464]
GNG521 = [15957, 16327]
PROBE_AT = (5, 10, 15, 20)


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


def write_rec(pp, rec):
    pp.parent.mkdir(parents=True, exist_ok=True)
    with pp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def find_rec(pp, trial, ptype):
    if not pp.exists():
        return None
    for line in pp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("trial") == trial and r.get("ptype") == ptype:
            return r
    return None


def run_block(matrix, nodes, sugar, bitter, arm, blk_i, base_seed):
    pp = OUTDIR / f"{arm}_blk{blk_i}.jsonl"
    ckpt = OUTDIR / f"ckpt_{arm}_{blk_i}"
    plasticity = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
    if (ckpt / "run_state.json").exists():
        run = TrainingRun.load(ckpt, matrix, nodes, plasticity, guard(), MN9_L)
    else:
        run = TrainingRun(matrix, nodes, plasticity, guard(), MN9_L,
                          f"retest_{arm}_{blk_i}", ckpt,
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
    if arm == "A":  # 20 consecutive GNG380-feed trials
        feed_count = 0
        for t in range(20):
            if find_rec(pp, t, "train") is None:
                s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(GNG380),
                              drive_body_ids=tuple(sugar), drive2_body_ids=(),
                              r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(s)
                feed_count += 1
                write_rec(pp, {"trial": t, "ptype": "train", "n_feed": feed_count,
                               "readout_hz": rec["readout_hz"],
                               "total_spikes": rec["total_spikes"],
                               "weight_diff": rec.get("weight_diff"),
                               "guard_fired": rec.get("guard_fired")})
                run.save()
            else:
                feed_count += 1
            if feed_count in PROBE_AT:
                for ptype in ("alone", "cosugar"):
                    if find_rec(pp, t, ptype) is None:
                        cos = ptype == "cosugar"
                        ps = TrialSpec(trial=t, seed=80_000 + blk_i * 1000 + t * 10 + (0 if cos else 1),
                                       cue_body_ids=tuple(GNG380),
                                       drive_body_ids=tuple(sugar) if cos else (),
                                       drive2_body_ids=(), r_cue_hz=200.0,
                                       r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                        prec = run.run_trial(ps)
                        write_rec(pp, {"trial": t, "ptype": ptype, "n_feed": feed_count,
                                       "readout_hz": prec["readout_hz"],
                                       "guard_fired": prec.get("guard_fired")})
                        run.save()
    else:  # arm B: 40 interleaved trials, GNG380-feed on odd indices
        feed_count = 0
        for t in range(40):
            if find_rec(pp, t, "train") is None:
                if t % 2 == 1:  # GNG380 feed
                    s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(GNG380),
                                  drive_body_ids=tuple(sugar), drive2_body_ids=(),
                                  r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                else:  # GNG521 withhold
                    s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(GNG521),
                                  drive_body_ids=tuple(bitter), drive2_body_ids=(),
                                  r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(s)
                if t % 2 == 1:
                    feed_count += 1
                write_rec(pp, {"trial": t, "ptype": "train", "n_feed": feed_count,
                               "readout_hz": rec["readout_hz"],
                               "total_spikes": rec["total_spikes"],
                               "weight_diff": rec.get("weight_diff"),
                               "guard_fired": rec.get("guard_fired")})
                run.save()
            elif t % 2 == 1:
                feed_count += 1
            if t % 2 == 1 and feed_count in PROBE_AT:
                for ptype in ("alone", "cosugar"):
                    if find_rec(pp, t, ptype) is None:
                        cos = ptype == "cosugar"
                        ps = TrialSpec(trial=t, seed=81_000 + blk_i * 1000 + t * 10 + (0 if cos else 1),
                                       cue_body_ids=tuple(GNG380),
                                       drive_body_ids=tuple(sugar) if cos else (),
                                       drive2_body_ids=(), r_cue_hz=200.0,
                                       r_drive_hz=200.0 if cos else 0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                        prec = run.run_trial(ps)
                        write_rec(pp, {"trial": t, "ptype": ptype, "n_feed": feed_count,
                                       "readout_hz": prec["readout_hz"],
                                       "guard_fired": prec.get("guard_fired")})
                        run.save()
    print(f"[{arm} blk{blk_i}] done", flush=True)


def main() -> int:
    matrix, nodes, sugar, bitter = load_world()
    for arm, bases in (("A", (42_000, 42_100, 42_200)), ("B", (42_300, 42_400, 42_500))):
        for blk_i, base_seed in enumerate(bases):
            run_block(matrix, nodes, sugar, bitter, arm, blk_i, base_seed)
    print("\nre-test complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
