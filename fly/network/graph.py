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


INHIBITORY_NEUROTRANSMITTERS = {"gaba", "glutamate"}


def nt_sign(nt: str | None) -> int:
    """Sign of a presynaptic neuron's outgoing synapses.

    The Shiu et al. reference weights every edge as
        w = sign * synapse_count * w_syn
    with sign strictly per presynaptic neuron (verified empirically: zero
    mixed-sign neurons among 138,005 in their Connectivity_783 table;
    32.5M excitatory / 22.0M inhibitory synapses). Standard adult
    Drosophila convention (Eckstein et al. NT predictions): acetylcholine
    is excitatory; GABA and glutamate are inhibitory. Unknown/unclear/
    monoaminergic neurons default to +1 (excitatory) and are recorded in
    the build report so the default is auditable.
    """
    if nt is None:
        return 1
    return -1 if str(nt).strip().lower() in INHIBITORY_NEUROTRANSMITTERS else 1


def build_signed_connectivity_matrix(
    neurons: list[dict],
    synapses: list[dict],
    return_report: bool = False,
):
    """Signed sparse adjacency matrix: w = nt_sign(source) * synapse_count.

    neurons: dicts with keys bodyId, nt (optional). synapses: dicts with
    keys source, target, weight_or_count, roi. Sign is applied per edge
    from the presynaptic neuron's neurotransmitter BEFORE summation, so
    per-ROI rows of an inhibitory pair sum to a negative weight.
    """
    node_ids = sorted({int(n["bodyId"]) for n in neurons})
    index_of = {root_id: i for i, root_id in enumerate(node_ids)}
    nt_of = {int(n["bodyId"]): n.get("nt") for n in neurons}

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for synapse in synapses:
        source = int(synapse["source"])
        target = int(synapse["target"])
        source_index = index_of.get(source)
        target_index = index_of.get(target)
        if source_index is None or target_index is None:
            continue
        rows.append(source_index)
        cols.append(target_index)
        data.append(nt_sign(nt_of.get(source)) * float(synapse["weight_or_count"]))

    matrix = sparse.csr_matrix(
        (np.asarray(data, dtype=float), (rows, cols)),
        shape=(len(node_ids), len(node_ids)),
    )
    matrix.sum_duplicates()
    matrix.sort_indices()

    if return_report:
        unknown = sorted(
            int(nid) for nid in node_ids
            if nt_of.get(nid) in (None, "unclear", "")
            or str(nt_of.get(nid)).strip().lower() not in {"acetylcholine", "gaba", "glutamate"}
        )
        report = {"unknown_nt_neurons": unknown}
        return matrix, node_ids, report
    return matrix, node_ids
    matrix.sum_duplicates()
    matrix.sort_indices()
    return matrix, node_ids
