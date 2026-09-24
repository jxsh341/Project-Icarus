"""Tests for the WP8 neural benchmark suite.

The benchmark harness must produce machine-readable, seed-disciplined
baselines for the three protocol pillars of Phase 1 WP8
(docs/PHASE_1_BASELINE.md, section 15):

- spontaneous activity: no stimulation, measures endogenous dynamics
- stimulus response: defined population Poisson-driven, measures latency /
  magnitude / recruitment / recovery
- circuit propagation: stimulated population -> first-order -> second-order
  -> downstream targets, a causal activity map

Every benchmark run must record: dataset, subgraph provenance, seeds,
duration, parameter provenance, and per-trial raw outputs.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.benchmarks.neural import (
    BenchmarkResult,
    benchmark_circuit_propagation,
    benchmark_spontaneous,
    benchmark_stimulus_response,
)


def _toy_graph() -> tuple[sparse.csr_matrix, list[int]]:
    # A -> B, A -> C, B -> D; C isolated from D
    rows, cols, data = [0, 0, 1], [1, 2, 3], [100.0, 100.0, 100.0]
    m = sparse.csr_matrix((data, (rows, cols)), shape=(4, 4))
    m.sum_duplicates()
    m.sort_indices()
    return m, [10, 20, 30, 40]


def test_benchmark_result_is_json_serializable() -> None:
    result = BenchmarkResult(
        benchmark="spontaneous",
        dataset="male-cns:v1.0",
        subgraph_provenance={"run_id": "run-005", "n_neurons": 4293},
        n_trials=2,
        duration_ms=100.0,
        seeds=[42, 43],
        params_provenance="fly.dynamics.lif.LIFParams (Shiu et al. reference)",
        per_trial=[{"total_spikes": 0, "n_spiking": 0}],
    )
    as_dict = result.to_dict()
    text = json.dumps(as_dict, indent=2)
    assert "spontaneous" in text

    restored = BenchmarkResult.from_dict(json.loads(text))
    assert restored.benchmark == "spontaneous"
    assert restored.seeds == [42, 43]


def test_spontaneous_benchmark_records_zero_activity_on_silent_graph() -> None:
    matrix, node_ids = _toy_graph()

    result = benchmark_spontaneous(matrix, node_ids, n_trials=3, duration_ms=50.0, seed_base=100)

    assert result.benchmark == "spontaneous"
    assert result.n_trials == 3
    assert result.seeds == [100, 101, 102]
    # unstimulated LIF network with no initial drive is silent
    for trial in result.per_trial:
        assert trial["total_spikes"] == 0
        assert trial["n_spiking"] == 0
        assert trial["mean_rate_hz"] == 0.0
        assert trial["active_fraction"] == 0.0


def test_stimulus_response_measures_latency_and_recruitment() -> None:
    matrix, node_ids = _toy_graph()

    result = benchmark_stimulus_response(
        matrix, node_ids, stimulated=[10], n_trials=3, duration_ms=200.0, seed_base=0
    )

    assert result.benchmark == "stimulus_response"
    assert len(result.per_trial) == 3
    for trial in result.per_trial:
        assert trial["stimulated_rate_hz"] > 0.0
        # latency defined and non-negative
        assert 0.0 <= trial["first_response_latency_ms"]
        # population recruitment: at least the stimulated neuron spikes
        assert trial["n_spiking"] >= 1
        # recovery is not measured in a single window; field present for schema stability
        assert "recovery" in trial


def test_circuit_propagation_maps_hops() -> None:
    matrix, node_ids = _toy_graph()

    result = benchmark_circuit_propagation(
        matrix, node_ids, stimulated=[10], n_trials=3, duration_ms=200.0, seed_base=0
    )

    assert result.benchmark == "circuit_propagation"
    first_trial = result.per_trial[0]
    # hop structure: seeds -> first-order (B, C) -> second-order (D)
    assert first_trial["hop_spiking"]["seeds"] >= 1
    assert first_trial["hop_spiking"]["first_order"] >= 1
    assert first_trial["hop_spiking"]["second_order"] >= 1
    # causal order: seeds fire no later than first order
    assert (
        first_trial["hop_first_spike_ms"]["seeds"]
        <= first_trial["hop_first_spike_ms"]["first_order"]
    )


def test_benchmarks_reject_unknown_ids() -> None:
    matrix, node_ids = _toy_graph()

    with pytest.raises(ValueError):
        benchmark_stimulus_response(matrix, node_ids, stimulated=[99], n_trials=1, duration_ms=10.0)
    with pytest.raises(ValueError):
        benchmark_circuit_propagation(matrix, node_ids, stimulated=[99], n_trials=1, duration_ms=10.0)


def test_benchmarks_reject_bad_counts() -> None:
    matrix, node_ids = _toy_graph()

    with pytest.raises(ValueError):
        benchmark_spontaneous(matrix, node_ids, n_trials=0, duration_ms=10.0)
    with pytest.raises(ValueError):
        benchmark_stimulus_response(matrix, node_ids, stimulated=[10], n_trials=0, duration_ms=10.0)
    with pytest.raises(ValueError):
        benchmark_circuit_propagation(matrix, node_ids, stimulated=[10], n_trials=1, duration_ms=0.0)
