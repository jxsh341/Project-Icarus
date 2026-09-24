"""Tests for duplicate handling in the canonical transform.

run-006 (depth-2 closure) re-fetches seed-incident edges in round 2: a
partner->seed edge returned by the partner's outgoing query also appears
in the seed's incoming query. 383,868 of its 1,948,344 raw rows are exact
duplicate (pre, post, roi, weight) keys. Summing duplicates would corrupt
the canonical matrix; the transform must deduplicate identical rows
before per-ROI summation, while still SUMMING genuinely distinct rows
(per-ROI splits, the documented duplicate-handling decision).
"""

import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.data.transform import load_snapshot_directory


def _write_adj(tmp_path: Path, direction: str, rows: list[dict]) -> None:
    (tmp_path / f"adjacencies_{direction}_batch_0000.json").write_text(
        json.dumps(rows), encoding="utf-8"
    )


def test_identical_duplicate_rows_are_deduplicated(tmp_path: Path) -> None:
    # the same edge row fetched twice (round-1 incoming + round-2 outgoing)
    row = {"bodyId_pre": 10, "bodyId_post": 20, "roi": "GNG", "weight": 5}
    _write_adj(tmp_path, "outgoing", [row, dict(row)])
    _write_adj(tmp_path, "incoming", [row])
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 10, "type": "A", "instance": "a"},
                    {"bodyId": 20, "type": "B", "instance": "b"}]),
        encoding="utf-8",
    )

    _, synapses = load_snapshot_directory(tmp_path)

    # three identical copies -> ONE synapse of weight 5, not 15
    assert len(synapses) == 1
    assert synapses[0].weight_or_count == 5


def test_distinct_roi_rows_still_summed(tmp_path: Path) -> None:
    # the documented duplicate-handling decision: per-ROI rows for the same
    # pair are distinct data and MUST be summed
    _write_adj(
        tmp_path, "out",
        [
            {"bodyId_pre": 10, "bodyId_post": 20, "roi": "GNG", "weight": 5},
            {"bodyId_pre": 10, "bodyId_post": 20, "roi": "SMP", "weight": 3},
        ],
    )
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 10, "type": "A", "instance": "a"},
                    {"bodyId": 20, "type": "B", "instance": "b"}]),
        encoding="utf-8",
    )

    _, synapses = load_snapshot_directory(tmp_path)

    # two ROIs -> two synapse records preserved (per-ROI provenance kept)
    assert len(synapses) == 2
    assert {s.roi for s in synapses} == {"GNG", "SMP"}


def test_duplicate_key_with_conflicting_weight_still_sums(tmp_path: Path) -> None:
    # if the same (pre, post, roi) ever appears with DIFFERENT weights,
    # that is not a fetch artifact - treat as data and sum (conservative).
    _write_adj(
        tmp_path, "out",
        [
            {"bodyId_pre": 10, "bodyId_post": 20, "roi": "GNG", "weight": 5},
            {"bodyId_pre": 10, "bodyId_post": 20, "roi": "GNG", "weight": 2},
        ],
    )
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 10, "type": "A", "instance": "a"},
                    {"bodyId": 20, "type": "B", "instance": "b"}]),
        encoding="utf-8",
    )

    _, synapses = load_snapshot_directory(tmp_path)

    # conflicting weights -> sum (data, not artifact)
    assert len(synapses) == 1
    assert synapses[0].weight_or_count == 7


def test_dedup_across_directional_files(tmp_path: Path) -> None:
    # row fetched as seed-incoming (round 1) and again as partner-outgoing
    # (round 2): same key, different files -> one synapse
    row = {"bodyId_pre": 30, "bodyId_post": 10, "roi": "GNG", "weight": 4}
    _write_adj(tmp_path, "incoming", [row])
    _write_adj(tmp_path, "outgoing", [dict(row)])
    (tmp_path / "neurons_batch_0000.json").write_text(
        json.dumps([{"bodyId": 10, "type": "A", "instance": "a"},
                    {"bodyId": 30, "type": "C", "instance": "c"}]),
        encoding="utf-8",
    )

    _, synapses = load_snapshot_directory(tmp_path)

    assert len(synapses) == 1
    assert synapses[0].weight_or_count == 4
