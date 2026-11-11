# ICA-M1-1 Phase B — Representational Separability (measured)

Prereg: `docs/ICA_M1_PREREG.md` (frozen pre-run, sha pinned in
`results/ica_m1/launcher_manifest.json`). Artifacts: `results/ica_m1/separability.json`,
`probes.jsonl` (18 probes). Substrate: run-007 pristine (`384406e9278ae0c0`),
no acquisition anywhere in Phase B. 4 location cues × 3 fresh seeds each
(Random(20261112), space 3.4M–3.42M, disjoint from all prior seed spaces).

## Measured results

| cue | type | n_spikes (3 seeds) | MN9_L Hz (3 seeds) |
|---|---|---|---|
| L_A | GNG521 [15957,16327] | 488, 533, 437 | 0, 0, 0 |
| L_B | GNG491 [14094] | 287, 295, 263 | 0, 0, 0 |
| L_C | GNG557 [12595] | 213, 197, 203 | 0, 0, 0 |
| L_D | GNG610 [128102] | 415, 503, 547 | 0, 0, 0 |
| U1 | GNG318 [524428] (unrelated) | 8990, 8668, 8531 | 79, 72, 74 |
| U2 | AN17A015 [75140] (unrelated) | 208, 204, 218 | 0, 0, 0 |

Pairwise across the 4 location cues (all 6 pairs, all seed combinations):
**cosine = 0.0 and Jaccard = 0.0 everywhere** — the cues activate fully disjoint
neuron populations. Within-cue repeatability across seeds: cosine 0.9991–1.0.

## Frozen criteria

- c1 active (n_spikes > 100): PASS all location probes (197–547).
- c2 not aliased (every pair max-Jaccard < 0.8 or max-cosine < 0.9): PASS
  (both are 0.0).
- c3 repeatable (within-cue mean cosine ≥ 0.95): PASS (≥ 0.9991).
- c4 guard silent (n_spikes < 150k): PASS (max 8,990, on U1).

**Verdict: SEPARABLE.** Measured from the substrate's actual spike sets, not
from location identifiers. Controls behave as designed: unrelated U1 has an
innate MN9 response (72–79 Hz) with no acquisition — proof that MN9 activity
alone is not retrieval; U2 is silent.

## Interpretation bound

Pre-acquisition, the four location cues are innately silent at the MN9_L readout
(0 Hz) — separability lives in the population activation pattern. The single
MN9_L readout can only signal "retrieved / not"; location identity is carried by
which cue/association id was presented (caller-side mapping), not by the
readout value itself.
