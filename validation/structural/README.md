# Snapshot Validation

`run-002` is the first valid live neuPrint snapshot run.
`run-004` is the first structurally closed local neuPrint subgraph snapshot.

Expected validation outputs per run:
- `metadata.json`
- `neurons_batch_*.json`
- `adjacencies_batch_*.json`
- `validation_summary.json`
- `manifest.json`

The current validation summary reports:
- neuron count
- edge count
- missing cell type count
- missing instance count
- missing region count
- dangling source count
- dangling target count
- self connection count
- duplicate edge count

Closed-subgraph validation must be computed across the whole run directory, not a single neuron batch. Use `summarize_snapshot_directory_validation()` for closed-subgraph runs; `summarize_snapshot_validation()` remains for single-batch views.

Canonical exploratory subgraph artifact: `data/processed/neuprint_snapshots/run-004` (DNge104 seed pair `12781, 556329`, 2939 neurons, 3325 edges, zero dangling endpoints).
