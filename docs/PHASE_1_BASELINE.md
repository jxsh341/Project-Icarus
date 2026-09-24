# Phase 1 Baseline

This document defines the implementation scope of `FLY-BASE-001`.

## Objective

Build a reproducible, validated computational baseline from official MaleCNS data before any cognitive augmentation.

## Rules

- Reproduce first. Modify later.
- Use official biological sources as structural truth.
- Preserve provenance for data, parameters, and results.
- Freeze the baseline once validation passes.

## Initial milestones

1. Environment setup and repository scaffolding
2. Dataset pinning and provenance capture
3. Connectome loader and structural validation
4. Reference LIF implementation
5. Published experiment reproduction
6. Baseline benchmarks and freeze

## Work-package registry

- **WP10** — DONE: computational cost baseline
  (`validation/reference/wp10_compute_baseline.json`). Profile: run-006
  4,552 steps/s (0.46× bio-realtime, 81 MB RSS); run-007 2,213 steps/s
  (0.24×, 73 MB — denser driven activity keeps the kick pipeline full).
  Archive wall-clock/storage for all completed runs. GPU/energy recorded
  N/A with reasons. psutil added as runtime dep.
- **WP8v2** — DONE: signed-connectome benchmarks (run-006 + run-007,
  n=30 each, checkpointed). spontaneous 0/30 (clean control);
  stimulus_response 298.8±20.6 spikes/s in 2 spikers (GABAergic
  suppression at benchmark scale); circuit_propagation genuine
  measured cliff (inhibitory seeds don't recruit; supersedes run-005's
  structural zero); sugar_recruitment 411.5±9.4 neurons (1.02%,
  bounded excitatory recruitment). Supersedes all run-005 unsigned
  benchmark numbers. Report:
  `validation/reference/wp8_benchmarks_v2_summary.json`.
- **WP6a** — DONE (commit ebf0f43, audit 6535713/12ec79f): implementation
  parity vs the Shiu reference on run-005 (unsigned inputs; valid as an
  implementation check, superseded biologically by WP6b).
- **WP6b** — DONE: signed-connectome reproduction on run-006
  (male-cns:v0.9, depth-2 closure). Both arms on identical signed
  inputs; diff +0.27%, TOST equivalent within ±10%, Spearman ρ = 0.9999.
  Report: `validation/reference/wp6b_signed_head_to_head.json`.
- **WP6c** — DONE (external anchor for the NT-sign convention): the
  sugar/bitter feeding experiment (Shiu et al. 2024 Fig 3a directional
  prediction) reproduced on run-007 (GRN-seeded depth-2 closure,
  male-cns:v0.9). Signed convention: bitter co-drive suppresses
  sugar-driven MN9 (40.6 → 0.0 Hz), matching the paper. Both ablated
  conventions fail to reproduce it (abl-glu +1.5 Hz, all-pos +0.5 Hz),
  and the glutamate-specific ablation shows GABA alone is insufficient
  — glutamatergic inhibition is specifically required. The NT→sign
  convention is now anchored to published biology, not convention alone.
  Report: `validation/reference/wp6c_sign_behavioral_anchor.json`.
  Limitations (population mapping is literature-based; directionality,
  not rate matching; MN9 is a circuit proxy) recorded in the report.

