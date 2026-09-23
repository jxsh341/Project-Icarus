"""Tests for transforming neuPrint snapshot rows into canonical records."""

import json
from pathlib import Path

from fly.data.transform import (
    load_neuron_records_from_snapshot,
    load_synapses_from_snapshot,
    load_snapshot_directory,
    summarize_snapshot_directory_validation,
    summarize_snapshot_validation,
)


def test_load_neuron_records_from_snapshot_maps_basic_fields(tmp_path: Path) -> None:
    snapshot = tmp_path / "neurons.json"
    snapshot.write_text(
        json.dumps(
            [
                {
                    "bodyId": 12781,
                    "type": "DNge104",
                    "instance": "DNge104_R",
                    "somaLocation": [1, 2, 3],
                }
            ]
        ),
        encoding="utf-8",
    )

    neurons = load_neuron_records_from_snapshot(snapshot)

    assert len(neurons) == 1
    assert neurons[0].root_id == 12781
    assert neurons[0].cell_type == "DNge104"
    assert neurons[0].instance == "DNge104_R"
    assert neurons[0].region is None


def test_load_synapses_from_snapshot_maps_edge_fields(tmp_path: Path) -> None:
    snapshot = tmp_path / "adj.json"
    snapshot.write_text(
        json.dumps(
            [
                {
                    "bodyId_pre": 12781,
                    "bodyId_post": 10141,
                    "weight": 28,
                    "roi": "GNG",
                }
            ]
        ),
        encoding="utf-8",
    )

    synapses = load_synapses_from_snapshot(snapshot)

    assert len(synapses) == 1
    assert synapses[0].source == 12781
    assert synapses[0].target == 10141
    assert synapses[0].weight_or_count == 28


def test_load_snapshot_directory_aggregates_batches(tmp_path: Path) -> None:
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 1, "type": "A", "instance": "A_R"}]),
        encoding="utf-8",
    )
    (tmp_path / "neurons_batch_0001.json").write_text(
        json.dumps([{"bodyId": 2, "type": "B", "instance": "B_L"}]),
        encoding="utf-8",
    )
    (tmp_path / "adjacencies_outgoing_batch_0000.json").write_text(
        json.dumps([{"bodyId_pre": 1, "bodyId_post": 2, "weight": 4, "roi": "GNG"}]),
        encoding="utf-8",
    )
    (tmp_path / "adjacencies_incoming_batch_0000.json").write_text(
        json.dumps([{"bodyId_pre": 3, "bodyId_post": 1, "weight": 2, "roi": "SAD"}]),
        encoding="utf-8",
    )

    neurons, synapses = load_snapshot_directory(tmp_path)

    assert [neuron.root_id for neuron in neurons] == [1, 2]
    assert len(synapses) == 2
    assert {synapse.source for synapse in synapses} == {1, 3}


def test_summarize_snapshot_validation_counts_records_and_missing_fields(tmp_path: Path) -> None:
    neurons_path = tmp_path / "neurons.json"
    adj_path = tmp_path / "adj.json"
    neurons_path.write_text(
        json.dumps(
            [
                {"bodyId": 1, "type": "A", "instance": "A_R"},
                {"bodyId": 2, "type": None, "instance": "B_L"},
            ]
        ),
        encoding="utf-8",
    )
    adj_path.write_text(
        json.dumps(
            [
                {"bodyId_pre": 1, "bodyId_post": 2, "weight": 4, "roi": "GNG"},
                {"bodyId_pre": 2, "bodyId_post": 3, "weight": 1, "roi": "GNG"},
                {"bodyId_pre": 2, "bodyId_post": 2, "weight": 1, "roi": "GNG"},
            ]
        ),
        encoding="utf-8",
    )

    report = summarize_snapshot_validation(neurons_path, adj_path)

    assert report["neuron_count"] == 2
    assert report["edge_count"] == 3
    assert report["missing_cell_type_count"] == 1
    assert report["missing_instance_count"] == 0
    assert report["missing_region_count"] == 2
    assert report["dangling_source_count"] == 0
    assert report["dangling_target_count"] == 1
    assert report["self_connection_count"] == 1
    assert report["duplicate_edge_count"] == 0


def test_summarize_snapshot_directory_validation_uses_all_batches(tmp_path: Path) -> None:
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 1, "type": "A", "instance": "A_R"}]),
        encoding="utf-8",
    )
    (tmp_path / "neurons_batch_0001.json").write_text(
        json.dumps([{"bodyId": 2, "type": "B", "instance": "B_L"}]),
        encoding="utf-8",
    )
    (tmp_path / "adjacencies_batch_0000.json").write_text(
        json.dumps([{"bodyId_pre": 1, "bodyId_post": 2, "weight": 4, "roi": "GNG"}]),
        encoding="utf-8",
    )

    report = summarize_snapshot_directory_validation(tmp_path)

    assert report["neuron_count"] == 2
    assert report["edge_count"] == 1
    assert report["dangling_source_count"] == 0
    assert report["dangling_target_count"] == 0
