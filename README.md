# fly-cognition

Connectome-Based Fly Cognitive Augmentation.

Phase 1 builds a reproducible, validated baseline: `FLY-BASE-001`.

## Status

Scaffolding initialized.

## Phase 1 priorities

1. Pin the official MaleCNS dataset/version
2. Build a reproducible ingestion pipeline
3. Validate the connectome structure
4. Implement a conservative reference LIF model
5. Reproduce at least one published reference experiment
6. Establish neural, behavioural, and compute baselines
7. Freeze `FLY-BASE-001`

## Repository structure

```text
fly-cognition/
├── README.md
├── LICENSE
├── CITATION.cff
├── .gitignore
├── pyproject.toml
├── .python-version
├── docs/
├── data/
├── fly/
├── experiments/
├── benchmarks/
├── validation/
├── configs/
├── results/
└── tests/
```

## Quick start

```bash
uv venv
uv sync
pytest
```

## Scientific rule

Never modify the system before understanding what the unmodified system does.
