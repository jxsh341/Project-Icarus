"""Transform neuPrint snapshot rows into canonical in-project records."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from fly.neurons.models import NeuronRecord
from fly.synapses.models import Synapse


def _read_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_neuron_records_from_snapshot(path: Path) -> list[NeuronRecord]:
    rows = _read_json(path)
    return [
        NeuronRecord(
            root_id=int(row["bodyId"]),
            cell_type=row.get("type"),
            instance=row.get("instance"),
            region=row.get("region"),
        )
        for row in rows
    ]


def load_synapses_from_snapshot(path: Path) -> list[Synapse]:
    rows = _read_json(path)
    return [
        Synapse(
            source=int(row["bodyId_pre"]),
            target=int(row["bodyId_post"]),
            weight_or_count=float(row["weight"]),
            roi=row.get("roi"),
        )
        for row in rows
    ]


def load_snapshot_directory(path: Path) -> tuple[list[NeuronRecord], list[Synapse]]:
    neuron_records: list[NeuronRecord] = []
    synapse_records: list[Synapse] = []
    for neuron_path in sorted(path.glob("neurons_batch_*.json")):
        neuron_records.extend(load_neuron_records_from_snapshot(neuron_path))
    for synapse_path in sorted(path.glob("adjacencies*_batch_*.json")):
        synapse_records.extend(load_synapses_from_snapshot(synapse_path))
    return neuron_records, synapse_records



def _summarize(neurons: list[NeuronRecord], synapses: list[Synapse]) -> dict[str, int]:
    neuron_ids = {neuron.root_id for neuron in neurons}
    edge_pairs = [(synapse.source, synapse.target) for synapse in synapses]
    pair_counts = Counter(edge_pairs)
    return {
        "neuron_count": len(neurons),
        "edge_count": len(synapses),
        "missing_cell_type_count": sum(1 for neuron in neurons if not neuron.cell_type),
        "missing_instance_count": sum(1 for neuron in neurons if not neuron.instance),
        "missing_region_count": sum(1 for neuron in neurons if not neuron.region),
        "dangling_source_count": sum(1 for synapse in synapses if synapse.source not in neuron_ids),
        "dangling_target_count": sum(1 for synapse in synapses if synapse.target not in neuron_ids),
        "self_connection_count": sum(1 for synapse in synapses if synapse.source == synapse.target),
        "duplicate_edge_count": sum(count - 1 for count in pair_counts.values() if count > 1),
    }


def summarize_snapshot_validation(neurons_path: Path, synapses_path: Path) -> dict[str, int]:
    neurons = load_neuron_records_from_snapshot(neurons_path)
    synapses = load_synapses_from_snapshot(synapses_path)
    return _summarize(neurons, synapses)


def summarize_snapshot_directory_validation(path: Path) -> dict[str, int]:
    neurons, synapses = load_snapshot_directory(path)
    return _summarize(neurons, synapses)
