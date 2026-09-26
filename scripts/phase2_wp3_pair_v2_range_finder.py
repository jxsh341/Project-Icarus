"""Acquisition gate for the frozen pair v2: eta* range-finder for
GNG611 + GNG622 under the FROZEN 1-hop L1 window.

Registered (registry, before launch): grid {1e-5, 1e-4, 1e-3},
10 accumulated training trials + 1 cue-alone probe per (cue, eta);
GNG611 seeds 31700-31709/probe 31750; GNG622 seeds 31800-31809/
probe 31850. eta* per cue = smallest expressing eta (probe > 0)
without guard fire. The pair is USABLE IN WP3/WP4 ONLY IF BOTH cues
express (probe > 0) at some eta.
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
OUTDIR = Path("results/phase2/wp3_pilot")
MN9_L = 10331
W_MAX = 766.0
CUES = {
    "GNG611": {"ids": [25821, 29976], "base": 31_700, "probe": 31_750},
    "GNG622": {"ids": [29819, 32179, 112815, 248046011], "base": 31_800, "probe": 31_850},
}
ETAS = [1e-5, 1e-4, 1e-3]


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "stage_b_pair_v2.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    def done(cue, eta):
        if not out.exists():
            return False
        return any(json.loads(l).get("cue") == cue and json.loads(l).get("eta") == eta
                   for l in out.read_text(encoding="utf-8").splitlines() if l.strip())

    for cue, spec_c in CUES.items():
        ids = spec_c["ids"]
        for eta in ETAS:
            if done(cue, eta):
                continue
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix0, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"b3_{cue}_{eta}", OUTDIR / f"ckpt_b3_{cue}_{eta}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            fired = None
            for t in range(10):
                s = TrialSpec(trial=t, seed=spec_c["base"] + t, cue_body_ids=tuple(ids),
                              drive_body_ids=tuple(sugar), drive2_body_ids=(),
                              r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(s)
                if rec.get("guard_fired"):
                    fired = rec["guard_fired"]
                    break
            probe_hz = None
            if not fired:
                ps = TrialSpec(trial=10, seed=spec_c["probe"], cue_body_ids=tuple(ids),
                               drive_body_ids=(), drive2_body_ids=(),
                               r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                               is_probe=True)
                prec = run.run_trial(ps)
                probe_hz = prec["readout_hz"]
                sparse.save_npz(OUTDIR / f"weights_b3_{cue}_{eta}.npz", run.matrix)
            rec_out = {"cue": cue, "eta": eta, "guard": fired, "probe_hz": probe_hz}
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec_out) + "\n")
                fh.flush()
            print(f"[{cue}] eta={eta}: guard={'FIRED' if fired else 'ok'} probe={probe_hz}",
                  flush=True)

    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== acquisition gate verdict ==", flush=True)
    gate = {}
    for cue in CUES:
        cue_rows = sorted([r for r in rows if r["cue"] == cue],
                          key=lambda r: ETAS.index(r["eta"]))
        star = None
        for r in cue_rows:
            if not r["guard"] and r["probe_hz"] and r["probe_hz"] > 0:
                star = r["eta"]
                break
        gate[cue] = star
        for r in cue_rows:
            print(f"  {cue} eta={r['eta']}: probe={r['probe_hz']} guard={r['guard']}")
        print(f"  -> {cue} eta* = {star}", flush=True)
    (OUTDIR / "stage_b_pair_v2_verdict.json").write_text(json.dumps(gate, indent=2),
                                                         encoding="utf-8")
    ok = all(v is not None for v in gate.values())
    print(f"\nGATE: {'OPEN - pair v2 usable in WP3/WP4' if ok else 'CLOSED - pair v2 cannot learn under frozen L1'}",
          flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
