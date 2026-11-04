# Phase 7 P5 preregistration — footprint-estimation sensitivity of selective erasure

Frozen 2026-11-04, BEFORE any P5 run. Question (open item: "rank-decay assumes
the known footprint"): how sensitive is erasure of memory A (GNG521, frozen
R1CK) to HOW the footprint is estimated? Three arms x 2 reps, all on the same
frozen R1CK (rank-A sha256 43313db6...f2589 pinned), fast analytic rank-decay
(tau=1.0, 25 cycles, W_EPS=1e-9 — bit-identity validated in P3 tests),
probes at cycles (5,15,25) x {aloneA, cosA} x 2 seeds.

## 1. Arms (edge sets computed deterministically from pristine + R1CK, sha-pinned)

- A_TRUE   : true footprint = acquired(R1CK final) - pristine, 25 edges,
             RANK_TRUE_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"
- B_THRESH4: estimated footprint = edges with acquisition-window |dw| >= 4.0
             (weights_trial_0030 - weights_trial_0001), 21 edges, misses the 4
             weakest true edges; RANK_THRESH4_SHA256 = "126304c7ebca532f344d97700f6677481e58cd30ad127e7ab0cac9f8b70d80e9"
- C_HOP1   : over-inclusive estimate = ALL edges incident (either direction)
             to cue-A nodes [15957, 16327], 112 edges (25 memory + 87 other);
             RANK_HOP1_SHA256 = "2f23a911609700f2ab327588dcf7b6de4112c1c1398dc8ba110e2c4c3864b092"

## 2. Seeds (Random(20261111); disjoint from ALL prior incl. P4/P4b spaces)

P5_PROBE_BASES = [3214562, 3208777, 3211318, 3205129, 3215016, 3210286]
probe space {b+100c+10p+s: c in (5,15,25), p in (0,1), s in (0,1)} = 12 seeds/rep.
Rep -> arm map: r0,r1 = true; r2,r3 = thresh4; r4,r5 = hop1.

## 3. Frozen criteria (non-aggregating; per-arm verdicts are the result)

Per rep: aloneA25 (2 seeds), cosA25 (2 seeds), guard silent (c5; any guard
firing invalidates the rep, reported not hidden).
- Arm A_TRUE: PASS iff aloneA25 == 0 (both seeds, both reps) AND all cosA25
  in [75, 95]. (Reference: re-confirms P4 c1/c4 on this probe grid.)
- Arm B_THRESH4: SENSITIVE iff any aloneA25 > 0 (missed weak edges leave
  residual memory); else INSENSITIVE-TO-WEAK-EDGES. cosA25 reported vs band.
- Arm C_HOP1: COLLATERAL iff any cosA25 outside [75, 95] (over-inclusive decay
  damages innate response); else CLEAN. aloneA25 reported.
Verdict -> results/phase7p5/P5_VERDICT.json. Harness sha pinned: HARNESS_SHA256 = "6d34d43549c458956b9be7237c9adb572b8b75654a90d85383532fc3d6b5641d" Discrepancy -> stop and document.

Amendments: none at freeze (2026-11-04).
