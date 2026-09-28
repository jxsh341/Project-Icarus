"""Fine-grained onset probe (registry 2026-09-27): trials 1-4 with a
cue-alone probe after EACH training trial, per (cue, block).

Resolves the trial-5 quantization caveat before the WP4 acquisition
protocol freezes. Probes are is_probe=True (no plasticity applied), so
training accumulation is clean. Frozen L1 (1-hop), shared eta*=1e-4,
cue PRIMARY, explicit 200 Hz. 3 blocks per cue.
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
    "GNG521": {"ids": [15957, 16327], "blocks": (36_000, 36_100, 36_200)},
    "GNG380": {"ids": [50843, 53901, 103327, 129624, 556072, 559464],
               "blocks": (36_300, 36_400, 36_500)},
}


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "onset_finegrained.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    def seen(cue, bi, trial, probe):
        if not out.exists():
            return None
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("cue") == cue and r.get("block") == bi and r.get("trial") == trial
                    and bool(r.get("probe")) == probe):
                return r
        return None

    for cue, spec_c in CUES.items():
        ids = spec_c["ids"]
        for bi, base in enumerate(spec_c["blocks"]):
            cfg = PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix0, nodes, HebbianRule(cfg), guard(), MN9_L,
                              f"onset_{cue}_{bi}", OUTDIR / f"ckpt_onset_{cue}_{bi}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            for t in range(4):
                if seen(cue, bi, t, False) is None:
                    s = TrialSpec(trial=t, seed=base + t, cue_body_ids=tuple(ids),
                                  drive_body_ids=tuple(sugar), drive2_body_ids=(),
                                  r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                    rec = run.run_trial(s)
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"cue": cue, "block": bi, "trial": t, "probe": False,
                                             "readout_hz": rec["readout_hz"],
                                             "guard": rec.get("guard_fired")}) + "\n")
                        fh.flush()
                # probe AFTER this trial's plasticity
                if seen(cue, bi, t, True) is None:
                    ps = TrialSpec(trial=t, seed=base + 501 + t, cue_body_ids=tuple(ids),
                                   drive_body_ids=(), drive2_body_ids=(),
                                   r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                                   is_probe=True)
                    prec = run.run_trial(ps)
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"cue": cue, "block": bi, "trial": t, "probe": True,
                                             "readout_hz": prec["readout_hz"],
                                             "guard": prec.get("guard_fired")}) + "\n")
                        fh.flush()
                    print(f"[{cue} blk{bi}] after trial {t+1}: probe MN9_L = {prec['readout_hz']} Hz",
                          flush=True)

    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== onset curves (probe Hz after each trial) ==", flush=True)
    summary = {}
    for cue in CUES:
        curves = []
        for bi in range(3):
            c = [r["readout_hz"] for r in rows
                 if r["cue"] == cue and r["block"] == bi and r.get("probe")]
            curves.append(c)
        summary[cue] = curves
        print(f"  {cue}: {curves}", flush=True)
    (OUTDIR / "onset_finegrained_summary.json").write_text(json.dumps(summary, indent=2),
                                                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
