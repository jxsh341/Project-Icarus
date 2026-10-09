# FLY-LEARN-001 — Phase 5 Experiment A: Confirmatory Replication Pre-Registration

**Status:** PRE-REGISTERED — frozen before any confirmatory run. No confirmatory
result exists in this document. Written 2026-10-09, after the dev-stage L4b
result and **before** the confirmatory experiment runs.
**Harness:** `scripts/phase4_wp_l4b_extinction.py` (constants frozen at lines
53–67; recorded as claim INFRA-2 in the claim inventory). The analysis script
must be written and committed **before** results are unblinded, per standing rule.

## What is being confirmed

The Phase 4 L4b result (dev-stage, 3 seed reps): the eligibility-then-sign
protocol eliminates the GNG521 cue-alone response (68–84 Hz → 0 spikes) while
preserving the innate cosugar pathway (78–88 Hz), with guard silence and all
carriers at floor. This experiment tests **replication under frozen conditions**
— implementation, parameters, seed sets, and success criteria all pre-registered
here — on an **independently drawn seed set**, drawn and committed below
**before** the first confirmatory run.

## Frozen implementation

- Commit: `a4c0e6b` (report-review-fixes state; 121/121 tests passing).
- Harness: `scripts/phase4_wp_l4b_extinction.py` as of that commit, constants at
  lines 53–67, UNCHANGED. Any deviation → registered as a deviation, not folded in.
- Baseline: run-007 closure (male-cns:v0.9), 40,290 neurons / 336,245 synapses.
- Protocol: eligibility-then-sign; per-trial JSONL checkpointing throughout;
  stability guard active on every trial; weight-hash checkpoints per cycle.

## Frozen parameters (harness lines 53–67)

| Parameter | Value |
|---|---|
| ETA | 1e-4 |
| THETA | 41.5 Hz |
| W_MAX | 766.0 |
| CUE | [15957, 16327] |
| PPL_TRIO | [11618, 11900, 529516] |
| UNTOUCHED (9 partners) | [13510, 18474, 12364, 14803, 14953, 66802, 516493, 524078, 555850] |
| N_CYCLES | 25 |
| PROBE_AT | (5, 10, 15, 20, 25) |
| REPS (dev) | 3 |
| TRAIN_SEED_BASE (dev) | 160,000 |
| PROBE_SEED_BASE (dev) | 162,000 |

**Dev-stage seed derivation (frozen record):** train seeds = 160,000 + rep·10000
+ cycle·100 + ...; probe seeds = 162,000 + rep·10000 + cyc·100 + r2·10 + off.
Exact derivation in harness source. **Confirmatory seeds must not overlap dev
seeds** (verified below).

## Confirmatory seed set (drawn and frozen HERE, before any run)

```
CONF_TRAIN_SEEDS = [860143, 860205, 860343, 860473, 860684, 860801, 860858, 860954]
CONF_PROBE_SEEDS = [970086, 970098, 970198, 970237, 970473, 970549, 970665,
                    970681, 970695, 970811, 970845, 970885, 970953, 970963, 970996]
```

**Derivation:** drawn 2026-10-09 from `random.Random(20261009)` — a fixed,
documented derivation reproducible from one integer. 8 train-family seeds from
the 860k block and 15 probe seeds from the 970k block; both blocks are disjoint
from the dev seed space ([160,000, 193,000) with slack for every offset family).
Drawn and written here BEFORE any confirmatory simulation ran. Disjointness,
distinctness, and block boundaries verified programmatically at freeze time.

## Success criteria (three-way, pre-registered)

All criteria evaluated on the confirmatory seed set only. A criterion not met →
its branch is reported as-is; no re-tuning, no post-hoc seed addition.

**PASS** requires **all** of:
1. Cue-alone response reaches 0 spikes (integer spike counts over the full
   1000 ms probe window — literal zero, the project's standing standard) by
   cycle ≤ 15, in **every** confirmatory rep.
2. Zero persists through cycle 25 (prespecified follow-up: probe points 15→25).
3. Cosugar probe at every probe point stays within the dev-stage envelope
   (78–88 Hz band; no point below 78).
4. Stability guard silent on every trial of every rep.
5. All 25 carriers + all 9 previously-unreachable partners at V_CLIP floors in
   every rep (weight forensics as in dev runs).

**NEGATIVE-A (mechanism fails to replicate):** any rep's cue-alone fails to reach
0 by cycle 15, OR zero fails to persist to cycle 25, OR carriers miss floor.

**NEGATIVE-B (collateral damage):** cosugar band violated (any point < 78 Hz)
OR guard fires, OR weight forensics show sign-flip / structural-zero alteration.

**Interpretation rules (pre-registered):**
- The result is per-rep; report all reps individually. No smoothing.
- Trials-to-zero distribution is a **descriptive** outcome, not a criterion.
- Trials-to-zero is only meaningful on trials where the guard stayed silent
  throughout that rep (else that rep is NEGATIVE-B regardless of readout).
- **Mixed outcomes rule:** if reps split across branches (e.g. 7 PASS / 1
  NEGATIVE-A), the verdict is MIXED, reported per-rep, and the seed set as a
  whole does NOT promote to confirmed. A MIXED verdict triggers re-examination
  of the protocol (registered as a protocol question, not silent re-tuning).
- N/A-with-reasons is not available for the headline criteria; the three-way
  split is exhaustive here.

**Dev-stage relationship:** the dev-stage result (3 reps, 160k-block seeds) is
development-stage evidence. If confirmatory = PASS, the dev result promotes to
**confirmed**. If NEGATIVE-A or MIXED, the dev result stays development-stage
and the discrepancy is investigated as a discrepancy (dose-diff-first standing rule).

## Output fields (the analysis script must emit, before unblinding)

Per rep: run_id, seed, cycles-to-zero (or not-reached), zero-persistence (c15→c25),
cosugar at each probe point, guard-fire count, per-carrier floor counts (25/9),
collateral-edge deltas. Aggregate: per-criterion PASS/NEGATIVE-A/NEGATIVE-B/MIXED
per rep and overall; trials-to-zero distribution; dev-vs-confirmatory drift table.

## Sample-size rationale

Dev stage: n=3 (exploratory). Confirmatory: n=8 independent reps — chosen
because trials-to-zero hit cycle 15 in 3/3 dev reps, and n=8 gives 2^3 more
resolution on the distribution's upper tail while remaining compute-feasible
(≈2.7× dev compute). Probe seeds: 15, matching the dev probe density. No power
analysis claimed — this is a replication with a pre-specified exhaustive
three-way split, not a powered effect-size test; the split's purpose is to
prevent partial replication from being read as success (the NEGATIVE-B
category exists for exactly that reason).

## What would falsify the structural principle

The eligibility-then-sign protocol is derived from the reachability census
principle: *an association can only be removed through a protocol that reopens
access to the coincidences that built it*. If confirmatory runs show unlearning
**without** sugar-phase recruitment (e.g., bitter-only extinction reaching the
9 untouched partners), the principle is falsified in its strong form. The dev
data say this cannot happen (PPL-trio input to those partners = 0, measured);
the confirmatory runs test the protocol's replication, not the principle's
falsification — but any anomaly in the untouched-partner floors is checked
against the principle's prediction (they should be reachable only via sugar).

## Standing-rule compliance checklist

- [x] Implementation frozen (commit a4c0e6b; harness constants lines 53–67)
- [ ] Analysis script committed before results unblinded — PENDING, by design
- [x] Seed set frozen in this document, drawn before any run
- [x] Three-way criteria frozen
- [x] No re-tuning; deviations registered as deviations
- [x] MIXED handling pre-specified
- [x] Borrowed-band caveat: cosugar envelope (78–88) is dev-measured, now frozen
- [x] A copy of this pre-registration is committed to the registry
- [x] Trial-dose explicitness (inherited from harness)

## Registry cross-references

- Dev result: PHASE_3_4_CLOSEOUT.md §L4b; claim inventory EXT-4
- Cosugar band provenance: claim inventory EXT-2 (REGRESSION entries exist for
  a reason; the 78–88 band carries its provenance)
- Coincidence principle: PLASTICITY_LANDSCAPE.md; PRIOR_ART_MEMO.md §positioning
- Reachability census: EXT-3 / EXT-3b
- Dev seed blocks: INFRA-2 (frozen harness record)
- The three-way split is exhaustive; MIXED is its own verdict, and a MIXED
  outturn cannot be aggregated into PASS.
