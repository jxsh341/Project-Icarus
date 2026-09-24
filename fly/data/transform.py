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
    synapse_records = _deduplicate_synapse_records(synapse_records)
    return neuron_records, synapse_records


def _deduplicate_synapse_records(synapses: list[Synapse]) -> list[Synapse]:
    """Collapse fetch-artifact duplicate rows before canonical use.

    Depth-2 (k-hop) snapshots re-fetch seed-incident edges in later rounds:
    the same (source, target, roi, weight) row can arrive once per round
    (e.g. as seed-incoming in round 1 and partner-outgoing in round 2).
    Verified on run-006: 383,868 of 1,948,344 raw rows are exact
    duplicates with zero weight mismatches. Summing those would corrupt
    the canonical matrix, so identical rows collapse to one.

    Rows sharing (source, target, roi) but with DIFFERENT weights are not
    fetch artifacts - they are treated as data and summed (conservative),
    matching the documented duplicate-handling decision for genuinely
    distinct rows (per-ROI splits remain separate Synapse records).
    """
    exact: dict[tuple[int, int, str | None, float], Synapse] = {}
    weight_conflicts: dict[tuple[int, int, str | None], float] = {}
    conflict_rows: dict[tuple[int, int, str | None], int] = {}
    order: list[tuple[int, int, str | None]] = []

    for syn in synapses:
        key_exact = (syn.source, syn.target, syn.roi, syn.weight_or_count)
        key_pair = (syn.source, syn.target, syn.roi)
        if key_exact in exact:
            continue  # identical row already recorded: fetch artifact
        if key_pair in weight_conflicts:
            # same (source, target, roi) as another row, different weight
            weight_conflicts[key_pair] += syn.weight_or_count
            conflict_rows[key_pair] += 1
            continue
        exact[key_exact] = syn
        if key_pair not in weight_conflicts:
            # first occurrence of this pair: remember for conflict merging
            weight_conflicts[key_pair] = syn.weight_or_count
            conflict_rows[key_pair] = 1
            order.append(key_pair)

    out: list[Synapse] = []
    emitted: set[tuple[int, int, str | None]] = set()
    for syn in synapses:
        key_pair = (syn.source, syn.target, syn.roi)
        if key_pair in emitted:
            continue
        emitted.add(key_pair)
        if conflict_rows[key_pair] > 1:
            out.append(
                Synapse(
                    source=syn.source,
                    target=syn.target,
                    weight_or_count=weight_conflicts[key_pair],
                    roi=syn.roi,
                )
            )
        else:
            out.append(syn)
    return out



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
