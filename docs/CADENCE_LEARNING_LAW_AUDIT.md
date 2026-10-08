# Cadence Learning-Law Source Audit — Investigation 01, Deliverable 2

**Project:** FLY-LEARN-001 (pre-Gate 2 research) | **Date:** 2026-10-08
**Source:** muellerberndt/cadence @ main (cloned read-only to scratch; GPL-3.0 — evaluation; clean-room rule REGISTERED in decisions registry BEFORE this audit and observed throughout: this document describes the law for understanding only; no variable names, control flow, or formulation choices herein may serve as a template for any fly-cognition implementation)
**Files read in full:** `src/cadence/plasticity.py` (1039 lines — ActorCritic, Valence, Bins), `src/cadence/learning.py` (rule header + contrast/apply semantics)

---

## The law, as implemented

Cadence's reward learning is a **three-factor rule** — per-synapse eligibility trace × broadcast dopamine (TD error) — on top of a **contrastive-Hebbian** supervised rule (free/nudged equilibrium settling; the equilibrium-propagation family):

```
e[e]    ← γ·λ·e[e] + contrast[e]          (per-synapse eligibility)
δ       =  r + γ·V(s′) − V(s)             (critic's TD error)
scale[e] += η · δ · e[e]                  (three-factor update)
```

The eligibility source is the **free/nudged contrast** — the difference between two settled equilibrium phases (output-nudged minus free), read per synapse from its two endpoints' activations. The critic is a separate linear readout of a designated neuron population, trained by its own trace and the TD error. The dopamine passes through a `Valence` transform: running-mean centering (phasic = deviation from tonic level), a noise floor, a cap, optional running-scale normalization. One life, one pass — no replay buffer, no epochs.

## The four audit questions, answered from source

**Q1 — Locality.** *Per-synapse local + one broadcast scalar.* The contrast reading is strictly local (two endpoint activations per synapse — "as local as settling itself"). The eligibility trace is per-synapse. The dopamine δ is a **global broadcast** computed by the critic from the settled state. So: local synapse mechanics, one global neuromodulatory scalar — architecturally the dopamine-analog of a real dopaminergic broadcast. Note: locality here is *engineering* locality, not spike-locality; the underlying "neural activity" variables are settled equilibrium activations, not spikes (the documented Level B failure).

**Q2 — Update conditions.** Plasticity fires only inside `learn()`, which requires a preceding *sampled* (non-greedy) action: eligibility belongs to the action actually taken (policy-gradient score of that action, temperature-aware). The update gate is the TD error against the critic's value prediction of the *settled state* — reward enters nowhere else. Configurable gating: dopamine centring (quiet while reward is typical), floor (sub-threshold surprises are nothing), cap (near-cap = learning from sign alone — monitored and reported as `capped`). A "time limit is not a terminal state" bootstrap rule distinguishes truncation from true episode ends.

**Q3 — Persistence.** Three tiers: (1) **learned parameters persist** — synapse scales, biases, critic weights — and `Brain.save` covers them across restarts; (2) **eligibility traces decay** at γ·λ per step and are zeroed at episode end — transient credit, not memory; (3) **optimizer state persists** (per-synapse RMS normalization, momentum) — adaptive-rate history outlives episodes. Matches its docs: "saved continuation includes pending feedback and memories."

**Q4 — Reversibility.** **Yes, structurally — and this is the load-bearing finding.** The update `scale += η·δ·e` is **sign-symmetric**: δ < 0 with positive eligibility *decreases* the weight. Negative prediction errors weaken recently-eligible associations. The weakening is eligibility-gated (only recently-active synapses move), but it is a genuine weakening mechanism — **exactly what frozen L1 measurably lacks** (Task B: GNG521 total negative, "potentiative-only cannot suppress an established excitatory association"; V_MAG grew 334 edges, all positive, zero weakening anywhere). Cadence's own docs frame memory as "possible interference"; the *source* shows the stronger fact: RPE-gated two-sided updates make unlearning possible without new structures, because the sign of the teaching signal does the work.

## Bearing on the L3/dopamine re-anchoring obligation

Phase 1's freeze requires sign re-anchoring on dopamine/serotonin/octopamine pathways **before L3 exists**. This audit's answer to "built from scratch or informed by a structured reference": the three-factor structure (per-synapse eligibility × broadcast RPE scalar, sign-symmetric) is the *class* of mechanism that supplies Task B's measured gaps (weakening; and via trace decay, partial consolidation dynamics). **Any fly-cognition implementation is designed from Schultz et al. (1997) and Bellec et al. (2020) first, per the registered clean-room rule; Cadence's source informs the design space, never the design.** The audit also sharpens the empirical question the re-anchoring must answer: whether the MaleCNS dopamine neurons' *actual wiring* supports a broadcast-scalar semantics or requires pathway-specific gating — a connectome question our snapshots can answer directly.

## Go/no-go (Investigation 01, closing)

| Role | Verdict | Basis |
|---|---|---|
| Biological runtime (Level A/B/C) | **NO — unsuitable** | Level B fails on documented grounds (no spikes; equilibrium activations); embedding skipped as process theater |
| Orchestration infra | Not pursued this phase | No Phase 3 need identified that justifies GPL-3 coupling |
| Comparator for cross-architecture claims | Downgraded to *suggestive parallel* (calibration correction registered) | Design choice vs measured finding must not be conflated |
| Structured reference for L3 mechanism class | **YES — informative, clean-room-governed** | Q4: sign-symmetric RPE×eligibility is the class that supplies the measured weakening gap |

**The investigation was allowed to conclude unsuitable, and did — for the runtime role — while yielding the one thing worth having: a concrete, literature-anchored mechanism class for Phase 3's named requirements.**

## Provenance

Clone at scratch (depth 1, main @ 2026-10-08); `plasticity.py` line references: three-factor update (L10-12, 740-741), Valence centring (L94-150), eligibility from contrast (L697-702), TD bootstrap (L706-713), done-row trace reset (L772-775), saturation diagnostic (L825-830); `learning.py`: contrastive-Hebbian rule (L1-23), centered contrast (L523-533). Clean-room rule and calibration correction: `docs/FLY_LEARN_001_DECISIONS.md`, 2026-10-08 sections.
