"""Tests for a neuPrint-backed streaming loader."""

import json
from pathlib import Path

import pytest

from fly.data.loader import (
    NeuPrintSnapshotConfig,
    NeuPrintStreamingLoader,
    ensure_neuprint_token,
)


class FakeNeuPrintClient:
    def fetch_neurons(self, body_ids: list[int]) -> list[dict]:
        return [
            {"bodyId": body_id, "type": f"type-{body_id}", "instance": f"inst-{body_id}"}
            for body_id in body_ids
        ]

    def fetch_adjacencies(self, body_ids: list[int], direction: str = "outgoing") -> list[dict]:
        if direction == "incoming":
            return [
                {"bodyId_pre": body_id - 1, "bodyId_post": body_id, "weight": 2, "roi": "GNG"}
                for body_id in body_ids
            ]
        return [
            {"bodyId_pre": body_id, "bodyId_post": body_id + 1, "weight": 2, "roi": "GNG"}
            for body_id in body_ids
        ]


def _config(tmp_path: Path, batch_size: int = 2) -> NeuPrintSnapshotConfig:
    return NeuPrintSnapshotConfig(
        dataset="male-cns:v1.0",
        batch_size=batch_size,
        snapshot_dir=tmp_path,
        server="https://neuprint.janelia.org",
    )


def test_snapshot_path_encodes_batch_bounds(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path, batch_size=500), client=FakeNeuPrintClient())

    path = loader.snapshot_path(kind="neurons", batch_index=2)

    assert path == tmp_path / "neurons_batch_0002.json"


def test_chunk_sequence_yields_expected_ranges(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path, batch_size=3), client=FakeNeuPrintClient())

    chunks = list(loader.chunk_sequence([10, 11, 12, 13, 14, 15, 16]))

    assert chunks == [
        [10, 11, 12],
        [13, 14, 15],
        [16],
    ]


def test_write_snapshot_batch_persists_records(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    path = loader.write_snapshot_batch(
        kind="neurons",
        batch_index=0,
        records=[{"bodyId": 1}, {"bodyId": 2}],
    )

    assert path.exists()
    assert path.read_text(encoding="utf-8") == '[\n  {\n    "bodyId": 1\n  },\n  {\n    "bodyId": 2\n  }\n]\n'


def test_snapshot_neurons_batches_and_writes_metadata(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    written = loader.snapshot_neurons([101, 102, 103])

    assert [path.name for path in written] == [
        "neurons_batch_0000.json",
        "neurons_batch_0001.json",
    ]
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["dataset"] == "male-cns:v1.0"
    assert metadata["server"] == "https://neuprint.janelia.org"
    assert metadata["neuron_batches"] == 2
    assert metadata["body_ids"] == [101, 102, 103]


def test_snapshot_adjacencies_outgoing_writes_directional_files(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    written = loader.snapshot_adjacencies([201, 202, 203])

    assert [path.name for path in written] == [
        "adjacencies_outgoing_batch_0000.json",
        "adjacencies_outgoing_batch_0001.json",
    ]
    first_batch = json.loads(written[0].read_text(encoding="utf-8"))
    assert first_batch[0]["bodyId_pre"] == 201
    assert first_batch[0]["bodyId_post"] == 202
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["adjacency_batches_outgoing"] == 2


def test_snapshot_adjacencies_incoming_targets_seeds(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    written = loader.snapshot_adjacencies([201, 202, 203], direction="incoming")

    assert [path.name for path in written] == [
        "adjacencies_incoming_batch_0000.json",
        "adjacencies_incoming_batch_0001.json",
    ]
    first_batch = json.loads(written[0].read_text(encoding="utf-8"))
    assert first_batch[0]["bodyId_pre"] == 200
    assert first_batch[0]["bodyId_post"] == 201
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["adjacency_batches_incoming"] == 2


def test_snapshot_adjacencies_rejects_unknown_direction(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    with pytest.raises(ValueError, match="unknown direction"):
        loader.snapshot_adjacencies([1], direction="sideways")


def test_snapshot_closed_subgraph_fetches_both_directions(tmp_path: Path) -> None:
    loader = NeuPrintStreamingLoader(_config(tmp_path), client=FakeNeuPrintClient())

    result = loader.snapshot_closed_subgraph([10, 20])

    adjacency_files = sorted(path.name for path in tmp_path.glob("adjacencies_*"))
    assert adjacency_files == [
        "adjacencies_incoming_batch_0000.json",
        "adjacencies_outgoing_batch_0000.json",
    ]
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert sorted(metadata["expanded_body_ids"]) == [9, 10, 11, 19, 20, 21]
    assert metadata["closed_subgraph"] is True
    assert metadata["seed_body_ids"] == [10, 20]
    assert metadata["expanded_neuron_batches"] == 3
    assert metadata["seed_adjacency_batches_outgoing"] == 1
    assert metadata["seed_adjacency_batches_incoming"] == 1
    assert result["neuron_snapshot_count"] == 3
    assert result["adjacency_snapshot_count_outgoing"] == 1
    assert result["adjacency_snapshot_count_incoming"] == 1


def test_ensure_neuprint_token_prefers_explicit_value() -> None:
    assert ensure_neuprint_token(explicit_token="abc123") == "abc123"
