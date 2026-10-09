# Connectome-Derived Learning: Results Summary

**One page.** Full methodology, located negatives, and provenance: `TECHNICAL_REPORT.md` in the same repository.

---

## What we built

A biologically real neural substrate, reconstructed and validated: a 40,290-neuron, 336,245-synapse closure of the Drosophila Male Adult Nerve Cord connectome (male-cns:v0.9, the Janelia-traced dataset), simulated with biologically-derived spiking dynamics and signed synaptic weights. Before any learning experiment, the un-trained network was frozen, benchmarked against the reference model, and shown to reproduce the innate feeding decision — sugar present, bitter absent, motor readout fires — across a 121-condition behavioral grid. Reproduce first; modify later.

## What it does

**It learns.** With one local, biologically-plausible plasticity rule — correlation-based weight change on the connections a cue neuron actually touches — the substrate acquires new associations: a neutral cue that starts at exactly zero response drives the feeding motor neuron to 70–86 Hz. Learning is not generic, though: a systematic screen showed it concentrates in a specific, rare anatomical configuration (strong convergent wiring onto the readout, no pre-existing leak), with ten of fifteen candidate neuron types failing baseline checks. *Where this connectome can learn is itself a mapped, measurable property.*

**It remembers.** After training, the learned state is bit-for-bit stable — verified at the level of individual synaptic weights — through extended periods with no input. The memory is a genuine fixed point of the network's quiet dynamics.

**It forgets — but only the right way.** The hard part, and where the science got interesting:

- Every conventional removal mechanism failed, and *we can say why in each case*. Extinction-by-aversive-pairing reaches only 60–64% of the association's synaptic carriers and erodes ~1% of it per 25 trials. Decay-based forgetting either strangles new learning or fails to protect it — the two needs are mathematically incompatible in one constant, measured on the network's own timing. Broadcast modulation (the textbook dopamine model) doesn't match this circuit's actual anatomy, which we mapped neuron-by-neuron.
- The insight that unlocked it: **an association can only be changed through the same coincidences that built it.** The unreachable carriers were unreachable because extinction-with-bitter removes the sugar that made them co-active in the first place. You can't erase a memory by taking away the thing that formed it — that also takes away your access to it.
- So the working protocol *re-opens* those coincidences (re-presenting sugar, which re-activates the full carrier population) while supplying the "weaken" signal from the network's own aversive pathway (a small, named cluster of dopamine neurons we identified as responding to bitter — a known biology, recovered from the data rather than assumed). **Result: the learned association falls from 70+ Hz to literally zero spikes — while the innate sugar-feeding pathway it must not damage stays fully intact.** Verified down to individual synaptic weights: every carrier erased, every innate connection preserved.

## What it is (and isn't) yet

One microcircuit, one task pair, one association taken through learn → retain → erase. The unlearning protocol worked on the feed-direction association; the suppressive-direction association has a mapped but unsolved boundary (62% of its carriers lack a known drive that can re-activate them — a real research question, not a scaling problem). Seed counts are development-stage; confirmatory runs are mechanical next steps. The findings are scoped to this closure — mushroom-body circuitry, the classic learning anatomy, is deliberately outside it.

## Why it matters

Others have shown that plasticity rules *can be added* to connectome data and produce learning and reversal — and the existing demonstrations (FlyWire whole-brain conditioning with reversal and decay; a necessity-ablated larval mushroom-body model; FlyWire MB reservoir learning) all concentrate on the **mushroom body**, the canonical learning center. This work's circuit contains no mushroom body at all: every result was measured in local gustatory/motor wiring outside the known learning center. It answers the questions those demonstrations leave open: *where in the substrate* learning can occur (a mapped, rare anatomical regime — itself a measurable property of the connectome), *why* each conventional removal mechanism fails (every failure located to a specific measured cause), and *which of the substrate's own pathways* accomplish removal, under a protocol derived from that anatomy rather than imposed on it. Every mechanism claim traces to named neurons, measured weights, and spike-count-verified outcomes; every summary is programmatically audited against raw records. The central principle — *memories live where their forming coincidences live* — is a structural law about wiring, not parameters, and it transfers to any substrate that has some.

## Artifacts

Repository (69 commits, 121 passing contract tests, per-trial checkpointed data for every experiment): available on request. Full technical report: `TECHNICAL_REPORT.md`. Decision registry documenting every design choice, deviation, and erratum: `FLY_LEARN_001_DECISIONS.md`.
