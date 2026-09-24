"""Tests for k-hop closed-subgraph snapshots (loader expansion depth).

run-005 (1-hop closure) contains ONLY edges incident to the seed pair:
100% of its 6789 edges touch a seed, so second-order propagation is a
structural zero, not a measurement. The 2-hop closure must fetch
adjacencies of ALL first-order partners so partner-to-partner edges exist.
"""

import json
from pathlib import Path

import pytest

from fly.data.loader import NeuPrintSnapshotConfig, NeuPrintStreamingLoader


class _FakeClient:
    """Records adjacency fetches; serves canned edge rows for any query."""

    def __init__(self, edge_rows):
        self.edge_rows = edge_rows
        self.adjacency_queries: list[tuple[tuple, str]] = []

    def fetch_adjacencies(self, body_ids, direction="outgoing"):
        self.adjacency_queries.append((tuple(body_ids), direction))
        # serve any edge whose queried endpoint matches
        rows = []
        for r in self.edge_rows:
            pre, post = r["bodyId_pre"], r["bodyId_post"]
            if direction == "outgoing" and pre in body_ids:
                rows.append(dict(r))
            elif direction == "incoming" and post in body_ids:
                rows.append(dict(r))
        return rows

    def fetch_neurons(self, body_ids):
        return [
            {"bodyId": b, "type": f"t{b}", "instance": f"i{b}"} for b in body_ids
        ]


def _loader(tmp_path: Path, edge_rows) -> tuple[NeuPrintStreamingLoader, _FakeClient]:
    config = NeuPrintSnapshotConfig(
        dataset="d", batch_size=500, snapshot_dir=tmp_path,
        server="https://example.invalid",
    )
    fake = _FakeClient(edge_rows)
    return NeuPrintStreamingLoader(config, fake), fake


def _snapshot_nodes(tmp_path: Path) -> list[int]:
    return sorted(
        {r["bodyId"] for p in sorted(tmp_path.glob("neurons_batch_*.json"))
         for r in json.loads(p.read_text(encoding="utf-8"))}
    )


def _snapshot_edges(tmp_path: Path) -> list[tuple[int, int]]:
    edges = set()
    for p in sorted(tmp_path.glob("adjacencies_*_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            edges.add((r["bodyId_pre"], r["bodyId_post"]))
    return sorted(edges)


def test_two_hop_closure_includes_partner_to_partner_edges(tmp_path: Path) -> None:
    # chain 1 -> 10 -> 100 and 1 -> 20 -> 200
    edge_rows = [
        {"bodyId_pre": 1, "bodyId_post": 10, "roi": "R", "weight": 5},
        {"bodyId_pre": 10, "bodyId_post": 100, "roi": "R", "weight": 5},
        {"bodyId_pre": 1, "bodyId_post": 20, "roi": "R", "weight": 5},
        {"bodyId_pre": 20, "bodyId_post": 200, "roi": "R", "weight": 5},
    ]
    loader, fake = _loader(tmp_path, edge_rows)

    out = loader.snapshot_closed_subgraph([1], depth=2)

    assert _snapshot_nodes(tmp_path) == [1, 10, 20, 100, 200]
    # the crucial property: partner->partner and partner->second-order edges exist
    edges = _snapshot_edges(tmp_path)
    assert (10, 100) in edges
    assert (20, 200) in edges
    assert out["expanded_body_id_count"] == 5
    # second-round queries targeted the first-order partners
    queried = {q[0] for q in fake.adjacency_queries}
    assert any({10, 20}.issubset(q) for q in queried)


def test_depth_one_matches_previous_behavior(tmp_path: Path) -> None:
    edge_rows = [
        {"bodyId_pre": 1, "bodyId_post": 10, "roi": "R", "weight": 5},
        {"bodyId_pre": 10, "bodyId_post": 100, "roi": "R", "weight": 5},
    ]
    loader, _ = _loader(tmp_path, edge_rows)

    out = loader.snapshot_closed_subgraph([1], depth=1)

    assert _snapshot_nodes(tmp_path) == [1, 10]
    assert _snapshot_edges(tmp_path) == [(1, 10)]  # 100 not reachable at depth 1
    assert out["expanded_body_id_count"] == 2


def test_depth_zero_is_seed_only(tmp_path: Path) -> None:
    loader, _ = _loader(tmp_path, [
        {"bodyId_pre": 1, "bodyId_post": 10, "roi": "R", "weight": 5},
    ])

    out = loader.snapshot_closed_subgraph([1], depth=0)

    assert _snapshot_nodes(tmp_path) == [1]
    assert out["expanded_body_id_count"] == 1


def test_invalid_depth_rejected(tmp_path: Path) -> None:
    loader, _ = _loader(tmp_path, [])
    with pytest.raises(ValueError, match="depth"):
        loader.snapshot_closed_subgraph([1], depth=-1)
