# ICA-M1-1 preregistration — Phases B (separability) and C (location association)

Frozen 2026-11-11 BEFORE any ICA-M1 run. Repo: fly-cognition @ `be845c0`.
Integrity constraints (assignment §7): learning rule, GNG521 reference protocol,
stability guard, MN9_L threshold (41.5 Hz) all UNCHANGED — verified by git at
close-out. No stimulus broadening: cue rate fixed 200 Hz, 1000 ms probes.

## Phase B — representational separability (pristine substrate, no acquisition)

- Substrate: `FlySubstrate.from_snapshot()` (run-007, pristine hash
  `384406e9278ae0c0` pinned).
- Location cues (4): L_A=GNG521 [15957,16327], L_B=GNG491 [14094],
  L_C=GNG557 [12595], L_D=GNG610 [128102]. Unrelated: U1=GNG318 [524428]
  (innate MN9 active — wrong-cue-with-innate-response control), U2=AN17A015
  [75140] (silent control).
- Probe per (cue, seed): `InputEvent(duration_ms=1000, ports=[cue @200Hz slot1])`,
  via `step()` (no plasticity). 3 seeds per cue, drawn from Random(20261112),
  range 3_400_000–3_420_000, disjoint from all prior seed spaces (prior spaces
  all live in 3_000_000–3_220_000; asserted in the runner).
- Metrics per probe: full spike-count vector, n_spikes, MN9_L Hz, spiking-set,
  1-hop structural footprint of the cue. Pairwise across the 4 location cues:
  Jaccard(spiking sets), cosine(spike-count vectors), |Δ MN9 Hz|. Within-cue
  across seeds: mean pairwise cosine (repeatability).
- Frozen criteria (non-aggregating):
  - c1 active: n_spikes > 100 for every location-cue probe.
  - c2 not aliased: every location-cue pair has Jaccard < 0.8 OR cosine < 0.9.
  - c3 repeatable: within-cue mean cosine >= 0.95 for every location cue.
  - c4 guard silent: n_spikes < 150_000 everywhere.
  - Verdict: SEPARABLE iff c1–c4; else PARTIALLY SEPARABLE / ALIASED with the
    failing pairs listed. U1/U2 reported as measured controls.

## Phase C — location-associated acquisition & retrieval (n=1 exploratory)

- Fresh substrate from snapshot. `learning.arm()` (frozen FROZEN_PLASTICITY).
- `acquire(cue=L_A, drive=sugar_R(17), n_trials=20, seed_base=<fresh>)`.
- Frozen criteria (non-aggregating, n=1):
  - a1 acquire returns id + footprint_sha256 + n_edges > 0; weight_hash changed.
  - a2 guard silent throughout (no LifecycleError).
  - a3 `present_cue(L_A)` → retrieved == True (readout_hz >= 41.5).
  - a4 wrong-cue control: `present_cue(L_B)` (never acquired) → readout_hz < 41.5.
  - a5 retention: 5 blank trials (no ports) → weight_hash unchanged AND
    present_cue(L_A) still retrieved.
- Verdict: DEMONSTRATED iff a1–a5; else PARTIALLY/NOT with failing criteria.
- This is n=1 EXPLORATORY, separate from Hybrid's preserved n=1 probe; the n=8
  protocol is reviewed (ICA_M1_N8_PROTOCOL_REVIEW.md) but NOT executed.

Artifacts: `results/ica_m1/` (separability.json, association.json, probes.jsonl,
launcher_manifest.json). Runner: `scripts/ica_m1_experiment.py` (guards: prereg
sha pinned, seed disjointness, pristine hash, api version).
