# fly-cognition

**Learning, keeping, and unlearning in a connectome-derived neural substrate.**

A computational research project built on the Drosophila melanogaster MaleCNS connectome (male-cns:v0.9, via neuPrint): reconstruct a biologically real circuit, validate it against the untrained organism's measured behavior, then ask whether — and *where*, and *why* — it can acquire, retain, and remove an associative memory. Full write-up: [`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md).

## Results

| Operation | Outcome | Status |
|---|---|---|
| **Reconstruct & validate** | 40,290-neuron / 336,245-synapse closure; LIF dynamics; signed synapse-count weights; reproduces the innate sugar/bitter feeding decision across a 121-condition drive grid | Frozen (`FLY-BASE-001`, commit `d0d7677`) |
| **Learn** | Yes, but rare and located: acquisition succeeds only in a narrow anatomical regime (strong second-order convergence onto the readout, no innate leak); 10/15 candidate neuron types fail baseline gates | Verified, multi-seed |
| **Keep** | Learned weights bit-identical through extended no-input periods — a genuine fixed point of quiet dynamics | Weight-hash-verified, 12 blocks |
| **Unlearn** | Every conventional mechanism fails for a *located* reason (extinction can't reach the sugar-recruited carriers; decay either strangles learning or fails to protect it; broadcast dopamine doesn't match the measured anatomy). Success came only from a protocol re-opening the coincidences that built the association: sugar-recruited eligibility + aversive sign. Result: 68–84 Hz → **literally zero spikes**, innate pathway untouched | Behavior replicated 8/8 at confirmatory stage (n=8 frozen seeds); **verdict MIXED per prereg — floors 21/25+8/9 with located residual edges**; not promoted to confirmed |
| **Certify forgetting** | Membership-oracle forgetting rate over all 11 unlearned reps: **11/11 classified never-learned** (oracle LOO 1.000, member recall 1.000); unchanged when the 4 residual-edge features are ablated — the residual synapses carry no inferable memory | **PASS** (Phase 6 WP-L6a, `docs/PHASE_6_PREREG.md`, commit `e60f308`) |
| **Erase at the synapse** | Rank-targeted multiplicative decay `w·e^(−1/τ)`, τ=1, on the sha256-pinned 25-edge footprint — drive-independent: **8/8 reps floor 25/25 carriers + 9/9 partners**, cue-alone zero by cycle 5, guard silent, no sign flips; clears all 4 dose-tail residuals that survived 25 cue+sugar cycles in Experiment A | **MIXED** — 7 PASS + 1 NEGATIVE-B (rep 5 cosugar 77 < 78 Hz band); floors 8/8 (WP-L6b, commit `d8e56e0`) |
| **Cross the boundary** | Same decay on GNG380 (158-edge footprint): **77/96 zero-input edges at floor** vs the 45/73-partner boundary the coincidence-gated mechanism could not reach; footprint 136/158 at floor; guard silent | **POSITIVE-BOUNDARY**, exploratory n=2 (WP-L6b g380 probe) |

The central principle the arc produced: **associations live where their recruiting coincidences live; removing the drive is not erasure but access surrender.** It predicted its own boundary (GNG380's suppressive association: 45/73 partners have no measured drive that can reopen their coincidence) before the boundary was checked.

Phase 6 separated three operations that are **not interchangeable**: (1) **behavioral extinction** — the learned response goes to zero spikes (demonstrated, replicated); (2) **information-level forgetting** — no tested membership oracle can distinguish the unlearned substrate from a never-learned one, residuals included (certified, FR 11/11); (3) **synaptic erasure** — the acquired footprint itself is driven to its numerical floor by drive-independent rank-targeted decay (demonstrated on GNG521 8/8; boundary-partial on GNG380). A system can do any one of these without the others; the arc now measures each separately.

All of this lives in local SEZ gustatory/motor circuitry — the closure contains no Kenyon cells, so nothing here touches the mushroom body, the canonical learning center (see [`docs/PRIOR_ART_MEMO.md`](docs/PRIOR_ART_MEMO.md) for the comparison to prior connectome-plasticity work).

## Phases

1. **Baseline (complete, frozen)** — ingestion pipeline, structural validation, reference LIF model, behavioral reproduction, `FLY-BASE-001` freeze.
2. **Learning (complete)** — cue screening (leg-2 expressibility first), acquisition for the surviving pair (GNG521 feed / GNG380 withhold), retention, and two located reversal failures (potentiative-only weights; coincidence waste above ~300 Hz).
3. **Neuromodulation (complete)** — dopamine census: pathway-specific, not broadcast; bitter→PPL trio, sugar→OA relay only; the "gate-DA" population silent under every tested drive (retired as a scope boundary). Broadcast DA, gated suppression, and fixed-decay consolidation each refuted by measurement.
4. **Unlearning (complete, dev-stage)** — eligibility-then-sign protocol: sugar-phase opens the carriers' coincidence, bitter-phase PPL sign applies the negative delta, V_CLIP floors. Extinction verified at spike-count level.
5. **Confirmation (complete)** — Experiment A executed on 8 frozen fresh seeds (`docs/PHASE_5_CONFIRMATORY_PREREG.md`): behavioral criteria 8/8, weight floors 21/25+8/9 with 4 located residual edges → **MIXED**, non-aggregated; dose-tail question registered, not patched (commit `0f71423`).
6. **Forgetting certification & targeted erasure (complete)** — WP-L6a forgetting-rate oracle **PASS** (FR 11/11, ablation-stable); WP-L6b rank-targeted decay **MIXED** on GNG521 (floors 25/25+9/9 in 8/8) with GNG380 probe **POSITIVE-BOUNDARY** (`docs/PHASE_6_PREREG.md`, commits `e60f308`, `d8e56e0`).
7. **Proposed, not yet preregistered** — from the 2026-11-03 external review (logged in the decision registry): predictive structural accessibility on held-out circuits; GNG380 confirmatory unlearning with behavioral readout (n>2); graded/parameterized forgetting; multi-memory coexistence & selective removal.

## Repository structure

```text
fly-cognition/
├── README.md
├── docs/            # technical report, decision registry, close-outs, pre-registrations
├── data/            # frozen neuPrint snapshots (run-007 baseline), seeds, checksums
├── fly/             # model: LIF dynamics, signed connectivity, plasticity, training runs
├── scripts/         # per-work-package experiment harnesses and audit instruments
├── benchmarks/      # neural/compute baselines
├── validation/      # head-to-head and behavioral anchor artifacts
├── results/         # per-trial JSONL checkpoints, weight matrices, census JSONs
└── tests/           # 154 contract tests (uv run pytest)
```

## Quick start

```bash
uv sync
uv run pytest          # 154 contract tests
uv run python scripts/phase4_report_claim_audit.py   # re-derive the report's claims from raw records
```

Every experiment harness checkpoints per-trial (JSONL + weight matrices), so any run can resume without silent state loss, and every number in the docs can be re-derived from `results/`.

## Scientific rules (standing)

- **Never modify the system before understanding what the unmodified system does** — reproduce first, modify later.
- **No constant travels to a context it wasn't measured for.**
- **When a plausible story and a measurement disagree, measure the disagreement** — every negative gets located, not waved off.
- **Pre-register criteria before data**; MIXED outcomes are their own verdict and never aggregate into PASS.
- **Fail loudly** — a verification with empty scope must not emit a clean verdict; runtime guards belong on every launch script.
- **Programmatically audit every close-out against raw records before it's called final** — claims are re-derived from data, never re-read as prose.

## Provenance

Dataset: male-cns:v0.9 via neuPrint (Janelia Research Campus). Baseline frozen at commit `d0d7677` (tag `FLY-BASE-001`); the arc through Phase 4 at commit `bfa796d`; Phases 5–6 through commit `d8e56e0`. Decision registry with origin stories for every rule: [`docs/FLY_LEARN_001_DECISIONS.md`](docs/FLY_LEARN_001_DECISIONS.md).
