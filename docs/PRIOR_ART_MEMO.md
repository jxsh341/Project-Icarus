# Prior-Art Memo — examined directly, 2026-10-09

Status: the comparative positioning in TECHNICAL_REPORT.md §7 and FUNDING_SUMMARY.md
was written from search snippets and was therefore **provisional**. This memo records
what direct examination of each prior project actually shows, and the axis along
which the comparison is now stated. This memo is the basis for the positioning;
the documents cite it.

## The axis that emerged from reading them

**All three prior projects operate on the mushroom body — the canonical learning
center, chosen because the literature says that's where flies learn.**
snuri00/fruit-fly-connectome: Kenyon cells + MBONs + PAM/PPL DANs, FlyWire whole
brain but learning confined to MB compartments. mb-dual-dan: larval MB, DAN-c1,
KC→MBON compartments (Winding 2023). PGCN: PN→KC→MBON + DAN ancillary, FlyWire.
Our run-007 closure contains **zero Kenyon cells**; every plasticity-bearing edge
we measured lives in local SEZ (subesophageal zone) gustatory/motor circuitry
outside the known learning center. Learning outside the MB is a different claim
from learning inside it, and none of the three prior projects addresses it.

Secondary differentiators, confirmed by reading:
- **Located failures**: we test each conventional removal mechanism until it fails,
  then locate the failure structurally (broadcast DA refuted by anatomy; gated
  suppression by effect size ~1.5 mV vs 350 Hz targets; fixed decay by a measured
  no-free-lunch). None of the three prior projects reports located failure modes;
  snuri00's steering-synapse control result (rule made things worse) is reported as
  a negative without structural location.
- **Spike-count-verified extinction**: our zero is literal (integer spike counts),
  not a thresholded readout. snuri00's conditioning readout is MBON rate changes;
  mb-dual-dan reports valence traces; PGCN reports an index (Blocking Index ~+0.99).
- **Self-audit discipline**: programmatic claim audit + reintroduction checks;
  not present in any of the three (their stats are honest but conventional).

## Per-project assessment

### snuri00/fruit-fly-connectome (FlyWire whole brain, Shiu-model LIF)

Read directly (README, full). What it is: a live whole-brain fly (138,639 neurons,
54.5M synapses, FlyWire v783, LIF on the Shiu et al. parameters), plus games as
readouts (DOOM, swatting). Learning: dopamine-gated MB plasticity (Kenyon cells
active in the 1.5 s before dopamine in a compartment have their KC→MBON synapses
depressed). Two Shiu-model changes needed: dopamine's fast synapses removed (else
reward excited thousands of KCs), and DANs selected by cell class because FlyWire
NT predictions label 5,172/5,177 KCs dopaminergic — both honest and documented.

Its own assessment of its learning result is notably honest: the DOOM improvement
is "a trend, not yet a demonstration" (paired t-test p=0.20, n=40). The
conditioning experiment (Tully & Quinn-style differential aversive conditioning,
Hige-style MBON readout) includes controls, reversal, and memory decay —
that part is solid.

Comparable on: conditioning + reversal + decay on a real connectome, honest stats.
Not comparable on: mechanism location (its negative is reported unlocated);
resolution of verification (rate readouts, not spike counts); substrate region (MB).

### Lyons800/mb-dual-dan (larval MB, Winding 2023)

The most rigorous of the three: a bioRxiv preprint (v0.1.1, Zenodo DOI
10.5281/zenodo.20326853), 37 passing regression tests, necessity ablations
(each of four architectural ingredients removed → phenomenon lost). Claims:
acquisition+extinction, novelty signaling, latent inhibition, fast reversal —
each requiring one ingredient on the same larval connectome substrate. Also has a
falsifiable biological prediction (DAN-c1 habituation, testable by calcium imaging).

Comparable on: rigorous methodology, connectome-grounded, necessity ablations.
Not comparable on: region (larval MB), and its learning is in silico RPE/surprisal
machinery added to the connectome (by design — that's its contribution), not
a measurement of where the substrate's own resources support learning.

### colehanan1/PGCN (FlyWire MB, reservoir + dopamine-gated synapses)

A pipeline: fixed innate odor paths + learnable dopamine-gated synapses, three
test phases (160 tests), veto gates, eligibility traces, counterfactual
microsurgery. Genuinely thorough test infrastructure. But the learned component
is again MB-concentrated (PN→KC→MBON core + DAN ancillary), and its headline
numbers (Blocking Index ±0.99) are index readouts.

Comparable on: test discipline, dopamine-gated plasticity on real wiring.
Not comparable on: region (MB), readout resolution, located failures.

## Revised positioning (basis for both external documents)

1. Prior connectome-plasticity work concentrates on the mushroom body, the
   canonical learning center. This work demonstrates learn/retain/unlearn **outside
   the mushroom body** — the closure contains no Kenyon cells — in local
   gustatory/motor circuitry the substrate uses for an innate behavior.
2. Prior work adds a plasticity rule to connectome data and shows the cycle works.
   This work maps **where** learning can occur (narrow regime), **why** each
   conventional removal mechanism fails (each failure located to a measured
   structural cause), and **which of the substrate's own pathways** accomplish
   removal under a protocol derived from the measured anatomy.
3. What is NOT claimed: priority on the cycle; generality beyond this closure;
   anything about MB/Kenyon-cell learning (absent from the closure). Updated
   2026-11-04: GNG380 unlearning is CLOSED (WP-L6b + P2 PASS 8/8), graded
   unlearning EXISTS and is quantitative (P3 PASS 16/16), Experiment A ran
   (MIXED, non-aggregating) and its dose-tail question is answered by WP-L6a
   (PASS: residuals not an inferable leak).
4. **Paper-level reading done 2026-11-04** (closes the provisional qualifier
   for the two repos that have one):
   - **mb-dual-dan** has a bioRxiv preprint (v0.1.1, Zenodo DOI
     10.5281/zenodo.20326853): "A dual-pathway dopaminergic code for reward
     prediction and epistemic surprise in the larval Drosophila mushroom
     body" — four-ingredient necessity ablations (signed RPE, Bayesian
     surprisal, surprisal-modulated lr, parallel valence traces) on the
     Winding 2023 LARVAL MB connectome, plus a falsifiable DAN-c1 habituation
     prediction. Region: larval MB; the learning machinery is added in silico
     (RPE/surprisal agents), not measured from the substrate's own resources.
     It does not address located removal failures, accessibility prediction,
     certified forgetting, or selective erasure.
   - **PGCN** is repo-only as of 2026-11-04 — no peer-reviewed paper or
     preprint DOI located; its README itself documents a caught 1000x
     KC->MBON weight bug and the mitigations. FlyWire adult MB
     (PN->KC->MBON + DAN), veto gates, microsurgery, Shapley causal analysis.
     Region: adult MB; readouts are index-level. Same non-coverage of our
     four questions.
   - **snuri00/fruit-fly-connectome** (whole-brain FlyWire): conditioning,
     reversal, decay — MB-based, behavior-level, no located synaptic failures.
   - ML-privacy prior art (arXiv:2410.22374 FNN, arXiv:2003.10933 Forsaken):
     read directly earlier; mapped to WP-L6a/L6b; port, not replication.
   Conclusion: positioning items 1-3 above STAND, now paper-grounded. The
   remaining honest qualifier is narrower: PGCN has no paper to read, so its
   claims are judged from its repo README/tests only.
