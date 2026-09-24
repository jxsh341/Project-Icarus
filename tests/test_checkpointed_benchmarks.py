"""Tests for checkpointed benchmark execution (WP8 v2 standard).

Multi-trial benchmark runs must be resumable: each trial appends to a
JSONL checkpoint the moment it completes, and a re-invocation skips
seeds already present. This is the structural lesson of the WP6c orphan
incident (a Hermes restart killed an uncheckpointed 60-trial run) -
now a standing rule for any multi-trial run, per review.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.benchmarks.neural import run_benchmark_checkpointed


def _toy_graph() -> tuple[sparse.csr_matrix, list[int]]:
    rows, cols, data = [0, 0, 1], [1, 2, 3], [100.0, 100.0, 100.0]
    m = sparse.csr_matrix((data, (rows, cols)), shape=(4, 4))
    m.sum_duplicates()
    m.sort_indices()
    return m, [10, 20, 30, 40]


def test_checkpointed_run_writes_one_line_per_trial(tmp_path: Path) -> None:
    ckpt = tmp_path / "trials.jsonl"
    result = run_benchmark_checkpointed(
        benchmark_fn="benchmark_spontaneous",
        matrix=_toy_graph()[0],
        node_ids=_toy_graph()[1],
        n_trials=4,
        duration_ms=50.0,
        seed_base=100,
        checkpoint=ckpt,
    )
    lines = [json.loads(l) for l in ckpt.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 4
    assert [t["seed"] for t in lines] == [100, 101, 102, 103]
    assert result.n_trials == 4
    assert [t["seed"] for t in result.per_trial] == [100, 101, 102, 103]


def test_checkpointed_run_resumes_and_skips_done_seeds(tmp_path: Path) -> None:
    ckpt = tmp_path / "trials.jsonl"
    # first invocation interrupted after 2 of 4 trials
    run_benchmark_checkpointed(
        benchmark_fn="benchmark_spontaneous",
        matrix=_toy_graph()[0],
        node_ids=_toy_graph()[1],
        n_trials=2,
        duration_ms=50.0,
        seed_base=100,
        checkpoint=ckpt,
    )
    assert len(ckpt.read_text(encoding="utf-8").splitlines()) == 2
    # resume: seeds 100/101 present, so only 102/103 run
    result = run_benchmark_checkpointed(
        benchmark_fn="benchmark_spontaneous",
        matrix=_toy_graph()[0],
        node_ids=_toy_graph()[1],
        n_trials=4,
        duration_ms=50.0,
        seed_base=100,
        checkpoint=ckpt,
    )
    lines = [json.loads(l) for l in ckpt.read_text(encoding="utf-8").splitlines()]
    assert [t["seed"] for t in lines] == [100, 101, 102, 103]  # no duplicates
    assert result.n_trials == 4
    assert [t["seed"] for t in result.per_trial] == [100, 101, 102, 103]
    # determinism: resumed seed 102 matches a fresh seed-102 run
    fresh = run_benchmark_checkpointed(
        benchmark_fn="benchmark_spontaneous",
        matrix=_toy_graph()[0],
        node_ids=_toy_graph()[1],
        n_trials=1,
        duration_ms=50.0,
        seed_base=102,
        checkpoint=tmp_path / "fresh.jsonl",
    )
    resumed_102 = [t for t in result.per_trial if t["seed"] == 102][0]
    fresh_102 = fresh.per_trial[0]
    assert resumed_102["total_spikes"] == fresh_102["total_spikes"]


def test_checkpointed_run_unknown_benchmark_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown benchmark"):
        run_benchmark_checkpointed(
            benchmark_fn="benchmark_nonsense",
            matrix=_toy_graph()[0],
            node_ids=_toy_graph()[1],
            n_trials=1,
            duration_ms=50.0,
            seed_base=0,
            checkpoint=tmp_path / "x.jsonl",
        )


def test_checkpointed_run_requires_checkpoint_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="checkpoint"):
        run_benchmark_checkpointed(
            benchmark_fn="benchmark_spontaneous",
            matrix=_toy_graph()[0],
            node_ids=_toy_graph()[1],
            n_trials=1,
            duration_ms=50.0,
            seed_base=0,
            checkpoint=None,
        )
