# fly-cognition

**Learning, keeping, and unlearning in a connectome-derived neural substrate.**

A computational research project built on the Drosophila melanogaster MaleCNS connectome (male-cns:v0.9, via neuPrint): reconstruct a biologically real circuit, validate it against the untrained organism's measured behavior, then ask whether — and *where*, and *why* — it can acquire, retain, and remove an associative memory. Full write-up: [`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md).

## Results

| Operation | Outcome | Status |
|---|---|---|
| **Reconstruct & validate** | 40,290-neuron / 336,245-synapse closure; LIF dynamics; signed synapse-count weights; reproduces the innate sugar/bitter feeding decision across a 121-condition drive grid | Frozen (`FLY-BASE-001`, commit `d0d7677`) |
| **Learn** | Yes, but rare and located: acquisition succeeds only in a narrow anatomical regime (strong second-order convergence onto the readout, no innate leak); 10/15 candidate neuron types fail baseline gates | Verified, multi-seed |
| **Keep** | Learned weights bit-identical through extended no-input periods — a genuine fixed point of quiet dynamics | Weight-hash-verified, 12 blocks |
| **Unlearn** | Every conventional mechanism fails for a *located* reason (extinction can't reach the sugar-recruited carriers; decay either strangles learning or fails to protect it; broadcast dopamine doesn't match the measured anatomy). Success came only from a protocol re-opening the coincidences that built the association: sugar-recruited eligibility + aversive sign. Result: 68–84 Hz → **literally zero spikes**, innate pathway untouched | Spike-count-verified, **development-stage (n=3)** — confirmatory replication pre-registered, not yet run |

The central principle the arc produced: **associations live where their recruiting coincidences live; removing the drive is not erasure but access surrender.** It predicted its own boundary (GNG380's suppressive association: 45/73 partners have no measured drive that can reopen their coincidence) before the boundary was checked.

All of this lives in local SEZ gustatory/motor circuitry — the closure contains no Kenyon cells, so nothing here touches the mushroom body, the canonical learning center (see [`docs/PRIOR_ART_MEMO.md`](docs/PRIOR_ART_MEMO.md) for the comparison to prior connectome-plasticity work).

## Phases

1. **Baseline (complete, frozen)** — ingestion pipeline, structural validation, reference LIF model, behavioral reproduction, `FLY-BASE-001` freeze.
2. **Learning (complete)** — cue screening (leg-2 expressibility first), acquisition for the surviving pair (GNG521 feed / GNG380 withhold), retention, and two located reversal failures (potentiative-only weights; coincidence waste above ~300 Hz).
3. **Neuromodulation (complete)** — dopamine census: pathway-specific, not broadcast; bitter→PPL trio, sugar→OA relay only; the "gate-DA" population silent under every tested drive (retired as a scope boundary). Broadcast DA, gated suppression, and fixed-decay consolidation each refuted by measurement.
4. **Unlearning (complete, dev-stage)** — eligibility-then-sign protocol: sugar-phase opens the carriers' coincidence, bitter-phase PPL sign applies the negative delta, V_CLIP floors. Extinction verified at spike-count level.
5. **Confirmation & generality (pre-registered, pending)** — Experiment A: confirmatory replication on frozen fresh seeds (`docs/PHASE_5_CONFIRMATORY_PREREG.md`); Experiment B: prospective test of the accessibility predictor on held-out circuits; Experiment C: graded unlearning (existence not assumed).

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
└── tests/           # 121 contract tests (uv run pytest)
```

## Quick start

```bash
uv sync
uv run pytest          # 121 contract tests
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

Dataset: male-cns:v0.9 via neuPrint (Janelia Research Campus). Baseline frozen at commit `d0d7677` (tag `FLY-BASE-001`); the arc through Phase 4 at commit `bfa796d`. Decision registry with origin stories for every rule: [`docs/FLY_LEARN_001_DECISIONS.md`](docs/FLY_LEARN_001_DECISIONS.md).
