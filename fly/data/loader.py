"""Minimal loader interfaces and snapshot helpers for Phase 1 scaffolding."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from fly.neurons.models import NeuronRecord
from fly.synapses.models import Synapse


class ConnectomeLoader:
    """Interface for converting official source tables into canonical records."""

    def load_neurons(self) -> Iterable[NeuronRecord]:
        raise NotImplementedError

    def load_synapses(self) -> Iterable[Synapse]:
        raise NotImplementedError


class NeuPrintClientProtocol(Protocol):
    def fetch_neurons(self, body_ids: list[int]) -> list[dict[str, Any]]: ...

    def fetch_adjacencies(
        self, body_ids: list[int], direction: str = "outgoing"
    ) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class NeuPrintSnapshotConfig:
    dataset: str
    batch_size: int
    snapshot_dir: Path
    server: str


def ensure_neuprint_token(explicit_token: str | None = None) -> str:
    if explicit_token:
        return explicit_token
    env_token = os.environ.get("NEUPRINT_TOKEN", "").strip()
    if env_token:
        return env_token
    raise RuntimeError("Missing neuPrint token: set NEUPRINT_TOKEN or pass an explicit token.")


class NeuPrintStreamingLoader:
    """Batch-oriented helper for snapshotting neuPrint query results locally."""

    def __init__(self, config: NeuPrintSnapshotConfig, client: NeuPrintClientProtocol) -> None:
        self.config = config
        self.client = client

    def snapshot_path(self, kind: str, batch_index: int) -> Path:
        self.config.snapshot_dir.mkdir(parents=True, exist_ok=True)
        return self.config.snapshot_dir / f"{kind}_batch_{batch_index:04d}.json"

    def metadata_path(self) -> Path:
        self.config.snapshot_dir.mkdir(parents=True, exist_ok=True)
        return self.config.snapshot_dir / "metadata.json"

    def chunk_sequence(self, values: Sequence[int]) -> Iterable[list[int]]:
        for start in range(0, len(values), self.config.batch_size):
            yield list(values[start : start + self.config.batch_size])

    def write_snapshot_batch(
        self,
        *,
        kind: str,
        batch_index: int,
        records: list[dict[str, Any]],
    ) -> Path:
        path = self.snapshot_path(kind=kind, batch_index=batch_index)
        path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def write_metadata(self, payload: dict[str, Any]) -> Path:
        path = self.metadata_path()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _merge_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = payload
        existing = self.metadata_path()
        if existing.exists():
            current = json.loads(existing.read_text(encoding="utf-8"))
            current.update(payload)
            metadata = current
        self.write_metadata(metadata)
        return metadata

    def snapshot_neurons(self, body_ids: Sequence[int]) -> list[Path]:
        written: list[Path] = []
        for batch_index, batch in enumerate(self.chunk_sequence(list(body_ids))):
            records = self.client.fetch_neurons(batch)
            written.append(
                self.write_snapshot_batch(kind="neurons", batch_index=batch_index, records=records)
            )
        self._merge_metadata(
            {
                "dataset": self.config.dataset,
                "server": self.config.server,
                "batch_size": self.config.batch_size,
                "body_ids": list(body_ids),
                "neuron_batches": len(written),
            }
        )
        return written

    def snapshot_adjacencies(
        self, body_ids: Sequence[int], direction: str = "outgoing"
    ) -> list[Path]:
        if direction not in {"outgoing", "incoming"}:
            raise ValueError(f"unknown direction: {direction!r}")
        written: list[Path] = []
        for batch_index, batch in enumerate(self.chunk_sequence(list(body_ids))):
            records = self.client.fetch_adjacencies(batch, direction=direction)
            written.append(
                self.write_snapshot_batch(
                    kind=f"adjacencies_{direction}",
                    batch_index=batch_index,
                    records=records,
                )
            )
        self._merge_metadata(
            {
                "dataset": self.config.dataset,
                "server": self.config.server,
                "batch_size": self.config.batch_size,
                "body_ids": list(body_ids),
                f"adjacency_batches_{direction}": len(written),
            }
        )
        return written

    def snapshot_closed_subgraph(self, seed_body_ids: Sequence[int]) -> dict[str, int]:
        outgoing_paths = self.snapshot_adjacencies(seed_body_ids, direction="outgoing")
        incoming_paths = self.snapshot_adjacencies(seed_body_ids, direction="incoming")

        expanded_body_ids: set[int] = set(seed_body_ids)
        for path in outgoing_paths + incoming_paths:
            rows = json.loads(path.read_text(encoding="utf-8"))
            for row in rows:
                expanded_body_ids.add(int(row["bodyId_pre"]))
                expanded_body_ids.add(int(row["bodyId_post"]))

        neuron_paths = self.snapshot_neurons(sorted(expanded_body_ids))
        self._merge_metadata(
            {
                "closed_subgraph": True,
                "seed_body_ids": list(seed_body_ids),
                "expanded_body_ids": sorted(expanded_body_ids),
                "expanded_neuron_batches": len(neuron_paths),
                "seed_adjacency_batches_outgoing": len(outgoing_paths),
                "seed_adjacency_batches_incoming": len(incoming_paths),
            }
        )
        return {
            "neuron_snapshot_count": len(neuron_paths),
            "adjacency_snapshot_count_outgoing": len(outgoing_paths),
            "adjacency_snapshot_count_incoming": len(incoming_paths),
            "expanded_body_id_count": len(expanded_body_ids),
        }
