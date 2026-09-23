"""Sparse connectivity matrix construction from canonical records."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from fly.neurons.models import NeuronRecord
from fly.synapses.models import Synapse


def build_sparse_connectivity_matrix(
    neurons: list[NeuronRecord],
    synapses: list[Synapse],
) -> tuple[sparse.csr_matrix, list[int]]:
    """Build a weighted sparse adjacency matrix (rows=source, cols=target).

    Multiple synapse rows between the same neuron pair (e.g. neuPrint emits
    one row per ROI) are SUMMED into a single edge weight. This duplicate-
    handling decision is documented in docs/MODEL_SPEC.md.
    """
    node_ids = sorted({neuron.root_id for neuron in neurons})
    index_of = {root_id: i for i, root_id in enumerate(node_ids)}

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for synapse in synapses:
        source_index = index_of.get(synapse.source)
        target_index = index_of.get(synapse.target)
        if source_index is None or target_index is None:
            continue
        rows.append(source_index)
        cols.append(target_index)
        data.append(synapse.weight_or_count)

    matrix = sparse.csr_matrix(
        (np.asarray(data, dtype=float), (rows, cols)),
        shape=(len(node_ids), len(node_ids)),
    )
    matrix.sum_duplicates()
    matrix.sort_indices()
    return matrix, node_ids
