# ICA-M1-1 — Review of the proposed n=8 contract-probe protocol

**Reviewed document:** Hybrid `docs/M1_ICARUS_CONTRACT_PROBE.md` §6 ("Proposed
multi-repetition protocol — FOR REVIEW, NOT EXECUTED"). **Not executed** — no
authorization was given, and Hybrid's original n=1 result stays a separate
preserved experiment. Review is against ICA-M1-1 §8's checklist and this repo's
standing rules (frozen seeds, config fingerprints, non-aggregating verdicts).

## Verdict: SOUND WITH REQUIRED CORRECTIONS — approve only after the corrections below

## What the proposal gets right

- Fresh substrate per repetition (no weight carry-over) — correct.
- Non-overlapping acquisition seed bases (`3_300_000 + k·10_000`, trial seeds
  `b+1..b+20` never repeat across reps) — correct for acquisition trials.
- Per-criterion counts + INCONCLUSIVE on incomplete reps — matches this repo's
  non-aggregating verdict discipline.
- Failure taxonomy exists (guard → stability failure class).
- Run as background job; cost estimate (≈25 trials × ≈90 s × 8 ≈ 5 h) is realistic
  against the n=1 probe's 274.8 s for ~25 trials.

## Required corrections

1. **Probe seeds are not varied across repetitions.** `present_cue`/`step` default
   `seed=0` in every rep — the retrieval measurement would reuse one probe seed 8
   times. Fix: draw a per-repetition probe seed base from the same disjoint draw
   (e.g. a second space `3_400_000 + k·10_000`, or extend the existing draw) and
   record it in each rep's manifest. Same for the 5 blank-trial seeds.
2. **No confidence interval / statistical treatment.** n=8 with a ≥7/8 rule is a
   count, not an estimate. Add: report the success count with a Clopper–Pearson
   (exact binomial) 95% interval, and state explicitly that 7/8 = "partial"
   (the proposal says this in prose; make it a formal verdict class).
3. **Configuration fingerprint missing.** Pin per run: `fly/api.py` version
   (v1.1.0), `SCHEMA_VERSION`, snapshot hash (`384406e9278ae0c0`), prereg sha,
   `FROZEN_PLASTICITY` config hash, guard thresholds, `RETRIEVAL_HZ=41.5`.
   Without these the 8 reps are not provably the same configuration.
4. **Environment must be frozen:** Icarus's own venv (numpy 1.26.4). Hybrid's
   attempt B showed the Hermes venv (numpy 2.x) fails inside scipy under memory
   pressure — record the interpreter + numpy/scipy versions in the manifest.
5. **Artifact discipline:** per-rep machine-readable JSON (the 5 measurements +
   hashes), one manifest per rep, quarantine (not deletion) of incomplete reps,
   and the original n=1 artifacts untouched and cross-referenced — never merged
   into the n=8 set.
6. **Seed-space disjointness must be asserted, not assumed:** assert the n=8
   spaces are disjoint from ALL prior Icarus seed spaces (dev/confirm/P6/P7/
   screen/P7B/E1/P3/P4/P4b/P5/ICA-M1), as every launcher in this repo does via
   `reproduce_draw` + prior-set guards. The proposal's range check covers only
   its own bases.
7. **Decision rule edge case:** define up front what a guard firing in a rep
   means for that rep's class (stability failure) and that a stability failure
   in ANY rep caps the verdict at PARTIAL even if 7/8 pass the rest.
8. **Do not tune after observing:** re-affirm in the protocol that no threshold
   (41.5 Hz), stimulus parameter, or scoring rule changes post-hoc; a new
   configuration is a new preregistered condition.

## Sample-size justification comment

n=8 is small but this is a *bounded-capability* qualification, not a rate
estimate for deployment; with the exact-binomial interval reported, 8/8 →
lower bound ≈ 0.63, 7/8 → ≈ 0.55 — honest about the bound. Acceptable for M1
qualification IF the interval is reported; otherwise the number looks stronger
than it is.

## Reproducibility

Each rep must be rerunnable from its manifest alone (fresh substrate, pinned
snapshot, recorded seeds, pinned config hashes) and produce the same weight
hashes — determinism per (matrix, seed) is already test-pinned in this repo.
