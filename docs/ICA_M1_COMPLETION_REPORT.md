# ICA-M1-1 Completion Report — Icarus location-encoding qualification (M1-GRIDFETCH)

Repo: fly-cognition. Run base: `be845c0`; deliverables commit below. All
experiments preregistered in `docs/ICA_M1_PREREG.md` before execution; artifacts
in `results/ica_m1/` (separability.json, association.json, probes.jsonl,
launcher_manifest.json with pinned prereg sha, snapshot hash, seeds, API version).

## Integrity statement (assignment §7 — verified, not asserted)

`git diff be845c0..HEAD -- fly/` is **empty**: no change to the learning rule
(`fly/plasticity.py`), dynamics, guard, or training harness. `RETRIEVAL_HZ = 41.5`
unchanged. GNG521 reference cue/protocol unchanged. No stimulus broadening (cue
200 Hz / 1000 ms probes; sugar drive 17 bodies). No weight change was treated as
proof of learning and no activity as proof of location retrieval — verdicts come
from the frozen criteria only.

## Results

- **Phase A** (`ICA_M1_LOCATION_ENCODING_AUDIT.md`): the API accepts arbitrary
  body-id sets as cues without internals changes; 4 gate-passing location-cue
  candidates identified (GNG521/GNG491/GNG557/GNG610). Limitation documented:
  single MN9_L readout — associations distinguishable by cue, not by output
  channel.
- **Phase B** (`ICA_M1_REPRESENTATIONAL_SEPARABILITY.md`): **SEPARABLE** — 4
  location cues produce fully disjoint activation (pairwise cosine/Jaccard = 0.0),
  repeatable across seeds (cos ≥ 0.9991), all location cues innately silent at
  MN9_L, unrelated-cue controls measured (U1 innate 72–79 Hz MN9, U2 silent).
  18/18 probes inside the stability envelope.
- **Phase C** (`ICA_M1_LOCATION_ASSOCIATION_PROTOCOL.md`, n=1 exploratory):
  **DEMONSTRATED** — acquire L_A (GNG521 cue, sugar drive, 20 trials, fresh seed
  base) → 25-edge footprint (sha `43313db60de5c3fa…`); cue-only retrieval
  84.0 Hz ≥ 41.5 (confidence 1.0); wrong cue L_B → 0.0 Hz, not retrieved;
  5 blank trials → weight hash unchanged and retrieval persists; guard silent.
- **n=8 protocol** (`ICA_M1_N8_PROTOCOL_REVIEW.md`): reviewed, NOT executed (no
  authorization). 8 required corrections listed (per-rep probe seeds, exact-
  binomial interval, config fingerprint incl. numpy/scipy versions, seed-space
  disjointness assertion, guard-firing verdict cap, etc.). Hybrid's original n=1
  remains a separate preserved experiment.

## Verdict

**LOCATION MAPPING DEMONSTRATED** — bounded: 4 grid locations mapped to distinct
gate-passing cue populations, measured separable on the pristine substrate, and
one location→association acquired and retrieved cue-only at n=1 with all
controls passing. Scope limits preserved: single-readout retrieval (identity via
cue/association id), n=1 acquisition evidence pending the reviewed n=8, reversal
learning remains NEGATIVE, and no general reasoning/planning/episodic-memory
claims are made. All negative/prior results (P1, reversal, guard on attempt A)
stand unmodified.
