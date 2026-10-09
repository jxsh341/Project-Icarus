# Learning, Keeping, and Unlearning in a Connectome-Derived Substrate

**A complete, honestly-scoped experimental arc on the Drosophila MaleCNS connectome**

FLY-BASE-001 / FLY-LEARN-001 Technical Report | 2026-10-09 | repository commit `4bd1fe5`

---

## Abstract

We ask whether a biologically-derived neural substrate — a 40,290-neuron, 336,245-synapse closure of the Drosophila melanogaster Male Adult Nerve Cord connectome (male-cns:v0.9), simulated with leaky integrate-and-fire dynamics and signed synapse-count weights — can support the three elementary operations of associative memory: **acquiring** an association through local plasticity, **retaining** it, and **removing** it. We find all three, each with its boundary located by measurement rather than assumed. Prior connectome-plasticity demonstrations exist (§7); the distinct contribution here is the located mechanism and located boundary, not the cycle's first-ness. Acquisition succeeds for precisely-characterized anatomical configurations (strong second-order convergence onto a readout, no innate leak) and fails elsewhere; ten of fifteen candidate neuron types fail baseline gates alone. Retention is bit-identical weight stability under verified-silent spontaneous dynamics. Removal fails under every conventional mechanism we tested — fixed-rate extinction, decay-based consolidation, broadcast modulation, gated suppression — each failure located to a specific structural cause — and succeeds only through a protocol that re-opens the very coincidences that built the association: sugar-recruited eligibility paired with aversive sign. The substrate can learn, keep, and — under one measured protocol, for one association — unlearn. The generalizing principle, predicted before testing and confirmed at its boundary: **associations live where their recruiting coincidences live; removing the drive is not erasure but access surrender.**

## 1. The substrate and its validation (Phase 1)

The starting point is not a model of a connectome but a frozen, validated instance of one. run-007 is a closed subgraph of male-cns:v0.9: 40,290 traced neurons, 336,245 signed edges (w = sign × synapse count; sign per presynaptic neurotransmitter, validated empirically — zero mixed-sign neurons in the reference data), simulated with an exact-integration LIF scheme replicating Brian2's `method='linear'` semantics, with measured refractory-kick-drop and Poisson-input timing behaviors.

Three validation layers preceded any learning work: structural (matrix-level properties against published statistics), dynamical (spike-count benchmarks against the reference model), and behavioral (a 121-condition grid over sugar × bitter drive rates — 11 × 11, 0–200 Hz in 20 Hz steps — establishing the innate feeding boundary: the readout MN9_L fires ≥41.5 Hz iff sugar is present and bitter absent — robust across staggered onsets, with 95% suppression under bitter co-presentation and 3.9 Hz residual). The neurotransmitter-to-sign mapping is explicitly scope-limited to the gustatory/motor neurons the behavioral grid validated; every later extension to dopaminergic circuitry was preceded by its own sign re-anchoring measurement (§4).

**Reproduce-first posture:** no learning rule touched the substrate until its un-learned behavior was frozen, checkpointed (per-simulation weight hashes), and reproducible bit-for-bit.

## 2. Acquisition: learning is rare, legible, and located (Phase 2)

A one-hop Hebbian rule (per-edge δ = η·x·y on cue-incident edges, sign-preserving V_MAG semantics, η = 1e-4) was the *only* mechanism Phase 2 permitted. The governing question was not "can the network learn" but "which of its populations can" — and the answer was narrow:

- Seven candidate families were screened with pre-registered gates (innate silence, no documented valence, cosugar preservation, structural expressibility). Six families failed on specific, different criteria — the joint criterion region is a genuinely narrow carve-out of this connectome, not a formality (a structural landscape finding in its own right: learnability concentrates in strong, non-leaking leg-2 convergence onto a shared readout; 10/15 batch-probed types failed baseline gates alone).
- The surviving pair (GNG521 feed-direction; GNG380 withhold-direction) acquired robustly: 0→69–86 Hz from exactly-zero baselines, seed-stable, guard-silent (a stability guard with pre-registered thresholds runs on every trial of every experiment in this report).
- The pair's comparability was measured, not assumed — and the fine-grained probe that resolved an apparent acquisition asymmetry found a *rate* asymmetry instead (sharp vs. noisy-ramp onset), which later became the coincidence-waste discovery of §3.

**Every negative on the path is located**: e.g., the apparent "direction-specific leg-2" claim was retracted when a dose-diff (interleaved schedules halve per-cue dose silently) showed the slow direction needed 15–20 trials, not 10 — a correction that itself became a standing rule (diff trial-dose before config when a result contradicts a prior measurement).

## 3. Retention and reversal: two well-earned negatives (Phase 2, Task B)

**Retention holds perfectly.** Thirty no-stimulus trials after acquisition, with the plasticity rule still live: all twelve blocks bit-identical from end-of-acquisition to end-of-retention (verified at weight-hash level, not inferred from flat readouts — the spontaneous dynamics that could have driven drift were separately verified dead-silent). The learned state is a fixed point of the quiet network.

**Reversal fails — twice, differently, both instructively.** Under the frozen rule:

- *GNG521 (feed→withhold)*: total negative. The established excitatory association is untouchable by aversive co-presentation at 2.5× the acquisition dose. Weights only grow (measured across the association's 25-edge carrier footprint: every delta positive) — the rule is potentiative-only. [The 334-edge figure that appeared in an earlier draft was GNG380's reversal-training edge count carried into the GNG521 context — the same context-drift class the project's claim-audit rule exists for, caught here on re-review.]
- *GNG380 (withhold→feed)*: a transient crossing. The readout crosses the decision threshold at trial 15 in 5/6 seeds, peaks, then **regresses** to 27 Hz by trial 25 while weights continue growing monotonically — a dynamical non-monotonicity, not decay. Mechanism isolated by traced replay: **coincidence waste.** The intermediates phase-lock to the shared drive; input arrivals at the readout rise 34% while its spikes fall 45%; kicks land on an already-depolarized membrane and collapse. The boundary is measured and reusable: waste onsets when convergent intermediates exceed ~300 Hz (⅔ of the refractory ceiling) — GNG521's intermediates run at 33% of ceiling and are stable at 2.75× crossing dose; GNG380's run at 78%. Consolidation-by-stop-at-crossing is therefore *conditional*, with the online predictor (intermediate rates, no readout probing needed) characterized from data.

## 4. The dopaminergic investigation: four hypotheses, four located outcomes (Phase 3)

D3 sign re-anchoring first (the Phase 1 freeze required it): dopamine's +1 default sign on GABA hubs is **directionally validated** by monotone stimulation sweeps. Then the census results, each a measurement that killed or reshaped a design:

1. **Broadcast dopamine is refuted for this closure.** 1,449 consensus-dopamine neurons (consensusNt census; the predicted-NT census counts 1,444 — both real, different fields) have only 796 local out-edges onto 188 targets; 33% of DA weight lands on a single octopamine neuron. The trained circuit receives essentially zero direct DA input.
2. **The appetitive/aversive dichotomy is confirmed from structure**, not assumed: bitter GRN drive fires PPL101/102/106 + PAM12 (130+ Hz); sugar drive fires *zero* DA neurons directly — its modulatory route is the octopamine relay. The populations are disjoint.
3. **Gated biophysical suppression is refuted by effect size**: the DA→inhibitory-hub pathway is real (weights −1 to −21 onto the coincidence-waste intermediates; strongest: −21 onto 15207, −17 onto 14642) but delivers ~1.5 mV mean hyperpolarization against hard-driven 350 Hz targets — and driving the gate inside training trials at 50–200 Hz changed nothing (intermediate climb and readout regression identical to control across all arms; the control reproduced the Phase 2 regression arc to the spike).
4. **Fixed-decay consolidation is refuted by a measured no-free-lunch**: the decay constant calibrated from the regression's own timing (λ ≤ 0.807 for consolidation-at-onset) strangles acquisition at every band value (peaks 10–19 Hz vs. 49 control) — because GNG380's acquisition *needs* the accumulation that consolidation forbids. Two requirements incompatible in one constant: measured, not argued.

Along the way, two latent implementation hazards were caught by test before any run could launder them: V_MAG's never-exercised negative-delta path silently *flips edge signs* when |δ|>|w| (a WP1-era bug pinned by trip-wire test), and a trial-wiring conflation (one binary flag gating coincidence, application, and sign) was found by reading the code and decoupled without redesign.

## 5. Unlearning: the negative ladder and the mechanism it located (Phase 3→4)

The extinction result that reframed everything: **bitter-paired extinction is structurally mis-designed.** It reaches a fixed 15–18-edge set (60–64% of the association's 25 carriers), erodes 1.1–1.45% of acquired mass per 25 trials, and — the reachability census finding — **the unreachable 40% is sugar-driven**: the partners that co-fired during acquisition (because sugar was present) cannot co-fire during bitter-only extinction (because sugar is absent). *You cannot weaken an association by removing the thing that built it, because removing it also removes access to what it built.* This principle predicted the GNG380 boundary before it was checked (below).

The working mechanism assembles entirely from measurements made before use:
- **Eligibility** accumulates from sugar-recruited coincidence — the census identified the untouched partners as sugar-driven; launch sanity confirmed 8/9 firing under cue+sugar from the acquired matrix.
- **Sign** arrives from the aversive pathway — the PPL trio, measured firing under bitter, applied as a per-trial scalar at apply-time (never-simultaneous with the appetitive phase, enforced structurally).
- **Persistence** across the phase boundary with *no* decay term — the Phase 3 decay constant was deliberately not carried over (a constant must not travel to a context it wasn't measured for; pinned by test).
- **Floors**: V_CLIP — magnitude decrease floored at zero, sign never flips, stored structural zeros survive (the WP1 eliminate-zeros contract, re-tested in this context).

**Result (development-stage, n=3 seed reps):** cue-alone response of the acquired association: 68–84 Hz at cycle 5 → **exactly zero spikes by cycle 15, held through cycle 25, all reps** — literal zero verified at spike-count level (integer counts over the full 1000 ms window), the project's standing standard. Cosugar probes never left 78–88 Hz: the innate sugar→readout pathway is untouched. Guard silent. All 25 carriers and all 9 previously-unreachable partners eroded to identical floors in every rep; six collateral mid-trajectory edges vary at 0.02–0.7 units across seeds (reported per audit, not smoothed). This is extinction, not graded weakening — the protocol as run had no dial.

**The generality boundary is structural and stated precisely:** GNG380's suppressive association spans 158 edges over 73 partners; 45 of those partners have zero input from the drive that built the association. The mechanism's key ingredient — a drive that re-opens the carriers' coincidence — has no measured analog for 62% of that footprint. Whether *any* protocol can reach them is the registered open question.

## 6. Method: the discipline the results stand on

The arc's characteristic move is the same at every scale: **when a plausible story and a measurement disagree, measure the disagreement.** Its instrumented forms, all standing in the registry with origin stories:

- **Pre-registration before data**: split criteria (PASS / NEGATIVE-A / NEGATIVE-B) — twice separating outcomes that a single pass/fail would have conflated (never-crossed vs. crossed-then-held are opposite findings).
- **Guards that earn their cost**: runtime assertions on launch scripts (twice caught their own launcher); probe purity (hash-unchanged through probes); stability guard on every trial; bit-for-bit resume verification.
- **Fail-loudly rules**: empty-scope guard (a verification that verifies nothing must not emit a clean verdict); resume-rate vs. compute-rate (stale data detection); quarantine, never aggregate, superseded artifacts.
- **No free constants**: every parameter calibrated against the substrate's own measured data (λ from the regression's timing; the L3c constant was *not* carried into L4a's context).
- **Programmatic document-claim audit before any close-out is final** — numeric claims re-derived from raw records, never re-read as prose. Its two catches on this report's own close-out: a range migrated between contexts (92→88), and a summary sentence widening "carriers identical" into "all edges identical" — prose generalizing past measurement, a failure mode distinct from wrong measurement.

## 7. Scope, in both directions

**Position relative to prior work:** connectome-based demonstrations of learning and reversal exist — e.g., dopamine-gated conditioning on FlyWire mushroom-body circuitry with reversal and decay (snuri00/fruit-fly-connectome; PGCN), and multi-phenomenon MB models on the larval connectome (mb-dual-dan) — typically by *adding* a plasticity rule to connectome data and showing the cycle works. This work's distinct contribution is orthogonal: it maps *where in the substrate* learning can occur (the narrow anatomical regime), *why* each conventional removal mechanism fails (each failure located to a measured structural cause), *which* of the substrate's own pathways accomplish removal and under what protocol, and the structural law governing all of it — with every claim traced to named neurons, measured weights, and spike-count-verified outcomes, and every summary audited programmatically against raw records.

**Established:** a validated frozen substrate; acquisition with a characterized narrow regime; retention at weight-hash level; reversal failure with two distinct measured mechanisms (potentiative-only weights; coincidence waste with its ~300 Hz boundary); the DA anatomy's true structure (pathway-specific, appetitive/aversive disjoint); unlearning of one association via the substrate's own dual pathways, spike-verified, with a located mechanism and a located boundary.

**Not established (and not claimed):** unlearning of the suppressive association (GNG380 — open on three measured grounds); graded (non-extinction) weakening; anything beyond development-stage seed counts on the Phase 3–4 items (confirmatory runs with frozen seed sets are the mechanical next step); generalization beyond this closure (MB/Kenyon cells are absent from it — the dopaminergic findings are SEZ-local).

The chain currently ends at: one microcircuit, one task pair, one learned-then-erased association, and a principle — *associations live where their recruiting coincidences live* — that predicted its own boundary condition correctly before the boundary was checked.

## 8. Provenance

Every number in this report traces to checkpointed JSONL artifacts and per-simulation weight matrices under `results/`, with design intent, deviations, and errata in `docs/FLY_LEARN_001_DECISIONS.md` (the working registry), close-outs at `docs/PHASE_3_4_CLOSEOUT.md` (claim-audited) and `docs/TASK_B_CLOSEOUT.md`, and the landscape note at `docs/PLASTICITY_LANDSCAPE.md`. 121 tests pin the infrastructure contracts cited throughout. Dataset: male-cns:v0.9 via neuPrint (Janelia); the v1.0 snapshot lineage was removed server-side and is documented as archived. Code and data: repository at commit `4bd1fe5` (69 commits on the arc).
