# Model Specification

## Phase 1 model

- Model family: leaky integrate-and-fire (LIF)
- Priority: correctness and traceability over speed
- Parameter source: published paper and reference implementation

## To document before freeze

- equations
- timestep
- refractory handling
- conductance or current update rules
- synaptic weight/count semantics
- stimulation protocol
- output measurement definitions

## Canonical graph: duplicate handling
the same neuron pair can appear multiple times (one row per neuropil compartment
where they connect). This is not a data error; it is per-ROI breakdown.

Decision for `FLY-BASE-001`:

- **Canonical sparse connectivity matrix:** per-ROI rows between the same neuron
  pair are **summed** into a single edge weight. The matrix is the
  connectome-level wiring graph used for simulation.
- **Snapshot layer:** per-ROI detail is preserved as-is on `Synapse.roi` so the
  breakdown can be recovered or re-aggregated later without re-querying.
- **Validation reporting:** `duplicate_edge_count` in the validation summary
  reports the number of extra per-ROI rows (rows beyond the first for each
  pair); `canonical_graph.aggregated_edge_count` reports the deduplicated edge
  count after summation.

Evidence from `run-004`: 3325 per-ROI adjacency rows → 277 extra per-ROI rows →
3048 aggregated unique edges; summed total weight 19608.0.

