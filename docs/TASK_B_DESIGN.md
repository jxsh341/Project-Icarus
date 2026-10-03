# Task B Design — Reversal under the Dose Rule

**Project:** FLY-LEARN-001 (Phase 2) | **Status:** Design draft, pre-registered before launch
**Date:** 2026-10-03
**Registry anchors:** 'WP4 ERRATUM (2026-10-01)' (dose artifact, retraction), 'WP4 addendum (2026-10-03)' (negative downgrade, proactive dose rule, seed scheme)

---

## 1. What Task B is

Protocol Task B: **reversal** — after acquisition, the trained direction is
inverted; the system must *unlearn* the first mapping and relearn the
opposite one. Reversal is the sharpest test of what was learned in WP4:
it requires genuine plasticity (a hard-coded mapping cannot reverse) and
it measures unlearning, which is plausibly slower than first acquisition.

## 2. The dose rule (root cause of the WP4 artifact, applied proactively)

The WP4 arm2 artifact happened because an **interleaved equal-trial
schedule silently halves per-cue dose** relative to a block schedule — a
property of the experimental design, invisible to config diffing. Rule:

> Every design **computes and pre-registers expected per-condition dose**
> (trials per cue per direction, under its chosen schedule) and **checks
> it against existing dose-response data before launch.**

### Dose table (computed now, from WP4 + pilot curves)

| condition | direction | dose needed (from data) | dose given | check |
|---|---|---|---|---|
| GNG521 retain-feed | feed | θ by trial 5–10 (sharp onset) | 15 block + 2 reversal-window probes | ≥ requirement ✓ |
| GNG380 retain-withhold | withhold | suppression ≤10 trials | 15 block + probes | ≥ requirement ✓ |
| GNG521 reversal→withhold | withhold | **unknown** (0/6 at 10 trials, single-probe; no dose reference for GNG521+bitter) | 25 block | room above 10 ✓ |
| GNG380 reversal→feed | feed | θ at 15–20 feed trials (pilot) | 25 block | ≥ 20 ✓ |

**Schedule decision (per-direction runs, NOT interleaved):** interleaving
is the mechanism that produced the artifact; reversal already plausibly
needs the highest trial counts. Each condition runs as its own block
schedule — every cue gets its full dose, no silent halving.

## 3. Design

### Stage R1 — Retention (per direction, learned directions only)

- **Conditions:** GNG521→feed, GNG380→withhold (the two directions that
  passed arm1 6/6). GNG521→withhold and GNG380→feed are NOT retention
  conditions — they never acquired.
- **Per condition:** 6 seed blocks. Phase 1: 15 feed-equivalent trials
  (full dose per the table). Phase 2: **retention probes at +0, +5,
  +10, +15, +20 trials post-acquisition** (no further training) — decay
  curve per seed. ≥2 probe sims per point at distinct seeds (probe-
  variance rule).
- **Pre-registered criterion:** readout stays on the learned side of θ
  at every retention point in ≥5/6 seeds (feed ≥41.5; withhold <41.5).
  Decay below θ = retention failure, recorded as such — not patched by
  retraining.

### Stage R2 — Reversal (per direction, from retained state)

- **Conditions:** from each R1 retained block, continue training with
  the direction inverted: GNG521 feed-trained → withhold drive
  (cue+bitter); GNG380 withhold-trained → feed drive (cue+sugar).
- **Per condition:** 25 reversal trials (dose table row 3–4; room above
  the unknown GNG521-withhold requirement; ≥20 for GNG380-feed).
  Probes at trials 1, 2, 3, 5, 10, 15, 15+5, 20, 25 (≥2 sims/point).
- **Pre-registered criteria (CORRECTED 2026-10-03 — the drafted
  parenthetical had the unlearning metrics SWAPPED, which made them
  contradict the relearning criteria; the reviewer's no-competing-
  drive probe exposed it):**
  - *Unlearning (GNG521, feed→withhold):* the OLD feed response is
    GONE **without the competing drive** — cue-alone probe < 41.5 by
    trial 25. (Cue-alone IS the no-competing-drive condition: no
    bitter in it.)
  - *Unlearning (GNG380, withhold→feed):* the OLD suppression is
    GONE under the old readout condition — cosugar probe ≥ 41.5 by
    trial 25.
  - *Relearning (GNG521):* cosugar < 41.5 by trial 25 (new withhold
    semantics). *Relearning (GNG380):* cue-alone ≥ 41.5 by trial 25
    (new feed semantics).
  - Both metrics reported per cue with across-seed spread; trials-to-θ
    as the speed metric; n=6 seeds development-grade (S22), WP6+
    confirmatory at 10 frozen seeds.

### Two-state gate (registered 2026-10-03, review-directed, BEFORE launch)

V_MAG is potentiative-only: unlearning cannot weaken the old pathway's
weights, so a cue passing R2 could be in either of two states —
**genuinely reorganized**, or **masked** (old pathway fully intact,
suppressed by a stronger competing association). The probe conditions
that distinguish them ALREADY exist in the 4-probe no-leakage set at
every point (cue-alone and cosugar for both cues) — zero added
simulation cost; what this gate adds is the CLAIM structure. Final
state of each reversed cue is classified (θ = 41.5):

| GNG521 (feed→withhold) | cue-alone | cosugar | claim |
|---|---|---|---|
| REVERSED | < θ | < θ | withhold semantics achieved |
| TWO-ASSOCIATION (masked) | ≥ θ | < θ | old feed intact + new suppression — claim "masked by a second competing association", NOT reversed |
| NOT REVERSED | ≥ θ | ≥ θ | old intact, no new direction |
| ERASED/PARTIAL | < θ | ≥ θ | old gone, no new direction |

| GNG380 (withhold→feed) | cosugar | cue-alone | claim |
|---|---|---|---|
| REVERSED | ≥ θ | ≥ θ | feed semantics achieved |
| TWO-ASSOCIATION (masked) | < θ | ≥ θ | old suppression intact + new feed — NOT reversed |
| NOT REVERSED | < θ | < θ | old intact, no new direction |
| ERASED/PARTIAL | ≥ θ | < θ | old gone, no new direction |

The discriminator probe for GNG521 is cue-alone (no competing drive);
for GNG380 it is cosugar (the old readout condition). A cue in the
TWO-ASSOCIATION cell passes unlearning+relearning as originally
drafted — which is exactly why the gate must exist before the run:
"reversed" and "masked by a second, competing association" are
different findings, and the difference is the kind of thing that
looked fine under original criteria in every prior case until someone
checked the condition nobody thought to ask about.

### Sign note for reversal (registered, because it is not obvious)

Reversal of *withhold* (GNG380) is sign-consistent with acquisition:
withhold training potentiated suppressive-effective connectivity, so
reversal = feed training toward the excitatory side — the new direction
is the mirror of the old one and the criteria above apply directly.

Reversal of *feed* (GNG521) has a subtlety: feed acquisition potentiated
excitatory cue→readout edges from exactly-zero baseline. "Unlearning"
that mapping means those edges must *weaken* — but frozen 1-hop Hebbian
V_MAG is potentiative-only on co-active pairs. The registered mechanism
for unlearning in this design is therefore **competitive**: the bitter
co-drive suppresses the readout during reversal training, and Hebbian
potentiation lands on the aversive-active subset of the cue's 1-hop
targets. Whether that suffices to move the readout across θ in the
reverse direction is exactly what R2 measures — **a failure is a
publishable negative** (the suppressive analog of unlearning may need
mechanisms beyond frozen L1; that would be a landscape-note extension,
never a silent mechanism change).

### Controls

- **L0-R:** identical schedules and seeds, plasticity=None, all blocks
  (12 R1 + per-direction R2) — the degenerate-null note applies: L0
  cue-alone is exactly 0 by construction.
- **No-leakage probes:** both cues × alone/cosugar at every probe point
  (cross-direction leakage measured by design, as in WP4).

### Infrastructure (carried from WP4 v2, all test-verified)

- Per-simulation weight checkpoints (`run.save()` after every sim;
  `TrainingRun.load()` with hash verification at block start) — the
  "checkpoint records ≠ checkpoint state" rule.
- Probe purity: hash-unchanged-through-probe, N-probes-no-accumulation
  (test-verified).
- Seeds: training 80000 + bi·100 + t; probe 90000 + bi·1000 + pt·10 +
  ty·2 + rep — **verified disjoint by computation before launch** (0
  internal collisions; min ranges above the prior max of 73193).
- Guard live (D6 thresholds); any fire = halt + report.
- Per-trial JSONL appends (per-record, verified).

## 4. Interpretation orders (registered before any data exists)

**If R1 retention fails (decay below θ):**
1. Genuine decay under frozen L1 — recorded as a NEGATIVE RESULT for
   retention (never patched by retraining within the same run).
2. Probe-variance artifact — only after the ≥2-probes/point check.

**If R2 reversal fails for GNG521 (feed→withhold):**
1. Insufficient aversive-active overlap (per-run signed weight-deltas
   check, as pre-registered in WP4).
2. η below the suppressive pathway's threshold — η=1e-3 follow-up arm.
3. Unlearning needs mechanisms beyond frozen L1 — NEGATIVE RESULT,
   landscape-note extension.

**If R2 reversal fails for GNG380 (withhold→feed):**
1. Dose check FIRST (the standing rule): confirm 25 reversal trials ≥
   the pilot-derived 15–20 requirement — the dose is met by design, so
   a failure here is structural, not dose.
2. Competitive-potentiation sufficiency check from weight-deltas.

## 5. What this design costs

12 R1 blocks × (15 trials + 5 probe points × 2 types × 2 sims) + 12 R2
blocks × (25 trials + 9 probe points × 2 types × 2 sims) + 24 L0-R
blocks ≈ **1,700 simulations**, overnight-scale, checkpointed per
simulation. Stage R1 and R2 are separable: R1 lands first and R2
launches only on retained blocks (a retained state is the required
input; an un-retained block fails fast and cheap).

## 6. Provenance

Dose-response data: WP3 pilot curves (`results/phase2/wp3_pilot/comparability_curves.jsonl`), WP4 arm1/arm2 block JSONLs (`results/phase2/wp4/`). Errata and standing rules: `docs/FLY_LEARN_001_DECISIONS.md`. Harness guarantees: `tests/test_wp4_io_persistence.py` (7 tests).
