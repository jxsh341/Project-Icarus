# L3 Design — Dopamine-Gated Plasticity on the Coincidence-Waste Hub

**Project:** FLY-LEARN-001 → Phase 3 | **Status:** Pre-registered design, before any implementation
**Date:** 2026-10-08 | **Registry anchors:** D-3 (pathway-specific gate), WP-D1/D2/D3 (censuses), Phase 1 freeze (re-anchoring obligation), Phase 2 Task B close-out (measured gaps)
**Clean-room status:** rule designed from Schultz et al. (1997) / Bellec et al. (2020) first; Cadence's implementation consulted for understanding only (audit on file). No Cadence-derived structure is copied.

---

## 1. What L3 is

Phase 2 established the substrate can **learn and keep but not unlearn**, and characterized *why* reversal fails: no weakening mechanism (potentiative-only V_MAG grew 334 edges, all positive), and no consolidation (coincidence waste regresses the readout past its crossing: intermediates entering the ~300 Hz regime — ⅔ of the 454.5 Hz refractory ceiling — collapse coincident arrivals at the readout).

L3 adds the **measured dopaminergic gate** to the frozen substrate: a pathway-specific, three-factor rule in which dopamine is not an invented scalar but the activity of 9 identified DA neurons converging on the AVLP597 inhibitory hub pair — the neurons that control the coincidence-waste regime.

The governing question: **does the substrate's own modulatory anatomy supply the two missing mechanisms — consolidation (gated suppression of over-synchrony) and weakening (sign-symmetric, eligibility-gated updates)?**

## 2. The measured anatomy (every stage from census artifacts)

```
sugar GRNs ──(direct, 7 cells→11608)──┐
bitter GRNs ──(mixed-sign 2-hop:      │
  exc via 11021, inh via 17709/518540)├──> OA relay (10120 OA-VPM4: 1,655 inputs,
                                       │      11608/12109 OA-VUMa2: ~1,300-1,400)
                                       │      MASSIVE multimodal integrator;
                                       │      sugar share 0.0–0.3% — state+reward
                                       │      conflated channel; valence-carrying
                                       v
                            9 gate-DA cells (10399, 10898, 10914, 11125,
                            12588, 13068, 520146, 520188, 529811)
                              │  core: 10898 (+12, 41% spec.), 10914 (+1, 50%),
                              │        520188 (+10, 39%)  — hub-gating core
                              │  broad: 12588 (66 tgts), 13068 (52 tgts)
                              v
                     AVLP597 PAIR: 10646 + 10094 (GABA; 1,457/1,385 targets,
                     |w| ≈ 9,154/8,214 — broad inhibitory gain-control hubs)
                              │
                              └── self-limiting loop (measured): 10646 → 13068, 520188 (−1 each)
                              └── DA↔OA reciprocal: 10399→11608/12109 (+6 each), 13068→10120 (+4)
                              └── ZERO edges from any gate cell onto MN9_L (upstream-of-readout confirmed)
```

**Known risk carried from WP-D3 (not silently resolved):** the OA relay is not a pure reward line — it is state+reward conflated (sugar = 0.0–0.3% of its input budget). L3 therefore reads **r at the sugar-GRN source** (GRN population activity), and treats OA conflation as a *testable prediction*: the gate-DA population's activity should correlate with sugar presence but carry state noise; WP-L3b measures how much.

## 3. The sign question — the re-anchoring obligation, made precise

The frozen matrix assigns ALL monoaminergic neurons sign **+1 by default** (`nt_sign`; auditable assumption, recorded at build). The gate-DA → AVLP597 edges (+12/+10/+9) are positive **by default, not by validation**. The Phase 1 freeze named exactly this: dopamine-pathway signs must be re-anchored **before L3 exists**.

The two hypotheses make opposite predictions:

- **H(+):** DA excites the GABA hubs → gate activity *increases* inhibitory gain → suppresses intermediates → counteracts coincidence waste. Under H(+), the anatomy is a consolidation mechanism.
- **H(−):** DA inhibits the GABA hubs (or shunts them) → gate activity *decreases* inhibitory gain → disinhibits intermediates → worsens over-synchrony. Under H(−), the gate is an arousal-like amplifier, and consolidation must live elsewhere.

**WP-L3a resolves this empirically before any plasticity is added** (below). No default is adopted silently.

## 4. The rule (three-factor, pathway-specific; clean-room-derived)

```
e[e]    ← γλ·e[e] + x_pre[e]·x_post[e]        (eligibility: cue-incident edges only —
                                                the frozen L1 window, V_MAG sign handling)
δ       = r + γ·V(s′) − V(s)                   (r = sugar-GRN population activity;
                                                V(s) = linear readout of gate-DA activity —
                                                the state estimate the anatomy already builds)
w[e]    ← w[e] + η·δ·e[e]                      (sign-symmetric: δ<0 with positive
                                                eligibility WEAKENS — the measured gap)
w[hub]  ← w[hub] + η_g · D(t) · g(hub_rate)     (the GATE: D(t) = gate-DA drive;
                                                modulates the hub pair's inhibitory gain)
```

The fourth line is the pathway-specific extension: dopamine does not broadcast onto all plastic edges — it acts through the measured hub pair, modulating the coincidence-waste regime the intermediates live in. Consolidation is then *biophysical* (gated suppression keeps intermediates below the ~300 Hz boundary), not an imposed stopping rule — with the measured self-limiting loop (10646 → gate-DA, −1) as the anatomy's own version of it.

**D3 variants rule applies:** V_MAG is the default update semantics (sign is a validated per-presynaptic property; LTP must not silently override it); V_SIGNED is a registered arm only, required for the weakening tests to cross zero on inhibitory edges if the data demands it.

## 5. Work packages

### WP-L3a — Sign re-anchoring (BEFORE any L3 plasticity; discharges the freeze obligation)
**Method:** In the *frozen* Phase 1 dynamics (no plasticity), drive the gate-DA population with Poisson stimulation across a rate sweep (as WP6c did for GRNs) and measure the hub pair's responses and downstream intermediate rates. Then drive the hub pair directly and measure intermediate/readout responses.
**Pre-registered criteria:** H(+) supported iff gate-DA stimulation *increases* hub-pair-driven intermediate suppression (intermediate rates fall / readout falls); H(−) iff the opposite. Ambiguity or nonlinearity → recorded as-is; the design adapts, never the data.
**Cost:** ~30 simulations. **Output:** the DA-sign anchor (validated or refuted), recorded in the registry and the freeze manifest.

### WP-L3b — Gate dynamics on the trained circuit (no plasticity change)
**Method:** Replay the GNG380 reversal scenario (the regressing block) with the gate-DA population driven at measured physiological levels; hub-pair gain modulated per WP-L3a's validated sign.
**Pre-registered criteria:** consolidation-hypothesis support iff gated hub suppression arrests the intermediate climb below the ~300 Hz boundary and the readout holds its crossing (vs. Task B's measured 49→27 regression). The self-limiting loop's effect is measured by comparing with/without the 10646→gate-DA feedback term.
**Cost:** ~50 simulations (5 blocks × sweep).

### WP-L3c — Full three-factor acquisition
**Method:** WP4's Task A protocol (arm1: the learned directions) + the gate. δ from r = sugar-GRN activity; V(s) from gate-DA activity.
**Pre-registered criteria:** acquisition at least as fast as Phase 2's (trials-to-θ per cue, per-cue baselines); guard silent; the dose rule and probe-variance rules apply throughout.

### WP-L3d — The weakening test (the decisive experiment)
**Method:** Task B's reversal protocol (GNG380 withhold→feed, the transient-crossing case) + the three-factor rule. δ goes negative when predicted reward exceeds delivered (extinction-style contingency reversal: sugar withheld).
**Pre-registered criteria, in order:** (1) does the acquired association weaken (cue-alone probe falls below θ)? (2) does the new direction consolidate (stop-at-crossing achieved biophysically, no regression)? (3) does the masking cell stay empty (two-state gate)? A null is a registered negative result — the substrate's modulatory anatomy does not supply weakening under this rule — never a silent mechanism change.

## 6. Standing rules (all inherited, all apply)

Dose-diff-first on any contradiction; probe purity (hash-verified); per-simulation weight checkpoints with bit-for-bit resume; resume-across-revision requires quarantine; fail-loudly-on-empty-scope; per-cue baselines; ≥2 probe sims/point; seeds verified disjoint pre-launch (new ranges: L3 train 150000+, probe 200000+, verified against all prior); development-stage labeling (§22) with nothing reading as confirmatory; guard live throughout.

## 7. Provenance

Anatomy: `results/phase3/wp_d1_da_census.json`, `wp_d2_gate_anatomy.json`, `wp_d3_oa_convergence.json` (+ input-dump and hub-output scripts). Measured constraints: Task B close-out, coincidence-waste probes (`mechanism_saturation_probe.json`, `gng521_extended_dose_probe.json`). Rule provenance: Schultz/Bellec via clean-room discipline; Cadence audit on file for the mechanism-class argument only.
