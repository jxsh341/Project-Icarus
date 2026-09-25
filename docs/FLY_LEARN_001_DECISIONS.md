# FLY-LEARN-001 — Pre-Implementation Decision Registry

**Status:** RESOLVED before WP1 (2026-09-25)
**Parent:** FLY-BASE-001 @ d0d7677 (tag FLY-BASE-001)
**Protocol:** Downloads/FLY-LEARN-001_Phase_2_Protocol.md v0.1
**Rule:** every deviation from the protocol as written is either (a) resolved
here with rationale and evidence, or (b) not taken. No silent amendments.

---

## D1 — WP4 task order: protocol Task-A-first is AMENDED → Task A (redesigned) + Task B as a paired first deliverable

**Protocol says** (§34 WP4): "Compare L0 vs L1 on Task A."
**Agent proposed** (review turn): start with Task B (reversal) because it is
guaranteed non-innate.
**Decision:** follow the protocol's Task-A-first sequence, with Task A
redesigned as the protocol itself requires (§10: "the desired response must
not be already completely encoded by the frozen baseline"), and run Task B
as the *paired* second experiment in WP4 (both before any L2 work). The
reversal-is-cleaner observation is recorded as a design rationale for
emphasizing Task B, not as a unilateral resequencing.
**Rationale:** the confound in naive Task A (innate sugar→feed already
solved by the frozen baseline; WP9: 121/121) is removed by *redesign*, not
by reordering. Task B remains the sharper single test and will follow
immediately; L0-vs-L1 acquisition is still measured first, as written.
**Redesigned Task A (frozen definition, AMENDED 2026-09-25 after the
cue-valence check):** the original neutral-cue choice (water LB3a /
IR94e LB1e) is REJECTED. The review asked whether either cue carries
innate valence beyond the sugar/bitter axes; both do:
- IR94e/LB1e: probe shows direct suppression of sugar-driven MN9_L
  (82 → 2–8 Hz, mean 5.2, n=5) — the substrate itself expresses the
  aversive interaction, matching Guillemin et al. 2024 (Cell Reports
  43:114625: IR94e activation drives mild feeding aversion) and
  Shiu figures.ipynb fig_3b (Sugar_Ir94e is a suppression condition).
- Water/LB3a: probe shows NO MN9_L expression (silent in 5/5) and only
  small local recruitment (~94 neurons) — safe in the closure — but
  literature shows ppk28+ water GRNs drive proboscis-extension/drinking
  (innately positive valence, state-dependent; sated flies avoid water,
  thirsty flies seek it: Jourjine et al.; Lin et al. 2014/2017). A cue
  whose biological valence is state-dependent is exactly the kind of
  hidden confound Phase 2 must not build its first association on.
**Replacement cue selection — criterion set FROZEN before any probe
(2026-09-25, review-driven):** a cue population must satisfy ALL of
(a)–(e), verified in order of cheapness:
- (a) excitatory NT (acetylcholine) — potentiation must be *able* to
  create expression; an inhibitory cue cannot be learned into a feed
  response;
- (b) structural path to the readout within <=3 hops — a cue with no
  path is UNLEARNABLE (potentiation with no route never expresses),
  which is impossibility, not neutrality;
- (c) probe-verified zero baseline MN9_L expression when driven alone;
- (d) no suppression of the innate sugar-feed program under
  co-stimulation (the IR94e failure mode);
- (e) no literature-documented or NT-mediated state-conditional
  valence (the water/LB3d/LB2b failure mode: hydration, salt-stress,
  arousal modulators);
- (f) target-set overlap between the two cues neither ~1.0 (same
  channel) nor ~0 with disjoint readout access.
**Structural census (2026-09-25, pre-probe):**
- **LB2a — LEADING CANDIDATE**: 4 neurons, all cholinergic, all Traced,
  out-deg 75-127, ALL upstream of MN9_L within 2 hops (criterion a, b
  satisfied structurally; c/d pending probe; e: no documented valence).
- **LB2b — DISQUALIFIED pre-probe**: 2 of 3 neurons are OCTOPAMINERGIC
  (the arousal/stress modulator) — the same state-conditional-valence
  category as water, caught by the NT census at zero simulation cost.
  The glutamatergic third is a single neuron (n=1 is not a population).
**Synthetic-cue fallback (criterion frozen now, per review):** if LB2a
fails its probe, synthetic SEZ-interneuron cues are selected by
structure, not arbitrariness — cholinergic, in-degree matched to
within 20% of each other, matched out-degree, both upstream of MN9_L
within 3 hops, non-overlapping target sets, no literature-documented
role in feeding/valence circuits. 'Arbitrary pair' was never a
defensible selection rule; matched-by-structure is.
**Status:** LB2a probe (criterion c/d verification) is the open item
blocking WP2, not WP1.**
**Evidence:** probe results/phase2/wp0_cue_valence_probe.jsonl (n=5
seeds/arm, explicit 200 Hz); structural census (this registry update);
Guillemin et al. 2024; Shiu fig_3b; WP9 grid.

## D2 — Substrate: run-007 only; MB-completeness recorded as a scope boundary

**Census (2026-09-25, measured, not assumed):**
- run-007 (40,290 neurons): 86 MBON, 206 PAM/PPL dopaminergic types,
  1,444 dopamine-NT, 369 serotonin, 84 octopamine neurons; **0 Kenyon
  cells**.
- run-006 (47,889): 20 MBON, 12 PAM/PPL, 85 dopamine — strictly less
  modulatory machinery.
**Decision:** run-007 is the learning substrate for all of Phase 2 (L1–L4).
**Scope boundary (inherited obligation from the freeze manifest):** the
mushroom body's *input* layer (Kenyon cells) is absent from the closure;
L3 (neuromodulated) experiments operate on DAN→MBON/modulatory structure
that exists in the closure, not a full KC→MBON→DAN loop. Any L3 result is
scoped as "closure-contained modulatory architecture," and the NT→sign
re-anchoring obligation (freeze manifest open_assumption) applies to
dopamine/serotonin/octopamine pathways before L3 numbers are interpreted.
A new MB-inclusive snapshot remains an option but is NOT taken now; it
would be a registered deviation if L3 work demands it.

## D3 — Signed-weight plasticity semantics: three named variants, no implicit choice

**Protocol gap (confirmed):** §8 L1 states Δw = η x_i y_j with no statement
of how it composes with signed weights. Our weights are signed synapse
counts (per-presynaptic NT; 32.7% of edges inhibitory; median |w|=2, p99=78,
max=766).
**Decision:** implement all three semantics as separately named, separately
tested PlasticityRule variants, selected per-experiment by explicit config:
- **V-mag** (default): Δw acts on |w|; sign preserved.
  `w <- sign(w) * (|w| + η·x·y)`, magnitude clipped ≥ 0.
- **V-signed**: Δw acts on w directly; a strong LTP event can cross zero
  and flip an inhibitory synapse excitatory (and vice versa). Recorded as
  biologically aggressive; used only as an explicitly registered arm.
- **V-clip**: Δw acts on w but is frozen at zero-crossing (no sign flips).
**Rationale:** the same discipline as the NT→sign convention: the choice is
a modeling assumption, so it is named, versioned, and tested rather than
picked implicitly inside the implementation. V-mag is default because sign
is a validated per-presynaptic property (WP6b) — LTP shouldn't silently
override it — but V-signed is retained because Hebbian potentiation of an
inhibitory synapse's *effect* is a real modeling position.

## D4 — η sweep range: scale-informed, not placeholder-copied

**Protocol says** (§26): η ∈ {10⁻⁵..10⁻¹} "exact range depends on the
simulator's weight scale."
**Measured scale:** median |w|=2, p75=5, p99=78, max=766, mean 6.70;
kick size w_syn·f_poi ≈ 69 mV at full drive.
**Decision:** sweep η ∈ {1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2,
1e-1}, 9 points, with per-point acquisition + stability + weight-drift
metrics, and an explicit instability threshold (see D6) whose crossing
truncates that arm. Initial expectation (to be verified, not assumed):
visible-but-bounded drift at η≈1e-4..1e-3 given x,y ∈ rate units.

## D5 — Parameter-default convention: ported to Phase 2 config objects from WP1

**Phase 1 lesson (three incidents):** the sugar-rate mislabel (150 vs 200 Hz,
twice) and the scoping-probe rate. Root cause class: reliance on parameter
defaults.
**Decision:** the Phase 2 `PlasticityConfig` (and every experiment config)
uses the same convention as WP9: **all parameters set explicitly via
dataclasses.replace / explicit constructor — no read-side defaults for any
quantity that defines an experimental condition**. The config object itself
is checkpointed (hashed) per run. A config-schema test asserts that
constructing a config with any field unset raises.

## D6 — Stability thresholds: pre-registered before any L1 run

**Freeze-manifest anchors (Phase 1 measured):**
- spontaneous: 0 spikes/30 trials → **instability if spontaneous rate > 5 Hz
  network-wide** (any endogenous activity is a regime change).
- all-pos pathological reference: 618K spikes/s → **instability if any
  1 s trial exceeds 150K spikes** (~4× the signed high-drive sugar+bitter
  maximum of ~41.5K, still ~4× below the epileptiform reference).
- E/I weight drift: **instability if total |inhibitory weight| changes by
  >20%** from the frozen baseline census (32.7% of edges; mean signed
  contribution to be computed at WP9-stability time).
- decision-boundary regression: L0 must reproduce the WP9 boundary
  (feed iff sugar ∧ ¬bitter) exactly in WP0 re-verification; any L1 arm
  whose *untrained* boundary differs is halted for diagnosis (Gate A/B).

## D7 — Interpretation boundaries reminder (from protocol §50, standing)

All Phase 2 claims are phrased as measured: "the substrate acquired an
association under the tested plasticity rule," never "developed
intelligence." Negative results (protocol §33 Failures A–H) stay in the
record with the same status as positive ones.

---

## Open items (not blocking WP1)

- exact neutral-cue GRN body-ID lists for Task A (fetch from server at WP2;
  types LB3a, LB1e — both present in run-007 per scoping census)
- reward-signal semantics for L1 (protocol §10 says reward is
  experimenter-side; whether L1-only arms see any gated signal at all is
  itself an arm: L1-pure (no gating) vs L1+reinforcement variant, to be
  registered when WP3 lands)
- compute costing of the §35 experiment matrix at Phase 1 measured rates
  (0.09–0.15 trials/s high-activity) before the confirmatory stage
