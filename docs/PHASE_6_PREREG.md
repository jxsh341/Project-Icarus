# FLY-LEARN-001 — Phase 6 Pre-Registration: Forgetting-Rate Certification (WP-L6a) and Rank-Targeted Forgetting (WP-L6b)

**Status:** PRE-REGISTERED — frozen 2026-11-03 at HEAD `93c18ed`, before any
Phase 6 run or analysis output exists. No Phase 6 result is in this document.
**Basis:** prior-art pass over arXiv:2410.22374 (FNN) and arXiv:2003.10933
(Forsaken) — see §1. Analysis scripts must be committed **before** results are
unblinded, per standing rule.

## 1. Prior art and what is adopted from it

| Paper | Mechanism | Adopted here as | Not adopted because |
|---|---|---|---|
| arXiv:2410.22374 (Hatua et al., FNN) | Per-neuron multiplicative forgetting factors φ(t)=e^(−t/τ), rank/top-N by forget-set activation; MIA score as effectiveness measure | WP-L6b's rank-targeted decay (mechanism); MIA-style metric (WP-L6a) | MNIST/Fashion-MNIST conv-net evidence only; transfer to a frozen sparse recurrent connectome is unproven and is exactly what WP-L6b tests |
| arXiv:2003.10933 (Liu, Forsaken) | Mask gradients from a generator (dopamine/active-forgetting analogy) + uniform forgetting-rate metric via membership oracle | The forgetting-rate / membership-oracle certification (WP-L6a) | Neuron masking is cruder than L4b's edge-level erosion; would damage innate pathways (cosugar). Retained only as a possible lesion-style ablation control, not a method |

Both are privacy-unlearning papers, not neuroscience: they neither threaten
nor support the project's novelty positioning (see PRIOR_ART_MEMO.md).

## 2. WP-L6a — retrospective forgetting-rate certification (no new training sims)

**Question (registered by Experiment A's MIXED verdict):** the unlearning left
4 residual synaptic edges in all 11 reps (16327→15649, 15957→15649,
16327→20178, 16327→516493) while the readout was at literal zero. Is the
association still *inferable* from the substrate — i.e., are the residuals an
information leak, or is the memory operationally forgotten?

**Design (membership-oracle analog, per Forsaken's forgetting-rate metric):**
- Member class (association learned): the 6 acquired GNG521 checkpoints
  `results/phase2/taskB_r1/ckpt_l1_gng521_feed_{0..5}`.
- Non-member class (never learned): the 6 pre-acquisition checkpoints
  `ckpt_l0_gng521_feed_{0..5}`.
- Test population: the 11 unlearned final matrices — dev
  `results/phase4/wp_l4b/ckpt_r{0,1,2}` and confirmatory
  `results/phase4/wp_l4b_confirm/rep_r{0..7}/ckpt_r0`.
- Features, per substrate: (i) white-box — the 25 footprint-edge weights
  (RANK_SET, hash below), changed-edge count, L1 |Δ| vs pristine over the full
  matrix; (ii) black-box — MN9_L (10331) readout Hz under cue-alone, cue+sugar,
  cosugar probes at 3 frozen seeds from the reserved 1.4M block. Behavioral
  values for the 11 test reps come from the existing probe JSONL rows — **no
  new simulations for the retrospective pass**.
- Oracle: logistic regression on standardized features; leave-one-out
  cross-validation over the 12 training checkpoints. **Validity gate:**
  LOO accuracy ≥ 10/12 AND all 6 member ckpts classified member in-sample.
- Forgetting rate: FR = fraction of the 11 unlearned reps classified
  non-member (Forsaken's AF/(BT+BF) adapted; BT = the 6 member ckpts must be
  detected as member before any FR is meaningful).

**Criteria (three-way, frozen):**
- PASS: valid oracle AND FR = 11/11.
- NEGATIVE-A (residuals leak): valid oracle AND FR < 11/11 — at least one
  unlearned substrate remains classifiable as learned → the dose-tail is an
  information leak → supports a longer/higher-dose protocol.
- NEGATIVE-B (instrument invalid): LOO < 10/12 or member recall < 6/6 →
  metric inconclusive; this is an instrument verdict, NOT a forgetting verdict.
- MIXED: reps split across classes → reported per-rep, non-aggregable.

**Ablation sub-test (pre-registered):** refit the oracle without the 4
residual-edge features; report ΔFR. If FR is unchanged at 11/11, the residual
synapses carry no inferable membership information → "behavioral extinction +
located residual synapses" is certified as the honest claim, answering the
registered protocol question.

**Artifacts:** `scripts/phase6_l6a_oracle.py` committed before unblinding;
output `results/phase6/wp_l6a/oracle_report.json`. The 1.4M shadow block is
used only for oracle behavioral probes on the 12 ckpts, and for a
fresh-shadow confirmation pass ONLY if the retrospective FR is MIXED.

## 3. WP-L6b — rank-targeted multiplicative forgetting on GNG521 + GNG380 probe

**New harness** `scripts/phase6_wp_l6b_rankforget.py` (the L4b harness stays
frozen, sha-pinned; L6b starts from the acquired checkpoint — no
re-acquisition). Mechanism, frozen:

- RANK_SET = the GNG521 acquisition footprint: exactly the 25 edges with
  nonzero acquired−pristine delta, sha256 of the sorted edge list
  `43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589`
  (recomputed from artifacts at launch; mismatch halts the run).
- Unlearning trial = **cue-alone @ 200 Hz only** (CUE = [15957, 16327], no
  drive) — drive-independent by construction, the key difference from L4b.
- After each unlearning trial: for each RANK_SET edge, w ← w·exp(−1/TAU0),
  TAU0 = 1.0 cycle; all other edges unchanged (τ = ∞). Then W_EPS snap:
  w < 1e-9 → 0.0 (preserves V_CLIP exact-floor semantics).
- N_CYCLES = 25; probes at cycles (5,10,15,20,25), cue-alone + cosugar, 2 reps
  each (L4b probe density); readout MN9_L = 10331; THETA = 41.5 Hz;
  W_MAX = 766.0; guard identical to L4b (max 150,000 spikes/trial, spontaneous
  5.0 Hz, inhibitory drift frac 0.20).
- Baseline: R1CK = `results/phase2/taskB_r1/ckpt_l1_gng521_feed_0`; pristine =
  `data/processed/neuprint_snapshots/run-007/connectivity_matrix_signed.npz`.

**GNG521 criteria (three-way, Phase-5 structure, frozen):**
- PASS requires ALL: cue-alone literal 0 spikes by cycle ≤ 15 in every rep;
  zero persists through cycle 25; cosugar within the dev envelope 78–88 Hz
  (no point below 78; upper excursions reported per-rep, as in confirm reps
  1/3 at 89/92); guard silent on every trial; floors 25/25 carriers + 9/9
  untouched partners in every rep (the dose-tail test — L4b and its
  confirmatory run achieved 21/25 + 8/9).
- NEGATIVE-A: cue-alone fails to reach 0 by c15, OR persistence fails, OR
  floors missed.
- NEGATIVE-B: any cosugar point < 78 Hz, OR guard fires, OR sign-flip /
  structural-zero alteration in weight forensics.
- MIXED: reps split across branches → per-rep verdict, non-aggregable, no
  promotion; triggers a registered protocol question, not silent re-tuning.

**GNG380 reachability probe (n=2 reps, separate exploratory verdict):** same
rule from `ckpt_l1_gng380_withhold_0`, RANK_SET = its 158-edge footprint
(sha256 `27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a`),
CUE = [50843, 53901, 103327, 129624, 556072, 559464]. Report per-edge floor
coverage, especially the 45 zero-input partners (the 62% no-measured-drive
set). Boundary criterion: POSITIVE-BOUNDARY = ≥ 1 of the 45 zero-input edges
reaches floor with guard silent (decay is not drive-gated) → the GNG380
boundary is a property of coincidence-gating, not of the substrate.
NEGATIVE-BOUNDARY otherwise.

## 4. Frozen Phase 6 seed set (drawn and verified HERE, before any run)

```
P6_TRAIN_SEEDS  = [1211723, 1217510, 1218820, 1221250, 1221372, 1225450, 1280661, 1281236]
P6_PROBE_SEEDS  = [1407167, 1414999, 1423372, 1424809, 1433282, 1442593,
                   1459348, 1466626, 1469306, 1469429, 1484366, 1489242,
                   1492128, 1496950, 1499659]
P6_SHADOW_SEEDS = [1400487, 1401210, 1401922, 1403359, 1403570, 1403976, 1405103, 1408656]  # RESERVED: WP-L6a oracle probes / fresh-shadow pass only
```

**Derivation:** `random.Random(20261103)` — see Amendment A1: train anchors
drawn from [1,200,000–1,300,000), probe anchors from [1,400,000–1,500,000),
each anchor's FULL expanded seed space checked collision-free at draw time;
shadow anchors (block [1,400,000–1,410,000), raw probe seeds, no space
expansion) are fixed from the original draw. **Verified programmatically at
draw time (2026-11-03):** dev space 211 seeds, confirmatory 697 (400 train +
297 probe/sanity); Phase 6 expands to 200 train + 315 probe seeds, 0 internal
collisions, 0 overlap with dev, confirmatory, or shadow seeds. The launcher
re-verifies all of this at launch (guard G3 semantics).

## 5. Execution order (frozen)

1. Commit `scripts/phase6_l6a_oracle.py` and `scripts/phase6_expB_analysis.py`
   (analysis before unblinding).
2. Commit `scripts/phase6_wp_l6b_rankforget.py` + `scripts/phase6_expB_launcher.py`
   (launcher modeled on `phase5_expA_launcher.py`: G1 sha-pin of harness,
   G2 harness immutability, G3 seed-space checks, G4 artifact-root guard,
   artifact-complete completion criterion, quarantine + idempotent relaunch).
3. Run WP-L6a retrospective pass (existing artifacts only).
4. Launch WP-L6b (8 reps GNG521 + 2 reps GNG380 probe) in the background;
   record process/run ids; never interpret partial results as the verdict.
5. Frozen analysis over complete artifacts → `results/phase6/wp_l6b/EXP_B_VERDICT.json`.

If the environment, repo state, or artifacts differ from this registration:
stop and document the discrepancy — never silently repair mid-experiment.

## 6. What would falsify / strengthen

- L6b PASS on GNG521 (25/25 + 9/9 floors, cosugar intact, 8/8) → the dose-tail
  is closed by drive-independent targeted decay; the unlearning claim
  strengthens to full synaptic erasure (promotion decision registered
  separately — a PASS here does not auto-promote; MIXED rules still apply).
- L6b floors missed again → the dose-tail is structural (an edge property), not
  a dose problem; the registered question is answered in that direction.
- L6a NEGATIVE-A → residual synapses are an inferable leak → longer-dose
  protocol justified. L6a PASS with stable ablation → residuals are
  behaviorally inert; "behavioral extinction + located residuals" is the
  certified claim.
- L6b GNG380 POSITIVE-BOUNDARY → the 62% boundary is coincidence-gating, and
  drive-independent decay is the first mechanism shown to reach those edges.

## 7. Standing-rule compliance checklist

- [x] New harness/analysis are separate files; frozen Phase 4/5 harnesses untouched
- [x] Seed set frozen in this document, drawn and verified before any run
- [x] Three-way criteria frozen per work package; MIXED non-aggregable
- [x] Analysis scripts committed before unblinding (execution step 1, by design PENDING)
- [x] No re-tuning; deviations registered as deviations/amendments
- [x] RANK_SET fixed by content hash, recomputed from artifacts at launch
- [x] Discrepancy rule restated in §5
- [ ] Registry copy of this pre-registration — PENDING (same commit as this doc)

## 8. Registry cross-references

- Experiment A verdict + registered dose-tail question: FLY_LEARN_001_DECISIONS.md
  §"Experiment A outcome"; `results/phase4/wp_l4b_confirm/CONFIRMATORY_VERDICT.json`
- Frozen Phase 5 registration + amendments: `docs/PHASE_5_CONFIRMATORY_PREREG.md`
- Corrected floors claim: claim inventory EXT-5 (REGRESSION); audit EXT-6 check
- Principle: PLASTICITY_LANDSCAPE.md; positioning: PRIOR_ART_MEMO.md
- Dev seed blocks: INFRA-2; confirmatory seeds: Phase 5 prereg §seed set

## 9. Amendments

**Amendment A1 (registered 2026-11-03, BEFORE any Phase 6 run — no
`results/phase6/` training artifacts exist at amendment time; the WP-L6a
oracle is the only Phase 6 process running and consumes only the shadow
block, which is unchanged).** The original seed draw verified expanded seed
spaces with the Phase 5 two-trials-per-cycle expansion, but the L6b harness
runs ONE unlearning trial per cycle (25 train seeds per anchor) and each
probe anchor spans ~2.5k seeds — under the correct L6b formulas the original
10k-wide blocks allowed cross-anchor collisions. Resolution: train/probe
anchors redrawn from `Random(20261103)` over the widened blocks
[1.2M–1.3M) / [1.4M–1.5M) with whole-space collision checks (algorithm in
`scripts/phase6_expB_analysis.py::reproduce_draw`, which must reproduce the
values above exactly). Shadow block unchanged. No criteria, sample sizes,
mechanisms, or RANK_SET hashes changed.

**Amendment A2 (registered 2026-11-03, BEFORE any WP-L6a result exists —
the first oracle run crashed with no report written).** The frozen design
instantiated the non-member class as the 6 `ckpt_l0_gng521_feed_*` checkpoints.
Artifact inspection shows those ckpts carry NO `weights_trial_*.npz` snapshots
(only `history.jsonl` + `run_state.json`; the wp4 v0 save defect). Their
`run_state.weight_hash` equals the pristine matrix hash (`384406e9278ae0c0`),
i.e. the never-learned substrate is unique by construction and equals pristine.
Resolution: non-member class = the pristine matrix, instantiated as
(pristine, seed) rows at the 8 shadow seeds (behavioral variance); member
class = 6 `ckpt_l1_gng521_feed_*` matrices × 4 shadow seeds (24 rows).
Oracle = class-balanced logistic regression over (matrix, seed) rows;
validity gate re-frozen as LOO accuracy ≥ 0.80 AND in-sample member-row
recall = 1.0. Test population, FR definition, ablation, and the three-way
verdict are unchanged.

**Amendment A3 (registered 2026-11-04, BEFORE the wide-oracle run — answers the
open item "oracle bounded by its feature set"; no new training sims, no gate or
threshold changes; script scripts/phase6_l6a_oracle_wide.py, report
results/phase6/wp_l6a/oracle_report_wide_A3.json):**
WP-L6a-A3 reruns the membership oracle with a WIDENED feature set on the same
frozen artifacts (A2 training pool: 6 l1 ckpts x shadow[:4] + 8 pristine rows;
test: 11 unlearned reps x shadow[:4] = 44 rows):
- F1 rank-set edge weights (25, as A2)
- F2 changed-edge stats vs pristine: n, L1, L2, std, max|dw|, frac_positive (6)
- F3 top-8 |dw| over all changed edges, sorted desc (8)
- F4 acquisition/unlearning trajectory: L1(dw) at trial quantiles
  [0.05, 0.2, 0.4, 0.6, 0.8, 1.0] of each ckpt's weights_trial_*.npz, normalized
  by the final L1 (6); pristine/l0 rows (no snapshots) get all-zero F4
- F5 behavior: per-row seed alone/cosugar mn9 (2) + held-out mean over
  shadow[4:] alone/cosugar (2) = 4
Gates and verdict logic identical to A2 (LOO >= 0.80, member recall == 1.0,
row-level FR; per-rep majority also reported). Ablation: drop the 4
residual-edge features as in A2. A3 PASS (FR = 44/44) narrows the oracle
bound to the widened feature set; any FR < 1 is reported as NEGATIVE-A.

None other at freeze (2026-11-03). Amendment policy identical to Phase 5: any
discrepancy found before results exist is registered here as an amendment with
the verifiable no-artifacts-exist evidence; after results exist, no term of
this registration changes — deviations are reported as deviations.
