# Phase 7 P3 preregistration — graded unlearning: rank-decay dose sweep on GNG521

Frozen 2026-11-04, BEFORE any P3 run. Question (Phase 7 order, after E1):
how do behavioral extinction and synaptic floor fraction scale with the
rank-decay dose (tau x cycles)? Rank decay is deterministic and
sim-independent (observe is a no-op; apply is w <- w*e^(-1/tau) with W_EPS
snap on the rank set), so predictions are analytic and exact; the fast
harness sims ONLY at probe cycles (validated bit-identical vs full
per-cycle sims in tests/test_phase7p3.py).

## 1. Design

Base: frozen R1CK `results/phase2/taskB_r1/ckpt_l1_gng521_feed_0`.
Rank set = ckpt - pristine nonzero edges (25; sha256 pinned
43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589, enforced in
harness and analysis).
16 reps: tau in (0.5, 1.0, 2.0, 4.0), rep r -> level r % 4. N_CYCLES = 25.
Probe cycles: alone at (5, 15, 25) x 2 seeds; cosugar at (25,) x 2 seeds.
(8 sims/rep instead of 45; probes registered at 3 cycle points because the
floor fraction is monotone in cycles.)

Harness `scripts/phase7p3_harness.py`, HARNESS_SHA256 = "bfa08c633b6252dafc2556e3c864b3b59a4e3be5332c9aab8a4ef986d7aadd51"
(launcher guard G1 before/after every invocation; injection keys
OUT/REPS/PROBE_BASE/TAU/MODE only). Modes: fast (analytic decay between
probe cycles) and full (per-cycle sim + decay, validation only).

## 2. Seeds (Random(20261108); 128 seeds, whole-space disjoint from all
3,167 prior seeds: dev/confirm/P6/P7/screen/P7B/E1)

P3_PROBE_BASES = [3010727, 3014764, 3007310, 3009771, 3012638, 3018165, 3000483, 3017981, 3013933, 3002659, 3013916, 3003576, 3000019, 3012238, 3009738, 3013224]

Probe space per base b: {b + 100*c + s: c in (5,15,25), s in (0,1)} u
{b + 1000 + s: s in (0,1)} (8 seeds).

## 3. Frozen criteria (per rep)

- c1 weight hash at every probe == hash of analytic decay
  w0*e^(-c/tau) snapped at W_EPS=1e-9 (exact equality).
- c2 alone mn9 at cycle 25 == 0 (both seeds) AND alone mn9 non-increasing
  across cycles 5 -> 15 -> 25 (per seed).
- c3 cosugar mn9 at cycle 25 within [75, 95] (both seeds; measured innate
  range across phases 77-92).
- c4 guard silent on all probe sims.
- c5 measured final floor fraction == analytic f_pred(25) exactly.

Aggregate PASS iff 16/16 reps pass; otherwise MIXED (non-aggregating;
per-rep table is the result). Discrepancy vs prereg -> stop and amend.

Amendments: none at freeze (2026-11-04).
