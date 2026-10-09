# Phase 3→4 Close-Out — Learning, Keeping, and Unlearning on the MaleCNS Substrate

**Project:** FLY-LEARN-001 | **Stage:** Development (n=3 seeds, §22; not confirmatory)
**Arc:** L3 (dopaminergic mechanisms) → L4 (eligibility-then-sign extinction)
**Verdict headline:** The substrate can **learn** (WP4), **keep** (R1), and — under one measured protocol, for one cue — **unlearn** (L4b). The unlearning mechanism is assembled entirely from measured components; its generality beyond GNG521's association is **open on measured grounds**, not assumed.

---

## 1. What was established, in order

| Finding | Status | Where measured |
|---|---|---|
| DA sign on GABA hubs is +1 directionally (H(+)); monotone excitation | Established | WP-L3a sweeps |
| Gated biophysical suppression of the coincidence-waste regime | **Refuted** (real pathway, below effect size) | WP-L3b, all rates |
| Fixed-λ eligibility decay as consolidation | **Refuted** (self-defeating for slow cues — the no-free-lunch is measured) | WP-L3c, full band |
| Broadcast-scalar dopamine | **Refuted** (pathway-specific; 0.0–5.1% coverage of trained circuits) | WP-D1 |
| The 9-cell "gate population" as a spiking gate signal | **Refuted** (0 Hz under every condition); retired as scope boundary | L3d census |
| Appetitive/aversive DA dichotomy | **Confirmed from measurement** (bitter fires PPL101/102/106+PAM12; sugar fires *zero* DA directly — its route is the OA relay) | L3d census |
| V_MAG with negative deltas exceeding weight magnitude flips sign | **Hazard caught RED** (latent since WP1; pinned by trip-wire test) | L3d guards |
| L3d extinction-by-bitter | NEGATIVE-A, doubly located: scope-capped (fixed 60–64% coverage) + rate-capped (1.1–1.45% mass / 25 trials) | L3d + scope check |
| The unreachable 40% is sugar-reachable | Q-A NO / Q-B YES — *extinction-by-bitter removes the drive that recruited the carriers* | Reachability census |
| Eligibility-then-sign extinction | **PASS** — 25/25 carriers eroded, 9/9 previously-unreachable partners reached, cosugar intact, guard silent, seed-stable | WP-L4b + edge forensics |

## 2. The unlearning result, stated at its exact strength

Cue-alone response of the acquired GNG521 feed association: 68–84 Hz at cycle 5 → **exactly zero spikes by cycle 15, held through cycle 25, all 3 reps** — verified at the spike-count level (`mn9_hz = len(spike_times)`, integer counts over the full 1000 ms window; the Task B/WP6c literal-zero standard), not a rounded display value. Cosugar probes never left 78–88 Hz (programmatic audit of all 30 records); the innate sugar→MN9 pathway is untouched (27 edges changed = 25 carriers + 2 collateral; structure preserved, nnz 336,245 unchanged, stored zeros intact). **Carrier outcomes are float-exact across reps** (all 25 carriers + all 9 previously-untouched edges land at identical V_CLIP floor values in every rep); six collateral mid-trajectory edges differ at the 0.02–0.7 level across seeds (partial erosion positions, seed-sensitive) — reported per the audit, not smoothed.

**"Extinguished, not diminished"** — with all 25 carrier edges at their V_CLIP floors, this is extinction, not graded weakening. The protocol as run had no dial; that graded weakening exists as a protocol-shaping question is open.

**Mechanism, all measured before use:** eligibility opened by sugar-recruited coincidence (the census found the untouched partners sugar-driven; launch sanity confirmed 8/9 firing under cue+sugar from the acquired matrix); sign supplied by the aversive phase (PPL trio, measured at 130+ Hz); persistence across the phase boundary with no decay term (the L3c λ deliberately *not* carried over — pinned by test; standing rule: no constant travels to a context it wasn't measured for); V_CLIP floors (pinned; sign never flips; stored zeros survive).

## 3. The generality boundary — stated precisely

**What the PASS covers:** one cue (GNG521), one protocol (sugar-eligibility phase → bitter-sign phase), one footprint shape (25 edges, 443 mass, 9 partners), development-stage n=3.

**The GNG380 question is genuinely open on three measured grounds** (structural census, no simulations):
1. **Scale and shape:** GNG380's withhold association is 158 edges over 73 partners — larger and far more diffuse (includes the hub 10646 and broad interneurons at 1000+ inputs). Erosion cost scales with both.
2. **The recruitment-drive gap:** only 28/73 partners have *any* bitter-GRN input; 45 have zero. The L4b mechanism's key ingredient — a drive that re-opens the carriers' coincidence — has **no measured analog on the GNG380 side** for 62% of its partners.
3. **The sign problem is not mirrored:** eroding a suppressive (withhold) association means restoring excitatory tone — positive deltas under some gate — and the mirror of L4b's sign arrangement has no measured source.

"The substrate can unlearn" is therefore proven for one association under one protocol; extension to the other learned association is an open mechanism question, registered as such.

## 4. The pattern the arc followed

Every stage converted a plausible mechanism into either a measurement or a located negative: broadcast → pathway-specific (census); gated suppression → refuted with effect-size arithmetic (L3a+L3b); fixed decay → refuted with the no-free-lunch measured across the full band (L3c); single-gate → refuted by the dichotomy census; conflated gate roles → found by reading the code, decoupled without redesign; extinction-by-bitter → doubly located (scope + rate), then *explained* (the census's sugar-recruiter finding); and the fix — eligibility-then-sign — inherited its every component from a measurement made before it was used. The three-factor structure (eligibility × valence × trace, identified as a mechanism class in the Cadence audit under clean-room discipline) turned out to be instantiable with substrate-honest sources at every factor.

Standing rules added along the way: runtime guards on every launch script (twice caught their own launcher); never-simultaneous re-derivation of NEVER-BOTH; no-constant-travels-between-contexts; fail-loudly-on-empty-scope (vacuous-check lesson); the criterion-split discipline (three-way outcomes pre-registered, twice catching real distinctions).

## 5. Provenance

Registry: `docs/FLY_LEARN_001_DECISIONS.md` (§ L3 design → L4b result, every deviation and erratum inline). Data: `results/phase3/` (wp_l3a/b/c, l3d + checks), `results/phase4/wp_l4b/` (training, probes, verdict forensics). Rules: `scripts/phase3_decay_rule.py`, `phase4_eligibility_sign_rule.py` (tested, default-off contracts pinned). Tests: 121 passing, including the V_MAG hazard trip-wire, never-both scan, decay-timebase pin, and V_CLIP floor contracts.

---

## 6. Document claim audit (2026-10-09)

Per review, this document was audited programmatically against the raw records before being treated as final. Two over-claims found and corrected in place:
1. **Cosugar range** was stated as 78–92; the records support 78–88 (the 92 was a carry-over from the L3d table, a context error of the same shape as the 334-vs-25 footprint slip).
2. **"Byte-identical edge outcomes across reps"** was stated; float-exact comparison of the three final matrices shows 6 of 336,245 entries differing — all collateral edges mid-erosion-trajectory (0.02–0.7 units, seed-sensitive). The carrier claims (25/25 at identical floors, 9/9 previously-untouched reached) survive the audit exactly; the summary sentence had quietly widened "carriers identical" into "all edges identical."

The audit method is itself on record (`scripts/phase4_closeout_claim_audit.py`): re-derive every numeric claim from raw JSONL and checkpoints rather than re-reading the prose. The two corrections are the kind the method exists to catch: plausible, directionally-harmless, and wrong.
