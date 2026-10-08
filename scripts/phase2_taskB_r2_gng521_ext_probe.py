"""Task B mechanism probe 2: GNG521 extended-dose replay (review-directed 2026-10-08).

THE QUESTION: does GNG521-feed acquisition self-degrade past its
crossing point the same way GNG380's reversal did (coincidence
waste), or is its clean 6/6 pass qualitatively stable? If GNG521
also arcs rise->peak->regress, then ANY sufficiently strong
acquisition in this substrate self-degrades past its peak and
stop-at-crossing is a UNIVERSAL training requirement, not a
reversal-specific patch.

Method: continue GNG521-feed training from R1's retained state
(blk0; = end-of-acquisition, bit-identical) for 40 MORE trials
(total dose 55 - well past WP4's 20 and R1's 15), same stimulus
wiring (cue PRIMARY 200, sugar SECONDARY 200), fresh seeds
87000+t (verified disjoint: r2 train ended 86124). Per trial:
traced sim (pre-update) recording MN9 spikes, arrival clustering
at MN9 (count, median IV, frac IV<2ms over its presynaptic
partners), and rates of the top-8 leg-2 intermediates (targets of
GNG521 members with edges into MN9_L, ranked by cue->X weight);
then the identical training update via run.run_trial.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
OUT = Path("results/phase2/taskB_r2/gng521_extended_dose_probe.json")
MN9_L = 10331
W_MAX = 766.0
ETA = 1e-4
CUE = [15957, 16327]
N_EXT = 40
SEED_BASE = 87_000


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_MAG, w_max=W_MAX))
    guard = PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0, inh_weight_drift_frac=0.20))
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    retained = TrainingRun.load(R1CK, matrix, nodes, rule, guard, MN9_L)

    # leg-2 intermediates: targets of cue members that have an edge into MN9_L,
    # ranked by cue->X weight sum in the RETAINED matrix
    mn9_col = nid[MN9_L]
    into_mn9 = retained.matrix[:, mn9_col].tocoo()
    has_mn9_edge = set(into_mn9.row.tolist())
    cue_rows = np.array([nid[c] for c in CUE])
    cand = []
    for x in has_mn9_edge:
        w = float(retained.matrix[cue_rows, x].sum())
        if w > 0:
            cand.append((w, x))
    cand.sort(reverse=True)
    inter_idx = [x for _, x in cand[:8]]
    INTER = [nodes[x] for x in inter_idx]
    print(f"leg-2 intermediates (cue-weight ranked): {INTER}", flush=True)

    run = TrainingRun(retained.matrix, nodes, rule, guard, MN9_L,
                      "gng521_ext", Path("results/phase2/taskB_r2/ckpt_gng521_ext"),
                      lif_params=lif_params)

    records = []
    for t in range(N_EXT):
        seed = SEED_BASE + t
        s = TrialSpec(trial=t, seed=seed, cue_body_ids=tuple(CUE),
                      drive_body_ids=tuple(sugar), drive2_body_ids=(),
                      r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
        params = dataclasses.replace(lif_params, r_poisson_Hz=s.r_cue_hz)
        lif = simulate_lif(
            run.matrix, nodes, params, duration_ms=s.duration_ms,
            stimulated=list(s.cue_body_ids),
            stimulated2=list(s.drive_body_ids),
            r_poisson2_Hz=s.r_drive_hz,
            seed=s.seed,
        )
        rec = run.run_trial(s)
        run.save()

        mn9 = len(lif.spike_times.get(MN9_L, []))
        # arrivals at MN9 from its CURRENT presynaptic partners
        pre = run.matrix[:, mn9_col].tocoo()
        arrivals = []
        for r in set(pre.row.tolist()):
            arrivals.extend(lif.spike_times.get(nodes[r], []))
        arrivals = np.sort(np.array(arrivals))
        if len(arrivals) > 1:
            iv = np.diff(arrivals)
            med_iv = float(np.median(iv))
            frac2 = float((iv < 2.0).mean())
        else:
            med_iv, frac2 = -1.0, -1.0
        rates = {nodes[x]: len(lif.spike_times.get(nodes[x], [])) for x in inter_idx}
        w_in = {nodes[x]: round(float(run.matrix[cue_rows, x].sum()), 1) for x in inter_idx}
        records.append({
            "trial": t, "seed": seed, "readout_mn9_hz": rec["readout_hz"],
            "trace_mn9_hz": mn9, "arrivals": int(len(arrivals)),
            "median_iv_ms": med_iv, "frac_iv_lt_2ms": frac2,
            "intermediate_rates_hz": rates,
            "cue_weight_sum_into_intermediates": w_in,
            "n_spiking": rec["n_spiking"], "total_spikes": rec["total_spikes"],
            "guard_fired": rec.get("guard_fired"),
        })
        inter_s = " ".join(f"{k}:{v}" for k, v in rates.items())
        print(f"t={t:>2} MN9={mn9:>3} arr={len(arrivals):>4} medIV={med_iv:>5.2f} "
              f"f2={frac2:.3f} | {inter_s}", flush=True)

    OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")
    # quick arc summary
    m = [r["trace_mn9_hz"] for r in records]
    peak = max(m)
    pk_t = m.index(peak)
    print(f"\nMN9 arc: start={m[0]} peak={peak} @t{pk_t} end={m[-1]} "
          f"({'RISE-PEAK-REGRESS' if m[-1] < peak * 0.8 else 'no regression >=80% of peak held'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
