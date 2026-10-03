# Pre-registered reliability / completeness thresholds (corrected 2026-10-03)

**Status:** corrected arithmetic applied before freeze. The 63-cell count was stale — it reflected the pre-S2-404-valid-population total (120 valid cells), not the current 113-cell population. All 7 pulled S2-404 cells were state-present; removing them from 120 drops state-present from 63 to 56.

**Current measured baseline (verified on 113 valid cells):**
- Silent failures: 57 / 113 = 50.4%
- State-present: 56 / 113 = 49.6%  (corrected from 63)
- Old reconciliation check (57 + 63 = 120) confirmed the error — that sum equals the old total, not 113.

**Projected pipeline-clean (pipeline-clean = reliability × completeness):**
- Current baseline (using current measured reliability/completeness factor 66%): 56/113 × 0.66 ≈ **33%** (corrected from 37%).
- Registered minimum bar (pre-registered 65% pipeline-clean × 48% deployed-rate): 0.65 × 0.48 ≈ **31% deployed** (≈1.0× vs corrected 33% baseline; NOT 2.5×).
- Stretch / optimistic (77% pipeline-clean × 48% deployed-rate): 0.77 × 0.48 ≈ **37% deployed** (≈2.3× vs corrected 33% baseline).

**Rule:** present both numbers separately — minimum-bar projection and stretch-case projection — never merge them into a single headline.

**Thresholds pre-registered (falsifiable):**
- Spontaneous-activity guard: >5 Hz network-wide = instability (frozen; WP6c 0/30 control confirms ceiling).
- Pathological-reference guard: >150K spikes in any 1 s trial = instability (frozen; 618K reference, 4× sugar+bitter max).
- E/I weight-drift guard: >20% change in total |inhibitory weight| from frozen census (32.7% of edges) = instability.
- Decision-boundary regression guard: L0 must reproduce WP9 boundary exactly; any deviation = halt.

**Reliability-first work order (gates completeness measurement):**
1. Run-checkpointing: `run.save()` after EVERY simulation; `TrainingRun.load()` at block start with hash verification. (WP4 v0 root cause: weight state never checkpointed; 24 completed blocks ≈10 h compute discarded.)
2. Seed disjointness: new scheme must have 0 overlaps with all prior stages and 0 internal collisions; verified by computation before launch.
3. Probe purity: `is_probe` must not apply plasticity; hash unchanged through probe; N-probes accumulation test.
4. Per-trial JSONL checkpointing (already adopted; verified by 7/7 I/O tests, suite 98/98).

**Verification targets (cheapest first):**
- Tests: `tests/test_lif.py`, `tests/test_plasticity.py`, `tests/test_wp4_io_persistence.py` (resume + hash + accumulation).
- Evidence artifacts: `results/phase2/wp4_seed_audit.json` (disjointness), `run_state.json` + weight `.npz` (checkpoint presence), `stage_b_eta_v2.jsonl` (accumulated matrices present post-probe).
