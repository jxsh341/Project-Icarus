# Phase 7 E1 preregistration — closed-loop conditioning on the embodiment scaffold

Frozen 2026-11-04, BEFORE any E1 run. Question (Phase 7 order: E1 after P1):
in the closed sensorimotor loop (`fly/embodiment/`, verified bit-identical
to the frozen `simulate_lif`), can the substrate acquire a predictive
cue -> proboscis-extension association such that the loop closes
autonomously — cue alone drives MN9_L >= 41.5 Hz, extension reaches
contact (>= 0.5), and sugar (present in the world but transduced only on
contact) becomes detected?

## 1. Design (paired, identical seeds across arms)

Arms: `learn` (Hebbian window-1 leg-1 rate-form plasticity applied per 1 s
step, identical rule/config/guard to phase-2 acquisition) vs `control`
(plasticity disabled, probe-only). 4 reps per arm, same seeds per rep.

Per rep:
- Taste: 8 episodes x 3 steps (1 s each). Episode starts proboscis
  EXTENDED (ext=1.0), cue_on, sugar_present -> sugar transduced.
- Probes (proboscis retracted, ext=0):
  - `alone`: cue_on, no sugar, 2 steps x 2 seeds — primary readout.
  - `closed`: cue_on + sugar_present, 3 steps x 2 seeds — loop-closure readout.
  - `sugonly`: sugar_present, no cue, 2 steps x 1 seed — negative control.

Harness `scripts/phase7e1_harness.py`, HARNESS_SHA256 = "58114c9b88a1492b8ce4c4174f70cc87132729919753f87bbbc4e3c56235b93d"
(launcher guard G1 before/after every invocation; injection keys
OUT/REPS/TASTE_BASE/PROBE_BASE only). Frozen sim via the embodiment ports
(stimulated/stimulated2/stimulated3); per-step seeds; footprint (post-taste
diff edges + sha256) dumped per rep.

## 2. Seeds (Random(20261107); whole-space disjoint from all 3,023 prior seeds:
dev+confirm+P6+P7+screen+P7B)

E1_TASTE_BASES = [2918500, 2912461, 2914467, 2901121]
E1_PROBE_BASES = [2904911, 2919923, 2910234, 2907990]

Spaces: taste {b+1..24}; probe {b+1000..b+1011} (alone: p+ s*10+k,
s in 0..1, k in 0..1; closed: p+20+s*10+k, s in 0..1, k in 0..2;
sugonly: p+40, p+41).

## 3. Frozen criteria

- c0 taste sanity: learn arm, every taste episode step-0 sugar_detected
  True; guard silent in both arms, all rows.
- c1 primary: learn arm `alone` step-1 mn9 >= 41.5 Hz in >= 3/4 reps (both
  probe seeds each); control < 41.5 in 4/4 reps.
- c2 loop closure: `closed` probe reaches sugar_detected True by step <= 2
  in >= 3/4 learn reps; 0/4 control reps any detection.
- c3 structure: control post-taste weight hash == pristine (384406e9278ae0c0);
  learn footprint non-empty and every changed edge is a cue 1-hop edge.

Aggregate: PASS iff c0-c3 all hold; otherwise MIXED (non-aggregating; the
per-rep table is the result). No partial-result interpretation; any
discrepancy vs this prereg -> stop and amend before running.

Amendments: none at freeze (2026-11-04).
