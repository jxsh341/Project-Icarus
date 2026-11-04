# Phase 7b preregistration — P1: predictive structural accessibility on held-out circuits

Frozen 2026-11-03, BEFORE any Phase 7b run. Question (registered from the
2026-11-03 external review, P1): does the accessibility of an association's
acquisition footprint predict whether it can be unlearned — tested on
circuits never used in any prior phase.

## 1. Held-out set selection (screening, frozen seeds, executed pre-freeze)

Candidate pool: the 15 batch-screened cue types (`results/phase2/wp2_cue_probe_batch_candidates.json`).
Gates, per type, on the PRISTINE matrix:
- G1 innate silence: cue-alone @200 Hz, 3 frozen seeds, mn9 == 0 on all.
- G2 expressibility: exists partner j with w+(cue->j) > 0 and w+(j->MN9_L) > 0.
Selection rule: types passing G1+G2, EXCLUDING GNG521/GNG380 (already used in
Phases 2-7), top 3 by convergence C = sum w+(cue->j)*w+(j->MN9_L), ties by name.

P7B_SCREEN_SEEDS = [2216871, 2289316, 2219795, 2279248, 2212879, 2253762, 2280595, 2282997, 2222261, 2255532, 2238927, 2222327, 2286874, 2298281, 2298018, 2299636, 2259783, 2279234, 2240961, 2224173, 2222296, 2203495, 2240261, 2235165, 2244223, 2206315, 2263618, 2208853, 2262597, 2273942, 2224375, 2262900, 2221361, 2273378, 2249497, 2214494, 2265237, 2235188, 2271654, 2256549, 2206121, 2292078, 2267708, 2296334, 2297615]

| type | cue bodyIds | cue-alone mn9 (3 seeds) | G1 | G2 | C |
|---|---|---|---|---|---|
| AN17A015 | [75140] | [0, 0, 0] | G1=pass | G2=pass | 2.0 |
| AN17A024 | [51068] | [0, 0, 0] | G1=pass | G2=pass | 5.0 |
| ANXXX255 | [516239] | [75, 76, 76] | G1=FAIL | G2=pass | 1458.0 |
| ANXXX462a | [19480] | [77, 76, 73] | G1=FAIL | G2=pass | 1140.0 |
| GNG318 | [524428] | [83, 74, 64] | G1=FAIL | G2=FAIL | 0.0 |
| GNG491 | [14094] | [0, 0, 0] | G1=pass | G2=pass | 76.0 |
| GNG521 | [16327] | [0, 0, 0] | G1=pass | G2=pass | 291.0 |
| GNG557 | [12595] | [0, 0, 0] | G1=pass | G2=pass | 276.0 |
| GNG610 | [128102] | [0, 0, 0] | G1=pass | G2=pass | 100.0 |
| GNG611 | [25821] | [0, 0, 0] | G1=pass | G2=pass | 4.0 |
| GNG622 | [32179] | [0, 0, 0] | G1=pass | G2=pass | 10.0 |
| IN05B094 | [800555] | [0, 0, 0] | G1=pass | G2=pass | 8.0 |
| PRW043 | [39767] | [0, 0, 0] | G1=pass | G2=FAIL | 0.0 |
| dorsal_tpGRN | [202063] | [58, 35, 50] | G1=FAIL | G2=pass | 31.0 |
| pIP1 | [10030] | [0, 0, 0] | G1=pass | G2=FAIL | 0.0 |

SELECTED HELD-OUT PAIRS (top 3 by C among passing, excl. GNG521/GNG380):
GNG557 cue=[12595] C=276.00; GNG610 cue=[128102] C=100.00; GNG491 cue=[14094] C=76.00.

## 2. Stages per pair x rep (2 reps per pair)

Harness `scripts/phase7b_harness.py`, HARNESS_SHA256 = "8880081415233dd9a604db2dc956e65da344d6cecde8d62f7292641e363e501a"
(launcher guard G1 before/after every invocation; injection keys
OUT/R1CK/CUE/TRAIN_SEED_BASE/PROBE_SEED_BASE/REPS only).

- acquire: from pristine, 20 trials cue+sugar @200 (feed), probes after
  trials (1,2,3,4,5,10,15,20) x {alone, cosugar} x 2 seeds.
  Acquisition criterion (frozen): cue-alone mn9 >= 41.5 at trial 20 (both
  probe seeds) AND guard silent. Pairs with <1/2 reps acquired are recorded
  as LOCATED NEGATIVES, not silently dropped.
- l6b: rank-targeted decay from the acquired ckpt (rule identical to Phase 6
  RankDecayRule, TAU0=1.0, W_EPS=1e-9), 25 cycles cue-alone, probes at
  cycles 5/10/15/20/25 x {alone, cosugar} x 2.
- l4b: eligibility-then-sign (phase4_eligibility_sign_rule, identical protocol
  to phase4_wp_l4b_extinction), 25 cycles sugar-then-bitter, same probes.

## 3. Census (predictor) per acquired rep

footprint = acquired - pristine nonzero edges (sha256 recorded); partners;
zero-input partners w.r.t. the sugar GRN population (recruiting drive);
z_edges = zero-input-edge fraction of the footprint.

## 4. Run seeds (Random(20261106); all spaces whole-space collision-checked and
disjoint from dev/confirm/P6/P7/screen — prior total 1,999 seeds)

P7B_ACQ_TRAIN = [2401583, 2402894, 2404377, 2407703, 2400250, 2410651]
P7B_ACQ_PROBE = [2413298, 2409127, 2400380, 2400816, 2403708, 2407047]
P7B_L6B_TRAIN = [2508933, 2504498, 2505612, 2510130, 2518959, 2504370]
P7B_L6B_PROBE = [2511107, 2500083, 2516586, 2500176, 2502542, 2518803]
P7B_L4B_TRAIN = [2616468, 2615760, 2616908, 2607600, 2606588, 2602337]
P7B_L4B_PROBE = [2611922, 2613679, 2617865, 2614122, 2602538, 2605200]
P7B_SHADOW = [2813570, 2802932, 2818560, 2809231]

Anchor k (0..5) = pair index*2 + rep, pairs sorted alphabetically
(GNG491, GNG557, GNG610). Spaces: acq_train {b+1..20}; acq_probe
{b + t*100 + r2*10 + off: t in (1,2,3,4,5,10,15,20), r2 in (0,1), off in (0,5000)} u {b+999};
l6b train {b+1..25}; l4b train {b + c*2 + ph: c in 1..25, ph in (0,1)};
unl probe {b + c*100 + r2*10 + off: c in (5,10,15,20,25), r2 in (0,1), off in (0,5000)} u {b+999}.

## 5. Frozen predictions and verdict

Per acquired pair-rep (6 total):
- P1a (accessibility predicts L4b unlearnability): |f_l4b - (1 - z_edges)| <= 0.15,
  where f_l4b = fraction of footprint edges at exact floor after 25 L4b cycles.
  Must hold in >= 5/6 reps.
- P1b (L6b is accessibility-independent): f_l6b >= 0.9 in >= 5/6 reps.
- Behavioral per rep, both mechanisms: c1 cue-alone == 0 at cycles 15/20/25 (both
  seeds); c2 cosugar at cycle 25 within [78, 88] (both seeds); c3 guard silent.
  All must pass on every evaluated rep.

Aggregate: PREDICTIVE-PASS iff >= 2/3 pairs acquired AND P1a AND P1b AND all
behavioral criteria. NEGATIVE-ACQUISITION if <= 1 pair acquired. Otherwise
MIXED (non-aggregating; per-rep outcomes are the result).

## 6. Execution order and guards

1. This prereg frozen+committed. 2. `scripts/phase7b_analysis.py` committed
   BEFORE any run (frozen logic; tests vs pass/mixed/malformed). 3. Launcher
   `scripts/phase7b_launcher.py` guards G1-G7 (see header). 4. Background runs;
   seeds used verified against this doc. 5. Frozen analysis emits
   `results/phase7b/P1_VERDICT.json`. No partial-result interpretation;
   discrepancy -> stop and amend.

Amendments: none at freeze (2026-11-03).
