"""WP-L3d: THE WEAKENING TEST (decisive experiment, L3_DESIGN.md §5).

Tests the one mechanism Phase 2 proved frozen L1 lacks: can the
substrate's own aversive pathway WEAKEN an established association?

Design (all pre-registered, all measured facts):
- Start from GNG521's ACQUIRED feed state (R1 ckpt_l1_gng521_feed_0,
  the retained bit-identical end-of-acquisition state): cue-alone
  readout 76-89 Hz, cosugar 80+, well above theta.
- 25 EXTINCTION-STYLE reversal trials: cue + BITTER co-presentation
  (the withhold direction - the same protocol that under L1 produced
  NOTHING for GNG521's old feed pathway).
- The rule: three-factor, pathway-specific, V_CLIP weakening:
  * appetitive gate (OA-relay, sugar) is ABSENT in extinction trials
    -> positive-delta accumulation OFF;
  * aversive gate (PPL trio: 11618, 11900, 529516 - the neurons
    bitter actually fires, measured) is PRESENT -> negative-delta
    weakening ON, applied to cue-incident edges whose post fired;
  * delta magnitude: eta * x * y (the L1 contrast), NEGATIVE sign,
    V_CLIP-floored at zero (registered; sign never flips).
- NEVER-BOTH runtime assertion: this script drives sugar XOR bitter,
  never both (guard test scans the spec builder too).
- Probes (2 reps/point, plasticity+drives off except cue-alone
  readout): cue-ALONE response - the acquired association's
  footprint - at trials 5/10/15/20/25. Plus cosugar probes (the
  readout condition) at the same points.

Pre-registered SPLIT criteria (before data):
- PASS (weakening): cue-alone readout falls below theta=41.5 by
  trial 25 (the acquired association is genuinely weakened through
  the substrate's own aversive pathway).
- NEGATIVE-A (no weakening): cue-alone stays >= theta throughout -
  the aversive gate's negative delta does not weaken the
  association (frozen-L1's deficit extends to the gated form).
- NEGATIVE-B (collapse): cue-alone falls but cosugar collapses too /
  guard fires - the weakening is unselective (breaks the innate
  program), not an association-weakening result.
Intermediate/partial outcomes recorded as-is.

Seeds: train 156000+t, probes 158000+t (disjoint; prior max 154200).
Guard live. Checkpointed per simulation. Development-stage.
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
OUT = Path("results/phase3/wp_l3d")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
CUE = [15957, 16327]
PPL_TRIO = [11618, 11900, 529516]   # the measured aversive-gate population
N_TRIALS = 25
PROBE_AT = (5, 10, 15, 20, 25)
TRAIN_SEED_BASE = 156_000
PROBE_SEED_BASE = 158_000
REPS = 3   # seed blocks


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def build_spec(t, seed, bitter_ids, sugar_ids, assert_never_both=True):
    """Extinction trial: cue PRIMARY @200 + bitter as the drive.
    NEVER-BOTH runtime assertion: sugar is NEVER co-active."""
    if assert_never_both and bitter_ids and sugar_ids:
        raise RuntimeError("NEVER-BOTH violated: sugar and bitter in one trial")
    return TrialSpec(trial=t, seed=seed, cue_body_ids=tuple(CUE),
                     drive_body_ids=tuple(bitter_ids), drive2_body_ids=(),
                     r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)


class GatedVClipRule:
    """L3d rule: aversive-gated V_CLIP weakening.

    Eligibility: cue-incident edges whose post fired (the L1 window,
    observed via the base HebbianRule path). Delta sign: NEGATIVE
    (extinction/aversive), applied with V_CLIP floor-at-zero via a
    base rule configured with V_CLIP semantics. The gate is the
    measured PPL trio: its presence is per-trial binary (bitter
    drive in this protocol => trio fires => gate ON); implemented
    by only applying updates when the aversive condition holds.
    """

    def __init__(self, eta: float, w_max: float):
        self.base = HebbianRule(PlasticityConfig(
            eta=eta, semantics=Semantics.V_CLIP, w_max=w_max))
        self.gate_on = False  # set per trial by the driver

    @property
    def config(self):
        return self.base.config

    def _negate(self):
        """Flip accumulated pending deltas to negative (weakening)."""
        self.base._pending = {k: -v for k, v in self.base._pending.items()}

    def observe_rate_pair(self, pre, post, weight, x_hz, y_hz):
        if not self.gate_on:
            return  # aversive gate OFF: no eligibility accumulates
        self.base.observe_rate_pair(pre, post, weight, x_hz=x_hz, y_hz=y_hz)

    def apply(self, weight):
        if not self.gate_on:
            return weight
        self._negate()
        return self.base.apply(weight)


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "l3d_weakening.jsonl"

    # sanity: the PPL trio actually fires under bitter in this protocol context
    chk = simulate_lif(matrix, nodes, lif_params, 1000.0,
                       stimulated=bitter, seed=PROBE_SEED_BASE + 999)
    trio_rates = {str(g): len(chk.spike_times.get(g, [])) for g in PPL_TRIO}
    print(f"PPL trio rates under bitter (sanity): {trio_rates}", flush=True)
    if all(v == 0 for v in trio_rates.values()):
        print("SANITY FAIL: PPL trio silent under bitter - aversive gate never opens",
              flush=True)
        return 1

    for rep in range(REPS):
        rule = GatedVClipRule(ETA, W_MAX)
        retained = TrainingRun.load(R1CK, matrix, nodes, rule.base, guard(), MN9_L)
        run = TrainingRun(retained.matrix, nodes, rule, guard(), MN9_L,
                          f"l3d_r{rep}", OUT / f"ckpt_r{rep}", lif_params=lif_params)
        arcs = []
        for t in range(N_TRIALS):
            rule.gate_on = True  # extinction trials: bitter present -> trio fires
            spec = build_spec(t, TRAIN_SEED_BASE + rep * 100 + t, bitter, None)
            rec = run.run_trial(spec)
            run.save()
            arcs.append(rec["readout_hz"])
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"rep": rep, "trial": t, "ptype": "train",
                                     "readout_hz": rec["readout_hz"],
                                     "weight_diff": rec.get("weight_diff"),
                                     "guard_fired": rec.get("guard_fired")}) + "\n")
            if (t + 1) in PROBE_AT:
                rule.gate_on = False  # probes: no gate, no plasticity
                for ptype, pseed_off in (("alone", 0), ("cosugar", 5000)):
                    for r2 in range(2):
                        pseed = PROBE_SEED_BASE + rep * 10000 + t * 100 + r2 * 10 + pseed_off
                        # probes via traced sim: cue-alone or cue+cosugar
                        lif = simulate_lif(
                            run.matrix, nodes, lif_params, 1000.0,
                            stimulated=list(CUE),
                            stimulated2=(list(sugar) if ptype == "cosugar" else None),
                            r_poisson2_Hz=(200.0 if ptype == "cosugar" else None),
                            seed=pseed)
                        mn9 = len(lif.spike_times.get(MN9_L, []))
                        with out.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"rep": rep, "trial": t,
                                                 "ptype": ptype, "rep2": r2,
                                                 "mn9_hz": mn9}) + "\n")
        print(f"rep {rep}: train arc {arcs}", flush=True)

    # verdict per SPLIT criteria
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== WP-L3d VERDICT (split criteria, pre-registered) ==")
    fires = [r for r in rows if r.get("guard_fired")]
    print(f"guard fires: {len(fires)}")
    for rep in range(REPS):
        final_alone = [r["mn9_hz"] for r in rows
                       if r["rep"] == rep and r["trial"] == 24 and r["ptype"] == "alone"]
        final_cos = [r["mn9_hz"] for r in rows
                     if r["rep"] == rep and r["trial"] == 24 and r["ptype"] == "cosugar"]
        first_alone = [r["mn9_hz"] for r in rows
                      if r["rep"] == rep and r["trial"] == 4 and r["ptype"] == "alone"]
        print(f"  rep {rep}: alone t5={first_alone} -> t25={final_alone}; cosugar t25={final_cos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
