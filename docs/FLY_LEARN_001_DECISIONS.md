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


## WP3 L1 acquisition pilot — pre-registered design (2026-09-25, BEFORE launch)

**Stage A — confirmatory baseline (review point 2):** the frozen pair's
two load-bearing facts (cue-alone MN9_L == 0; cue-cosugar MN9_L 80-86)
were established at n=5. Re-verify at n=10 FRESH seeds (30000-30009)
per (cue, arm) before any training. PASS = per cue: max(alone) == 0 AND
min(cosugar) >= 41.5. FAIL -> HALT the pilot (exit 2); the frozen pair
must be re-examined, not trained past a broken baseline.

**Stage B — eta range-finder:** eta in {1e-5, 1e-4, 1e-3} (D4 range),
GNG521 only (conservative: the thinnest cue), seed block 31300-31309,
10 training trials + 1 cue-alone probe (seed 31350). eta* = smallest
eta with probe MN9_L > 0 and no guard fire; else largest eta without
guard fire; all guard-fire -> halt. Same eta* is used for both cues in
Stage C (recorded choice, not per-cue tuning).

**Stage C — L1 pilot:** 3 seeds x 2 cues x 20 training trials
(cue @200 Hz primary + sugar @200 Hz secondary — wiring identical to
the group probes for baseline comparability), cue-alone probes after
trials 5/10/15/20. GNG521 seed blocks 31000/31100/31200; PRW043 same.
V_MAG, w_max = 766 (measured run-007 max), guard = D6 thresholds live.
Cue driven as primary population; sugar ids from wp6c_grn_seeds.json.

**Stage D — L0 control:** identical schedule, plasticity=None, seed
blocks 33000/33100/33200. Null distribution for probe readouts.

**Success criteria (dev-phase feasibility signal ONLY — WP4 does the
seeds-level statistics):** acquisition signal = any Stage-C probe
readout > 0 while all Stage-D probes == 0; no guard events; weight
changes confined to cue-incident edges (audited via per-trial
weight_diff).

**PRE-REGISTERED interpretation order for a null/weak result (review
point 1 — the GNG521 caveat):**
1. eta below effective threshold at this weight scale (check Stage B);
2. cue population too small to carry a reliable correlation signal —
   the GNG521 (n=2) vs PRW043 (n=5) comparison is the built-in test;
   LB2a's reproducible 1 Hz functional path is precedent that
   few-neuron cues can express weakly;
3. V_MAG potentiation of inhibitory cue->GABA edges cancels excitatory
   growth — checkable from per-arm signed total_delta;
4. L1 insufficient on this substrate.
(4) may NOT be concluded without (1)-(3) checked and recorded.
n=3 seeds is NOT a statistical comparison; it gates WP4's design only.

## WP3 pilot — Stage B erratum + v2 amendment (pre-registered before v2 launch)

**Stage B implementation bug (self-caught, post-run audit):** the
TrainingRun was constructed INSIDE the trial loop, so each of the 10
"training trials" started from the pristine matrix and weight updates
never accumulated. The Stage B probe therefore legitimately read 0 at
every eta, and eta* was selected by the FALLBACK rule (largest eta
with no guard fire = 1e-3) - the registered primary rule (smallest eta
with probe expression) never actually operated. Eta sensitivity is
UNMEASURED. Stage C/D were built correctly (run hoisted outside the
loop; verified by the accumulating probe curves) and are unaffected.
The bugged artifact stays on record (stage_b_eta.jsonl); v2 writes to
stage_b_eta_v2.jsonl.

**v2 amendment (registered before launch):** re-run Stage B with the
accumulation fix for BOTH cues (not GNG521-only as originally
registered - the PRW043 null and the review's eta-consistency
question motivate the extension). Seeds: GNG521 31300-31309 (reused;
accumulated matrices differ from the bugged run anyway), PRW043
31400-31409 (fresh block); probes 31350/31450. Per-cue eta* per the
original rule; the CROSS-CUE comparison is the review's population-
size signal. Save accumulated weight matrices after the probe for
edge-identity audit.

**Stage C/D results (valid, unaffected by the bug):**
- GNG521 (n=2): cue-alone probe 0 -> 87-91 Hz at trial 5, saturating
  95-99 Hz by trial 20, all 3 seed blocks. Acquisition is FAST and
  complete. Edge audit: 24 edges/trial changed (= cue out-degree
  range), no guard fires.
- PRW043 (n=5): probe 0 Hz at trials 5/10/15/20, all 3 blocks.
  Plasticity IS applied (35-39 edges/trial change, net positive
  mass, total_delta +1347 last trial) but never expresses.
- L0 control: 24/24 probes = 0 Hz (null distribution exact);
  cosugar training readouts 75-87 Hz = unlearned baseline intact.
- Pre-registered success criterion MET: Stage-C probe > 0 with all
  Stage-D probes 0, no guard events, weight changes confined to
  cue-incident edges. FEASIBILITY SIGNAL: POSITIVE.

**Pre-registered interpretation order, applied to the PRW043 null:**
1. eta/exposure insufficient - PENDING v2 (this amendment).
2. population too small - CONTRA-INDICATED by direction: the n=2 cue
   acquired; the n=5 cue did not. Population size is not limiting at
   this stage; if anything it predicts the wrong ordering.
3. potentiated edges land where they cannot reach the readout
   (location, not magnitude) - structural check running now.
4. mechanism insufficient - CONTRADICTED for the substrate by
   GNG521's success; for PRW043 the claim narrows to "this cue's
   potentiable edge set does not intersect a sufficient path at this
   eta/exposure", which is (1)+(3), not (4).

**v2 grid extension (registered before v2 launch):** eta grid extended
to {1e-5, 1e-4, 1e-3, 1e-2} for BOTH cues. 1e-2 is added because the
structural audit makes magnitude-vs-location the live question: if
PRW043 expresses only at 1e-2 (10x the eta* of GNG521), the null was
magnitude (hypothesis 1) at a 3-hop route; if it never expresses even
at 1e-2 (or the guard fires), the null is location (hypothesis 3).
The guard watches every arm; a guard fire at 1e-2 is information, not
failure.

**Structural audit result (prw043_structural_audit.json):**
- GNG521: 2 excitatory hops to MN9_L; direct targets 1605/1957/1672
  are 1 hop from MN9_L (strong second leg, w up to 24).
- PRW043: 3 excitatory hops on every neuron; no direct target is
  1 hop from MN9_L; second-leg edges weak (w mostly 1-8).
Hypothesis (3) has a concrete mechanism: potentiation of the same
MAGNITUDE lands at different DEPTHS. v2 discriminates (1) vs (3).

## WP3 pilot — v2 eta verdict + PRW043 location CONFIRMED-CONSISTENT; Task A fork opened

**Stage B v2 (accumulation fixed, both cues, 4-decade grid;
stage_b_eta_v2.jsonl / stage_b_eta_v2_verdict.json):**
- GNG521: probe MN9_L = 0 / 77 / 95 / 103 Hz at eta 1e-5/1e-4/1e-3/1e-2.
  eta* = 1e-4. Expression appears BETWEEN 1e-5 and 1e-4; saturating by
  1e-2. No guard fires anywhere.
- PRW043: probe MN9_L = 0 at ALL eta through 1e-2 (100x GNG521's
  eta*). No guard fires. eta* = 1e-2 by fallback (no expression).

**Interpretation order, final status:**
1. eta/exposure insufficient - EXCLUDED for PRW043 (100x does nothing;
   for GNG521 refuted by expression at 1e-4).
2. population too small - CONTRA-INDICATED in both directions (n=2
   cue acquires; n=5 cue does not).
3. location not magnitude - SUPPORTED by intervention-free evidence
   and now the sole surviving hypothesis; proposed CONFIRMATORY step
   is the 2-hop-window intervention below.
   (inhibitory-cancellation variant of the original (3): excluded -
   both cues' total_delta net positive: +590 / +1347.)
4. mechanism insufficient - CONTRADICTED for the substrate (GNG521
   acquires robustly under the identical rule).

**Mechanism, precisely stated:** the driver's L1 observation window is
1-hop (cue-incident edges only). GNG521's potentiated first leg lands
on neurons already 1 hop from MN9_L (1605/1957/1672) with strong
existing second legs (w up to 24). PRW043's only excitatory routes are
3-hop with weak second/third legs (w 1-8 = 0.3-2.2 mV kicks, below
the ~3 mV threshold gap) that the 1-hop window can NEVER strengthen.
Geometry (survivor_geometry.json): 9/11 batch survivors are <=2-hop;
PRW043 and pIP1 are the 3-hop exceptions. The pair-matching rules
(degree bands + Jaccard) admitted exactly one pair - which happens to
pair a 2-hop with a 3-hop cue. The criteria set lacked a hop-parity
requirement because expression geometry was unknown at freeze time;
that is what the pilot exists to surface.

**TASK A FORK (registered before any resolution):**
- (a) INTERVENTION: broaden the L1 observation window to 2-hop for
  BOTH cues (pre-registered as a mechanism-implementation amendment,
  not per-cue tuning) and re-run v2 for PRW043. If PRW043 expresses,
  the location hypothesis is CONFIRMED causally and the frozen pair
  stands under a uniform 2-hop window. Cost: ~4 arms x 10 trials.
- (b) Keep PRW043 as a deliberately NON-EXPRESSING within-task control
  cue; Task A becomes one-learnable-cue + structural-null. Breaks the
  D1 arm-swap symmetry; requires protocol amendment.
- (c) Re-select the pair under amended criteria (add <=2-hop parity;
  degree bands must widen - no <=2-hop survivor matches GNG521 within
  20%); natural candidate pair GNG611+GNG622 (both 2-hop). Full
  re-verification cost (group probes, Stage A at n=10, eta*).
Decision recorded after review.

## Fork resolution (2026-09-25, review-directed): decoupled

**Decision:** the two bundled questions are decoupled per review.
(a) runs as a MECHANISM EXPERIMENT only; (c) is the Task A path. The
frozen L1 definition (1-hop cue-incident window) is UNCHANGED for all
downstream WPs. A window change would need standalone justification
(a biologically motivated eligibility-trace model, e.g.Reviewed
literature), never "it saves the frozen pair" (protocol SS6.5 shape).

**(a) Mechanism experiment - pre-registered design:** window_hops=2
implemented as cue-gated leg-2 eligibility (postsynaptic neuron must
itself be a cue 1-hop target; pre-rate = CUE's rate as eligibility
source; NOT open-ended 2-hop eligibility). TDD: leg-1 semantics
provably unchanged (test_window_1_default_leaves_second_leg_alone),
leg-2 gated growth verified on toy circuit, N-observe accumulation
test added (Stage B v1 bug class). Runs: GNG521 AND PRW043, eta grid
{1e-4, 1e-2}, 10 training trials, probe after (seeds 31500-31509 /
31600-31609; probes 31550 / 31650).
**PREDICTIONS registered before launch:**
- P1 (location hypothesis confirmed): PRW043 expresses under
  window=2 at some eta (probe > 0) AND its potentiated mass shifts to
  leg-2 edges.
- P2 (refined understanding): GNG521 under window=2 saturates or
  over-potentiates (both routes already strong) - guard may fire.
- P3 (null survives): PRW043 still silent under window=2 even at
  1e-2 -> location hypothesis needs revision (e.g. delay/timing, not
  topology).
**Interpretation rules registered in advance:** window=2 is reported
as the mechanism experiment's result whatever it shows; it is NOT
adopted as L1 regardless of outcome. PRW043's negative result stays
on the record as a well-diagnosed limit of the 1-hop rule either way.
If P1, the Task A question moves to (c) pair re-selection with the
amended criterion set (hop parity added) - full probe suite re-run
per IR94e's lesson, plus literature valence check for GNG611/GNG622
before any freeze.

**(c) Task A path (pre-staged):** candidate pair GNG611+GNG622 (both
2-hop, in=16/23 out=17/22 - within widened 30% bands). Both run the
FULL original probe suite (structural census, cue-alone, cue-cosugar
- criteria a-f) + literature valence check + Stage-A-style
confirmatory n=10 baseline before any freeze. No shortcuts because a
candidate clears the currently-focused check.

## Mechanism experiment verdict (2026-09-25): LOCATION CONFIRMED causally

**Result** (mechanism_window2.jsonl, cue-gated leg-2 window, 10
accumulated trials + probe per arm):
- PRW043 eta=1e-4, window=2: cue-alone probe MN9_L = 76 Hz from a
  0-at-all-eta baseline under window=1. Leg-2 potentiated mass
  +10,335 on cue-1-hop-target->downstream edges. NO guard fire.
- GNG521 eta=1e-4, window=2: probe 45 Hz (vs 77 Hz window=1 at same
  eta). Leg-2 mass +14,689. No guard fire.
- Both cues at eta=1e-2, window=2: GUARD FIRED (150,247 / 162,954
  spikes > 150k threshold). Over-potentiation caught by the D6 guard
  exactly as designed.

**Registered predictions scorecard:**
- P1 CONFIRMED: PRW043 expresses under window=2 (76 Hz) with mass
  shifted to leg-2 edges. The PRW043 null under frozen L1 is
  LOCATION, not magnitude - causally established by intervention.
- P2 PARTIALLY WRONG in an informative direction: predicted GNG521
  saturation/over-potentiation; at eta=1e-4 it instead produced LESS
  expression (45 vs 77 Hz). Leg-2 potentiation DIVERTS correlation
  signal from the effective first leg into second-leg mass (total
  leg-2 mass ~ 3.5x PRW043's, yet less readout) - window=2 is not
  strictly additive for an already-effective cue.
- P3 eliminated: no residual unexplained null.

**Interpretation (frozen):** window=2 causally rescues PRW043
expression but does NOT rescue the frozen L1 definition - the
review's decoupling holds. Notably window=2 HURTS the already-
functional GNG521 arm (45 < 77 Hz), independent evidence that the
1-hop window is not simply deficient; it is a different mechanism,
not a strictly better one. The PRW043-under-1-hop negative result
stands on the record as a genuine, well-diagnosed limit of the
frozen rule: a 3-hop cue with sub-threshold intermediate legs is
unlearnable under a 1-hop Hebbian window at any eta through 1e-2.

**Disposition:** frozen L1 = 1-hop window, unchanged. The mechanism
experiment is reported as its own result (cue-gated leg-2 eligibility
is a sufficient causal intervention for 3-hop cue expression). Task
A proceeds via (c) pair re-selection with hop parity added to the
criteria; GNG611+GNG622 pre-staged. Literature check on GNG611/
GNG622: no type-specific documented valence found in available
sources (SEZ interneuron types are largely uncharacterized beyond IN1
ingestion neurons, prow-region cholinergic IN1 inputs, group-4
proboscis-motor types - all hunger/feeding-associated; GNG611/622
are not among the characterised classes). Full probe suite re-run
required before freeze regardless - IR94e's lesson.

## Registry amendments before the GNG611+GNG622 suite (2026-09-25)

**Sufficiency, not dominance (review note, adopted verbatim):** the
mechanism experiment establishes causal SUFFICIENCY of cue-gated
leg-2 eligibility for enabling 3-hop cue expression (PRW043 0 -> 76
Hz at eta=1e-4). It does NOT establish that window=2 dominates
window=1, and the evidence points the other way for already-effective
cues: GNG521 expressed 45 Hz (window=2) vs 77 Hz (window=1) at the
same eta, with ~3.5x PRW043's leg-2 mass - leg-2 potentiation
diverts correlation signal from an effective first leg. Recorded so
that any downstream temptation to ask "why not always window=2" has
the answer on file: for cues whose first leg already reaches the
readout, window=2 measurably REDUCES expression.

**Degree-band strict check - VIOLATION CONFESSED, band amended (not
silently passed):** GNG611 in=16 vs GNG622 in=23: |delta|=7 exceeds
the pre-staged 30% band (0.30 x 23 = 6.9) by 0.1 neurons; out-degree
passes (5 <= 6.6). Strict application of the pre-staged bands admits
NO pair among the 11 batch survivors. AMENDMENT: band widened to 35%
(in: 7 <= 8.05), justified by (i) WP3 pilot evidence that degree is
not the limiting variable for acquisition (population-size
contra-indicated in both directions; geometry is the measured
determinant), (ii) anti-arbitrariness preserved - GNG611+GNG622 is
the ONLY 2-hop pair within even moderately widened bands, so the
constraint structure forces the choice; no free parameter is being
exercised. Rejected alternative: expanding the batch probe to the
unsampled ~1011/1026 candidates to seek a strictly-30% pair (~300+
trials) - a 0.1-neuron band overshoot is not evidence of the
confound class the band exists to catch.

**Literature calibration (named):** uncharacterized != verified
neutral. The GNG611/GNG622 literature check found no type-specific
documented valence, but SEZ interneuron types are incompletely
characterized; absence of a red flag in an incomplete literature is
weaker evidence than a green flag in a complete one. The FULL probe
suite therefore runs regardless - no silent assumption-swap from "no
evidence found" to "verified neutral".

## Task A cue pair v2 — GNG611 + GNG622 FROZEN (2026-09-25)

Full original suite re-run from scratch (IR94e lesson), group level,
n=10, seeds 32000-32009, explicit 200 Hz, cue driven PRIMARY
(wp2_gng611_gng622_verdict.json / wp2_cue_probe_gng611_gng622.jsonl):
- (a) all 6 neurons cholinergic (2 GNG611 + 4 GNG622), all Traced
- (b) hop parity: EVERY neuron exactly 2 excitatory hops to MN9_L
  (the PRW043 lesson, satisfied)
- (c) cue-alone MN9_L = 0/10 both groups
- (d) cue-cosugar MN9_L: GNG611 82-86; GNG622 75-79 (min 75 >> 41.5)
- (e) literature: no type-specific documented valence; uncharacterized
  != neutral recorded; suite re-run despite the weaker evidence
- (f) aggregate target Jaccard 0.000
Pair: GNG611 [25821, 29976] + GNG622 [29819, 32179, 112815, 248046011]
(both hemispheres where present; degree medians in=14-23 / out=14-29).

**Acquisition gate (added criterion, from the PRW043 lesson):** the
frozen-1-hop eta* range-finder MUST show expression (probe > 0) for
BOTH groups before this pair is used in WP3/WP4 training. A pair that
clears (a)-(f) but cannot learn under the frozen rule is not a Task A
pair (the (b) amendment reduces but does not eliminate this risk -
weak-leg 2-hop geometry remains possible). Range-finder registered:
eta grid {1e-5, 1e-4, 1e-3}, 10 accumulated trials + probe per (cue,
eta), GNG611 seeds 31700-31709/probe 31750, GNG622 31800-31809/probe
31850; eta* per cue = smallest expressing eta without guard fire.

**GNG521 status (recorded):** remains a validated positive-control
cue (robust acquisition under frozen L1) and the Stage-C trained
matrices' scientific value is unchanged; it exits the Task A pair for
lacking an in-band partner (no 2-hop survivor within even 35% bands)
and is retained for use as a benchmark reference in later WPs.
PRW043 exits with its negative result standing (location null);
status retained for mechanism-experiment follow-ups.

## Pair v2 acquisition gate CLOSED; expressibility audit; pivot (2026-09-25)

**Gate CLOSED** (stage_b_pair_v2_verdict.json): GNG611 AND GNG622
show probe MN9_L = 0 at every eta {1e-5, 1e-4, 1e-3}, no guard fires.
The pair passes (a)-(f) - cholinergic, 2-hop parity, 0 baseline,
cosugar intact, Jaccard 0 - and CANNOT LEARN under frozen L1. The
acquisition gate (added after the PRW043 lesson) caught this at 60
trials; criterion (b)'s hop-parity amendment was necessary but not
sufficient - hop count was a PROXY for the real variable.

**Expressibility audit (expressibility_audit.json, all 11 batch
survivors + 4 acquisition-tested types):** the separating variable is
LEG-2 STRENGTH INTO THE READOUT - max/sum weight of the cue's 1-hop
targets' positive edges directly into MN9_L:
- GNG521 (ONLY expresser): 3 direct routes, max leg-2 w=96, sum=98
- GNG611: 2 "direct" routes but w=1 (sum net 0.0) - dead weight
- GNG622: 1 route, w=5
- PRW043: 0 direct routes (3-hop geometry)
- 7 untested survivors span the range (GNG557: max 92 near-GNG521;
  IN05B094/AN17A015: w=1 dead weight)
This is a structural refinement of the lesson from the pilot, not a
contradiction: PRW043 (no leg-2 at all) and GNG611 (leg-2 present
but negligible) both fail; hop parity captured the PRW043 failure
mode but not the GNG611/622 one.

**Criterion amendment (replaces hop parity as the freeze gate for
expressibility): (b') leg-2 expressibility - a cue qualifies only if
its 1-hop target set contains >=1 target with a positive edge into
MN9_L of w >= THRESH_leg2.** Calibration: the only measured expresser
has max leg-2 = 96; all measured non-expressers have <=5. A principled
cut needs a measured threshold, not a round number - and GNG557 (max
leg-2 = 92, 1 route, untested) is the natural candidate partner.
**GNG557+GNG521 fails the original pairing rules (in-deg 8 vs 47 =
82% apart, outside even 35% bands)** - so the pairing bands, which
exist to control a confound degree was never shown to cause (WP3:
population size contra-indicated both directions), now conflict with
the expressibility criterion. RESOLUTION: (b') is a hard gate;
degree bands remain as recorded preference but yield when they admit
no compliant pair - recorded as a criterion-conflict resolution, not
a silent relaxation. New candidate pair: GNG521 + GNG557.
GNG557 must run the FULL original suite (c)-(f) + literature check +
its own eta* range-finder before any freeze. If GNG557 fails, the
remaining 2-hop strong-leg-2 pool is thin (GNG491 max 5, GNG610
max 7, AN17A024 max 4) - fallback is a documented protocol
discussion, not another quiet criterion edit.

## GNG557 diligence — degree-asymmetry check PRE-REGISTERED (2026-09-25, before any GNG557 acquisition data)

**Factual correction (recorded):** the asymmetry direction was
inverted in review: GNG521 in-deg = 47, GNG557 in-deg = 8 (batch
census). The concern is UNCHANGED in substance - 6x presynaptic-
surface asymmetry between task arms - but the proven expresser is
the high-degree one and the new candidate is the thin one (population
intuitions invert again, consistent with WP3's contra-indication of
population size for learnability).

**Why the check matters (review point, adopted):** the degree band may
have guarded ARM COMPARABILITY (statistical symmetry between task
arms), not learnability. Task A's D1 arm-swap partially controls
cue-level asymmetries (each cue trains in each role across arms),
but a systematic acquisition-speed or noise difference between cues
would still surface as arm-level variance WP4 must interpret.

**Registered design:**
- GNG557 full suite first: literature check -> census (a)/(b') ->
  group probes (c)/(d) n=10 seeds 32100-32109 -> (f) Jaccard vs
  GNG521. Any criterion fail -> fallback fork (registry), no freeze.
- eta* range-finder: grid {1e-5, 1e-4, 1e-3}, 10 accumulated trials
  + probe; GNG557 seeds 31900-31909, probe 31950.
- SHARED eta rule (restated from the pilot): both task cues run at
  the same eta - the smallest eta at which BOTH express. If GNG557
  eta* = 1e-4 (same as GNG521), shared eta = 1e-4 and BOTH cues get
  fresh 3x20 curves at 1e-4 (GNG521's existing Stage C ran at 1e-3,
  the v1 fallback, and is NOT the comparison basis). If GNG557
  needs 1e-3, shared eta = 1e-3 and GNG521's existing Stage C curve
  serves as its comparison arm.
- Curves: 3 blocks x 20 trials + probes at 5/10/15/20 per block.
  GNG557 blocks 32200/32300/32400 (+500 probe offsets); GNG521 (if
  fresh) blocks 32500/32600/32700 (+500).

**Registered comparison metrics (computed from the curves, both cues
at shared eta):**
1. trial-of-first-expression per block (first probe > 0)
2. probe level at trial 5 (early) and trial 20 (saturated) per block
3. cross-block SD of the trial-20 level
4. guard events
**Registered interpretation rules:**
- COMPARABLE: both cues express by trial 5, trial-20 levels within
  ~15 Hz, similar cross-block SD -> arms interpretable symmetrically;
  note in WP4 handoff.
- ASYMMETRIC (speed): one cue trails by >1 probe interval
  consistently -> record acquisition-speed asymmetry as a WP4
  interpretation caveat; D1 arm-swap becomes REQUIRED (not merely
  available) for symmetric claims.
- ASYMMETRIC (noise): cross-block SD differs >2x -> same caveat,
  plus WP4 power analysis must use the noisier cue's variance.
- Either asymmetry is recorded REGARDLESS of the freeze decision;
  it does not block the freeze (both cues expressing is the freeze
  gate), it modifies how WP4 interprets arm differences.

## GNG557 diligence — comparability analysis pre-registered BEFORE its curve exists (2026-09-25)

**Review refinement adopted:** the degree band's purpose is ARM
COMPARABILITY (both arms of the D1 swapped-assignment design should
learn at comparable speed/noise), not a learnability guard. The band
yields to the (b') expressibility gate for GNG521+GNG557 (in-deg
47 vs 8), and is REPLACED by this pre-registered analysis.

**Comparability analysis (registered before GNG557 has any
acquisition data):** matched 20-trial curves for BOTH cues at the
SHARED eta* = smallest eta at which both express with no guard fire.
Fresh seed blocks: GNG521 34000/34100/34200, GNG557 34300/34400/
34500; probes (cue-alone) after trials 5/10/15/20 at base+500.
Metrics: (i) per-cue eta* from range-finders; (ii) trial-to-first-
expression (probe > 0; granularity 5 trials); (iii) plateau = mean
trial-20 probe readout; (iv) across-block spread of (ii) and (iii).
**Interpretation rule (fixed now):** asymmetry is recorded as a
cue-identity covariate for ALL WP4 interpretation; the D1 arm-swap
still controls the cue->direction confound, so speed asymmetry does
not invalidate Task A, but cross-arm effect-size claims must state
it. NOT a freeze gate - a required analysis whose result ships with
the pair wherever the pair is used.

**Diligence order for GNG557 (all before any freeze):**
1. literature valence check (type-specific; uncharacterized !=
   neutral recorded)
2. full original suite (c)-(f): census (nt/status/hops/in-out/
   leg-2 max), group cue-alone + cue-cosugar probes n=10 (seeds
   33600-33609), aggregate target Jaccard vs GNG521
3. eta* range-finder under FROZEN 1-hop L1, grid {1e-5,1e-4,1e-3},
   seeds 33700-33709, probe 33750
4. comparability curves per the design above (needs eta* from 3)
5. freeze decision: pair v3 = GNG521 + GNG557 iff suite passes AND
   acquisition gate opens; comparability covariate recorded either
   way. If GNG557 cannot learn: fallback = documented protocol
   discussion (strong-leg-2 pool after GNG557 is thin: GNG491 max 5,
   GNG610 max 7, AN17A024 max 4).

## GNG557 verdict: suite FAIL on (c); acquisition OPEN — the (b')-(c) trade-off (2026-09-25)

**Result** (wp2_gng557_verdict.json / wp2_cue_probe_gng557.jsonl /
stage_b_gng557.jsonl): GNG557 [12595, 12901], both cholinergic/Traced,
2-hop, max leg-2 = 92 on both neurons, Jaccard vs GNG521 = 0.023.
- (c) FAIL: cue-alone MN9_L = [0,0,0,0,2,0,1,1,1,0] - 4/10 seeds
  express 1-2 Hz. Mean 0.6 Hz. NOT zero-baseline.
- (d) PASS: cosugar 82-87.
- Acquisition: eta*=1e-4 (probe 20 Hz), rising to 66 Hz at 1e-3, no
  guard fires. The (b') criterion is PREDICTIVE - strong leg-2 gave
  exactly the predicted learnability.
- FREEZE: NO.

**The trade-off, stated precisely:** the same strong direct leg into
the readout that makes a cue LEARNABLE under a 1-hop Hebbian window
((b') satisfied) is what gives it a weak INNATE expression tail
((c) violated). GNG521 achieves both (leg-2 max 96, baseline 0/20
across two n=10 suites) - but is apparently unusual in doing so.
This is a structural tension in the criterion set, not a flaw in one
candidate: the joint density of {strong leg-2, zero innate tail} is
low in this closure. Candidates measured so far: 2 expressers
(GNG521 0-tail, GNG557 0.6-Hz tail), 9 non-expressers.

**Pre-registered comparability analysis note:** GNG557's innate tail
is itself an arm-comparability asymmetry (its baseline is 0.6 Hz vs
GNG521's 0.0) - so the degree-band concern and the (c) concern
CONVERGE on the same question: are the two arms comparable? Both
reasons point the same way.

**The emerging pattern (candidate-selection audit trail):** five
families probed; every failure at a different criterion -
IR94e (d), water (e-literature), LB2a (c+d), GNG611/622 (b'-
expressibility), GNG557 (c). The criterion set is now measured as a
whole: each criterion has caught a real candidate that passed all
the others. The set is doing its job; the JOINT density of
satisfying all of them is the scarce commodity.

**FORK (registered before resolution):** pair v3 is dead under the
frozen criteria. Options:
- (i) Widen the search: batch-probe the remaining ~1011 unsampled
  cholinergic candidates for {leg-2 max >= 20-ish, (c), (d)} - the
  audit trail suggests several hundred are structurally eligible;
  cost ~2-4 background-hours, mechanical, no new criteria. Pre-stage:
  structural pre-filter (leg-2 max, (a)) FIRST at zero simulation
  cost, then probe survivors in batches of 15.
- (ii) Accept GNG521 alone as a single-cue design with the
  withheld-direction problem solved by the WITHIN-cue comparison
  (cue-alone vs cue+cosugar readout directions), dropping the
  two-cue arm-swap. Protocol change, re-registered.
- (iii) Accept the innate tail as a cue-identity covariate (like the
  comparability covariate) and freeze GNG521+GNG557 anyway - REJECTED
  by the standing rule: (c) exists to make 'learned' attributable to
  plasticity, and a 0.6 Hz innate tail is a real confound for a
  boundary measured to 1 Hz precision, not a bookkeeping nuance. The
  1 Hz innateness is distinguishable from learned expression only
  statistically, and the whole point of Task A is clean attribution.
Recommendation recorded: (i) first - mechanical, no criteria change,
and the pool is large; (ii) held as the fallback if the widened
search exhausts; (iii) rejected with reasoning above.

## Widened-search design notes (2026-09-26, review-directed, BEFORE pool probing)

**GNG521-as-fluke held explicitly:** five families, five different
killing criteria - the joint requirement (strong leg-2 AND zero
innate leak AND clean valence AND structural match) may carve a
genuinely NARROW region of this connectome. A second qualifying pair
may not exist by volume alone. The widened search is run as a
measured survey with a stopping rule (below), not an assumption that
the pool contains a pair.

**(iii)-rejection consistency (made explicit):** accepting GNG557's
0.6 Hz innate tail would hold this candidate to a LOWER standard than
WP6c's literal-zero verification and the WP9 spontaneous 0/30 control
- an inconsistency in standards, not a judgment call. Rejected.

**(ii) elevated from fallback to LIVE candidate design, registered
concretely:**
- single cue = GNG521 (the one clean expresser; baseline 0/20
  cue-alone, 80-88 cosugar)
- feed-direction readout: cue-alone MN9_L (trained: cue+sugar)
- withhold-direction readout: cue+cosugar MN9_L suppression below
  the 41.5 Hz boundary (trained: cue+bitter; postsynaptic site =
  bitter-active inhibitory interneurons, per the registry corollary)
- two independent substrate instances (fresh matrices from the frozen
  baseline): instance-1 trained feed, instance-2 trained withhold
- statistics: direction is within-cue, between-instance; cue identity
  is CONSTANT, so direction asymmetries attribute to the readout
  directions, not to cue identity. LOST vs two-cue: no cue-identity
  counterbalancing (arm-swap), no cross-cue transfer test. GAINED:
  the three structural-null cues (GNG611/GNG622/PRW043) become clean
  negative controls for the generalization test - novel-stimulus
  probes that cannot learn by construction.
**Stopping rule for (i):** probe the pre-filtered pool in batches;
if the first 3 batches (45 candidates) yield no candidate with
{zero leak AND acquisition}, OR the pre-filtered pool exhausts, tally
the trade-off pattern; if outcomes are dominated by the (b')-(c)
trade-off, adopt (ii) as the primary design and archive the survey
as the measurement of the qualifying region's sparsity.

**Retrospective check commissioned before probing (review
hypothesis):** does route structure - multiplicity/redundancy vs
concentration - separate GNG521 (leg-2 96, NO leak) from GNG557
(leg-2 92, 0.6 Hz leak)? A sharper variant motivated by the existing
data: GNG557's SINGLE-neuron probe was clean (0/5) while its GROUP
probe leaked - pointing at coincident leg-1 summation on shared
strong-leg2 targets as the leak mechanism (group members' kicks
summing on the same target). Hypothesis: leak requires coincident
leg-1 at/near single-kick firing threshold on a strong-leg2 target;
learnable-without-leak = strong leg-2 with SUB-threshold coincident
leg-1 (spontaneous drive cannot fire the relay; potentiation can
raise it). The refined pre-filter is adopted ONLY if the retrospective
data supports it; otherwise the raw filter stands and probes decide.

## Leak mechanism + two-feature screen + pool (2026-09-26, pre-launch)

**Retrospective leak analysis (leak_structure_retrospective.json) - the
review's redundancy hypothesis REFUTED, the two-variable instinct
CONFIRMED.** Route multiplicity does NOT separate leak from clean
(GNG521: 4 routes but 3 are leg2=1 dead weight; GNG557: 2 routes).
The separating variable is LEG-1 STRENGTH INTO THE STRONG-LEG-2 HUB:
- GNG521: leg1=4 into a leg2=96 hub -> clean, learnable
- water_LB3a: leg1=7 into a leg2=92 hub -> clean (the clincher:
  same max leg-2 as GNG557, opposite leak outcome)
- GNG557: leg1=27 into a leg2=92 hub -> 0.6 Hz leak. Mechanism:
  27 x 0.275 = 7.4 mV/kick >> ~3 mV gap -> the cue ALONE drives the
  hub over threshold -> the strong leg-2 spikes MN9_L reliably.
**Mechanistic statement (learnable-without-leak):** leg-1 must be
SUB-THRESHOLD (cue alone cannot fire the hub); leg-2 must be STRONG
(hub->readout, so sugar-driven hub activity during co-presentation
can potentiate the cue->hub correlation into expression). Training
works because SUGAR drives the hub during co-presentation - the cue
needs to correlate, not cause. Registered prediction: water_LB3a
would express if acquisition-tested (clean structure); remains
excluded on (e) literature grounds regardless. LB2a anomaly noted:
its 1 Hz leak through weak routes (max leg2=5, leg1=11) does not fit
the sub-threshold frame - recorded as unexplained; the screen RANKS,
the probe suite decides.

**Two-feature screen, VALIDATED on all four acquisition-knowns before
use:** L (learnable): max leg2 >= 20; N (no-leak): max leg1 among
strong-leg2 routes <= 8. Pool: 143 types pass (prefilter_pool.json).
Thresholds are CALIBRATED from the measured anchors (clean pair at
leg1=4 inside; leak case at leg1=27 outside; strong leg-2 saturates
at 92-96) and the pool is INSENSITIVE to the exact values (+-7%
across W2 in {10,20,50} x W1 in {8,12}) - not tuned to a desired
pool size. Screen-validates-clean on the knowns: GNG521 PASS,
GNG557/611/622 FAIL, matching every measured outcome.

**Wrinkle recorded:** the 143-type pool is dominated by central-brain
AN types whose routes run through the same leg2=92/96 hub clusters;
the hub is not SEZ-specific. This does not violate any criterion but
is recorded for interpretation.

**Batch probe (launched 2026-09-26):** pool ranked by n_routes then
type name (pre-declared order, no cherry-picking); probe in batches
of 15, group level, cue-alone + cue-cosugar, n=10 seeds per arm
(34000-34009 block), explicit 200 Hz, cue driven PRIMARY; freeze-grade
criteria (c) max(alone)==0 and (d) min(cosugar)>=41.5; checkpointed.
Target: >=2 passing types for the pair; if the first 15-batch yields
<2, continue to the next 15. Secondary analyses reported alongside:
per-batch pool diagnostics (where failures landed).

## Batch-1 partial results; leak-mechanism refutation; GNG380 lead (2026-09-26)

**Batch-1 partial (5/15 probed before a session interrupt; checkpoint
resumes free):** BM_Taste (d) FAIL (cosugar_min=0 - full suppression;
type name says taste modality, and it behaves like one); BM_Hau (c)
FAIL - leaks 47-77 Hz; GNG467 (c) FAIL - leaks 53-71 Hz; JO-F (c)+(d)
PASS; GNG380 (c)+(d) PASS at freeze-grade n=10 (alone 0/10,
cosugar_min 80).

**Leak-mechanism REFUTATION (self-caught, registered):** my
sub-threshold-hub hypothesis (leak = cue alone firing the strong-leg-2
hub via strong leg-1) is refuted by the batch data on THREE variants:
- v1 max-per-route leg-1: GNG467 l1=2 predicted clean, leaks 53-71.
- v2 summed leg-1 into strong hubs: GNG467 sum=5 predicted very
  clean, leaks; GNG380 sum=99 into hub 502 predicted leak, clean.
- v3 total transitive 2-hop drive: same inversions.
The hypothesis survives ONLY for GNG557 (l1=27 sums over 2 members;
plausibly hub-driven). GNG467/BM_Hau leak through something none of
the simple leg-1/leg-2 features capture (candidates: 3-hop amplified
chains; broad recruitment of the sugar pathway by the cue's wider
fan-out; hub-hub interactions). NOT solved. Consequence, registered:
leak is NOT structurally predictable by any feature measured so far;
the screen's job narrows to ranking by LEARNABILITY (leg-2 strength,
which HAS validated perfectly: every expresser has leg2 >= 92, every
non-expresser <= 5); criterion (c) remains an EMPIRICAL gate only.
Direct member->MN9_L edges checked for all seven types: NONE exist -
that trivial explanation is also dead.

**JO-F flag ((e)-spirit):** JO-F is a Johnston's Organ neuron class
(mechanosensory: hearing/gravity/wind; in males JO mediates courtship-
song detection - a documented, heavily valenced modality). It passed
(c)+(d), but using a real sensory channel with documented behavioral
programs re-introduces the water/IR94e problem class. EXCLUDED from
pair consideration pending a full (e) literature check it would
plausibly fail; kept on the batch record as probe-PASS.

**GNG380 - the lead candidate (diligence in progress):**
Cell Type Explorer (Reiser lab): GNG380 = SEZ/GNG-local cholinergic
interneuron type (88-94% of innervation within GNG; AKA CB2820 in
Flywire), no documented feeding/valence function; uncharacterized !=
neutral, so probes decide. Census: 6 members, all cholinergic/Traced,
NO direct MN9_L edges, Jaccard vs GNG521 = 0.056, max leg-2 = 96,
l1-into-strong-hubs = 2 (cleanest profile measured outside GNG521).
Freeze-grade (c)/(d) already passed at n=10. In-degrees heterogeneous
(14-197) - the pre-registered comparability analysis quantifies what
this costs. REMAINING for pair v4 (GNG521+GNG380): eta* range-finder
under frozen L1 (launched: grid {1e-5,1e-4,1e-3}, seeds
34100-34109/probe 34150), then the pre-registered comparability
curves at the shared eta*, then freeze decision.

**Batch-1 remainder (10 types) resuming in background** as audit
trail and backup pool in case GNG380 fails a later gate.

## Batch-1 complete: 3/15 survive; GNG380 gate OPEN at eta*=1e-4 (2026-09-26)

**Batch-1 full result (batch2_probe.jsonl, 15 types x 2 arms x 10
seeds, freeze-grade n):** survivors JO-F ((e)-flagged, mechanosen-
sory courtship modality - excluded pending the full (e) check),
GNG380, GNG108. Ten of fifteen types LEAK at full feed-mode rates
(63-90 Hz cue-alone) or suppress cosugar to 0 - the pre-filter's
'clean-profile' types are mostly pre-wired into the feed program.
This MEASURES the review's sparsity prediction: the joint criterion
region is narrow; GNG521 was closer to a fluke than a representative
case. The 143-type pool exists; passing (c)+(d) is the scarce part.
Continuing batches remain available but are no longer the critical
path - GNG380 has passed everything each failed candidate failed.

**GNG380 eta* range-finder (stage_b_gng380_verdict.json): eta* =
1e-4 (probe 4 Hz), rising to 130 Hz at 1e-3, no guard fires at any
eta. Gate OPEN.** Pair v4 = GNG521 + GNG380 at the SHARED eta* =
1e-4 (both cues' individual eta* agree - no shared-vs-individual
tension). GNG380: 6 members, all cholinergic/Traced, no direct MN9_L
edges, Jaccard vs GNG521 = 0.056, max leg-2 = 96, l1-into-strong-hubs
= 2 (cleanest measured profile), CTE-documented as SEZ-local
(AKA CB2820/Flywire), no documented feeding/valence function.

**Remaining before pair v4 freeze:** GNG108 ((c)+(d) PASS at n=10;
backup + comparability-relevant; needs leg-2 census + eta*) and the
pre-registered comparability curves (GNG521 vs GNG380 at shared
eta*=1e-4, 3 seed blocks each, 20 trials, probes at 5/10/15/20).
GNG108's diligence is cheap and runs after the comparability curves
(the pair decision does not depend on it).

## Comparability result; PAIR v4 FROZEN: GNG521 + GNG380 (2026-09-26)

**Comparability analysis (comparability_summary.json / comparability_
curves.jsonl). Registered deviation recorded: seed blocks 35000-35500
used instead of the pre-registered 34000-34500, which the batch
probe's 34000-34009 block overlapped; design otherwise exactly as
pre-registered (3 blocks x 20 trials, probes at 5/10/15/20, shared
eta*=1e-4, frozen 1-hop L1):**
- trial-to-first-expression: GNG521 [5,5,5]; GNG380 [5,5,5] -
  IDENTICAL; both cues express by the first probe in every block.
- plateau (trial-20 probe): GNG521 [81,84,83]; GNG380 [86,83,81].
- across-block spread: 3 Hz vs 5 Hz - same order as the between-cue
  plateau difference itself.
**CUE-IDENTITY COVARIATE (per the registered interpretation rule):
NO MATERIAL ASYMMETRY.** The degree-band concern (in-deg 47 vs
14-197) produces no measurable acquisition-speed or plateau
asymmetry at the shared eta*. Cross-arm effect-size claims in WP4
may proceed; the covariate ships with the pair as "negligible".

**PAIR v4 = GNG521 + GNG380 FROZEN as the Task A cue pair.** Every
registered freeze condition met:
- (a) both cholinergic, all Traced; no direct MN9_L edges
- (b') expressibility VALIDATED by acquisition, not just predicted:
  both have leg2=96 with sub-threshold l1 (4 / 2), and both express
  at the SAME eta*=1e-4 - the shared-eta* rule holds with zero
  per-cue tension
- (c) cue-alone 0/10 fresh consumption-grade seeds (GNG521 now 0/30
  across three independent suites); no leak
- (d) cosugar mins 80 / 82 - feed program intact under co-drive
- (e) literature: both functionally uncharacterized (CTE: GNG380 =
  SEZ-local AKA CB2820); uncharacterized != neutral recorded; the
  probes decided
- (f) target Jaccard 0.056
- acquisition gate OPEN (probe 77 Hz / 130 Hz at 1e-3-scale arms)
- comparability measured and symmetric (above)

**Training parameters frozen with the pair (WP4 consumption):**
eta=1e-4, V_MAG, w_max=766, 1-hop window (frozen L1 unchanged),
cue=PRIMARY 200 Hz, sugar=SECONDARY 200 Hz, readout MN9_L,
feed-direction readout = cue-alone rate (baseline 0), withhold-
direction readout = cue+cosugar rate (baseline 80-86), theta=41.5,
probes after trials 5/10/15/20, L0 control = identical schedule with
plasticity=None.

**Backup diligence (launched, non-gating): GNG108 eta* range-finder**
(seeds 36000-36009, probe 36050, grid {1e-5,1e-4,1e-3}) - batch
survivor, (c)+(d) PASS, screen profile leg2=96/l1=4, nearly identical
to GNG521's structure. If it expresses, it is the validated backup
cue; if not, the backup pool is batch-2+ (128 unprobed types remain).

**Open, non-blocking:** water_LB3a expressibility prediction test
(registered prediction: clean structure leg2=92/l1=7 => expression;
excluded as a cue on (e) grounds regardless; ~30 trials if run -
model validation only).

## Pair v4 — GNG521 + GNG380 FROZEN (2026-09-26)

**Comparability analysis result (comparability_summary.json, pre-
registered design, shared eta*=1e-4, 3 fresh blocks x 20 trials each,
probes at 5/10/15/20):**
- GNG521: first-expression trial 5 in 3/3 blocks; plateau 81/84/83
  (spread 3 Hz).
- GNG380: first-expression trial 5 in 3/3 blocks; plateau 86/83/81
  (spread 5 Hz).
The 6x in-degree asymmetry (47 vs 14-197 heterogeneous) did NOT
surface as acquisition-speed or reliability asymmetry at the measured
granularity. The pre-registered interpretation rule is satisfied:
asymmetry recorded as a cue-identity covariate - and the measured
asymmetry is negligible. NOTE: trial-5 is the earliest probe point,
so 'first-expression at trial 5' means 'by trial 5'; granularity is
coarse, but identical across all blocks for both cues.

**FREEZE CHECKLIST (pair v4 = GNG521 + GNG380):**
- (a) both cholinergic (GNG521 [15957,16327]; GNG380 6 members,
  all Traced)
- (b') leg-2 expressibility: GNG521 max 96; GNG380 max 96 - and BOTH
  verified by acquisition (77 / 4 Hz probes at eta*=1e-4; both > 0)
- (c) zero baseline: GNG521 0/15 (two independent n=10 suites);
  GNG380 0/10 (freeze-grade)
- (d) cosugar intact: GNG521 82-86; GNG380 min 80
- (e) literature: both types have NO documented feeding/valence
  function (GNG521 uncharacterized; GNG380 CTE-documented SEZ-local,
  AKA CB2820/Flywire, uncharacterized function); uncharacterized !=
  neutral recorded; both probe-verified clean at freeze-grade n
- (f) Jaccard 0.056 - low, but BOTH cues have verified readout
  access (both express), so the criterion's failure mode (disjoint
  readout access) is excluded; recorded explicitly
- eta*: BOTH 1e-4 - no shared-vs-individual tension; shared value
  recorded
- comparability: measured, favorable (above)
- guard: no fires in any arm of any stage

**PAIR V4 FROZEN.** The D1 arm-swap design applies unchanged: both
cues support both directions (feed-acquisition readout = cue-ALONE
MN9_L, baseline exactly 0; withhold-acquisition readout = cue+COSUGAR
MN9_L, baseline 80-86). Direction assignment swapped between training
arms. WP3 amended close-out follows; WP4 launches on this pair.

**Candidate-selection audit trail (final, 7 families):** IR94e (d),
water (e-lit), LB2a (c+d), GNG611+GNG622 (b'-expressibility),
GNG557 (c innate tail), batch-1 leaks x10 (c/d pre-wired), JO-F
(e-flag). Every criterion has caught real candidates; the joint
region is narrow and now MEASURED (143-type pool, 3 probe-passing
types in batch 1, of which 2 defensibly neutral-by-probe +
1 excluded on (e)).
