"""Pre-registered acquisition-comparability analysis (registry 2026-09-25,
design fixed BEFORE GNG380/GNG557 acquisition data existed; run at
pair v4 = GNG521 + GNG380, shared eta* = 1e-4, frozen 1-hop L1).

Fresh seed blocks: GNG521 34000/34100/34200... — RESERVED blocks were
34000-34500 for the earlier plan; those were consumed by the batch
probe (34000-34009) — WAIT: batch used 34000-34009 for PROBES (no
plasticity), distinct trial streams. To avoid any collision the
comparability run uses blocks 35000/35100/35200 (GNG521) and
35300/35400/35500 (GNG380), probes at base+500. Registered amendment:
seed blocks changed from the pre-registration to avoid overlap with
the batch-probe seed block; the design (3 blocks x 20 trials,
probes at 5/10/15/20, shared eta*) is unchanged.

Metrics (registered): (i) per-cue eta* [known: both 1e-4]; (ii)
trial-to-first-expression (probe > 0); (iii) plateau (mean trial-20
probe); (iv) across-block spread of (ii)/(iii). Asymmetry = recorded
cue-identity covariate for ALL WP4 interpretation; NOT a freeze gate.
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
ETA = 1e-4
CUES = {
    "GNG521": {"ids": [15957, 16327], "blocks": (35_000, 35_100, 35_200)},
    "GNG380": {"ids": [50843, 53901, 103327, 129624, 556072, 559464],
               "blocks": (35_300, 35_400, 35_500)},
}


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "comparability_curves.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    def key_exists(cue, blk, trial, probe):
        if not out.exists():
            return None
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("cue") == cue and r.get("block") == blk and r.get("trial") == trial
                    and bool(r.get("probe")) == probe):
                return r
        return None

    for cue, spec_c in CUES.items():
        ids = spec_c["ids"]
        for bi, base in enumerate(spec_c["blocks"]):
            cfg = PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix0, nodes, HebbianRule(cfg), guard(), MN9_L,
                              f"cmp_{cue}_{bi}", OUTDIR / f"ckpt_cmp_{cue}_{bi}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            for t in range(20):
                prev = key_exists(cue, bi, t, False)
                if prev is None:
                    s = TrialSpec(trial=t, seed=base + t, cue_body_ids=tuple(ids),
                                  drive_body_ids=tuple(sugar), drive2_body_ids=(),
                                  r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                    rec = run.run_trial(s)
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"cue": cue, "block": bi, "trial": t, "probe": False,
                                             "readout_hz": rec["readout_hz"],
                                             "guard": rec.get("guard_fired")}) + "\n")
                        fh.flush()
                if (t + 1) in (5, 10, 15, 20):
                    prev = key_exists(cue, bi, t, True)
                    if prev is None:
                        ps = TrialSpec(trial=t, seed=base + 500, cue_body_ids=tuple(ids),
                                       drive_body_ids=(), drive2_body_ids=(),
                                       r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                        prec = run.run_trial(ps)
                        with out.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"cue": cue, "block": bi, "trial": t, "probe": True,
                                                 "readout_hz": prec["readout_hz"],
                                                 "guard": prec.get("guard_fired")}) + "\n")
                            fh.flush()
                    else:
                        pass
            print(f"[{cue} blk{bi}] done", flush=True)

    # aggregate
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== comparability metrics (shared eta*=1e-4) ==", flush=True)
    summary = {}
    for cue in CUES:
        firsts, plateaus = [], []
        for bi in range(3):
            probes = [(r["trial"] + 1, r["readout_hz"]) for r in rows
                      if r["cue"] == cue and r["block"] == bi and r.get("probe")]
            first = next((t for t, h in probes if h > 0), None)
            firsts.append(first)
            plateaus.append(probes[-1][1] if probes else None)
        summary[cue] = {"trial_to_first_expression": firsts,
                        "plateau_trial20": plateaus,
                        "spread_first": max(x for x in firsts if x) - min(x for x in firsts if x) if all(firsts) else None,
                        "spread_plateau": (max(plateaus) - min(plateaus)) if all(plateaus) else None}
        print(f"  {cue}: first-expression at trials {firsts}; "
              f"plateau {plateaus} (spread {summary[cue]['spread_plateau']})", flush=True)
    (OUTDIR / "comparability_summary.json").write_text(json.dumps(summary, indent=2),
                                                       encoding="utf-8")
    print("\nwrote comparability_summary.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
