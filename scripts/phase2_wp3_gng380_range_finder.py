"""GNG380 eta* range-finder under FROZEN 1-hop L1 (registry 2026-09-26).

Grid {1e-5, 1e-4, 1e-3}, 10 accumulated trials + probe per eta,
seeds 34100-34109, probe 34150. eta* = smallest expressing eta
without guard fire. Gate: probe > 0 at some eta -> pair v4
(GNG521+GNG380) advances to comparability curves.
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
ETAS = [1e-5, 1e-4, 1e-3]
GNG380 = None  # resolved at runtime


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "stage_b_gng380.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    meta = {}
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            meta[r["bodyId"]] = r
    ids = [b for b, r in meta.items() if r.get("type") == "GNG380" and b in idx]
    print(f"GNG380 members: {ids}", flush=True)

    for eta in ETAS:
        if out.exists():
            rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
            if any(r.get("eta") == eta for r in rows):
                continue
        cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
        run = TrainingRun(matrix0, nodes, HebbianRule(cfg), guard(), MN9_L,
                          f"b5_{eta}", OUTDIR / f"ckpt_b5_{eta}",
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
        fired = None
        for t in range(10):
            s = TrialSpec(trial=t, seed=34_100 + t, cue_body_ids=tuple(ids),
                          drive_body_ids=tuple(sugar), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            if rec.get("guard_fired"):
                fired = rec["guard_fired"]
                break
        probe_hz = None
        if not fired:
            ps = TrialSpec(trial=10, seed=34_150, cue_body_ids=tuple(ids),
                           drive_body_ids=(), drive2_body_ids=(),
                           r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0, is_probe=True)
            probe_hz = run.run_trial(ps)["readout_hz"]
            sparse.save_npz(OUTDIR / f"weights_b5_{eta}.npz", run.matrix)
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"eta": eta, "guard": fired, "probe_hz": probe_hz}) + "\n")
            fh.flush()
        print(f"eta={eta}: guard={'FIRED' if fired else 'ok'} probe={probe_hz}", flush=True)

    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    eta_star = None
    for r in rows:
        if not r["guard"] and r["probe_hz"] and r["probe_hz"] > 0 and eta_star is None:
            eta_star = r["eta"]
    (OUTDIR / "stage_b_gng380_verdict.json").write_text(
        json.dumps({"eta_star": eta_star, "rows": rows}, indent=2), encoding="utf-8")
    print(f"\neta* = {eta_star}; gate {'OPEN' if eta_star else 'CLOSED'}", flush=True)
    return 0 if eta_star else 1


if __name__ == "__main__":
    raise SystemExit(main())
