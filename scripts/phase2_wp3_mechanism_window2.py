"""WP3 mechanism experiment (fork option (a), decoupled per review).

Question: is the PRW043 null LOCATION, not magnitude? Causal test:
cue-gated leg-2 eligibility (window_hops=2), pre-registered
predictions P1/P2/P3 (registry). NOT an L1-definition change - the
frozen L1 window stays 1-hop for all downstream WPs.

Arms: both cues x eta {1e-4, 1e-2} x 10 accumulated training trials
+ 1 cue-alone probe. GNG521 seeds 31500-31509/probe 31550;
PRW043 seeds 31600-31609/probe 31650. Checkpointed per trial.
"""

from __future__ import annotations

import dataclasses
import json
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
ARMS = {
    "GNG521": {"ids": [15957, 16327], "base": 31_500, "probe": 31_550},
    "PRW043": {"ids": [25250, 26891, 37670, 39767, 69045], "base": 31_600, "probe": 31_650},
}
ETAS = [1e-4, 1e-2]


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    out = OUTDIR / "mechanism_window2.jsonl"
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    def already(cue, eta):
        if not out.exists():
            return False
        return any(json.loads(l).get("cue") == cue and json.loads(l).get("eta") == eta
                   and json.loads(l).get("done")
                   for l in out.read_text(encoding="utf-8").splitlines() if l.strip())

    for cue, spec_c in ARMS.items():
        ids = spec_c["ids"]
        for eta in ETAS:
            if already(cue, eta):
                continue
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix0, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"mx_{cue}_{eta}", OUTDIR / f"ckpt_mx_{cue}_{eta}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            fired = None
            for t in range(10):
                s = TrialSpec(trial=t, seed=spec_c["base"] + t, cue_body_ids=tuple(ids),
                              drive_body_ids=tuple(sugar), drive2_body_ids=(),
                              r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0,
                              window_hops=2)
                rec = run.run_trial(s)
                if rec.get("guard_fired"):
                    fired = rec["guard_fired"]
                    break
            probe_hz = None
            leg2_mass = None
            if not fired:
                ps = TrialSpec(trial=10, seed=spec_c["probe"], cue_body_ids=tuple(ids),
                               drive_body_ids=(), drive2_body_ids=(),
                               r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                               window_hops=2, is_probe=True)
                prec = run.run_trial(ps)
                probe_hz = prec["readout_hz"]
                # leg-2 potentiated mass: edges (m->n), m a cue 1-hop target
                d = (run.matrix - matrix0).tocoo()
                idx_of = {n: i for i, n in enumerate(node_ids)}
                cue_rows = {idx_of[b] for b in ids if b in idx_of}
                leg1 = set()
                for ci in cue_rows:
                    leg1.update(run.matrix.getrow(ci).indices.tolist())
                mass = 0.0
                for r_, c_, w_ in zip(d.row, d.col, d.data):
                    if r_ in leg1 and c_ not in cue_rows:
                        mass += w_
                leg2_mass = round(float(mass), 1)
                sparse.save_npz(OUTDIR / f"weights_mx_{cue}_{eta}.npz", run.matrix)
            rec_out = {"cue": cue, "eta": eta, "guard": fired, "probe_hz": probe_hz,
                       "leg2_potentiated_mass": leg2_mass, "done": True}
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec_out) + "\n")
                fh.flush()
            print(f"[{cue}] eta={eta} window=2: guard={'FIRED: ' + fired if fired else 'ok'} "
                  f"probe={probe_hz} leg2_mass={leg2_mass}", flush=True)

    print("\n== registered predictions check ==", flush=True)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        print(f"  {r['cue']} eta={r['eta']}: probe={r['probe_hz']} leg2={r['leg2_potentiated_mass']} guard={r['guard']}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
