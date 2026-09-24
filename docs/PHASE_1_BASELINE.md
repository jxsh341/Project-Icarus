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

- **WP6a** — DONE (commit ebf0f43, audit 6535713/12ec79f): implementation
  parity vs the Shiu reference on run-005 (unsigned inputs; valid as an
  implementation check, superseded biologically by WP6b).
- **WP6b** — DONE: signed-connectome reproduction on run-006
  (male-cns:v0.9, depth-2 closure). Both arms on identical signed
  inputs; diff +0.27%, TOST equivalent within ±10%, Spearman ρ = 0.9999.
  Report: `validation/reference/wp6b_signed_head_to_head.json`.
- **WP6c** — OPEN (external anchor for the NT-sign convention): reproduce
  a published behavioral experiment from Shiu et al. (feeding or
  antennal grooming; drive sugar-sensing gustatory or mechanosensory
  neurons) on the MaleCNS signed connectome. The standard NT→sign
  convention (ACh +, GABA/glutamate −) is currently convention-inferred;
  this experiment tests it against published biology. Blocks treating
  sign-affected benchmark numbers as ground truth; does not block WP8
  mechanical benchmarking.

