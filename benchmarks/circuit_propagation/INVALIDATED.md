# benchmarks/circuit_propagation — INVALIDATED 2026-09-23

## Status

**The circuit-propagation result in this directory is INVALID as a biological claim.**

Recorded finding: seeds (2) -> first-order 458 spikers -> second-order 0 spikers.

## Why invalidated

The run-005 subgraph was built with 1-hop closure: it contains ONLY edges
incident to the seed pair (verified: 100% of 6789 edges touch a seed;
zero second-order candidate neurons exist in the node set). "Propagation
stops at hop 2" is therefore a **structural zero** — a construction
artifact of the snapshot, not a measurement of the network.

The same truncation is present in the WP6 head-to-head arms (both ran on
run-005), so their per-neuron agreement is unaffected (same inputs), but
any multi-hop propagation claim from run-005 is void.

## Resolution

- `fly/data/loader.py` `snapshot_closed_subgraph` now supports k-hop
  closure (`depth` parameter, default 1 = legacy behavior).
- A depth-2 snapshot (run-006) will be fetched and the propagation
  benchmark re-run on it.
- Spontaneous and stimulus-response benchmarks remain valid: spontaneous
  activity does not depend on second-order edges (network is silent
  regardless), and stimulus-response measures seeds + first-order only,
  both fully present in run-005.

## Kept for the record

The original result files are preserved unmodified as the record of the
invalid measurement and its diagnosis.
