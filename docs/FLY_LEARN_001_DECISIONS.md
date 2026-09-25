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


## Cue selection — probe and screen results (2026-09-25, post-WP1)

**LB2a probe VERDICT: REJECT on both frozen criteria**
(results/phase2/wp2_cue_probe_lb2a.jsonl, n=5 seeds 21000-21004, explicit 200 Hz).
- (c) FAIL: cue-alone MN9_L = 1 Hz in 5/5 seeds (criterion: max == 0).
  Perfectly reproducible single spike; possibly an onset transient —
  noted as a criterion refinement candidate (steady-state window
  instead of whole-trial count), but this does NOT rescue LB2a because
  (d) fails regardless.
- (d) FAIL: co-drive with sugar suppresses MN9_L 82 -> [9,10,19,30,54] Hz,
  4/5 seeds below the frozen 41.5 Hz threshold (criterion: min >= 41.5).
- Mechanism: co-drive recruits ~2x the neurons sugar alone does
  (n_spiking 859-985 vs 440) while MN9_L FALLS — the LB2a direct
  cholinergic path is dominated by recruited inhibitory intermediates.

**Path-influence screen: validation FAIL — rankings discarded per the
pre-registered rule** (results/phase2/wp2_synthetic_cue_screen.json).
- Validated on 3/4 measured cases (sugar +88.6k, bitter -732.7k,
  ir94e -209.1k — all correct signs; these are the STRONG-influence
  regime).
- FAILED on LB2a: predicted net +772 (positive) vs measured
  co-suppression. Boundary: linear path-product sums are gain-blind;
  they are unreliable precisely in the weak-influence regime where
  Task A cue candidates live. Structural screening cannot substitute
  for a direct probe of criterion (d). The screen's candidate/pair
  outputs are NOT to be used for selection.

**Design insight — criterion (d) is load-bearing for the minimal L1
acquisition experiment:** the first L1 experiment is Pavlovian-shaped
(cue co-presented with sugar during training), because pure Hebbian
learning needs postsynaptic activity to correlate with cue activity,
and the co-presented sugar is what supplies it. A co-suppressing cue
corrupts both the coincidence signal and the trained direction.
Symmetric-task corollary: the aversive direction's postsynaptic site
is the inhibitory INTERNEURON (active under bitter co-drive), not
MN9_L itself (near-silent, nothing to correlate) — Hebbian-legal, but
a different edge set; recorded for the two-cue design.

**Root-cause hypothesis for three straight cue rejections:** the
run-007 closure is seeded/centered on the feeding hub; its local
cholinergic neighbors sit in an inhibitory-rich neighborhood, so
co-drive tends to recruit suppression. Prediction: candidates farther
from the hub (weaker structural paths, e.g. central-brain types)
are less likely to co-suppress. The batch probe below tests this
implicitly.

**Batch probe (launched 2026-09-25, background):** enumerate ALL
cholinergic, non-sensory/motor (type-prefix LB/Gr/Ir/ppk/MN/DN/ES/og/CG
excluded), <=2-hop-upstream-of-MN9_L neurons with in-deg 5-400 and
out-deg 5-200; probe each as a single-neuron cue at explicit 200 Hz,
arms cue-alone + cue-cosugar, 5 seeds each (22000-22004), frozen
criteria unchanged, checkpointed to
results/phase2/wp2_cue_probe_batch.jsonl. If >15 candidates pass the
filter, sample every k-th by bodyId (rule stated in advance,
screen-independent) — single-neuron probes are a SCREEN; survivors
get probed again as populations/type-groups before any cue is frozen.
If NO candidate passes (d), the pre-declared fork is a documented
protocol discussion (withhold-direction task, alternate readout, or
Task A restructure) — not a quiet criterion rewrite.


## Task A cue pair — FROZEN (2026-09-25)

**Batch probe** (results/phase2/wp2_cue_probe_batch.jsonl, 15 sampled
candidates, cue-alone + cue-cosugar, 5 seeds each, explicit 200 Hz):
11/15 PASS both frozen criteria. The four rejects all failed (c) by
driving MN9_L alone at 50-81 Hz - they are pre-wired into the feed
program (ANXXX462a, dorsal_tpGRN, ANXXX255, GNG318: hub-adjacent),
independently confirming the hub-distance hypothesis.

**Pair selection** (pre-declared rules: in/out-degree within 20%,
target Jaccard < 0.2): exactly ONE pair qualifies -
results/phase2/wp2_cue_pairs.json.
- **Cue A: GNG521-type** - 2 members [15957, 16327], in=47/out=19
- **Cue B: PRW043-type** - 5 members [25250, 26891, 37670, 39767,
  69045], in=51/out=20, target Jaccard 0.0

**Population-level verification** (pre-declared freeze gate;
results/phase2/wp2_cue_probe_groups.jsonl, 5 seeds each, explicit
200 Hz, driven as the PRIMARY population exactly as the training
driver will drive them):
- GNG521 group: alone MN9_L=[0,0,0,0,0]; cosugar=[82,83,86,84,84]
- PRW043 group: alone MN9_L=[0,0,0,0,0]; cosugar=[80,83,81,81,82]
Both PASS (c) and (d) at group level. PAIR FROZEN as the Task A cues.

**Two-direction readout definitions (established by the probe):**
- FEED-acquisition readout: cue-ALONE MN9_L rate. Baseline 0 Hz in
  10/10 group-probe trials, so ANY post-training expression is
  attributable to potentiation. Trained by cue+sugar co-presentation
  (Pavlovian; sugar supplies postsynaptic activity).
- WITHHOLD-acquisition readout: cue+COSUGAR MN9_L rate. Baseline
  80-86 Hz (feed mode intact for both cues), so learned suppression
  has room to appear. Trained by cue+bitter co-presentation; the
  postsynaptic site is the inhibitory interneuron population active
  under bitter (registry corollary above), Hebbian-legal.
Both cues support BOTH directions. Cue->direction assignment is
arbitrary (swapped between training arms per D1's anti-confound
design); both arms are now fully specified.

**Cue-pair properties worth noting for the write-up:** both types are
SEZ local interneurons (GNG = subesophageal ganglion; PRW = prow),
cholinergic, non-sensory, non-motor - circuit-level cues rather than
sensory-neuron cues, which is the registry's synthetic-fallback
family. The all-sensory candidates (water/IR94e/LB2a/LB2b) are all
rejected; the surviving pair is exactly the structurally-matched
interneuron family the fallback criterion described.
