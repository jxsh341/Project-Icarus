# WP4 Report — Task A Acquisition, L0 vs L1

**Project:** FLY-LEARN-001 (Phase 2) | **Stage: DEVELOPMENT** (protocol §22 band 5–10; NOT the confirmatory result — that requires a separately pre-registered frozen seed set, WP5+)
**Design:** pre-registered before launch (`docs/FLY_LEARN_001_DECISIONS.md`: 'WP4 pre-registration' + amendment + v2 relaunch); D1 arm-swap; 6 seed blocks/arm; frozen L1 (1-hop V_MAG), shared η\*=1e-4; θ = 41.5 Hz symmetric primary criteria; trials-to-θ as speed metric; per-cue baselines mandatory (refined covariate); guard live; per-simulation weight checkpoints; probes verified read-only by test (hash unchanged) and N-probes-no-accumulation test.
**Data integrity:** v2 seed scheme verified disjoint from all prior stages incl. discarded v0 (audit artifact `wp4_seed_audit.json`); 24/24 blocks complete (52 records each); L0 cue-alone is exactly 0 by construction → the feed-direction comparison is a **one-sample claim against a degenerate null** ("is L1 above θ at each seed"), not a two-sample test with a real null distribution.

## Headline result (n=6 seeds/arm, trial-20 probes)

| arm | cue | direction | L1 readout (6 seeds) | criterion | L0 control |
|---|---|---|---|---|---|
| arm1 | GNG521 | FEED | alone: 81, 80, 69, 77, 77, 74 | **≥θ all 6/6 PASS** | 0,0,0,0,0,0 |
| arm1 | GNG380 | WITHHOLD | cosugar: 2, 4, 2, 4, 3, 6 | **<θ all 6/6 PASS** | 83, 87, 85, 85, 85, 86 |
| arm2 | GNG521 | WITHHOLD | cosugar: 89, 84, 83, 84, 87, 84 | <θ 0/6 **FAIL** | 82, 83, 83, 87, 81, 84 |
| arm2 | GNG380 | FEED | alone: 3, 4, 9, 4, 4, 6 | ≥θ 0/6 **FAIL** | 0,0,0,0,0,0 |

Guard: **0 fires in all 24 blocks.** Cross-direction leakage: none in the failing direction (withhold-trained GNG380 cue-alone stays 0; feed-trained GNG521 cosugar stays 83–92) — failure never produced wrong-direction expression; it produced *no* direction-appropriate expression.

**Acquisition succeeded in arm1 (both directions) and failed in arm2 (both directions).** L1-vs-L0: arm1 feed = every seed above θ over an exactly-zero null; arm1 withhold = suppression to 2–6 Hz against an 83–87 Hz L0 baseline (a 15–25× reduction, every seed below θ).

## The cue×direction interaction

Potentiation occurred in BOTH arms (per-trial `weight_diff` nonzero everywhere — arm2 blk0 trial 19: 233 edges changed, Σ|Δ| 419.6), so arm2's failure is **not** "plasticity did nothing": it learned, toward something that didn't express. Each cue's FEED direction was trained in exactly one arm (D1 swap), so cue and direction are crossed, not confounded: **GNG521 learned feed-only; GNG380 learned withhold-only.** The asymmetry is real, seed-stable (0/6 vs 6/6 — no overlap), and NOT an artifact of noise, guard, or trajectory stitching.

## Pre-registered interpretation order (withhold failures)

1. **Inhibitory-edge overlap** — checkable from per-run signed weight-deltas: GNG521-withhold (arm2) potentiated cue-incident edges, but the cosugar suppression never crossed θ while its own L0 baseline (81–87) sat un-suppressed. Overlap between GNG521's aversive-active 1-hop targets and the sugar-drive hub is insufficient.
2. **η below the suppressive pathway's threshold** — registered, not run: WP5 follow-up at η=1e-3 withhold-only arm.
3. **Withhold needs mechanisms beyond frozen L1** — recorded as a *negative result*, never a silent mechanism change.

GNG380-feed (arm2) fails for its own reason, not covered by that order: GNG380's strong leg-2 (96) is evidently **pathway-specific** — it reaches the readout through sugar-path hubs (its withhold direction worked, i.e. its leg-2 carries suppressive-effective connectivity) but its feed-mode potentiation never cleared θ against the exactly-zero baseline. Same shape as GNG521's mirror image: each cue's leg-2 geometry is direction-asymmetric.

## What this means

- **Task A's primary question (L0 vs L1) is answered affirmatively at development grade in arm1**: Hebbian plasticity on the frozen substrate produces acquisition in BOTH directions when the cue's geometry supports that direction — feed from exactly-zero baseline, withhold from an 83–87 Hz innate baseline down to 2–6 Hz, guard silent, no leakage.
- **The learned-direction asymmetry is a new structural finding** (extends the landscape note): leg-2 connectivity that enables acquisition is not just rare — it is *direction-specific per cue*. GNG521's leg-2 feeds the readout's excitatory side; GNG380's feeds the suppressive side. A cue that learns both directions was not found; whether one exists is an open structural question for WP5+.
- **WP5 (retention) proceeds on the learned directions only**: GNG521-feed and GNG380-withhold, at confirmatory seed count (§22), with the asymmetry carried as a covariate and the η=1e-3 withhold follow-up arm registered.
- Cross-direction claims (reversal, generalization) must be designed around the fact that neither cue learned its opposite direction — Task B (reversal) as specified requires direction-switchable cues, which the current pair is not (GNG521: feed-only; GNG380: withhold-only).

## Provenance

All 24 block JSONLs + per-simulation weight checkpoints: `results/phase2/wp4/`; discarded v0 (superseded design, 24 completed blocks, ~10 h compute, never aggregated): `results/phase2/wp4_discarded_v0/`; seed audit: `wp4_seed_audit.json`; registry: `docs/FLY_LEARN_001_DECISIONS.md`.
