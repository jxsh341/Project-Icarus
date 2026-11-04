# Phase 7 P4 preregistration — multi-memory interference / selective removal

Frozen 2026-11-04, BEFORE any P4 run. Question (final Phase 7 item): can one
acquired association be erased without disturbing another on the same
substrate? Cue A = GNG521 [15957, 16327] (frozen R1CK, 25-edge solo
footprint, sha256 43313db6...f2589 pinned); cue B = GNG491 [14094]
(held-out circuit that acquired cleanly in P1, 37-edge solo footprint sha
d27905a1...). Measured pre-freeze: the two solo footprints are DISJOINT
(overlap = 0 edges), so the frozen prediction is perfect selectivity.

## 1. Design (4 reps)

Per rep, harness `scripts/phase7p4_harness.py`, HARNESS_SHA256 = "f044cd07097457ccc084fa9c827c0ac9ada95f68717d4fcfae2864f7697f9de9":
- acq: load R1CK (memory A present), 8 trials cueB+sugar feed (seeds
  ACQ_BASE+1..8), acquisition probes aloneA/aloneB (2 seeds each,
  ACQ_BASE+100+s). Combined matrix saved; footprints dumped (combined vs
  pristine, B-added = combined vs R1CK, overlap check == 0 enforced).
- unlearn: fast analytic rank-decay of A's 25 solo edges (tau=1.0, 25
  cycles, W_EPS=1e-9 snap; sim-independent decay validated bit-identical in
  P3 tests), probes at cycles (5,15,25) x {aloneA, aloneB, cosA, cosB} x 2
  seeds (UNL_BASE+1000+100c+10p+s). Rank-A final weights + B-edge
  before/after dumped.

## 2. Seeds (Random(20261109); 136 seeds, whole-space disjoint from all 3,295
prior seeds: dev/confirm/P6/P7/screen/P7B/E1/P3)

P4_ACQ_BASES = [3206018, 3201559, 3216050, 3209507]
P4_UNL_BASES = [3213898, 3212168, 3205975, 3200267]

acq space {b+1..8} u {b+100, b+101}; unl space
{b+1000+100c+10p+s: c in (5,15,25), p in 0..3, s in (0,1)}.

## 3. Frozen criteria

- c0 both memories acquired: acq probes aloneA >= 41.5 AND aloneB >= 41.5
  (both seeds), 4/4 reps, guard silent.
- c1 selective erasure: aloneA mn9 == 0 at cycle 25 (both seeds), all reps.
- c2 memory B survives: aloneB mn9 >= 41.5 at cycle 25 in >= 3/4 reps.
- c3 structure: A-solo edges at exact floor == analytic f_pred(25)
  (w0*e^(-25) < 1e-9 per edge); B-added edges bit-unchanged (b_unchanged).
- c4 innate intact: cosA and cosB at cycle 25 within [75, 95], all seeds.
- c5 guard silent on all rows.

Aggregate PASS iff c0-c5; otherwise MIXED (non-aggregating; per-rep table is
the result). Discrepancy -> stop and amend.

Amendments: none at freeze (2026-11-04).
