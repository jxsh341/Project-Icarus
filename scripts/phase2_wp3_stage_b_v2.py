"""WP3 Stage B v2: corrected eta range-finder, both cues, accumulation fixed.

The bugged v1 constructed TrainingRun inside the trial loop (updates
never accumulated; probe read 0 at all eta; fallback selected 1e-3).
v2 hoists the run outside the loop - identical to Stage C's correct
structure - and probes after 10 ACCUMULATED training trials.

Registered design (registry, before this launch):
  cues: GNG521 (seeds 31300-31309) AND PRW043 (seeds 31400-31409)
  eta grid: {1e-5, 1e-4, 1e-3, 1e-2}
  probes: cue-alone, seed 31350 / 31450, after trial 10
  per-cue eta* = smallest eta with probe expression (readout > 0) and
  no guard fire; else largest eta with no guard fire; all guard ->
  halt. Save the accumulated matrix after each arm.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUTDIR = Path("results/phase2/wp3_pilot")
MN9_L = 10331
W_MAX = 766.0
CUES = {
    "GNG521": {"seeds": (31_300, 31_350), "ids": [15957, 16327]},
    "PRW043": {"seeds": (31_400, 31_450), "ids": [25250, 26891, 37670, 39767, 69045]},
}
ETA_GRID = [1e-5, 1e-4, 1e-3, 1e-2]


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "stage_b_eta_v2.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    eta_star = {}
    for cue, spec_c in CUES.items():
        ids = spec_c["ids"]
        base_seed, probe_seed = spec_c["seeds"]
        for eta in ETA_GRID:
            # resume support: skip completed (cue, eta) arms
            rows = []
            if out.exists():
                rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
            if any(r.get("cue") == cue and r.get("eta") == eta for r in rows):
                continue
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix0, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"b2_{cue}_{eta}", OUTDIR / f"ckpt_b2_{cue}_{eta}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            fired = None
            for t in range(10):
                s = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(ids),
                              drive_body_ids=tuple(sugar), drive2_body_ids=(),
                              r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(s)
                if rec.get("guard_fired"):
                    fired = rec["guard_fired"]
                    break
            if not fired:
                ps = TrialSpec(trial=10, seed=probe_seed, cue_body_ids=tuple(ids),
                               drive_body_ids=(), drive2_body_ids=(),
                               r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                               is_probe=True)
                prec = run.run_trial(ps)
                probe_hz = prec["readout_hz"]
                sparse.save_npz(OUTDIR / f"weights_b2_{cue}_{eta}.npz", run.matrix)
            else:
                probe_hz = None
            rec_out = {"cue": cue, "eta": eta, "guard": fired, "probe_hz": probe_hz}
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec_out) + "\n")
                fh.flush()
            print(f"[{cue}] eta={eta}: guard={'FIRED' if fired else 'ok'} "
                  f"probe_MN9_L={probe_hz}", flush=True)

    # aggregate + per-cue eta*
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== v2 verdict ==", flush=True)
    for cue in CUES:
        cue_rows = [r for r in rows if r["cue"] == cue]
        cue_rows.sort(key=lambda r: ETA_GRID.index(r["eta"]))
        star = None
        for r in cue_rows:
            if not r["guard"] and r["probe_hz"] is not None and r["probe_hz"] > 0:
                star = r["eta"]
                break
        if star is None:
            for r in reversed(cue_rows):
                if not r["guard"]:
                    star = r["eta"]
                    break
        eta_star[cue] = star
        for r in cue_rows:
            print(f"  {cue} eta={r['eta']}: guard={r['guard']} probe={r['probe_hz']}", flush=True)
        print(f"  -> {cue} eta* = {star}", flush=True)

    (OUTDIR / "stage_b_eta_v2_verdict.json").write_text(
        json.dumps(eta_star, indent=2), encoding="utf-8")
    if all(v is None for v in eta_star.values()):
        print("HALT: all arms fired the guard", flush=True)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
