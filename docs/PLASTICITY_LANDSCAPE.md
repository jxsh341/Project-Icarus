# The Plasticity Landscape of a Connectome-Derived Substrate

**Project:** FLY-LEARN-001 (Phase 2), parent baseline FLY-BASE-001 @ d0d7677
**Status:** Standalone finding note — independent of Task A's outcome
**Date:** 2026-09-27
**Evidence base:** seven candidate families, 15-type batch probe (300 trials), four acquisition range-finders, three structural-screen refutations — all checkpointed under `results/phase2/`, decision audit trail in `docs/FLY_LEARN_001_DECISIONS.md`

---

## The finding

When a frozen, validated Drosophila connectome substrate (40k-neuron
run-007 closure, LIF dynamics, signed synapse-count weights) is asked
*which of its intrinsic neuron populations could serve as learnable
cues* under a simple 1-hop Hebbian plasticity rule, the answer is:
**very few, and they are anatomically specific.**

Across seven candidate families and a 15-type batch probe selected
from a structurally pre-filtered pool of 143 eligible types:

- **10 of 15** batch candidates failed the *baseline* gates alone —
  either they already drive the feeding readout (innate expression at
  63–90 Hz, "leak"), or they suppress the innate feeding program under
  co-stimulation.
- Every surviving candidate before the final pair died on a
  **different, specific criterion**: IR94e (aversive interaction with
  the sugar program), water GRNs (state-conditional valence), LB2a
  (weak functional path + co-suppression), GNG611/GNG622 (structurally
  2-hop but expressibility-dead — leg-2 weights of 1–5), GNG557
  (learnable but carries a 0.6 Hz innate expression tail), JO-F
  (documented mechanosensory/courtship valence).
- The two survivors — GNG521 (2 neurons) and GNG380 (6 neurons) —
  share a specific configuration: **strong leg-2 convergence onto the
  readout** (max second-leg weight 96 and 96) via hubs the cue alone
  **cannot** drive over threshold, with zero baseline expression and
  no documented behavioral valence.

## Why this is a result, not a process description

The expectation going in was that cue candidates would be plentiful —
that the hard part would be the learning mechanism, not the substrate
geometry. The measured reality is the opposite: **under this
plasticity rule, learnability on this connectome is concentrated in a
small, specific anatomical configuration, not diffusely available.**
The mechanism is legible:

1. **Learnability requires strong leg-2.** A 1-hop Hebbian window can
   only potentiate cue-incident edges. Expression therefore requires
   the cue's 1-hop targets to already hold strong edges into the
   readout (every measured expresser: leg-2 ≥ 92; every
   non-expresser: ≤ 5). A cue with no such convergence is a
   structural null at any learning rate — 100× the working η produced
   zero expression in the 3-hop case.

2. **Innate silence requires weak leg-1.** The same hubs that carry
   the strong leg-2 must be unreachable by the cue alone — else the
   cue drives the hub, and the strong leg-2 spikes the readout
   innately (GNG557: leg-1 = 27 into a leg-2 = 92 hub → 0.6 Hz leak;
   GNG521: leg-1 = 4 into a leg-2 = 96 hub → clean). Training works
   because the innate drive (sugar) drives the hub during
   co-presentation; the cue only needs to correlate, not cause.

3. **Leak is not structurally predictable (yet).** Three successive
   structural screens — max leg-1 per route, summed leg-1 into strong
   hubs, total transitive 2-hop drive — each validated on some knowns
   and were refuted by the batch data (GNG467: summed leg-1 = 5, leaks
   at 53–71 Hz; GNG380: summed leg-1 = 99 into a hub, clean). The
   leak mechanism for most failing types remains an open question;
   only the empirical probe decides.

The joint density of {strong leg-2, weak leg-1, zero leak, no valence,
comparable dynamics} is the scarce commodity — measured at 2 defensibly
usable types out of 15 probed from a 143-type pre-filtered pool.

## What it means downstream

- **For Task A:** the cue pair is a constrained resource, and any
  claim about "the substrate learned X" must carry the caveat that the
  cue geometry that permits learning is rare — the experiment works
  because the pair was found by exhaustive diligence, not because the
  substrate is saturated with learnable cues.
- **For plasticity-rule comparisons (WP6+):** the landscape itself is
  a dependent variable. A rule change (2-hop windows, neuromodulated
  gating) that widens the learnable region is a measurable,
  falsifiable improvement claim — the batch probe protocol is now a
  reusable instrument for measuring it.
- **For the MB/central-brain question (L3):** the closure contains
  86 MBONs and 206 PAM/PPL types but zero Kenyon cells; if
  neuromodulated learning later requires KC→MBON loops, this
  closure's cue-selection instrument will need a new snapshot — the
  landscape measured here is the SEZ-local one.

## Provenance

Every probe, screen, and rejection is checkpointed and committed:
`results/phase2/wp2_cue_probe_batch.jsonl` (batch 1),
`wp2_cue_probe_gng611_gng622.jsonl`, `wp2_gng557_verdict.json`,
`wp3_pilot/batch2_probe.jsonl`, `leak_structure_retrospective.json`,
`screen_v2_check.json`, `prefilter_pool.json`,
`expressibility_audit.json`, and the decision registry
(`docs/FLY_LEARN_001_DECISIONS.md`) which records each candidate's
death with its criterion, evidence, and the reasoning for every
criterion amendment made along the way.

---

## Addendum (2026-10-09, Phases 3-4): learn, keep, unlearn - and where each boundary sits

**The landscape's original claim is extended by measurement.**
Under the frozen substrate:

- **Learn** (WP4): yes - in the narrow, leg-2-convergent
  anatomical regime this note originally characterized.
- **Keep** (R1): yes - retention is bit-identical weight stability
  under dead-silent spontaneous activity.
- **Unlearn (Phase 2 frozen L1): no - now located at three
  measured levels.** Coincidence-reachability (the carriers of an
  association are co-active only with the drive that recruited
  them - removing that drive removes access), protocol scope
  (extinction-by-bitter reaches 60-64% of carriers, a fixed set),
  and rate (1-2% of acquired mass per 25 trials at frozen eta).
- **Unlearn (Phase 4 eligibility-then-sign): yes, for GNG521's
  association - with the mechanism stated exactly.** Re-present
  the recruiting drive (sugar: it opens the carriers' coincidence)
  to accumulate eligibility; supply the valence sign from the
  aversive pathway (the PPL trio); the erosion reaches 100% of
  carriers and drives the association to literal-zero
  (spike-count-verified extinction). The substrate's own dual
  pathways, not an invented mechanism.
- **The generality boundary is structural, not rhetorical:** the
  GNG380 withhold association (158 edges, 73 partners, 45 with
  zero input from the drive that built it) lacks the recruitment
  structure the mechanism depends on. Whether ANY protocol can
  reach those carriers is the open question - the same
  reachability framing this note's original census used for
  acquisition, now applied to removal.

**The cross-cutting principle the arc adds to the landscape:**
associations live where their recruiting coincidences live.
Anything that wants to change them - strengthen, suppress, or
erase - must open those same coincidences; drive removal is not
erasure but access surrender. This is the sentence the whole
Phase 3->4 negative-result ladder (biophysical gating, fixed
decay, single-gate, conflation, bitter-extinction) was climbing
toward.
