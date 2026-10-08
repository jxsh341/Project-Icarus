# Task B Close-Out — FLY-LEARN-001 Phase 2

**Stage:** Development (protocol §22: 5–10 seeds; n=6 blocks/condition — NOT confirmatory; that requires a separately pre-registered frozen seed set)
**Verdict summary:** Acquisition **YES** (WP4) · Retention **YES** (R1) · Reversal **NO** — blocked for GNG521, unstable for GNG380 (R2)
**Mechanism identified:** GNG380's reversal regression = **coincidence waste at MN9_L**; conditional, not universal (GNG521 excluded by extended-dose replay)
**Registry:** `docs/FLY_LEARN_001_DECISIONS.md` (all sections 2026-10-03 → 2026-10-08) | **Data:** `results/phase2/taskB_r1/`, `taskB_r2/` | **Commit:** through `715cb8b` + this close-out

---

## 1. Design provenance (what ran, vs what was registered)

| Stage | Registered | As-run deviations (all registered) |
|---|---|---|
| R1 retention | 2 learned directions only (GNG521-feed, GNG380-withhold); weights frozen during retention; 5 probe points | 3 probe points in the first launch (loop-bound bug, erratum); R1-v2 rewrote retention as 15 acq + 15 no-stimulus trials with rule ACTIVE — divergence rendered moot by direct weight-hash verification: **bit-identical** end-acq → end-retention in all 12 blocks (spontaneous silence confirmed at weight level) |
| R2 reversal | 25 trials/condition from retained states; corrected unlearning criteria (old response gone WITHOUT competing drive); two-state gate; ≥2 reps/point | Gate bugs fixed pre-launch (cue filter 10-03; final point t=25 10-08) with test battery; stale 10-04 artifacts quarantined (`quarantine_2026-10-08/`), never aggregated; resume-rate standing rule added |

Seeds: R1 train 80000+, R1 probe 90000+, R2 train 85000+, R2 probe 120000+, mechanism probes 87000+ — all verified pairwise disjoint by computation, pre-launch. Per-simulation weight checkpoints; probe purity test-verified (hash unchanged); guard live; **0 fires across every Task B simulation**. L0-R controls matched-schedule, degenerate-null stated (L0 cue-alone ≡ 0 by construction).

## 2. Results

### R1 — Retention (n=6/condition)
**12/12 blocks RETAINED.** GNG521-feed: cue-alone 76–89 Hz, flat across all points. GNG380-withhold: cosugar 0–5 Hz, suppressed throughout. L0: exactly as constructed (0s / 81–86). Weight-freeze verified at hash level — the "retention under frozen weights" claim is measured, not inferred.

### R2 — Reversal (n=6/condition, final-state two-state gate)
**Both cues 6/6 NOT REVERSED. The masking cell was never occupied** — the competitive mechanism never even established a shadow association.

- **GNG521 (feed→withhold): total, seed-stable negative.** Old feed intact (cue-alone 80–87, cosugar 84–89, both ≫ θ=41.5; L0 unchanged 84–90). Nothing suppressed at 25 trials — 2.5× WP4's dose. **WP4's 10-trial negative is structural, not dose-limited:** potentiative-only V_MAG + bitter co-drive cannot suppress an established excitatory association. Interpretation step 3 (pre-registered): unlearning requires mechanisms beyond frozen L1.
- **GNG380 (withhold→feed): transient crossing + regression — the run's central finding.** All 6 blocks (±2 Hz): cosugar 2–3 → 31–34 (t9) → 40–46 (t14), **crosses θ at trial 15 in 5/6 blocks** (blk5's 40 Hz is a boundary case within probe noise, honestly not counted), train readout peaks 49, then **regresses to 26–27 by t25**. Weights never weaken (334 grown edges, all positive; V_MAG is potentiative-only) — the rise-fall is a dynamics phenomenon.

### The regression mechanism — coincidence waste (review-directed WHY-chase)

Hypothesis triage on the regressing block (deterministic replays, same seeds):
1. **Refractory saturation of intermediates: EXCLUDED** — rates rise monotonically 183→358 Hz, plateau at 78% of the 454.5 Hz ceiling, never decline while MN9 falls 49→27.
2. **Grown inhibition interference: EXCLUDED** — 0/334 grown edges negative; none land on MN9's 10 inhibitory inputs.
3. **Mechanism (measured): coincidence waste.** MN9's input arrivals ROSE 3045→4076 (+34%) while its spikes FELL 49→27 (−45%); arrivals cluster at median 0.2 ms (99.9% < 2 ms). Intermediates phase-locked to the shared cue drive over-synchronize MN9's inputs; with τ_syn=5 ms and threshold clipping, coincident kicks collapse on the already-depolarized membrane. **Readout spike count is non-monotone in total drive in the coincidence regime.**

### Generality — conditional, not universal (review-directed extended-dose replay)

GNG521-feed replayed 40 trials past its retained state (dose 55, 2.75× crossing): **flat 86–95 Hz, no arc.** Its intermediates run 120–165 Hz = **33% of ceiling**; GNG380's run 350–358 Hz = **78%**. The discriminator is the **intermediates' rate regime**: coincidence waste onsets when convergent leg-2 intermediates climb toward ~300+ Hz (≈⅔ of refractory ceiling). GNG521's clean pass is a qualitatively stable outcome; GNG380-class cues (many members, strong distributed leg-2, hard-driven intermediates) self-degrade past peak.

## 3. What Phase 3 inherits (named, measured, priced)

1. **Weakening mechanism** — required for any reversal: potentiative-only rules cannot unlearn. GNG521's total negative prices it precisely.
2. **Consolidation = stop-at-crossing, conditional:** needed for GNG380-class cues; GNG521-class trains stably. **Online policy (the open question between mechanism-identified and mechanism-usable):** monitor the leg-2 intermediates' own rates during training (no MN9 probe needed) — when they enter the ~300 Hz warning regime, probe once for the crossing and stop. Characterized from both probes' data; implementing and validating the online detector is Phase 3 mechanism work.
3. **Landscape note extension:** acquisition YES, retention YES, reversal NO (blocked/unstable); coincidence waste is a substrate property (synchronized convergent input collapsing sub-linearly near threshold), not an artifact of this cue pair or rule.

## 4. Standing rules added during Task B (all registry-registered)

- Checkpoint records ≠ checkpoint state; resume must be indistinguishable from uninterrupted (bit-for-bit test).
- Resume across a design revision requires quarantine first; **resume-rate vs compute-rate** is the stale-data detection signal.
- A verification must **fail loudly on empty scope** (vacuous-check lesson).
- Dose-diff first when a result contradicts an earlier measurement of the same nominal condition.
- Probe-purity tests; per-cue baselines; ≥2 probe sims/point; honest boundary-case counting (blk5 = near-miss, not crossing).

## 5. Provenance

Every number above traces to checkpointed JSONL artifacts: R1 `l1/l0_{cond}_blk*.jsonl` (78 records/block), R2 `l1/l0_{rev}_blk*.jsonl` (81 records/block), mechanism probes (`mechanism_saturation_probe.json`, coincidence probe output, `gng521_extended_dose_probe.json`), weight diffs from per-simulation checkpoints. Errata, near-misses, and as-run divergences are registered in `docs/FLY_LEARN_001_DECISIONS.md` rather than smoothed.
