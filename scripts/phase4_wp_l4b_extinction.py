"""WP-L4b: THE DECISIVE RUN - eligibility-then-sign extinction (Phase 4).

Protocol per cycle (cycle = one sugar phase + one bitter phase,
NEVER-SIMULTANEOUS structural: each trial has exactly ONE drive):
- SUGAR-PHASE trial: cue PRIMARY @200 + sugar @200. The full
  25-edge footprint co-fires (the 9 untouched partners are
  sugar-driven - the census); eligibility accumulates, sign NOT
  applied (inner.apply(weight, None) returns unchanged).
- BITTER-PHASE trial: cue PRIMARY @200 + bitter @200. The PPL trio
  fires (sanity-checked in L3d at 130+ Hz); bitter-reachable
  eligibility also accumulates; then apply with sign=-1 applies
  the negative delta to ALL live pending (both phases' worth).

From GNG521's ACQUIRED state (R1 ckpt, retained bit-identical).
25 cycles, probes at cycles 5/10/15/20/25 (cue-alone + cosugar,
2 reps, traced sims). 3 seed reps.

Split criteria (pre-registered):
- PASS: cue-alone < theta=41.5 by cycle 25 AND cosugar intact.
- NEGATIVE-A: real coverage fails - the 9 untouched edges show no
  weight change in the final-vs-initial diff (coincidence did not
  open for them under cue+sugar).
- NEGATIVE-B: unselective collapse (cosugar breaks / guard fires).

Coverage check built into the verdict: final-vs-initial matrix diff
intersected with the 9 untouched edge keys.

Seeds: train 160000+ (rep*1000 + phase + t), probes 162000+. Prior
max 158xxx - disjoint. Checkpoints per simulation (KNOWN LIMITATION
registered in-doc: the rule's pending eligibility lives in the rule
object, not the checkpoint; mid-cycle interruption loses the
current half-cycle's pending only - cycle-boundary state is safe).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import (HebbianRule, PlasticityConfig, PlasticityGuard,
                            Semantics, StabilityThresholds)
from fly.training import TrainingRun, TrialSpec

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase4_eligibility_sign_rule import EligibilitySignRule  # noqa: E402

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
OUT = Path("results/phase4/wp_l4b")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
CUE = [15957, 16327]
UNTOUCHED = [13510, 18474, 12364, 14803, 14953, 66802, 516493, 524078, 555850]
PPL_TRIO = [11618, 11900, 529516]
N_CYCLES = 25
PROBE_AT = (5, 10, 15, 20, 25)
REPS = 3
TRAIN_SEED_BASE = 160_000
PROBE_SEED_BASE = 162_000


class PhaseDriverRule:
    """Adapter: TrainingRun calls apply(weight); this delegates to
    inner.apply(weight, sign) with the driver-set phase sign.
    sign=None during sugar phase (accumulate only); -1 at bitter
    phase apply. Coincidence logic stays in TrainingRun (single
    source of truth)."""

    def __init__(self, inner: EligibilitySignRule):
        self.inner = inner
        self.sign = None  # driver sets per phase

    @property
    def config(self):
        return self.inner.config

    def observe_rate_pair(self, pre, post, weight, x_hz, y_hz):
        self.inner.observe_rate_pair(pre, post, weight, x_hz=x_hz, y_hz=y_hz)

    def apply(self, weight):
        return self.inner.apply(weight, sign=self.sign)


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def phase_spec(t, seed, drive_ids):
    """One drive per trial - NEVER-SIMULTANEOUS structural. Cue always
    present (the conditioned stimulus)."""
    if not drive_ids:
        raise RuntimeError("phase trial requires exactly one drive")
    return TrialSpec(trial=t, seed=seed, cue_body_ids=tuple(CUE),
                     drive_body_ids=tuple(drive_ids), drive2_body_ids=(),
                     r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "l4b_extinction.jsonl"

    # ---- LAUNCH SANITY: do the 9 untouched partners fire under cue+sugar
    # from the ACQUIRED state? (the coverage precondition - logged, not verdict)
    base_rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
    retained = TrainingRun.load(R1CK, matrix, nodes, base_rule, guard(), MN9_L)
    chk = simulate_lif(retained.matrix, nodes, lif_params, 1000.0,
                       stimulated=list(CUE), stimulated2=list(sugar),
                       r_poisson2_Hz=200.0, seed=PROBE_SEED_BASE + 999)
    partners_firing = {str(p): len(chk.spike_times.get(p, [])) for p in UNTOUCHED}
    n_firing = sum(1 for v in partners_firing.values() if v > 0)
    print(f"LAUNCH SANITY: untouched partners firing under cue+sugar "
          f"(acquired state): {n_firing}/9 -> {partners_firing}", flush=True)
    if n_firing == 0:
        print("SANITY FAIL: no untouched partner fires under cue+sugar - "
              "coverage cannot open; NEGATIVE-A guaranteed", flush=True)

    w_initial = retained.matrix.copy()

    for rep in range(REPS):
        inner = EligibilitySignRule(ETA, W_MAX)
        rule = PhaseDriverRule(inner)
        run = TrainingRun(retained.matrix.copy(), nodes, rule, guard(), MN9_L,
                          f"l4b_r{rep}", OUT / f"ckpt_r{rep}", lif_params=lif_params)
        for cyc in range(1, N_CYCLES + 1):
            # sugar phase: accumulate, no application
            rule.sign = None
            s_spec = phase_spec(cyc * 2, TRAIN_SEED_BASE + rep * 1000 + cyc * 2, sugar)
            rec_s = run.run_trial(s_spec)
            run.save()
            # bitter phase: accumulate bitter-reachable + APPLY negative
            rule.sign = -1
            b_spec = phase_spec(cyc * 2 + 1, TRAIN_SEED_BASE + rep * 1000 + cyc * 2 + 1, bitter)
            rec_b = run.run_trial(b_spec)
            run.save()
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"rep": rep, "cycle": cyc,
                                     "sugar_readout": rec_s["readout_hz"],
                                     "bitter_readout": rec_b["readout_hz"],
                                     "pending_after_sugar": inner.pending_count(),
                                     "guard_fired": rec_b.get("guard_fired")}) + "\n")
            if cyc in PROBE_AT:
                for ptype, off in (("alone", 0), ("cosugar", 5000)):
                    for r2 in range(2):
                        pseed = PROBE_SEED_BASE + rep * 10000 + cyc * 100 + r2 * 10 + off
                        lif = simulate_lif(
                            run.matrix, nodes, lif_params, 1000.0,
                            stimulated=list(CUE),
                            stimulated2=(list(sugar) if ptype == "cosugar" else None),
                            r_poisson2_Hz=(200.0 if ptype == "cosugar" else None),
                            seed=pseed)
                        mn9 = len(lif.spike_times.get(MN9_L, []))
                        with out.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"rep": rep, "cycle": cyc,
                                                 "ptype": ptype, "rep2": r2,
                                                 "mn9_hz": mn9}) + "\n")
        print(f"rep {rep} done", flush=True)

    # ---- VERDICT (split criteria) + coverage check ----
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== probe trajectories ==")
    for rep in range(REPS):
        for ptype in ("alone", "cosugar"):
            pts = []
            for cyc in PROBE_AT:
                vals = [r["mn9_hz"] for r in rows
                        if r["rep"] == rep and r["cycle"] == cyc and r["ptype"] == ptype]
                pts.append(f"c{cyc}:{vals[0]},{vals[1]}")
            print(f"  rep {rep} {ptype:>7}: {' '.join(pts)}")

    fires = [r for r in rows if r.get("guard_fired")]
    print(f"\nguard fires: {len(fires)}")

    # coverage: final matrix vs initial, on the 9 untouched edges
    for rep in range(REPS):
        run_chk = TrainingRun.load(OUT / f"ckpt_r{rep}", matrix, nodes,
                                   HebbianRule(PlasticityConfig(
                                       eta=ETA, w_max=W_MAX,
                                       semantics=Semantics.V_CLIP)),
                                   guard(), MN9_L)
        final = run_chk.matrix
        d = (final - w_initial).tocoo()
        changed = {(int(r), int(c)): float(v) for r, c, v in zip(d.row, d.col, d.data) if v != 0}
        untouched_keys = {(nid[c], nid[p]) for p in UNTOUCHED for c in CUE}
        hit = {k: v for k, v in changed.items() if k in untouched_keys}
        print(f"rep {rep}: weakened-edge union {len(changed)}; "
              f"untouched-partner edges changed: {len(hit)} of 9 -> "
              f"{[(nodes[k[0]], nodes[k[1]], round(v,1)) for k, v in hit.items()]}")

    # verdict
    print("\n== VERDICT (split criteria, pre-registered) ==")
    finals = [r["mn9_hz"] for r in rows if r["cycle"] == 25 and r["ptype"] == "alone"]
    cosg = [r["mn9_hz"] for r in rows if r["cycle"] == 25 and r["ptype"] == "cosugar"]
    below = [v < THETA for v in finals]
    intact = all(v >= 75 for v in cosg)
    print(f"  final cue-alone: {finals} -> below theta: {below}")
    print(f"  final cosugar: {cosg} -> intact: {intact}")
    if all(below) and intact:
        print("  PASS: association weakened through the substrate's own pathways")
    elif intact:
        print("  NEGATIVE-A or partial: coverage/rate question - see edges above")
    else:
        print("  NEGATIVE-B: unselective collapse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
