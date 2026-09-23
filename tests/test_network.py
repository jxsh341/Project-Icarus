"""Tests for building the sparse connectivity matrix from canonical records."""

import json
from pathlib import Path

from fly.network.graph import build_sparse_connectivity_matrix
from fly.neurons.models import NeuronRecord
from fly.synapses.models import Synapse


def _neurons() -> list[NeuronRecord]:
    return [
        NeuronRecord(root_id=1, cell_type="A"),
        NeuronRecord(root_id=2, cell_type="B"),
        NeuronRecord(root_id=3, cell_type="C"),
    ]


def test_build_sparse_connectivity_matrix_sums_per_pair() -> None:
    synapses = [
        Synapse(source=1, target=2, weight_or_count=4, roi="GNG"),
        Synapse(source=1, target=2, weight_or_count=2, roi="SAD"),
        Synapse(source=2, target=3, weight_or_count=1, roi=None),
    ]

    matrix, node_ids = build_sparse_connectivity_matrix(_neurons(), synapses)

    assert node_ids == [1, 2, 3]
    assert matrix.shape == (3, 3)
    assert matrix.format == "csr"
    assert matrix[0, 1] == 6.0
    assert matrix[1, 2] == 1.0
    assert matrix[0, 0] == 0.0


def test_build_sparse_connectivity_matrix_ignores_dangling_edges() -> None:
    synapses = [
        Synapse(source=1, target=99, weight_or_count=5, roi="GNG"),
    ]

    matrix, node_ids = build_sparse_connectivity_matrix(_neurons(), synapses)

    assert node_ids == [1, 2, 3]
    assert matrix.nnz == 0


def test_build_sparse_connectivity_matrix_from_run(tmp_path: Path) -> None:
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 1, "type": "A"}, {"bodyId": 2, "type": "B"}]),
        encoding="utf-8",
    )
    (tmp_path / "adjacencies_batch_0000.json").write_text(
        json.dumps(
            [
                {"bodyId_pre": 1, "bodyId_post": 2, "weight": 3, "roi": "GNG"},
                {"bodyId_pre": 1, "bodyId_post": 2, "weight": 2, "roi": "SAD"},
            ]
        ),
        encoding="utf-8",
    )

    from fly.data.transform import load_snapshot_directory

    neurons, synapses = load_snapshot_directory(tmp_path)
    matrix, node_ids = build_sparse_connectivity_matrix(neurons, synapses)

    assert node_ids == [1, 2]
    assert matrix[0, 1] == 5.0
