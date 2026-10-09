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

## Fine-grained onset probe + landscape note (2026-09-27, pre-registered before launch)

**Review point adopted: the trial-5 quantization caveat must be
resolved before the acquisition protocol freezes**, because WP5-WP7
compare rates/magnitudes at a precision coarse probes could wash out.

**Design (registered):** per (cue, seed block): ONE run, training
trials 1-4 with a cue-alone PROBE after EACH trial (probes are
is_probe - no plasticity applied, accumulation clean). GNG521 blocks
36000/36100/36200; GNG380 36300/36400/36500; probe seeds base+501..+504.
Frozen L1, shared eta*=1e-4, cue PRIMARY, explicit 200 Hz.

**Interpretation rule (fixed now, before data):**
- Identical onset pattern at trial-1 granularity -> comparability
  claim upgraded from 'by trial 5' to trial-level resolution.
- Divergence in trials 1-4 (one cue expresses at k, the other later)
  -> recorded as the REFINED cue-identity covariate: an acquisition-
  speed asymmetry exists below the comparability design's
  resolution. Pair v4 STAYS FROZEN (the D1 arm-swap still controls
  the cue->direction confound; selection criteria are unaffected),
  but ALL WP4+ rate/slope comparisons must use PER-CUE baselines and
  report onset per cue - never pooled. This is a covariate
  refinement, not a selection reopening.
- Zero expression before trial 5 in BOTH cues at both granularities
  is also informative: it locates onset in (4,5] and the WP4
  protocol should probe at trial 4 AND 5.

**Landscape note (review point 2):** the seven-family audit trail is
being written up NOW as its own scientific note
(docs/PLASTICITY_LANDSCAPE.md) while every candidate's death is fresh
and precisely characterized - the finding is independent of Task A's
outcome: under frozen 1-hop Hebbian plasticity, learnability on this
connectome is concentrated in a specific anatomical configuration
(strong leg-2 convergence onto the readout), empirically sparse
(3/15 batch types pass (c)+(d); 2 of those defensibly neutral), and
NOT structurally predictable from leak-side features (three screen
variants refuted).

## Fine-grained onset result (2026-09-27): divergence CONFIRMED below coarse resolution

**Result** (onset_finegrained_summary.json, trials 1-4 probed after
EACH trial, 3 blocks per cue, frozen L1, eta*=1e-4):
- GNG521: [0,0,0,62] / [0,0,0,75] / [0,0,0,62] - onset SHARP at the
  trial-4 boundary, perfectly reproducible, step-function shape
  (silent -> near-plateau in one trial).
- GNG380: [0,8,3,26] / [0,2,0,0] / [0,0,19,7] - onset GRADUAL and
  NOISY: low-rate flickers (2-8 Hz) anywhere from trial 2-3, one
  block with no expression through trial 4, inconsistent across
  seeds, ramp shape.

**Per the pre-registered interpretation rule:** a real acquisition-
speed/shape asymmetry exists below the comparability design's
resolution - the 6x in-degree gap surfaces in ONSET DYNAMICS (sharp
vs noisy-ramp), not in first-expression-at-probe or plateau. PAIR V4
STAYS FROZEN (D1 arm-swap still controls cue->direction; selection
criteria unaffected). MANDATORY for WP4+: (i) per-cue baselines and
per-cue onset reporting, never pooled across cues; (ii) acquisition
protocols probe at trial granularity 1-5 (both cues located onset
in (1,4]); (iii) GNG380's noisier onset means its direction claims
need across-seed spread reported, not just means. This refines the
cue-identity covariate; it does not reopen selection.

## WP4 pre-registration (Task A acquisition, L0 vs L1) - registered BEFORE launch

**Frozen inputs:** pair v4 (GNG521 [15957,16327]; GNG380 [50843,
53901,103327,129624,556072,559464]); shared eta*=1e-4; frozen 1-hop
V_MAG; w_max=766; guard = D6 thresholds live; cue PRIMARY @200,
drive SECONDARY @200 (feed=sugar_R, withhold=bitter_R from
wp6c_grn_seeds.json); duration 1000 ms.

**Arms (D1 anti-confound swap):** arm-1 = GNG521->feed,
GNG380->withhold; arm-2 = GNG521->withhold, GNG380->feed.
3 seed blocks per arm: arm-1 37000/37100/37200, arm-2 37300/37400/
37500. Identical seed structure across arms; only the drive
assignment swaps.

**Schedule per run:** 20 interleaved training trials (even: GNG521
trained toward its assigned direction; odd: GNG380). Probes (no
plasticity) after trials 1,2,3,4,5,10,15,20 - 4 probes per point:
cue-A alone, cue-A cosugar, cue-B alone, cue-B cosugar (cross-
direction leakage measured by design). Probe seeds base+1000+trial.
L0 control: identical schedule+seeds, plasticity=None, all 6 runs.

**Success criteria (frozen now):**
- Feed acquisition: L1 feed-assigned cue's cue-alone probe > 0 by
  trial 20 in every run; L0 cue-alone probes = 0 throughout.
- Withhold acquisition: L1 withhold-assigned cue's cue+cosugar
  probe < 41.5 Hz (frozen WP9 threshold) by trial 20; L0 stays
  >= 75.
- Per-cue reporting mandatory (refined covariate); n=3 seeds/arm is
  pilot-grade - WP5+ confirmatory uses 10 seeds per protocol S12.
- Guard silent throughout; any fire = halt + report.

**Pre-registered interpretation order if WITHHOLD direction fails:**
(1) insufficient inhibitory-edge overlap - check per-run signed
weight-delta on negative cue-incident edges (potentiated GABA-edge
mass present but cosugar suppression absent = overlap insufficient);
(2) eta below the suppressive pathway's threshold - recorded,
WP5 follow-up at eta=1e-3 withhold-only arm; (3) withhold needs
mechanisms beyond frozen L1 - registered as NEGATIVE RESULT (never
a silent mechanism change; the leg-2 geometry that enables feed
learning has no measured suppressive analog yet).

**Known risk recorded honestly:** bitter co-drive suppresses
broadly, so the cue's potentiated edge set under withhold training
is the aversive-active subset of its 1-hop targets; whether that
subset's inhibitory mass can beat the 80-86 Hz sugar drive is
EXACTLY what WP4 measures. A withhold null is a publishable result
(landscape note already covers the geometry framing), not a failure
of the run.

## WP4 amendment (pre-launch, review-directed): symmetric criteria + seed count

**Feed criterion FIXED (asymmetric criteria were a real confound in
the frozen draft):**
- PRIMARY (both directions, symmetric): the assigned readout CROSSES
  theta=41.5 Hz in the assigned direction by trial 20 - feed: cue-
  alone probe >= 41.5; withhold: cue+cosugar probe < 41.5.
- SECONDARY: any-expression (feed: > 0; withhold: any decrease below
  the 75-86 baseline range) - reported, never load-bearing.
- Acquisition-speed metric: trials-to-theta (first probe point at/
  beyond the criterion), reported per cue with across-seed spread -
  GNG380's ramp makes this the meaningful speed measure, not
  first-expression.
Rationale: the draft's feed criterion (> 0) would have been
satisfiable by GNG380's 2-8 Hz onset flickers while the withhold
criterion sat at the decision threshold - a difference between
directions could have come from the criteria themselves. The theta
readout exists to make 'feed' mean something specific; the criteria
now both sit at it.

**Seed count RAISED per protocol S22 (development stage: 5-10 seeds,
seed-as-unit S23/S24):** WP4 runs 6 seed blocks PER ARM (was 3) -
arm-1 seeds 37000/37100/37200/37600/37700/37800; arm-2
37300/37400/37500/37900/38000/38100. n=6 seeds/arm at seed-level
aggregation, powered for GNG380's observed across-seed spread
(trial-5 probes: 3-34 Hz). L0 control: same 12 blocks, plasticity
None. n=6 is inside the protocol's 5-10 development band; the
WP5+ confirmatory stage remains 10 frozen seeds per S22.

**Probe schedule unchanged** (1,2,3,4,5,10,15,20 - both cues
located onset in (1,4]; trials-to-theta measured at the same
granularity for both cues). Cross-direction probes at every point
(4 probes/point) unchanged. Interleaving unchanged. D1 arm-swap
unchanged. Guard live. Interpretation orders unchanged.

## WP4 v2 relaunch (2026-09-27, post-audit)

**Reviewer's flush-at-block-end hypothesis: empirically DISPROVEN**
(two mid-block samples: 39 records -> 52, exactly matching the
cumulative schedule; the writer appends per-record). But the audit it
triggered found three REAL defects, worse than the hypothesis:
- **(1) Weight state was NEVER checkpointed in v0** (run.save() never
  called; 0 run_state.json, 0 weight .npz files): a mid-block resume
  would have replayed completed trials WITHOUT their potentiation -
  records from two different weight trajectories stitched silently.
  This is the trajectory-stitching failure the reviewer's question
  was circling; it is worse than lost compute.
- (2) The v0 seed scheme had 4 training-seed overlaps with onset
  probe seeds (37001-37004) and 16 probe/train collisions
  (38000-38113 range).
- (3) The missing-dir crash was real but trivial (mkdir added).

**v0 run DISCARDED per fresh-seeds rule:** ALL 24 BLOCKS COMPLETED
(verified by file count 2026-09-27: 24/24 block JSONLs, all 52
records) on the flawed design - roughly 10 HOURS of compute
discarded, preserved at results/phase2/wp4_discarded_v0/ as the
superseded artifact; never to be aggregated with v2. The "zero lost
trials" claim in the launch report was WRONG - corrected: the
compute was lost on discard, nothing lost from the record (files
intact). CORRECTION TRAIL for this erratum: first stated "7 blocks
(~50 min)" - a miscount; the reviewer caught the self-contradiction
(24 blocks at ~25 min/block cannot be 50 min); file count settles
it: 24 completed, ~10 h.

**v2 fixes (all verified by tests before relaunch):**
- run.save() after EVERY simulation; TrainingRun.load() at block
  start with hash verification (tests: resume continues from
  checkpointed weights, reproduces continuation bit-for-bit, no
  stitching; I/O artifacts appear after first simulation).
- New seed scheme: training 40000 + bi*100 + t; probe
  50000 + bi*1000 + t*10 + pi (bi = global block index 0-23).
  VERIFIED disjoint from ALL prior stages including discarded v0
  (0 overlaps, 0 internal collisions; audit artifact
  results/phase2/wp4_seed_audit.json).

**Development-stage labeling (reviewer point, registered):** WP4 is
DEVELOPMENT-stage per protocol S22 (5-10 seeds); nothing in its
report reads as confirmatory - the confirmatory stage requires a
separately pre-registered frozen seed set (S22) and runs in WP5+.

**L0 zero-variance note (reviewer point, registered):** L0 cue-alone
is exactly 0 by construction - the feed-direction comparison is
"is L1 above zero at each seed" (a one-sample claim against a
degenerate null), not a two-sample test with a real null
distribution. The analysis states this; no fake two-sample framing.

## WP4 RESULT (2026-09-28, development-stage; report: docs/WP4_REPORT.md)

**Arm1 PASSES both directions (6/6 seeds each):** GNG521-feed
(alone 69-81, all >= theta=41.5; L0 exactly 0) and GNG380-withhold
(cosugar 2-6, all < 41.5; L0 83-87 - suppression to ~1/15 of
baseline). Guard silent in all 24 blocks. Cross-direction leakage:
none - failures produced NO direction-appropriate expression, not
wrong-direction expression.

**Arm2 FAILS both directions (0/6 each):** GNG521-withhold (cosugar
83-89 vs L0 81-87, never suppressed) and GNG380-feed (alone 3-9,
never above theta). Potentiation OCCURRED in both arms (weight_diff
nonzero per trial; arm2 blk0 t19: 233 edges, sum|D| 419.6) - arm2
learned toward something that did not express.

**RETRACTED (2026-10-01, reviewer-caught): the 'cue x direction
interaction / GNG380 learned withhold-ONLY' claim above was a
TRIAL-BUDGET ARTIFACT, not a structural finding.** The audit:
(1) configs verified correct from records - arm2 GNG380-feed train
trials read 81-89 Hz (sugar co-drive wired, no rate default, no
label swap); arm2 GNG521-withhold train trials read 0 (bitter
wired); budget 10/10 per cue as designed. (2) The pilot's own
GNG380 feed curve (20 CONSECUTIVE trials) was 3-34 Hz at trial 5,
5-19 Hz at trial 10, 19-21 at 15, and only 81-86 at 20 - the ramp
crosses theta between feed-trials 15-20. Arm2's interleaved
schedule delivers only 10 feed trials by the trial-20 probe point,
and arm2's GNG380 alone-probes (3-9 Hz) sit INSIDE the pilot's
trial-10 range. Same ramp, half the budget - there is no conflict
with the pilot and no direction-specificity. 'Seed-stable 0/6' was
stability of an under-dosed schedule, not of a structural property.
CORRECTED asymmetry: GNG521 = feed YES / withhold NO (genuine:
GNG380 suppressed by withhold-trial 5 with the SAME 10-trial budget
GNG521-withhold never engaged in - the contrast is built into the
arms); GNG380 = withhold YES / feed UNKNOWN at 10 trials (re-test
launched). Task B reopening ON HOLD pending the re-test.

**Per-registered interpretation orders applied:** GNG521-withhold
fails at step 1 (inhibitory-edge overlap insufficient - potentiation
present, suppression never crossed theta); eta=1e-3 withhold-only
follow-up arm REGISTERED for WP5. GNG380-feed fails outside that
order (pathway-specific leg-2: its suppressive connectivity works,
its feed-mode potentiation never cleared theta against the
exactly-zero baseline) - recorded as its own negative result.

**Downstream (registered):** WP5 retention proceeds on the LEARNED
directions only (GNG521-feed, GNG380-withhold) at confirmatory seed
count (S22), asymmetry carried as covariate. Task B (reversal) as
specified requires direction-switchable cues - the current pair is
not; reversal design must be reopened with this finding on record.

**Erratum CORRECTED (reviewer-caught):** v0 = 24 COMPLETED blocks
(~10 h compute discarded; earlier '7 blocks / ~50 min' was a
miscount; file count verified 24/24, all 52 records). Probe purity
VERIFIED BY TEST (hash unchanged through probe; N-probes no
accumulation; 7/7 I/O tests, suite 98/98).

## GNG380-feed re-test (2026-10-01, registered before launch)

Reviewer's option-1 vs option-2 resolved by a two-arm re-test:
- **Arm A (budget test):** 20 CONSECUTIVE GNG380-feed trials x 3
  seeds (42000/42100/42200) - exact replication of the pilot's
  schedule at WP4's seed scheme. Prediction: alone crosses theta
  between trials 15-20 (replicating pilot 81-86).
- **Arm B (interleave test):** 40 interleaved trials (GNG380-feed
  odd, GNG521-withhold even - arm2's structure doubled) x 3 seeds
  (42300/42400/42500) - GNG380 receives 20 feed trials, same as
  arm A, but alternating with bitter-drive trials. If B also
  crosses theta by feed-trial 15-20: arm2's failure was pure
  budget, no suppression. If B stays low while A crosses: the
  interleaved (bitter-alternating) context suppresses GNG380's
  excitatory path - a REAL finding (reviewer option 2), and the
  WP4 interleave design itself would be implicated for future
  multi-cue schedules.
Probes: alone + cosugar at feed-trials 5/10/15/20 (A) and at
cumulative feed-trials 5/10/15/20 (B, probe after the Nth feed
trial); probe seeds 80000+bi*1000+t*10+pi (A) / 81000+... (B) -
disjoint from all prior ranges (nothing above 73193 in use).
Frozen L1, eta*=1e-4, guard live, per-simulation checkpoints,
explicit 200 Hz. Interpretation registered above.

## WP4 ERRATUM (2026-10-01, reviewer-caught): 'direction-specific leg-2' RETRACTED - dose artifact

**The reviewer's conflict was real and resolved by data already on
disk (no new compute):** arm2 GNG380-feed (3-9 Hz at final probe)
vs the WP3 pilot (81-86 Hz) looked like a direct contradiction.
CONFIG DIFF: clean - all drive rates explicit 200.0 in both scripts,
eta=1e-4 both; no rate-default reversion, no wiring mix-up (drive=
sugar for feed in both). THE REAL DIFFERENCE: DOSE. The pilot gave
GNG380 20 CONSECUTIVE feed trials; WP4's interleaved schedule gives
each cue 10 (odd indices only). At MATCHED dose the curves AGREE:
- pilot at 10 feed trials: 5, 5, 19 Hz (below theta)
- WP4 arm2 final probe (= 10 feed trials): 3-9 Hz across 6 seeds
The pilot's 81-86 Hz was at 20 feed trials (19-21 at 15 trials,
STILL below theta). GNG380 crosses theta between feed-trials 15-20;
arm2 gave it 10. **GNG380 CAN learn feed - the pilot replicated in
WP4 at matched dose.** 'GNG380 learned withhold-only' is WRONG.

**Corrected findings:**
- Arm1 STANDS: GNG521-feed 6/6 (10 trials suffice - sharp onset);
  GNG380-withhold 6/6 (suppression fast, <=10 trials). No leakage,
  guard silent.
- Arm2 GNG380-feed 0/6 = DOSE ARTIFACT, not structural. Retracted
  from the landscape framing (the landscape note itself never
  claimed direction-specificity - no edit needed there).
- Arm2 GNG521-withhold: genuine NEGATIVE at 10-trial dose (no dose
  reference exists for GNG521+bitter anywhere in the project);
  pre-registered interpretation order stands; eta=1e-3 follow-up
  registered for WP5.
- NEW FINDING (replaces the retracted one): per-direction
  ACQUISITION SPEED differs - GNG521-feed fast (theta by trial 5-10),
  GNG380-feed slow (theta at 15-20 feed trials), GNG380-withhold
  fast (<=10 trials), GNG521-withhold not achieved at 10 trials.
  The equal-trials interleaved design UNDER-DOSES slow directions;
  per-direction dose must be matched to per-direction speed in any
  design that trains both directions in one run.
- Task B implication CHANGES: not 'cues cannot switch directions'
  (retracted) but 'per-direction dose matching required'; reversal
  design reopening proceeds on the dose finding.
- Probe-variance caveat registered: blk5 showed an 81 Hz probe at 5
  feed trials (single probe per combo per point; probe-seed variance
  can spike; came back down at later points). WP5+ probes should
  average >=2 probe sims per point at distinct seeds.

**Standing rule (new):** when a WP4-style result contradicts an
earlier measurement of the same nominal condition, FIRST diff the
trial-dose (trials-per-direction per arm), not just the config -
interleaved designs halve per-cue dose silently.

## WP4 addendum (2026-10-03, review-directed): negative-result downgrade + proactive dose rule

**GNG521-withhold negative DOWNGRADED to provisional** (reviewer
point 1): the blk5 probe-variance caveat applies to it, and more
severely - a single probe per point could sit just under theta by
noise (false NEGATIVE risk; the symmetric case of blk5's false-
positive spike to 81 Hz). No dose reference exists for
GNG521+bitter anywhere in the project. '0/6 FAIL' must NOT be read
with arm1-pass confidence until it has the >=2-probes-per-point
treatment now required going forward. Arm1's clean passes are the
strong results; this negative is weaker evidence, explicitly.

**Dose-diffing rule upgraded from reactive to PROACTIVE (reviewer
point 2):** the v0 root cause was a DESIGN property (interleaved
equal-trial schedules silently halve per-cue dose), which is why the
config diff came back clean. NEW RULE: every future design
COMPUTES and pre-registers expected per-condition dose (trials per
cue per direction under its interleaving scheme) and CHECKS it
against existing dose-response data BEFORE launch. Applied to Task B
below (dose table in docs/TASK_B_DESIGN.md).

**Seed scheme for Task B (verified disjoint by computation NOW,
pre-launch):** training 80000 + bi*100 + t (bi 0-11; verified max 81129 for t in range(30), 81114 for R1's t 0-14);
probe 90000 + bi*1000 + pt*10 + ty*2 + rep (bi 0-11, pt 0-6, ty
0-3, rep 0-1; max 101067; >=2 probe sims per point per type).
0 internal collisions; min ranges > prior max (73193).

## R2 masking probe + R1 interpretation (2026-10-03, pre-launch, review-directed)

**Reversal outcome has TWO possible states:** under potentiative-only
V_MAG, R2 reversal works by ADDING a new strong pathway that
outcompetes the old one at the readout - not by weakening the old
weights. A cue passing R2's criterion is therefore either (i)
GENUINELY REORGANIZED or (ii) MASKED - old pathway fully intact,
suppressed by a stronger competing drive present during the reversal
protocol's own probes. Different predictions under a condition R2
must test: the reversed cue probed WITHOUT the competing drive after
reversal succeeds.

**MASKING TEST (registered, LOAD-BEARING for R2 claims):**
- GNG521 (feed->withhold reversal; old = excitatory): cue-ALONE probe
  (no bitter, no sugar) at the final reversal points. alone >= theta
  = MASKED (old pathway intact; readout reflects the current winner);
  alone < theta = GENUINE REORGANIZATION (old response gone even
  without the competitor - includes the case of a spontaneously
  active new suppressive pathway).
- GNG380 (withhold->feed reversal; old = suppressive): cue+COSUGAR
  probe at the final points. cosugar < theta STILL = old suppression
  intact (NOT unlearned - two state-dependent mappings);
  cosugar >= theta = GENUINE REORGANIZATION.
- >=2 sims/point. Claim entitlement: 'reversed' requires the masking
  test passed; otherwise the finding is 'masked by a second,
  competing association' (two-association coexistence - still a
  result, a different one). Registered BEFORE any R2 data exists.

**R1 interpretation (ambiguity resolved pre-launch):** weights are
FROZEN during retention - no decay mechanism exists in the model -
so the 'decay curve' is a DISTRIBUTIONAL STABILITY test at the
retained state: 5 points x 2 reps x 4 probe types at distinct seeds,
plasticity off (is_probe). The +N spacing is decorative; points are
repeated measurements. Point passes iff BOTH reps on the learned
side of theta (conservative: a wrong-side spike = instability
signal); block passes iff all points pass; criterion >=5/6 blocks.
Below-theta = recorded retention failure - investigated, never
patched by retraining.

**Seed ranges (verified pairwise-disjoint by computation NOW):**
- R1 training 80000 + bi*100 + t (bi 0-11, t 0-14; max 81114)
- R1 probes 90000 + bi*1000 + pt*10 + ty*2 + rep (pt 0-4; max 101047)
- R2 training 85000 + bi*100 + t (t 0-24; verified max 86124 -
  separate range: R2 continues R1's blocks, so it cannot reuse
  80000+ ranges)
- R2 probes 120000 + bi*2000 + pt*10 + ty*2 + rep (pt 0-6; verified
  max 142047; base 120000 - far above every other range, collision
  impossible by construction. CORRECTION TRAIL: the first draft
  (95000 + bi*1000) collided with r1_probe at 280 values; bi*2000
  still collided at 160 (r1 bi=7 window = r2 bi=1 window at 97000);
  caught by the pre-launch pairwise check, settled by computation
  before launch)
- L0-R shares R1's seed structure BY DESIGN (matched-seed paired
  comparison, as in WP4)
- all pairwise disjoint (verified after TWO collision fixes), above prior max 73193
- CORRECTION: the 'WP4 addendum' seed line said 'max 81229' - typo;
  verified max is 81129 (t in range(30)) / 81114 (R1's t 0-14).

## R2 criteria fix (2026-10-03, review-directed, duplicate-run reconcile)

**SELF-CAUGHT BUG (exposed by the reviewer's probe):** the drafted R2
unlearning criteria had the metrics SWAPPED - GNG521 unlearning was
written as 'cosugar >= theta' (contradicting relearning 'cosugar <
theta') and GNG380's as 'cue-alone >= theta' (= its relearning
criterion). CORRECTED: unlearning = OLD response gone WITHOUT the
competing drive (GNG521: cue-alone < theta - the no-competing-drive
condition itself; GNG380: cosugar >= theta - the old readout
condition). The probe the reviewer asked for IS the corrected
unlearning criterion; the draft would have mis-read the very probes
that already existed.

**Retention-phase design decision (registered, ambiguity resolved):**
'retention probes at +0/+5/+10/+15/+20 trials post-acquisition (no
further training)' is ambiguous about what the intervening trials
are. RESOLVED: 20 SPONTANEOUS trials (no cue, no drive) with the
frozen rule ACTIVE (plasticity on - the rule does not turn off in
quiet periods). Under potentiative-only Hebbian the learned edges
cannot weaken; retention failure modes are (1) baseline drift from
spontaneous potentiation (readout spontaneous rate rises, specificity
blurs), (2) guard fires. Both recorded as genuine retention results,
never patched. L0-R spontaneous trials run plasticity=None
(deterministic per seed - 1 sim per type per point; the 2-sim
variance rule is meaningless for a deterministic control, noted).

**R1 acquisition gate:** after 15 acquisition trials, the direction
metric must be on the learned side of theta; blocks failing
acquisition are recorded as acquisition failures and their retention
result is N/A-with-reason (standing convention).

NOTE (reconcile): an interrupted turn had already registered the masking
test + seed ranges ('R2 masking probe + R1 interpretation (2026-10-03)') and
launched R1; the committed design (weights FROZEN during retention,
distributional-stability interpretation) is authoritative. My
'spontaneous trials with rule active' variant is WITHDRAWN - it was a
duplicate of already-registered structure and conflicts with the running
design. The criteria-swap fix above stands (it corrected the drafted R2
unlearning parenthetical; the masking-test probes the reviewer asked for
ARE the corrected unlearning criteria).

## R1 implementation erratum (2026-10-03, pre-analysis): 3 probe points, not 5

**Discrepancy found on first inspection of the artifacts:** the
registry's R1 design states '5 points x 2 reps x 4 probe types', but
the running script's loop bound (for t in range(15), with
PROBE_POINTS=(0,5,10,15,20)) means t=15 and t=20 never fire - the
data carry **3 probe points (t=0,5,10)**, 39 records/block (15
training + 3x8 probes).

**Substance preserved, power reduced:** the committed design already
registers that the +N spacing is decorative and the points are
REPEATED MEASUREMENTS of the same retained state (weights frozen
during retention - no decay mechanism exists). 3 points x 2 reps = 6
repeated measurements per probe type per block, still above the
>=2-per-point variance rule. What is lost is rep count (6 vs 10 per
type per block); what is NOT lost is the design's validity - the
retained-state stability measurement is intact.

**Disposition:** recorded, NOT patched mid-run (the run is ~21/24
blocks complete; re-running for 2 extra repeated measurements would
cost hours for no additional design validity). The registry's R1
design text stands as intent; THIS erratum is the implementation
record. Any report must state 3 points / 6 reps, never 5/10.

## R1 RESULT + R2 launch (2026-10-03)

**R1 RETENTION: 12/12 blocks PASS** (development-stage, 3 probe points
x 2 reps per the implementation erratum):
- GNG521-feed (alone, both reps, t=10): blk0 77/75, blk1 79/78,
  blk2 78/78, blk3 87/84, blk4 76/68, blk5 80/82 - all >= theta.
- GNG380-withhold (cosugar, both reps, t=10): blk0 2/3, blk1 1/2,
  blk2 1/5, blk3 2/4, blk4 1/5, blk5 5/1 - all < theta.
- L0-R control: cue-alone EXACTLY 0 across every control block
  (degenerate null as registered); guard 0 fires across all 24 blocks.
**Retention is clean at the retained state** - no drift, no guard
activity, both learned directions stable.

**R1 process note:** R1 was externally killed (process.kill) at 21/24
blocks after ~30h; the resume was free and exact (L1 12/12 skipped;
the partial L0 block completed to 39 records; L0 is deterministic
under plasticity=None so partial-block resume reproduces the same
results). Per-simulation checkpointing validated in production.

**SELF-CAUGHT BUG #2 (same family as the load-traps, caught before any
R2 data ran):** the R2 retention gate filtered R1 probes by ptype only
- but the no-leakage set records BOTH cues at every point, so the
gate mixed the trained cue's values (77/75) with the untrained cue's
(0/0, by construction) and read EVERY block as retention-FAIL,
exiting R2 immediately with 12 N/A-with-reason records. Fixed by
filtering on the trained cue. (The N/A files are superseded artifacts,
never evidence.) Family lesson, now twice in one stage: any criterion
reading a multi-subject probe set MUST filter to its subject - the
same class as the load() plasticity gate.

**R2 launched (retained-state start VERIFIED in production):** first
block's t=1 probes read GNG521-alone 83/85 Hz (the acquired state) and
GNG380-alone 0 / cosugar 84-85 (leak-free baseline intact) - the
retained matrix is loaded, not pristine. Reversal training shows
plasticity active on the retained state (trial-0 weight_diff: 12 edges
changed). 24 blocks (12 L1 + 12 L0-R from the same retained states),
25 trials each, masking-test probes at every point + final set,
corrected unlearning criteria, guard live, per-simulation checkpoints.

## R2 near-miss + account correction (2026-10-08, pre-verdict)

**CORRECTION of my own 10-03 claim:** 'R2 launches automatically on
retained blocks' was a claim, not a mechanism - there is NO auto-chain.
R2 did not run on 10-03/10-04 against R1 v1's verdict; the first true
launch was today 10-08 after R1 v2 completed.

**The stale-artifact near-miss (stitched-trajectory class, caught
pre-aggregation):** a 10-04 R2 attempt left 12 l1/l0 gng521_rev
blocks + 12 buggy-gate R2_NA files (gate read t=10 AND mixed both
cues' probes: final_point_vals like [77,75,0,0] prove the mixed read)
plus checkpoint dirs in results/phase2/taskB_r2/. Today's first
relaunch RESUMED those checkpoints - 12 'blocks' in ~5 min was the
tell (real compute is ~12 min/block): it was re-emitting 10-04 data
computed from R1 v1's END-OF-ACQUISITION state, not the registered
end-of-retention input state. ALL of it quarantined to
taskB_r2/quarantine_2026-10-08/ (36 + 2 artifacts); never aggregated.

**R1 v2 as-run structure (verified from record counts, 78/block):**
acquisition = trials 0-14 with drive (inherited records from v1's
run, valid acquisition); retention = trials 15-29 no stimulus,
plasticity ACTIVE (spontaneous coincidences possible); probes at
0,5,10 (acq-phase) and 15,20,25 (ret-phase; t=30 never fires,
range(30)). The 12/12 RETAINED verdict stands on t=25 ret-phase
probes. Weights are NOT frozen in the as-run retention (registry
intent said frozen; the run applied the rule during quiet trials -
distributional stability held ANYWAY: GNG521 flat 76-89, GNG380
suppressed 0-5, guard 0 fires). Recorded as as-run vs registered
intent divergence, not patched retroactively.

**Gate fixes verified in the live R2:** corrected final point (t=25),
cue filter (fixed 10-03), 12/12 blocks admitted, 0 N/A files.
Entry probes confirm correct input state (GNG521 alone 83 Hz at
block entry = the acquired+retained state).

**Standing rule (extends the resume rule):** resume across a DESIGN
REVISION is forbidden without a provenance check - checkpoints and
JSONLs from a superseded design must be quarantined BEFORE relaunch,
because find_rec/checkpoint resume will silently continue the old
trajectory. The 5-minute '12 blocks done' speed was the detection
signal: resume-completion rate >> compute rate means stale data.

## R1 retention weight-freeze VERIFIED (2026-10-08, review-directed check)

**The reviewer's inference is now a measurement.** Direct weight-hash
comparison across the retention phase (checkpoint files are
trial-keyed: weights_trial_15 = end-of-acquisition train t=14;
16-30 = the 15 no-stimulus retention trials): ALL 12 L1 BLOCKS
bit-identical end-acq -> end-retention. The rule was LIVE but had
nothing to act on (spontaneous activity dead silent - WP8's 0/30,
now confirmed at the weight level in Task B context). The as-run vs
registered divergence is therefore MOOT: R1's 12/12 RETAINED verdict
was measured under an effectively frozen condition, and 'retention
under frozen weights' may be claimed with evidence, not inference.

**R2 inheritance checked:** R2 has NO retention phase (25 reversal
trials + probes only), so the unfrozen-retention behavior cannot
propagate; R2's input state = R1's end-of-retention weights =
bit-identical to end-of-acquisition - the cleanest possible provenance.

**SELF-CAUGHT VACUOUS-CHECK lesson (my own second attempt):** the
intermediate hash check used a wrong phase boundary (sim-counted 38)
against trial-keyed filenames with only 30 files - every block was
skipped and the check printed 'ALL IDENTICAL' VACUOUSLY. Caught by
asserting scope (check 3 asserts max(files) >= boundary+15 and
fails loudly on layout surprises). Standing rule: a verification must
FAIL LOUDLY when its scope is empty - a check that verifies nothing
must not emit a clean verdict. (Same class as the v0 'zero lost
trials' claim: assertions without coverage.)

## Task B R2 REVERSAL VERDICT (2026-10-08, development-stage, n=6 blocks/condition)

**Both cues: 6/6 NOT REVERSED by the final-state two-state gate.**
Guard 0 fires across all 24 blocks. No block landed in the
TWO-ASSOCIATION (masked) cell - masking never occurred; the
competitive mechanism did not even establish a second association.

**GNG521 (feed->withhold): total negative, seed-stable.** Old feed
pathway fully intact (alone 80-87, cosugar 84-89, both >> theta);
no suppression acquired at 25 trials (L0 84-90 unchanged). The WP4
10-trial negative is now STRUCTURAL at 2.5x dose: bitter co-drive +
potentiative-only V_MAG cannot suppress an established excitatory
association. Interpretation step 3: unlearning needs mechanisms
beyond frozen L1. PUBLISHABLE NEGATIVE.

**GNG380 (withhold->feed): TRANSIENT CROSSING + REGRESSION - the
finding of the run.** Full trajectories (all 6 blocks, tight +-2 Hz):
cosugar rises monotonically 2-3 -> 16-17 (t4) -> 31-34 (t9) -> 40-46
(t14), CROSSES theta=41.5 at trial 15 in 5/6 blocks (both reps; blk5
at 40 just short), peaks ~trial 15-16 (train readout 49), then
REGRESSES to 26-27 by trial 25. cue-alone follows the same arc
delayed (0 -> 43-44 at t14 -> 26-27). Weight evidence: potentiation
CONTINUES throughout (n_edges_changed 212->300+ per trial, never
zero) - the rule keeps strengthening cue-incident edges past the
point where the readout peaked; the regression is over-accumulation
degrading the readout, not decay (weights never weaken - V_MAG is
potentiative-only; the rise-fall is a DYNAMICS phenomenon, readout
nonmonotonicity under monotone weight growth).

**Verdict per registered criteria:** trials-to-criterion (any
crossing): 5/6 blocks at trial 15 - the old suppression CAN be
eroded by competitive potentiation. Final state: 6/6 NOT REVERSED -
the crossing does not CONSOLIDATE; no stable new association forms
within the registered dose.

**Pre-registered interpretation applied:** reversal under frozen L1
is NOT BLOCKED but UNSTABLE: the competitive mechanism erodes the
old association and passes theta transiently, but cannot consolidate
a new one; continued training degrades the readout back below
theta. Reversal-relevant mechanism deficits, ranked: (1) no
consolidation/stabilization mechanism; (2) no weakening mechanism
(same as GNG521's finding); (3) dose overshoot is real and
measured - the 25-trial registered dose contains the crossing
(trial 15) and the regression (trial 25); a reversal protocol
needs a stopping/consolidation criterion, not more trials.

**Landscape note extension (registered):** this closes the Task B
question for L1: acquisition YES (WP4), retention YES (R1),
reversal NO - blocked for GNG521 (cannot suppress), unstable for
GNG380 (crosses but cannot hold). Reversal thus joins the
L3/dopamine-class mechanisms as OUT OF SCOPE for frozen L1 - the
substrate can learn and keep but cannot unlearn. Cross-architecture
note: Cadence's designers treat two-association coexistence
(TemporalMemory.protect, interference-managed records) as a core
operating condition - consistent with our measurement that without
an explicit weakening mechanism reversal is competition-or-nothing. [CALIBRATION CORRECTION 2026-10-08, review-directed:
DOWNGRADED from 'cross-architecture validation' to a SUGGESTIVE
PARALLEL. The comparison conflates two different kinds of claims:
Cadence's competitive/interference-based memory is a DOCUMENTED
DESIGN CHOICE ('we built it this way'); our masking-or-nothing
result is a MEASURED EMPIRICAL FINDING ('it behaves this way').
Similar vocabulary ('interference', 'competition', protect()) is
not evidence the same computational principle operates in both -
it is two designers, for different reasons, both ending up without
a weakening mechanism. Possible real convergence (weakening is
hard, so both route around it) OR coincidental vocabulary overlap;
the evidence does not distinguish. Carried forward as a parallel
worth noting, NEVER as validation - the same calibration discipline
as TOST, applied in reverse: qualitative resemblance must not
borrow the rhetorical weight of a measured result.]

**Downstream (registered):** Phase 2 Task B closes as a
characterized negative + transient finding. The protocol's reversal
aspiration transfers to Phase 3 with a MECHANISM REQUIREMENT:
consolidation (stop-condition or stabilization) + weakening
(direct or competitive) are prerequisites; both are now measured,
named, and priced in the landscape note, not assumed.

## R2 mechanism probe: GNG380 regression = COINCIDENCE WASTE at MN9_L (2026-10-08, review-directed)

The review asked WHY the GNG380 transient regresses before the
close-out scopes Phase 3 consolidation. Three hypotheses were
distinguishable from data; two are now EXCLUDED and the mechanism
pinned, by two probes on the regressing block (replay blk0 from the
retained state, same seeds - deterministic):

**(1) Refractory saturation of intermediates: EXCLUDED.** Per-neuron
traces (saturation probe, 8 intermediates x 25 trials): rates rise
monotonically 183 -> 358 Hz and PLATEAU at ~350-358 Hz = 78% of the
454.5 Hz refractory ceiling (t_refractory=2.2ms) - never decline,
never saturate, while MN9 falls 49 -> 27.

**(2) Interference via grown inhibition: EXCLUDED.** Weight diff
t1->t25: ALL 334 grown edges are POSITIVE (0 negative); zero
grown-negative targets among MN9's 10 inhibitory inputs.

**(3) Readout-side ceiling: superseded by the sharper finding.**
MN9's input ARRIVALS rose 3045 -> 4076 (+34%, partners=23) while
its SPIKES fell 49 -> 27 (-45%): more drive, less output. Arrivals
cluster at median inter-arrival 0.2 ms with 99.9% < 2 ms at BOTH
trial 14 and 24 - the inputs are massively coincident (intermediates
phase-locked to the shared cue Poisson source). With tau_syn=5ms and
threshold-clipping, coincident kicks on an already-depolarized
membrane collapse: past threshold, each additional arrival within
the coincidence window buys less than one spike. THE MECHANISM IS
COINCIDENCE WASTE: monotone weight growth over-synchronizes the
intermediates, over-synchronizing MN9's inputs; the readout's
spike count is NON-MONOTONE in total drive in the coincidence
regime. Peak output occurs at the drive level where arrival gain
stops beating coincidence loss - trial 15-16 in this block.

**Phase 3 consolidation requirement, SHARPENED (replaces 'stabilize
somehow'):** consolidation is NOT a plasticity-rule problem alone -
it is a DYNAMICS problem. A stopping rule keyed to the readout's own
derivative (or intermediate-output correlation) is implementable
now: train until the probe readout crosses theta, THEN STOP - the
transient's peak IS the consolidated state. Named: STOP-AT-CROSSING.
The deeper fix (desynchronization or effective-rate readout) is a
mechanism-design question for Phase 3, now posed sharply.

**blk5 boundary case (review point, registered):** blk5's trial-15
cosugar readout was 40 Hz vs theta 41.5 - a NEAR-MISS within probe
noise, explicitly NOT counted as a crossing. The transient-crossing
phenomenon is therefore 5/6 clean crossings + 1 boundary case; its
seed-stability is real (all 6 blocks show the rise-peak-regress arc
within +-2 Hz) but the crossing count is honestly 5/6, not 6/6.

## GNG521 extended-dose replay (2026-10-08, review-directed): NO regression - coincidence waste is CONDITIONAL, not universal

**The reviewer's generality question answered by replay:** GNG521-feed
continued 40 trials past R1's retained state (total dose 55, 2.75x
its WP4 crossing dose; fresh seeds 87000+t, disjoint). MN9_L readout
FLAT at 86-95 Hz across all 40 trials (peak 95 @t35, end 92 - no
arc). GNG521's clean 6/6 pass is a QUALITATIVELY STABLE outcome,
not a snapshot before an unobserved peak.

**The discriminator (measured, both cues):** intermediate RATE
REGIME. GNG521's leg-2 intermediates (12807, 12364, 567143) run
120-165 Hz = ~33% of the 454.5 Hz refractory ceiling - far from the
coincidence regime. GNG380's run 350-358 Hz = 78% of ceiling - deep
in it. The mechanistic boundary: coincidence waste onset when
convergent intermediates' rates climb toward the ~300+ Hz regime
(2/3 of ceiling), where their phase-locking to the shared drive
starts collapsing coincident kicks at the readout.

**Phase 3 requirements, FINAL SHARPENING:**
- Stop-at-crossing is a CONDITIONAL requirement - needed when a
  cue's leg-2 intermediates enter the high-rate synchrony regime
  (GNG380-class: many cue members, strong distributed leg-2, hard-
  driven intermediates), NOT universal (GNG521-class is stable at
  2.75x dose).
- ONLINE peak detection (the reviewer's practical gap): the
  early-warning signal is the INTERMEDIATES' OWN RATES, recordable
  during training trials WITHOUT probing MN9_L - when leg-2
  intermediates approach ~300 Hz, coincidence-waste onset is
  imminent. This converts stop-at-crossing from a hindsight label
  into an implementable control policy: monitor intermediate rates;
  probe once for the crossing when they enter the warning regime;
  stop at crossing. Characterized from data both probes produced.

## Cadence clean-room rule (2026-10-08, registered BEFORE the learning-law source audit)

GPL-3.0 derivative-work discipline: any L3/dopamine-class mechanism
built AFTER reading Cadence's source must be DESIGNED FROM THE
CITED LITERATURE FIRST (Schultz et al. 1997 RPE; Bellec et al. 2020
eligibility traces - already in the project's reference list) -
with Cadence's implementation consulted for UNDERSTANDING ONLY,
never as a template. No Cadence-derived variable names, control
flow, or specific formulation choices may carry into
fly-cognition's implementation. This is the clean-room discipline
that would be warranted regardless of license; GPL-3 makes it
explicit rather than assumed. Reading the source for the audit is
fine (evaluation); copying its structure is not.

## Investigation 01 scope confirmation (2026-10-08)

Per review: the embedding milestone is SKIPPED (the representation
question is settled by Cadence's own docs - 'Cadence does not
model spikes' - Level B fails on documented grounds; an embedding
experiment would be process theater). The learning-law source
audit proceeds NOW as the only open deliverable, structured
around the reviewer's four questions: LOCALITY (what information
does each update use), UPDATE CONDITIONS (what triggers
plasticity; how observations/rewards/settled states gate it),
PERSISTENCE (what survives episodes/restarts), REVERSIBILITY (can
an acquired association be changed when contingency reverses, or
only accumulated over). The audit's bearing: whether Phase 3's
dopamine-pathway mechanism is built from scratch or informed by a
structured reference - with the clean-room rule above governing
any influence. The study remains ALLOWED TO CONCLUDE UNSUITABLE.

## Phase 3 opening: DA census (WP-D1, 2026-10-08) - PATHWAY-SPECIFIC, not broadcast

**The re-anchoring obligation's structural question, answered from the
frozen snapshot (results/phase3/wp_d1_da_census.json).** 1,449
consensus-dopamine neurons in run-007's closure (vocabulary note: the
census's first pass matched 'DA' against a lowercase-'dopamine'
vocabulary and found 0 - string error, caught by the empty-scope
guard, re-run correct; the guard did its job).

**The broadcast hypothesis is FALSE for this substrate.** Measured:
- Only 440/1,449 DA neurons have ANY out-edge in the closure (median
  out-degree 0; max 66). The closure is SEZ/motor-local; most CNS DA
  cells project elsewhere (MB etc.) and are pruned out.
- 796 total DA out-edges onto just 188 distinct targets - and the
  #1 target (266/796 = 33% of ALL DA weight) is bodyId 10120 =
  OA-VPM4_L, itself an OCTOPAMINE neuron. DA's heaviest local
  projection is onto a modulatory peer, not onto the motor circuit.
- Onto our trained circuits: ZERO DA edges onto MN9_L, onto either
  cue population, or onto GNG521's intermediates. 13 DA neurons
  reach GNG380's 8 intermediates (mainly 10646/AVLP597 - a GABA
  interneuron - and 63701/DNd02), = 5.1% of DA out-weight. The
  trained circuit is essentially OUT of the local DA field.

**Consequences for the three-factor (RPE x eligibility) rule:** the
clean broadcast-scalar form (Cadence's class) is NOT structurally
honest for L3-on-this-closure. Options the census opens, all Phase 3
design decisions: (a) pathway-specific dopamine: DA modulates the
GNG380-class intermediates (esp. the GABA hub 10646) - a FAR more
interesting target: DA->10646 gating could modulate the very
coincidence-waste regime Task B characterized; (b) broadcast via
the octopamine relay (DA->OA-VPM4->?) - a two-stage modulatory
cascade, needs its own census; (c) extend the closure to include MB
if L3 requires canonical DAN->MBON structure (the freeze
obligation's named concern; new snapshot cost).

**Reward and state definitions (reviewer's other two scoping items)
- registered as OPEN design questions, answerable AFTER the DA
target decision:** r from the substrate (e.g. sugar-GRN activity vs
consumption), V(s) over a state representation (candidates: MN9
rate, SEZ population vector, the trained circuit's own activity).
No fiat reward. All three items scoped from measured constraints,
per the project's standing method.

## Phase 3 DECISION D-3 (2026-10-08, user-directed): pathway-specific DA gate on the coincidence-waste hub

**Decision:** L3's dopaminergic mechanism anchors on option (a) -
pathway-specific DA onto the GNG380-class intermediates, gating the
GABA hub 10646 (AVLP597) - the neuron that carries the
coincidence-waste regime Task B characterized. NOT broadcast scalar
(structurally dishonest per WP-D1); NOT the octopamine relay (a
derivative census can follow later); NOT the MB closure extension
(only if canonical DAN->MBON structure becomes load-bearing).

**Why this anchor:** it is the one point where Phase 2's sharpest
measured finding (coincidence waste, 300 Hz boundary, stop-at-crossing
requirement) and Phase 3's mechanism requirement (eligibility-gated
weakening) meet a real anatomical substrate with measured DA
inflow. DA gating of 10646 could implement consolidation
(suppressing over-driven intermediates = biophysical stop-at-
crossing) and weakening (gated negative sign onto over-active
paths) without inventing anatomy.

**Sequencing consequences (registered):** the reward and state
definitions (open design questions) now scope against THIS pathway:
the gate's honesty depends on what drives the 13 DA neurons
themselves - WP-D2 census (inputs to those DA cells: sugar GRNs?
cue? readout feedback?) determines whether 'r' can be read from the
substrate or must be supplied. The clean-room rule governs the rule
design (Schultz/Bellec first; three-factor modified to
pathway-specific per measured anatomy).

## WP-D2: gate anatomy complete (2026-10-08) - reward pathway EXISTS in substrate; the gate is self-limiting

**The 9 DA neurons gating the hub 10646** (weights +1 to +12;
dominant: 10898/AVLP476 +12, 12588/PPM1201 +12, 520188/AVLP610 +10,
10399/PPL202 +9). Small, named, measurable population.

**THE REWARD PATHWAY IS REAL (measured, 4 stages):**
  sugar GRNs -> OA-VUMa2 relay (11608: SEVEN sugar-GRN inputs;
  12109: two) and OA-VPM4 (10120, via 2-hop interneurons 10557/
  11173/12675/12230/12808) -> the gate-DA cells (12109->10399 +4,
  13068 +4; 11608->10399 +2, 13068 +2, 12588 +1) -> hub 10646.
**The reviewer's 'r' question has a substrate-honest answer: r =
sugar-GRN activity, and the substrate already routes it to the gate
through the octopamine relay.** No fiat reward needed. (Bitter
reaches 10120/11608 weakly (1 edge each) - an asymmetry to keep.)

**THE GATE IS SELF-LIMITING (closed loop, measured):** the hub
10646 INHIBITS two of its own gate-DA cells (13068 -1, 520188 -1).
DA gates the hub; the hub suppresses the gate. As the hub enters the
high-rate coincidence regime, its own DA gate is withdrawn - **the
anatomy contains a built-in biophysical stop-at-crossing**,
precisely the consolidation requirement Task B measured. This is
the substrate's OWN answer to the over-synchrony problem, not an
invented mechanism.

**Other input structure of the gate cells (recorded):** octopamine
drives 6/9 (OA-VPM4 10120, OA-VUMa2 11608/12109); 520146/SIP106m is
driven almost solely by 3 AN09B017e glutamate neurons (+21/+23/
+17) - a dedicated channel; PPM1201 pair (12588/13068) integrates
~24 mixed inputs each incl. strong inhibition (SMP604 -18, CL114
-5/-3); the hub's own feedback appears in both. NO sugar/bitter/
cue/MN9 input is DIRECT - all modulatory input arrives via OA or
interneurons. L3's state representation question narrows: the
gate-DA cells' own activity IS a candidate state estimate (they
integrate OA relay + hub feedback).

**Design consequence for L3 (registered):** the three-factor rule,
pathway-specific form (per D-3), can be implemented with measured
anatomy at every stage: eligibility on cue-incident edges (frozen
L1 generalization), dopamine = the 9-cell gate population's
activity (driven by sugar via OA - substrate-honest r), gate
target = the hub's inhibitory gain (modulating the
coincidence-waste regime), self-limiting via the measured 10646->
gate feedback. Clean-room rule governs the rule design (Schultz/
Bellec first, pathway-specific per measured anatomy).

## WP-D3: OA-relay convergence census (2026-10-08) - three refinements, one partial walk-back

**(1) The OA relay is a MASSIVE MULTIMODAL INTEGRATOR, not a reward
line (walks back the optimistic WP-D2 reading).** Measured input
budgets: OA-VPM4/10120 has 1,655 inputs (|w|=6,904; exc 5,046 /
inh 1,858) with 0.0% sugar weight; OA-VUMa2/11608: 1,303 inputs,
sugar |w|=12 of 4,774 = 0.3%; 12109: 1,409 inputs, sugar 0.1%.
The sugar->OA->gate pathway EXISTS but sugar is a DROP in the
relay's budget - the relay integrates central-brain state
(13121, 522734, 523043, 14391, 11785...) overwhelmingly. HONEST
CONSEQUENCE FOR L3: OA activity is NOT a pure reward signal - it
is state+reward conflated. Either (a) the model's r must be the
sugar-GRN component read at the source (GRN population activity),
with OA treated as the anatomy's own state-conflated carrier, or
(b) L3 adopts the conflation and tests it empirically. Design
decision, registered as open - not silently resolved.

**(2) BITTER REACHES THE RELAY TOO, with MIXED SIGNS (valence test
answered: the channel is not pure).** 2-hop same-sign paths
measured: excitatory via 11021 (bitter GRNs +39..+58 -> 11021 ->
10120 +2); inhibitory via 17709/518540 (bitter -> LNs -> relay,
negative products). So sugar and bitter BOTH arrive at the relay,
differently signed through different interneurons. The gate channel
carries VALENCE, not just reward presence. This is richer than the
'pure r' assumption - and matches feeding circuitry expectations.

**(3) The gate population is HETEROGENEOUS: a specific core + broad
integrators + a reciprocal DA<->OA loop.** Output specificity onto
the 8 GNG380 intermediates: 10898=41%, 10914=50%, 520188=39% (the
hub-gating CORE, all also target 10646 with the top weights +12/
+10/+1... and 10914 -> 12489 gaba); vs broad fan-out cells
12588 (66 targets), 13068 (52 targets) at 12%/8% specificity.
MN9_L receives ZERO from all 9 (the gate modulates intermediates
upstream of the readout - exactly the design's intent). NEW
STRUCTURE FOUND: (i) gate-DA -> OA relay reciprocal edges
(10399->11608/12109 +6 each; 10898->10120 +2; 13068->10120 +4;
520146->10120 +2) - a DA<->OA modulatory loop, the relay's own
feedback; (ii) 11125/529811 -> 10094 - the SECOND AVLP597 cell
(the hub's type-sibling; 10094 also appeared as 10898's input).
The 'AVLP597 gate' is really an AVLP597 PAIR: 10646 (driven) +
10094 (gated by the other DA cells).

**Net for the L3 design doc (registered):** the three-factor rule
keeps its pathway-specific form, but the census demands: r defined
at the sugar-GRN source OR conflation adopted-and-tested (open
decision); gate target generalized to the AVLP597 PAIR (10646 +
10094) with per-cell measured weights; the DA<->OA loop recorded as
part of the circuit (its dynamics are a testable prediction: does
gate activity feed back to alter relay drive?); bitter's mixed-sign
arrival means the gate's semantics are VALENCE-carrying, so
sign-derivation for DA-on-GABA must handle both directions
(expected-signed potentiation AND suppression contexts).

## L3 DESIGN REGISTERED (2026-10-08, docs/L3_DESIGN.md) - pre-implementation

**The L3 design is pre-registered with measured anatomy at every
stage.** Key registrations:
- The gate-DA -> AVLP597-pair edges are sign +1 BY DEFAULT (the
  frozen nt_sign gives all monoamines +1, auditable assumption).
  The re-anchoring obligation comes due HERE: WP-L3a resolves
  H(+) vs H(-) empirically BEFORE any L3 plasticity exists, using
  frozen-dynamics stimulation sweeps (WP6c-style). No default is
  adopted silently.
- The OA relay conflation (WP-D3) is handled by reading r at the
  sugar-GRN SOURCE and treating OA conflation as a TESTABLE
  PREDICTION measured in WP-L3b - not by fiat.
- The hub pair are broad gain-control hubs (1,457/1,385 targets,
  |w| ~9k each) - the gate modulates a gain field, not a dedicated
  line; this is registered as the design's honest description.
- WP-L3a (sign re-anchoring, ~30 sims) -> WP-L3b (gate dynamics on
  the regressing block, ~50 sims, pre-registered criterion: gated
  suppression arrests the intermediate climb below 300 Hz and the
  readout holds its crossing) -> WP-L3c (three-factor acquisition
  on Task A) -> WP-L3d (the weakening test on Task B reversal,
  criteria in order: weakening / consolidation / masking-cell-empty;
  a null is a registered negative, never a mechanism change).
- Seeds: L3 train 150000+, probe 200000+ (disjointness to be
  verified by computation pre-launch per standing rule).
- All Task B standing rules inherited; clean-room discipline
  governs the rule (Schultz/Bellec-first design).

## WP-L3a RESULT (2026-10-08): DA sign re-anchored DIRECTIONALLY H(+); gate strength below effect-size at baseline - decisive test moves to WP-L3b

**Implementation bug caught + corrected first (recorded):** the
original Sweep C never passed the swept rate into the sim (the run
helper hardcoded 200 Hz) - the sweep degenerated to a 2-point
contrast, and its apparent suppression (14642 42->32 etc.) was
SINGLE-REP SEED NOISE. Fix: third Poisson channel (stimulated3)
added to simulate_lif, TDD (3 tests: default-off bit-identical,
drives targets, independent rates; suite 106/106), defaults-off so
no existing behavior changes. Sweeps A and B were valid throughout
(rates entered via dataclasses.replace correctly).

**Sweep A (VALID, monotone):** gate-DA drive excites hub 10646
monotonically (0->48 Hz across 0->200 Hz drive; +1-default sign
produces real excitation at the DA->GABA edge). 10094 nearly silent
(3 Hz max) - the pair is asymmetric; network inhibition (10646
itself, or its targets) clamps it even under direct drive.

**Sweep B (valid as hub-recruitment):** direct drive -> 10646 at
196 Hz @200; intermediates silent - B had NO baseline activity, so
suppression was unmeasurable by design; its purpose (sign
verification) is served by the weight check below.

**Sweep C v2 (VALID, 3 reps/rate, corrected channel):** the honest
null. Intermediates flat across the full rate sweep (deltas +-3 Hz
on 19-55 Hz baselines), MN9 stable 82-85, while hub 10646 rises
16->56 Hz with gate drive. NO suppression at baseline.

**Connectivity check (load-bearing, from the frozen matrix):** the
pathway is REAL and WEIGHTY: 10646 -> 15207 (-21), -> 14642 (-17),
-> 14793 (-8), -> 63701 (-3), -> 15014/12583/12256 (-2/-2/-1);
10094 parallel (-12/-15/...). Gate-DA -> hub edges +1..+12 (9
cells, onto 10646). Structural H(+) circuit COMPLETE.

**Quantitative reconciliation (registered):** hub at 52 Hz (what
200 Hz gate-DA drive produces) delivers -5.8 mV kicks at ~1/19 ms
-> ~1.5 mV mean hyperpolarization - insufficient against
cue+sugar-driven intermediates at 50 Hz in the PRISTINE matrix.
The mechanism is present, directionally H(+), but its effect size
at baseline drive is below measurement. NOT a refutation of H(+):
the decisive test is the TRAINED state (WP-L3b as pre-registered),
where intermediates climb toward 300 Hz and the readout regression
occurs - the regime the gate was chosen for.

**Verdict (discharges the re-anchoring obligation as far as frozen
dynamics allow):** DA-on-GABA sign = H(+) DIRECTIONALLY VALIDATED
(monotone excitation, real inhibitory pathway). GATE STRENGTH:
below effect-size at baseline; WP-L3b (gate on the trained,
regressing circuit) is the decisive consolidation test. The
obligation's remaining scope (pathway-specific efficacy) transfers
to WP-L3b - registered, not silently assumed.

## WP-L3b RESULT (2026-10-09): gate-DA drive does NOT arrest the coincidence-waste climb - consolidation-by-gated-suppression REFUTED at tested rates

**Control-reproduction gate: PASS exactly.** The 0-Hz arm reproduced
Task B blk0's measured arc to the spike (2->49 peak @ t15, -> 27 @
t24) - the replay is valid and the arms comparable.

**The decisive sweep, clean negative at every rate:** gate-DA drive
at 50/100/150/200 Hz INSIDE the training trials (TrialSpec gate
channel, default-off test-pinned) changed NOTHING: final readout
25-27 (never held theta) in all arms; intermediates at ~350-360 Hz
at the final probe in EVERY arm (arrested=False across the board);
climb trajectories statistically identical (206/274/348/357/359 at
the 5 probe points, +-2 Hz across arms). The gate's effect size is
below measurement even in the trained, regressing regime.

**Verdict per the pre-registered interpretation order:** the
consolidation-by-gated-suppression hypothesis is REFUTED at the
tested drive rates (50-200 Hz). This is a registered negative
result, NOT a silent mechanism change. The L3b criterion (arrest
below 300 Hz + readout holds crossing) failed on both components.

**Why (measured, from WP-L3a's arithmetic + this run):** the hub
pair's per-kick influence (~1.5 mV mean hyperpolarization at the
rates gate-DA achieves) is simply too weak against intermediates
hard-driven at 350+ Hz by 300-400 weight-sum cue edges. The
AVLP597 pair are broad gain-control hubs for the CENTRAL BRAIN
targets (|w| 9k across 1,400 targets), but onto THESE SEZ-adjacent
intermediates their edges are -1..-21 - an order of magnitude
below what the drive regime requires.

**What survives and what doesn't:**
- SURVIVES: the H(+) sign anchor (WP-L3a: DA excites the hubs,
  monotone - validated); the measured anatomy (all censuses stand);
  the self-limiting loop's EXISTENCE.
- REFUTED: gated suppression AS THE CONSOLIDATION MECHANISM at
  physiological drive rates. The DA->AVLP597->SEZ-intermediates
  pathway exists structurally but is not strong enough to implement
  stop-at-crossing biophysically in this closure.

**Registered fork for L3c/L3d (decision required before further
plasticity work):** (a) proceed to the three-factor rule with
PLASTICITY-based gate action (DA-gated ELIGIBILITY rather than
DA-gated biophysics - the gate decides WHERE learning applies,
not WHEN the circuit saturates), which the anatomy supports
without needing biophysical effect size; (b) test supra-physio
rates (>200 Hz) - registered as a rate-extension arm, flagged as
biologically strained; (c) re-scope L3's consolidation component
to the plasticity rule itself (eligibility decay = stop-at-
crossing analog) and treat the DA anatomy as the VALUATION/
credit path only. Option (c) is the current lean: it keeps every
measured fact load-bearing and moves consolidation into the one
place the rule was always going to need it anyway.

## L3 fork RESOLVED (2026-10-09, user-directed): (c)+(a); (b) rejected; decay calibration pre-registered

**Decision D-4:** (b) supra-physio rates REJECTED outright - 'biologically
strained' is the same rescue-vs-evidence flag as every prior one in this
project's history. (c)+(a) adopted: consolidation re-scoped to the rule
(eligibility decay as the stop-at-crossing analog) with DA anatomy as the
valuation/credit path; (a) eligibility-gating registered as an
INDEPENDENT mechanism requiring its own measurement.

**CRITICAL registration (reviewer-directed): (a) was NOT refuted by
WP-L3b.** WP-L3b measured the BIOPHYSICAL DRIVE question: can DA->
intermediate synaptic weight suppress 350+ Hz activity through membrane
dynamics? Cleanly NO. But eligibility-gating is a LEARNING-RULE-LEVEL
effect - a multiplicative factor on the eligibility trace keyed to DA
presence/level, not to DA's synaptic kick strength. The -1..-21 edge
weights that killed gated-suppression are NOT the relevant number for
(a). Any future reader must not assume (a) was tested and refuted by
L3b's numbers. (a) needs its own measurement: what DA signal actually
REACHES these synapses (even weak/sparse/non-driving contact could
suffice for a gating role) - a volume-transmission question, separable
from the suppression question.

**Pre-registered calibration target for (c)'s decay constant (registered
BEFORE any WP-L3c code exists, reviewer-directed):** the eligibility
decay time constant must be CALIBRATED AGAINST Task B's own measured
timing data, not chosen freely. Specific target: decay must produce
consolidation at or before the point coincidence waste historically
onsets - the GNG380 regression: crossing at ~trial 15 (5/6 blocks),
intermediate climb through ~300 Hz at trial ~9-14 (measured: 274 @
t9, 348 @ t14), peak 49 @ t15-16, regression below theta by t24.
Verification target: the decay-calibrated rule, run on the SAME
reversal trajectory, must arrest the readout's fall (or never let it
rise past the consolidation point) at or before t15 - VERIFIED against
the existing regression trajectories, not assumed. A decay constant
chosen independently of that data would be inventing a mechanism to
fit a hoped-for outcome - the exact trap this project has avoided.

## D-4 calibration DERIVED from Task B's own trajectory (2026-10-09)

**The decay constant is not free - it is measured.** Model: per-trial
eligibility accumulation with per-trial decay lambda; consolidation
requires the INCREMENTAL eligibility (lambda^(t-1) * c) to be
negligible (<5% of per-trial contrast) by the measured
coincidence-waste onset (t=15). From Task B's measured timing:
  lambda^14 <= 0.05  =>  lambda <= 0.807  (tau <= 4.67 trials,
  half-life <= 3.24 trials)
Calibration band for the rule: **lambda in [0.70, 0.807]** -
within it, cumulative effective eligibility plateaus at 3.3-5.0x
per-trial contrast by t9-14 (so acquisition still works: WP4's
GNG521 crossed theta at t5-10, well within the pre-plateau rise),
and the increment is <5% by t15 (so potentiation pressure is spent
by the measured onset). lambda=0.99 (gamma*lam of the
Cadence-class default) would leave an 87% increment at t15 -
NOT a consolidation mechanism at this timescale; the derived band
is what the substrate's own measured dynamics demand.

**Pre-registered verification (binds WP-L3c):** replay the GNG380
reversal with the decay-eligible rule at lambda = 0.75 (band
center); criterion: readout holds theta at t24 OR never crosses
(consolidation engaging pre-crossing is acceptable per the
registered interpretation), intermediates <= ~300 Hz at t14+.
Fail = registered negative; no parameter search past the band.

## D-4 correction (2026-10-09, review-directed): criterion SPLIT; gamma pinned; strangle-risk PREDICTION registered

**CRITERION SPLIT (replaces the flawed equivalence):** 'holds theta
at t24' and 'never crosses' are OPPOSITE findings, not equivalent
wins. Registered outcomes for the GNG380 decay replay:
- PASS (consolidated reversal): crossed theta at some trial, then
  held theta at t24.
- NEGATIVE-1 (acquisition strangled): never crossed - decay too
  aggressive; the aggression needed to spend potentiation by onset
  prevented the association from forming at all. 'Learns but cannot
  hold' vs 'cannot learn' are different failure modes.
- NEGATIVE-2 (crossed but regressed): decay insufficient at the
  band value; coincidence waste not arrested.

**GAMMA PINNED:** in this trial-based, non-sequential formulation,
the TD discount gamma = 1 EXPLICITLY. The trace update's decay
factor is lambda alone (e <- lambda*e + contrast); the calibrated
band [0.70, 0.807] is lambda, NOT the product gamma*lambda. The
registry pins this so the two cannot drift independently. (The
Cadence-class default gamma*lam ~0.99 note referred to their
sequential-formulation default; irrelevant here with gamma=1.)

**PREDICTION (registered BEFORE the run, first-order arithmetic on
GNG380's own measured dynamics - not GNG521's fast case):** the
original calibration's 'acquisition survives' check used GNG521's
t5-10 crossing. GNG380 is the SLOW, late-crossing cue (t15, rising
2->49 over the full 15 trials). Under lambda=0.75, cumulative
weight growth at t15 reaches only ~48/120 = 40% of the no-decay
value (geometric-sum arithmetic on the measured per-trial contrast),
and the trace plateaus at 4x per-trial contrast - readout asymptote
~2 + 0.40*(49-2) = ~21 Hz, BELOW theta. PREDICTED OUTCOME:
NEGATIVE-1 (acquisition strangled) for GNG380 at the band center.
If confirmed, the finding is that decay-consolidation at the
calibrated band is SELF-DEFEATING for slow cues - the decay
aggression needed to stop potentiation by onset prevents the slow
cue from ever crossing - and consolidation must be STATE-DEPENDENT
(gated by crossing/delta), strengthening the (a) eligibility-gating
path. The run decides; the arithmetic only predicts.

## WP-L3c RESULT (2026-10-09): decay-consolidation REFUTED for slow cues - the no-free-lunch is MEASURED

**The decisive replay, all arms, control verified first:** L1
control reproduced Task B's regression arc exactly (2->49 @ t15,
->27 @ t24 - third independent reproduction). Then the calibrated
band, every value:
- lam=0.70: arc plateaus 4-10, peak 10, final 7 - never crossed.
- lam=0.75: arc plateaus 7-13, peak 13, final 7 - never crossed.
- lam=0.807 (band edge): arc plateaus 2-19, peak 19, final 15 -
  never crossed.
**VERDICT per the SPLIT criteria: NEGATIVE-1 (acquisition
strangled) at ALL THREE band values.** The registered prediction
(asymptote ~21 Hz, sub-theta) was confirmed and slightly
over-optimistic - real growth is weaker still.

**The measured no-free-lunch:** consolidation at Task B's own
timing requires lam <= 0.807 (increment <5% by t15). GNG380's own
acquisition requires enough cumulative potentiation by t15 to
cross theta - which lam=0.807's discounting denies (the geometric
series reaches only ~1/3 of L1's linear sum by t15, and the
readout tracks proportionally: 19 vs 49). **The two requirements
are incompatible in a single constant: lam <= 0.807 strangles;
lam ~1 regresses. Decay-based consolidation is SELF-DEFEATING for
slow-acquiring cues.** This closes the (c)-only path: a fixed
decay constant cannot serve both acquisition and consolidation on
this substrate's measured dynamics.

**Registered consequence (strengthens (a)):** consolidation must
be STATE-DEPENDENT, not rate-constant-dependent. The (a)
eligibility-gating mechanism - DA presence/level as a
multiplicative factor on the trace, keyed to the substrate's own
reward timing (sugar via OA relay) - naturally provides this:
eligibility accumulates freely during acquisition (DA active while
sugar is delivered), and the DISENGAGEMENT of potentiation happens
via the DA signal's own dynamics rather than a pre-set decay.
This is not a rescue - it is the anatomy the censuses measured
doing the work the fixed constant cannot. WP-L3d as pre-registered
(tests weakening) proceeds with the three-factor rule in its
DA-GATED form: e in (gate) * contrast; the gate's timing comes
from the measured reward pathway, not a free parameter.

**Standing: (c) alone = measured negative (this WP). (a) = the
surviving consolidation mechanism hypothesis, now the load-bearing
one. The D-4 prediction did its job: the run was worth running
BECAUSE the outcome was pinned in advance.**

## WP-L3d pre-launch census (2026-10-09, review-directed): bitter routes through a DIFFERENT DA population; sugar drives NONE of them; the gate-population hypothesis is REFUTED in its drive form

**Q2 answered - and it kills the single-gate design for both
conditions:** traced frozen-dynamics sims (3 reps each, >5 Hz in
>=2/3):
- BITTER-only drive activates 4 DA neurons: 11618/PPL102 (130 Hz),
  11900/PPL101 (132), 529516/PPL106 (47), 138585/PAM12 (9). Three
  PPL-class + one PAM - CONSISTENT with the PPL-aversive
  literature.
- SUGAR-only drive activates ZERO DA neurons in this closure. Not
  'few' - zero, at 200 Hz GRN drive, 3 seeds. Sugar's DA influence
  in run-007's SEZ-local closure is INDIRECT ONLY (via the OA
  relay, too weak at one remove to fire DA on its own).
- Overlap sugar^bitter: ZERO. Two disjoint populations.
The reviewer's concern was exactly right: reusing one gate node
with a sign flip would have imported an assumption the connectome
contradicts. Bitter-weakening gates through PPL101/102/106 (+
PAM12), NOT through the 9 gate-DA cells.

**Q1 answered - gate-on cannot be defined as DA-rate activity in
this closure:** the 9-cell 'gate population' fires at 0 Hz under
baseline, sugar, AND bitter. Their DA identity was never a
firing-pathway membership in these conditions - they are
modulators that act (if at all) at sub-threshold/volume-transmission
strength. A rate threshold on them is not derivable because they
have no measurable rate response. THE GATE-ON SIGNAL CANNOT BE
THEIR SPIKING. This refutes the WP-D2 'gate population activity as
V(s)/gate' design in its spiking form.

**Q3 consequence + what SURVIVES:** the DA-gated eligibility design
survives ONLY if the gate reads a non-spiking variable. The
substrate-honest candidates, in order of measured support:
(1) OA-RELAY ACTIVITY as the appetitive gate (WP-D2: 11608/12109
receive 7/2 direct sugar-GRN inputs; they ARE driven by sugar -
the relay fires under sugar, the DA cells do not);
(2) the PPL trio (11618/11900/529516) as the AVERSIVE gate -
bitter DOES fire them, robustly (130+ Hz), and they are the
population whose spiking actually tracks aversive presence;
(3) eligibility semantics: with per-trial binary conditions (sugar
  present or bitter present), the gate is per-trial PRESENT/ABSENT
  - no threshold needed; freeze-vs-decay is moot at the binary
  level (eligibility persists across the trial boundary under
  gate=1 and does not accumulate under gate=0).
REGISTERED for WP-L3d: appetitive trials gate eligibility ON via
the OA relay's sugar response; aversive trials gate the WEAKENING
term via the PPL trio's bitter response (sign-symmetric delta
requires the aversive gate for negative updates); the 9-cell
gate-DA population is RETIRED as the gate signal (retained in the
anatomy record; their role, if any, is volume-transmission
modulation below spiking threshold - out of modeling scope for
frozen dynamics, recorded as an explicit scope boundary).

## WP-L3d contract guards (2026-10-09, review-directed): NEVER-BOTH enforced; V_MAG weakening hazard CAUGHT BY TEST

**Guard 1 - NEVER-BOTH:** static scan of every Phase 2/3 script's
TrialSpec constructions: NO trial combines sugar and bitter drives
(the scanner's one flag was a false positive across an if/else
branch - verified by reading; sugar-only and bitter-only trials in
separate branches). Enforced going forward by a runtime assertion
in the WP-L3d trial builder + a standing test
(tests/test_l3d_contract_guards.py) that scans all scripts for the
pattern and fails loudly on any violation. The binary either/or
gate model's precondition is now verified, not trusted.

**Guard 2 - THE V_MAG WEAKENING HAZARD (caught RED, before any
run):** driving V_MAG with delta=-50 on w=+10 produces w=-40, NOT
w=0. The existing V_MAG branch (sign(w0) * min(abs(w0)+delta,
w_max)) adds negative deltas to the magnitude, which FLIPS THE
EDGE'S SIGN when |delta| > |w0| - exactly what V_MAG exists to
forbid, undiscovered since WP1 because Phase 2 never applied a
negative delta larger than the weight (all potentiation was
positive; V_MAG's negative-delta path was never exercised).
WP-L3d's weakening pathway would have hit it on the first aversive
trial.

**REGISTERED: the L3d weakening semantics is V_CLIP-FLOOR, not
V_MAG and not V_SIGNED.** Rationale (per D3's variants rule):
- V_MAG: REFUTED for weakening (the caught hazard - silent sign
  flip past zero);
- V_SIGNED: registered-arm only, 'biologically aggressive' per D3 -
  allows an inhibitory synapse to turn excitatory; NOT the default
  for the weakening pathway;
- V_CLIP: floors at the zero crossing (w0>0, new<0 -> 0.0), and
  its zeroed-edge-stays-dead branch (w0==0 -> 0.0) preserves the
  stored-zero contract. The weakening pathway uses V_CLIP
  semantics: magnitude DECREASE floored at zero, sign NEVER flips,
  w=0.0 remains structural (verified by test: driven to exactly
  0.0, the edge survives in the sparse structure).
The zero-vs-absent hazard from WP1 is therefore covered for the
new context BY TEST, not by assumed generalization of the earlier
fix.

**Registry note (reviewer's third point, recorded):** the gate-tied
fixed-sign delta is a SIMPLIFIED binary rule, NOT a full RPE - no
value estimate, no shrinking-as-predicted brake. The self-limiting
protection in WP-L3d relies on the EMPIRICAL characterization
(GNG521-class stability at 2.75x dose; coincidence waste
conditional on intermediate regime), NOT on any built-in rule
brake. A future reader must not assume more self-regulation than
the two registered facts supply.

## WP-L3d RESULT (2026-10-09): NEGATIVE-A - the aversive gate's weakening is REAL but ~100x TOO WEAK to touch the acquired association

**The decisive weakening test, 3 seed reps, guard 0 fires, sanity
gate passed at launch (PPL trio 132/132/48 Hz under bitter in
protocol context).**

**Trajectories (all reps, both probe types, 5 points - the shape
matters, not just endpoints):**
- cue-ALONE: flat 70-85 Hz across t5-t25 in every rep. The
  acquired association never moved. NOT a slow-fall-that-needs-
  more-trials shape - flat.
- cue+COSUGAR: flat 84-92 throughout. The innate program is
  untouched. NEGATIVE-B excluded cleanly.

**Mechanism forensics (from per-trial weight_diff):** the gate
DID act - negative deltas applied EVERY trial (11-13 edges
changed, total_delta -5.0 to -13.0, shrinking toward floors as
weights approach zero). But magnitudes: max_abs_delta 0.9-1.9
against potentiated edge weights in the HUNDREDS (GNG521's
acquired leg-1 edges grew to ~740 of 766 w_max in R1). At
eta=1e-4 and x*y <= 200*200, one trial's delta is ~1-4 weight
units. Weakening an edge holding ~740 units needs ~200-700
trials. 25 extinction trials remove ~1-2% of the acquired
potentiation. **The mechanism is structurally sound and
quantitatively ~2 orders of magnitude too weak at the frozen
eta.** Training-trial readouts read 0 Hz (bitter co-drive
suppresses MN9_L during training - the known broad suppression;
probes are the valid measurement, and they are flat).

**Per the pre-registered split criteria: NEGATIVE-A (no
weakening).** Registered as-is. The honest decomposition:
- What worked: the aversive gate opened (measured); V_CLIP
  weakening applied with correct sign and floors (weight_diff
  proves it); selectivity held (cosugar intact, guard silent).
- What failed: effect size at the frozen learning rate. The
  substrate HAS an aversive-to-DA weakening channel; at eta=1e-4
  it cannot erode an association built at the same eta over 15
  trials - SYMMETRY BREAK: acquisition accumulates in one
  direction only (potentiation), while weakening must remove
  what acquisition built, at the same rate. Over equal trial
  counts the best it can do is a draw - and the association was
  built over 15 trials, then RETAINED (R1 verified bit-identical
  weights), so 25 extinction trials at the same eta cannot
  remove it (needs ~equal accumulated magnitude, which means
  ~equal trials at equal eta - but the coincidence-waste
  regime caps useful acquisition at ~t15 anyway).

**Phase 3 ledger closes with this finding:** the substrate's own
aversive pathway provides a REAL but WEAK weakening channel -
real in sign/floor/selectivity, weak in rate. The remaining
design space for genuine reversal (registered, for Phase 4):
(1) eta asymmetry (weakening rate > acquisition rate -
  biologically motivated: LTD/LTP ratio literature, but a NEW
  parameter requiring its own calibration vs Task B data);
  (2) prolonged extinction (the ~200-700 trial estimate - test
  durations this substrate has not run; unbounded-scale
  question);
  (3) accept the Phase 2/3 joint conclusion as the finding: on
  this closure, under frozen-rate learning, associations are
  effectively irreversible - 'can learn, can keep, cannot
  unlearn' now extends to 'even with the substrate's own
  aversive pathway engaged'.

## WP-L3d scope-vs-rate check (2026-10-09, review-directed): SCOPE-CAPPED at ~60-64% coverage; eta-asymmetry alone CANNOT reverse

**The reviewer's alternative was right, and it changes the fork.
From per-trial checkpoints (no new sims):**

1. **Extinction touches a SMALL FIXED SET: 15-18 edges per rep**
   (11-13 per trial, stable across 25 trials; 0-4 new edges
   recruited in the second half - NOT growing coverage). Not a
   slow version of acquisition; a narrow slice of it.

2. **Coverage vs acquisition footprint: 60-64%.** GNG521's
   acquisition footprint is 25 cue-incident edges (correcting the
   earlier 334 figure - that was GNG380's count; registered
   correction). Extinction reaches 15-16 of them. ~40% of the
   association's edges are NEVER TOUCHED by this protocol.

3. **Mass: 1.1-1.45% removed** (4.9-6.4 units vs 443.4 acquired
   mass).

**FORK DECISION, revised per the measured answer:**
- Fork (1) eta-asymmetry ALONE: INSUFFICIENT BY MEASUREMENT.
  Raising eta erodes the same 15-16 edges faster but never touches
  the remaining ~9-10; the association's readout is carried by
  the full 25-edge set (R1: cue-alone 76-89 Hz from their joint
  mass). Even eta-infty on 64% of the footprint leaves the
  association's remaining carriers intact - at best partial
  weakening to a plateau, never reversal. REGISTERED.
- The REAL Phase 4 question is the reviewer's fourth option: can
  ANY extinction protocol reach the untouched 40%? The touched
  set is coincidence-gated (cue+bitter timing lines up for those
  edges' postsynaptic partners; the untouched 9-10 edges' partners
  stay silent under this protocol). Varying presentation patterns
  to recruit different coincidences is the candidate mechanism;
  whether it CAN recruit them is a testable structural question.
- Fork (2) prolonged extinction: also scope-limited - more trials
  at the same protocol erode the same 15-16 edges toward their
  floors and stop. ~200-700-trial arithmetic was rate-framing;
  scope-framing says it converges to partial. REGISTERED.

**L3d final characterization (both negatives combined):**
extinction under this protocol is DOUBLY limited - scope (60-64%
coverage, fixed set) and rate (1-2% mass per 25 trials on the
covered subset). Either alone would prevent reversal; both are
measured. The Phase 2/3 joint conclusion STANDS and sharpens:
under frozen-rate learning and fixed-protocol extinction, this
substrate's associations are irreversible in BOTH senses - the
channel exists but its reach and rate are both bounded.

## Reachability census - QUESTION SCOPE registered before the run (reviewer-directed)

The census answers TWO distinct questions, and the registry states
explicitly which result licenses which claim:
- Q-A (PROTOCOL-FAMILY reachability): can cue+bitter-style
  presentations (the registered extinction family: cue PRIMARY,
  one innate drive, any timing/pattern variation) drive the
  untouched partners to coincide with the cue? A NO here licenses
  only: 'this protocol family cannot reach them'.
- Q-B (CLOSURE-WIDE reachability): do the untouched partners
  receive input from ANY identifiable population in run-007's
  closure (any NT, any type - not just PPL/sugar/bitter GRNs)
  that a differently-designed protocol could recruit? A NO here -
  and only here - licenses the strong claim: 'irreversibility is
  a property of the substrate's reachable coincidence structure'.
The census reports BOTH, separately. A Q-A-negative + Q-B-positive
result means Phase 4's mechanism question becomes 'WHICH
population, and can it be driven honestly?' - a design question.
A Q-A+QB double-negative makes the joint finding final in the
strong form.

## Reachability census RESULT (2026-10-09): Q-A NO, Q-B YES - the untouched 40% is SUGAR-DRIVEN; extinction's protocol family is structurally mis-designed

**Q-A (protocol-family): NO.** The 9 untouched edges' partners
(GNG029, GNG132, DNge080, GNG211, GNG128, GNG370, GNG368, SLP471,
DNge077) receive essentially nothing from the extinction protocol's
populations: bitter-GRN input 0-2, PPL-trio input 0, cue-only
input 1-5. Under cue+bitter presentations these partners CANNOT
co-fire with the cue - the coincidence never opens, which is
exactly why the L3d touched set was fixed at 15-18 edges. The
registered claim licensed: THIS protocol family cannot reach the
untouched 40%.

**Q-B (closure-wide): YES - and the reaching population is
SUGAR.** The untouched partners are richly connected within the
closure (119-496 inputs each): GNG029 has +20 sugar-GRN input,
GNG128 +15, GNG132 +8, DNge077 +5, GNG370 +2; SLP471/DNge080/
GNG211/GNG368 are driven by other SEZ/central populations
(GNG171, GNG483, DNge069, AN01B018...). The strong claim
('irreversibility is a property of the substrate's reachable
coincidence structure') is NOT licensed: a differently-designed
protocol CAN in principle recruit these partners - and the most
direct recruiter of three of them is the SUGAR pathway itself.

**THE STRUCTURAL IRONY (the finding's punchline):** the untouched
40% of the association's carriers are the edges whose partners are
SUGAR-CO-ACTIVE ones - they were recruited during ACQUISITION
precisely because cue+sugar co-presentation drove them (the
coincidence that built them), and they are unreachable during
EXTINCTION precisely because extinction removes the sugar that
drove them. Cue+bitter does not reach them because SUGAR does.
Extinction-with-bitter is structurally mis-designed for this
footprint: it removes the very drive that recruited - and now
maintains access to - the association's carriers. The correct
extinction protocol is counterintuitive: CUE + SUGAR + AVERSIVE
GATE (PPL) - re-present sugar (holding the partners reachable and
coincident) while the aversive gate supplies the negative delta.
But that violates the registered NEVER-BOTH precondition for the
BINARY gate model... unless the gates are PROTOCOL-SEQUENCED
rather than trial-internal: sugar-recruited coincidence within
the trial, aversive delta applied at a different time or by a
third factor modulating the same trial's delta sign.

**Phase 4 fork, now measured:** the design question is no longer
'can anything reach the 40%' (sugar can) but 'how is the
aversive delta applied to sugar-maintained coincidences without
violating the gate model's preconditions'. Candidate designs,
all testable: (1) interleaved trials (sugar-coincidence trials
alternating with aversive-delta trials - eligibility persists
across the inter-trial gap per the L3d binary-gate semantics);
(2) within-trial sequencing (sugar phase then bitter phase in one
trial - requires re-deriving the NEVER-BOTH as never-simultaneous,
which the binary model permits: gates are per-trial PRESENT/ABSENT
but a trial may have two phases); (3) a third modulatory factor
(PPL onto the eligibility gate itself - LTD-gating rather than
delta-sign-flipping; anatomically checkable: do the PPL trio
project onto the touched partners or the hub?). All three are
registered as Phase 4 design candidates with the census as their
measured foundation.

## Phase 4 design decision (2026-10-09, review-directed): (3) DROPPED; (2) adopted in ELIGIBILITY-THEN-SIGN form; conflation CONFIRMED and resolvable without redesign

**(3) dropped on the reviewer's evidence:** the census measured
PPL-trio input to the 9 untouched partners at ZERO - there is no
eligibility there for an LTD-gate to act on. (3) changes behavior
only on the already-touched 15-18 edges = rate dimension, the one
the census showed matters less than scope. Not the bottleneck.

**Conflation check (code-read, fly-l3d rule as committed):**
CONFIRMED and worse than framed - the gate_on flag controls (a)
eligibility accumulation (observe_rate_pair returns early when
off), (b) whether ANY update applies (apply returns early), and
(c) the sign (_negate hard-wired to gate-on). One binary variable
does all three jobs; 'opens coincidence' and 'sets sign' are the
same signal in the implementation, exactly as the reviewer
suspected. Naive interleaving/sequencing under this code = more
acquisition on the untouched subset (sugar opens coincidence AND
positive sign).

**Resolvable WITHOUT redesign:** the decoupling machinery already
exists - observe/apply are separate calls; _pending persists
across them; TrainingRun flushes per trial. The eligibility-then-
sign design needs only: (i) eligibility accumulation driven by
whichever population actually opens coincidence (sugar for the
untouched partners - Q-B), gated OFF from sign; (ii) a separate
per-trial SIGN source (bitter/PPL phase or trial) applied at
apply-time to whatever eligibility is live; (iii) NEVER-BOTH
renegotiated from never-co-present to never-SIMULTANEOUS -
within-trial phases or alternating trials, both of which the
binary per-trial gate model permits with explicit re-registration.
This is the three-factor structure the Cadence audit identified,
now with substrate-honest sources: eligibility from coincidence
(sugar-recruited), valence from the aversive phase (PPL), combined
via persistence - the trace machinery L3c built and L3d exercised.

**Phase 4 WP-L4a (registered, pre-implementation):** implement
the decoupled rule (eligibility source, sign source, persistence
across phase/trial boundary); unit tests pin: (1) eligibility
accumulates under sugar-phase with sign-source absent; (2) a
subsequent bitter-phase applies NEGATIVE delta to the live
eligibility (full 25-edge footprint reachable - the untouched 9
partners co-fire under cue+sugar); (3) never-simultaneous holds
(sugar phase and bitter phase never overlap in one simulation
step); (4) V_CLIP floors preserved. Then WP-L4b: the decisive
run - cue+sugar eligibility phase + bitter sign phase, cycled,
from the acquired state; criteria split pre-registered: PASS iff
cue-alone < theta by trial 25 AND cosugar intact; NEGATIVE-A iff
untouched-edge coverage still fails (coincidence did not open
under sugar phase); NEGATIVE-B iff unselective collapse.

## WP-L4b RESULT (2026-10-09): PASS - the association is genuinely weakened through the substrate's own dual pathways; full-footprint coverage measured at the edge level

**The decisive run completed (3 reps; the verdict-aggregation code
crashed post-run on a missing-key - training rows lack 'ptype';
data fully intact, verdict computed from checkpoints).**

**Probe trajectories (cue-alone | cosugar, 2 reps per point):**
- cue-ALONE: c5: 68-84 -> c10: 26-72 -> c15: **0,0** -> c20/c25:
  0,0. COLLAPSED TO EXACTLY ZERO by cycle 15, in all 3 reps.
- cue+COSUGAR: 78-92 at every probe point, all reps. INTACT.
- Guard: 0 fires. NEGATIVE-B excluded.

**Edge-level forensics (final-vs-initial, from checkpoints):**
- Footprint: 25/25 acquisition edges WEAKENED in every rep.
- The 9 previously-UNTOUCHED edges: 9/9 WEAKENED - 8 to exactly
  0.0 (29.6->0, 36.0->0, 25.2->0, 17.7->0, 15.4->0, 6.8->0, 6.0->0,
  5.8->0) and the 1.0-weight edge to 0.9 (at floor trajectory).
  The scope problem is solved at its measured root: the
  sugar-eligibility phase opened the coincidence bitter could not.
- Selectivity: 27 total edges changed = 25 footprint + 2
  collateral (bitter-phase-reachable, non-footprint cue edges);
  the sugar->MN9 innate pathway untouched (cosugar probes
  explain); structure preserved (nnz 336245 -> 336245, stored
  zeros intact).
- Seed-stable: all 3 reps byte-identical edge outcomes.

**Verdict per the pre-registered split criteria: PASS.** Cue-alone
0 < theta=41.5 by cycle 25 (in fact by cycle 15) AND cosugar
intact. NEGATIVE-A excluded by direct edge measurement (not
inferred from the readout). NEGATIVE-B excluded by cosugar +
guard.

**ERRATA (honest, registered):**
1. The JSONL field 'pending_after_sugar' is MISLABELED - it is
   recorded after the bitter phase's flush, so it measures
   post-CYCLE pending (=0 always), not post-sugar-phase
   accumulation. Harmless to the verdict (the weight_diff and
   edge forensics carry the evidence); field name corrected in
   any successor script.
2. The cue-alone collapse to exactly 0 (not just <theta) reflects
   FULL footprint erosion: with all 25 carrier edges at their V_CLIP
   floors, the cue-alone probe has no residual pathway. 'Weakened'
   here means ERASED on its carriers. Noted for interpretive
   precision: the protocol did not produce graded weakening, it
   produced extinction.

**WHAT THIS COMPLETES (the Phase 2->4 arc):** the substrate can
learn (WP4), keep (R1), and - via the eligibility-then-sign dual-
pathway protocol - UNLEARN (L4b). The mechanism is the three-
factor structure with substrate-honest sources at every factor:
eligibility from sugar-recruited coincidence (the census's Q-B
finding, confirmed firing at launch), sign from the aversive
pathway (the PPL trio, measured), persistence with no decay
(pinned), V_CLIP floors (pinned). Nothing invented; every component
measured before use.

**Scope caveats (standing):** development-stage n=3 (S22); the
GNG380-class stronger footprint (~740-weight edges) has NOT been
tested for erosion rate under this protocol - the L3d rate
arithmetic suggests more cycles may be needed there; whether
graded (non-extinction) weakening is achievable by protocol
shaping is open. Both are registered as the honest boundary of
this PASS.
