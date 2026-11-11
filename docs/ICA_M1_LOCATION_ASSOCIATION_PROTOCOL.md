# ICA-M1-1 Phase C — Location Association Protocol (n=1 exploratory)

Preregistered in `docs/ICA_M1_PREREG.md` (frozen before the run). Executed by
`scripts/ica_m1_experiment.py`; artifacts in `results/ica_m1/association.json`.

## Design (smallest acquisition experiment)

1. Fresh substrate from the run-007 snapshot (pristine hash pinned).
2. Arm the frozen plasticity rule (unchanged: Hebbian V_CLIP, eta=1e-4,
   w_max=766, cue→1-hop, structural edges only).
3. Encode location L_A as cue GNG521 [15957, 16327]; `acquire(cue, drive=
   sugar_R 17 bodies, n_trials=20, seed_base=fresh)` — the API defaults Hybrid's
   n=1 probe already used, with a fresh disjoint seed base.
4. Probes (no plasticity): `present_cue(L_A)` (retrieval), `present_cue(L_B)`
   (wrong-cue control, never acquired), 5 blank trials then `present_cue(L_A)`
   again (retention + weight-hash stability).

## Frozen criteria (non-aggregating)

a1 acquired (id + footprint + weight_hash changed) · a2 guard silent ·
a3 cue-only retrieval ≥ 41.5 Hz (frozen threshold, unchanged) ·
a4 wrong cue < 41.5 Hz · a5 blank-trial retention (hash unchanged + still
retrieved).

## Controls included

No-acquisition baseline = Phase B probes on the pristine substrate (same cues,
same rates). Incorrect cue = L_B probe post-acquisition. Acquisition-disabled
= Phase B itself (probes never learn; `step` applies no plasticity).
Shuffled location→cue mapping and unrelated cue = Phase B U1/U2 measurements.

## Explicitly out of scope

The Hybrid n=8 multi-repetition protocol is REVIEWED in
`ICA_M1_N8_PROTOCOL_REVIEW.md` and NOT executed here (no authorization).
Hybrid's original n=1 probe remains a separate preserved experiment.
