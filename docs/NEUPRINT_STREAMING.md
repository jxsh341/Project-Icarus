# neuPrint Streaming Loader

## Purpose

Use neuPrint for batched remote access during exploration, then materialize exact query results into immutable local snapshot files for `FLY-BASE-001`.

## Strategy

1. Query the `male-cns:v1.0` dataset in batches.
2. Persist each batch to `data/processed/neuprint_snapshots/`.
3. Record dataset id, query parameters, batch size, fetch date, and token-independent metadata.
4. Treat the resulting snapshot set as the frozen local input for downstream validation.

## CLI

```bash
uv run python scripts/neuprint_snapshot.py \
  --dataset male-cns:v1.0 \
  --snapshot-dir data/processed/neuprint_snapshots/run-001 \
  --body-ids 12781,556329 \
  --mode both
```

Closed-subgraph mode:

```bash
uv run python scripts/neuprint_snapshot.py \
  --dataset male-cns:v1.0 \
  --snapshot-dir data/processed/neuprint_snapshots/run-004 \
  --body-ids 12781,556329 \
  --mode closed-subgraph \
  --token-file .neuprint_token
```

Set `NEUPRINT_TOKEN` in the environment or pass `--token` or `--token-file`.

## Run status

- `run-002`: first valid live snapshot (neurons + adjacencies, seed pair only)
- `run-003`: intermediate diagnostic run; superseded
- `run-004`: first closed subgraph, outgoing edges only; superseded by `run-005`
- `run-005`: canonical exploratory closed subgraph, **bidirectional** (4293 neurons,
  7832 per-ROI edge rows, 6789 aggregated edges, zero dangling endpoints)


## Why this exists

This lets us avoid downloading all artifacts up front while still converging to a reproducible, local baseline input.
