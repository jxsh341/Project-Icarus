# Phase 7 preregistration — WP-P2: GNG380 confirmatory unlearning (rank-targeted decay)

Frozen 2026-11-03, BEFORE any Phase 7 run. Commit point: parent of this file's
first commit. Any discrepancy between this document and the execution
environment/artifacts -> STOP and register an amendment; never silently repair.

## 1. Objective

Phase 6's GNG380 probe (n=2, exploratory per `docs/PHASE_6_PREREG.md` WP-L6b)
found: 77/96 zero-input edges at floor, 136/158 footprint edges at floor,
guard silent, cosugar (cue+sugar) 80-86 Hz at every probe point from cycle 5,
cue-alone 0 Hz. WP-P2 is the CONFIRMATORY replication: n=8 fresh frozen seeds,
with behavioral criteria frozen in advance, testing whether drive-independent
rank-targeted decay unlearns the GNG380 withhold association while preserving
the innate pathways.

## 2. Baselines (measured 2026-11-03 on the acquired R1 ckpt
`results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0`, probe seed 3999999,
1000 ms, r_poisson_Hz=200):

| probe | mn9_hz |
|---|---|
| cue (GNG380 6 GRNs) alone | 0 |
| cue + sugar @200 | 1 (< 41.5: withhold suppression, matches acquisition criterion) |
| sugar alone @200 | 81 |
| cue + bitter @200 | 0 |

Reference boundary (Phase 4 census, re-verified by analysis): 158 footprint
edges, 73 partners, 45 zero-input partners, 96 zero-input edges.

## 3. Protocol (harness byte-frozen, reused unchanged)

- Harness: `scripts/phase6_wp_l6b_rankforget.py`, sha256
  `08110ddfb2ae3b2a89782c4a48b4bd5e4a52f9f171febb8b91236dcd28427508`
  (launcher guard G1 verifies before AND after every rep).
- `L6B_TARGET=g380`; start ckpt `ckpt_l1_gng380_withhold_0`; RANK_SET =
  158-edge footprint, sha256
  `27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a`
  (harness self-checks at every launch).
- Per rep: 25 cycles, one cue-alone trial @200 Hz per cycle (seed
  TRAIN_SEED_BASE + cyc), then w <- w*e^(-1/TAU0), TAU0=1.0, W_EPS=1e-9 snap;
  probes at cycles 5/10/15/20/25 x {alone, cosugar} x 2 rep2 (probe seeds
  PROBE_SEED_BASE + cyc*100 + r2*10 + off, off 0=alone / 5000=cosugar).
- REPS=8, OUT=results/phase7/p2_g380/rep_r{r} injected in memory only.

## 4. Seeds (drawn from random.Random(20261104); spaces disjoint from dev
(211), confirmatory (697) and all Phase 6 (523) spaces — 1,431 prior seeds)

P7_TRAIN_SEEDS = [1697083, 1682813, 1627400, 1642332, 1648603, 1665375, 1677507, 1602650]
P7_PROBE_SEEDS = [1829889, 1850768, 1800854, 1885113, 1870982, 1876815, 1881164, 1890843, 1809651, 1859953, 1849235, 1803714, 1858755, 1889545, 1821002]
P7_SHADOW_SEEDS = [2071733, 2061762, 2092505, 2031367, 2015119, 2037455, 2090298, 2038162]

Train space per anchor: {base+c, c=1..25} (200 total). Probe space per
anchor: {base + c*100 + r2*10 + off : c in (5,10,15,20,25), r2 in (0,1),
off in (0,5000)} u {base+999} (315 total). Shadow: the 8 seeds themselves,
reserved for analysis-time probes only.

## 5. Per-rep criteria (frozen) and verdict branches

Let cosugar(c) = the 2 mn9_hz values at probe cycle c in {5,10,15,20,25};
alone(c) likewise. Final matrix = rep ckpt_r0 final weights. Analysis-time
probes on the final matrix: sugar-alone and cue+bitter, 2 seeds each from
P7_SHADOW_SEEDS[0..3] (sugar: shadow[0], shadow[1]; bitter: shadow[2],
shadow[3]).

- c1 behavioral recovery: every cosugar value at cycles 15, 20, 25 >= 41.5 (6/6).
- c2 innate restoration: both cosugar values at cycle 25 within [78, 88].
- c3 innate pathways intact: both sugar-alone probes in [78, 88] AND both
  cue+bitter probes < 41.5.
- c4 guard silent: no cycle row has guard_fired.
- c5 weight floors: zero-input edges at floor >= 75 of 96 AND footprint
  edges at floor >= 130 of 158.
- c6 structure: no sign flips on footprint edges vs acquired; no new nonzero
  edges outside (pristine-nonzero u acquired-footprint).

Branch per rep: PASS iff c1..c6 all true. Else NEGATIVE-A if any of
c1/c2/c5/c6 fails; NEGATIVE-B if any of c3/c4 fails; both -> NEGATIVE-A+NEGATIVE-B.
Aggregate: PASS iff 8/8 PASS; NEGATIVE-* iff 8/8 share one negative branch;
otherwise MIXED. MIXED is non-aggregating: per-rep branches are the result,
never promoted.

## 6. Execution order and guards (same discipline as Phase 5/6)

1. This prereg frozen and committed. 2. Analysis script
   `scripts/phase7_p2_analysis.py` committed BEFORE any run (verdict logic
   frozen; tests vs positive/negative/mixed/malformed). 3. Launcher
   `scripts/phase7_p2_launcher.py` with guards G1 harness sha, G2 injection
   keys only {TRAIN_SEED_BASE, PROBE_SEED_BASE, REPS, OUT}, G3 P7 spaces
   collision-free and disjoint from dev+confirm+Phase6, G4 output root holds
   only known artifacts (complete reps skipped, incomplete quarantined),
   G5 OUT never a dev/confirm/phase4/phase6 dir, G6 prereg anchors reproduce
   from the Random(20261104) draw, G7 cwd = repo root. 4. Run reps in
   background; verify actual seeds used against this document. 5. Frozen
   analysis emits `results/phase7/p2_g380/P2_VERDICT.json`. No partial-result
   interpretation; raw outputs, per-seed results, weight hashes, manifest and
   logs preserved.

## 7. Queued after WP-P2 (proposed, not preregistered): P1 predictive
structural accessibility on held-out circuits; E1 closed-loop learning in the
embodiment scaffold; P3 graded unlearning dose curves; P4 multi-memory
interference / selective removal.

Amendments: none at freeze (2026-11-03).
