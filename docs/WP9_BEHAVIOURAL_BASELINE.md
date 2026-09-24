# WP9 — Behavioural Baseline: Taste-Driven Action Selection

**Status:** SCOPED (defined from validated substrate properties; not yet implemented)
**Plan anchor:** FLY-BASE-001 §16 task 8 — "Action selection under competing stimuli"
**Substrate:** run-007 GRN-seeded closure (40,290 neurons, 336,245 signed edges, male-cns:v0.9), WP6b/6c-validated

## Why this task (scoping rationale, evidence-based)

The validated substrate does NOT support arbitrary behavior. Measured properties:
- Excitatory sensory drive → bounded local recruitment (17 GRNs → 411.5 ± 9.4 neurons, 1.02%)
  [WP8 sugar_recruitment, n=30]
- Bitter-only aversive drive → recruitment WITHOUT motor output (597 ± 3 spiking,
  MN9_L literal 0 spikes; composition 406 cb_intrinsic / 37 descending / 31
  ascending / 12 endocrine / 63 cb_sensory / 24 sensory_ascending — an
  aversive-state network, not a motor program) [probe n=5, this scoping pass]
- Sugar and bitter programs overlap in only 65/~500 neurons — distinct programs
- Sugar and bitter programs overlap in only 65/~500 neurons — distinct programs
- No endogenous activity (0/30 spontaneous) — all activity attributable to drive
- MN9_L is the paper-validated feeding readout (WP6c: 81.3 Hz sugar → 0.0 bitter)

Navigation/foraging tasks would assume spatial representations that no validated
component here provides. The smallest task this circuit demonstrably supports is a
**decision**: which motor program wins under competing sensory drives.

## Environment

- **Stimulus space:** sugar-GRN drive rate r_sugar ∈ [0, 200] Hz; bitter-GRN drive
  rate r_bitter ∈ [0, 200] Hz (two-population Poisson via `stimulated`/
  `stimulated2`, validated semantics).
- **Dynamics:** the signed connectome, `simulate_lif` (WP6b-verified vs Shiu
  reference; TOST-equivalent, ρ=0.9999).
- **Episode:** single 1,000 ms trial (one decision window; steady-state readout).
- **Not modeled (recorded N/A with reasons):** real-time wall-clock interaction
  (sim/bio ratio 0.24–0.46× — batch protocol only), spatial environment,
  locomotion. The WP10 measurement stands: interactive loops are infeasible at
  these closure sizes without a faster inner loop; WP9 is event-driven batch.

## Initial state

All neurons at `LIFParams` defaults (v = v_rest, g = 0); silent baseline verified
(0 spikes in 30/30 spontaneous trials). No hidden state between trials.

## Observations (what the agent-perspective observer sees)

Network spike trains over the trial. For analysis: per-neuron firing rates,
first-spike latencies, population recruitment counts.

## Action space / behavioral readout

The connectome's action space is its motor output (the fly has no arbitrary
action vocabulary in this formulation):
- **Feed:** MN9_L rate ≥ threshold θ_feed (proboscis-extension program active;
  MN11D_R/MN4b_R as corroborating readouts)
- **Withhold (reject):** MN9_L < θ_feed (feeding program suppressed)
- Threshold θ_feed pre-specified from the sugar-only distribution (WP8
  sugar_recruitment n=30: 82.2 ± 1.6 Hz; θ_feed = 40 Hz, the midline between
  the bimodal sugar/bitter regimes: sugar-only 81.3–82.2 Hz vs bitter
  co-drive 0.0 Hz, WP6c + WP8)

## Reward / objective (experimenter-side, not injected into the network)

- **Success:** network selects the biologically correct action for the stimulus:
  sugar-dominant → feed; bitter-dominant or mixed at aversive ratios → withhold.
- **Quantitative target:** a decision boundary in (r_sugar, r_bitter) space,
  mapped by sweeping the drive grid, with correct-side accuracy.
- No reward signal enters the network (baseline behavior only — no learning,
  no plasticity; that is the frozen-baseline point).

## Test protocol

1. Sweep the (r_sugar, r_bitter) drive grid (the paper's own 11×11 protocol
   cell 23–24, 0–200 Hz in 20 Hz steps), n=10 seeds/cell, checkpointed.
2. Derive the empirical decision boundary from MN9_L response.
3. Generalization probe: off-grid ratios, left-out seeds.
4. Competing-drives dynamics: simultaneous onset vs staggered onset
   (bitter arrives 200 ms into a sugar trial — suppression latency measured).
5. Null controls: spontaneous (no drive) → withhold by construction;
   driven-but-silent MN9_R stays 0 (structural, already explained).

## Success metric

- Boundary sharpness: |Δ MN9_L rate| across the boundary vs within-region
  variance (expect ≥ 2 orders of magnitude from WP6c: 81.3 Hz vs 0.0 Hz).
- Behavioral accuracy on the labeled grid: fraction of cells classified
  correctly against the biological ground truth (sugar-pure → feed;
   any-bitter-dominant → withhold; the paper's Fig 3a direction).
- Suppression latency under staggered onset (ms from bitter onset to
  MN9_L silence).

## What WP9 does NOT claim

- No learning, no plasticity, no reward-modulated changes (frozen baseline).
- No spatial navigation, no locomotor dynamics — motor-program selection only.
- Not a claim that the fly's bitter response is only withholding; the closure
  contains aversive-state machinery (endocrine DMS, descendings) whose
  downstream effectors (VNC-side) are outside this brain closure. Recorded
  as a scope boundary, not a failure.

## Open items before implementation

- [ ] Grid sweep run (11×11 × 10 seeds, checkpointed — ~4 h at WP6c per-trial
      cost on the signed arm; the mixed cells will be slower than sugar-only)
- [ ] Decision-boundary extraction + θ_feed calibration from the sugar-only
      distribution
- [ ] Staggered-onset timing protocol (needs a delayed-drive capability:
      sugar from t=0, bitter from t=200 ms — small `simulate_lif` extension,
      TDD)
- [ ] WP9 report: boundary map, accuracy, latencies, limitations
