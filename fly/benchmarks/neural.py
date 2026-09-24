"""WP8 neural benchmark suite.

Machine-readable, seed-disciplined baselines for the three protocol
pillars of Phase 1 WP8 (FLY-BASE-001 plan, section 15):

- spontaneous activity: no stimulation; endogenous dynamics of the graph
  under the reference LIF model
- stimulus response: a defined population is Poisson-driven; measures
  latency, magnitude, recruitment, and recovery schema
- circuit propagation: stimulated population -> first-order -> second-order
  -> downstream targets, producing a causal activity map

All benchmarks run on the validated reference LIF implementation
(fly.dynamics.lif), which is pinned to the Shiu et al. (2024) reference
and verified against it (validation/reference/wp6_head_to_head.json).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif


@dataclass(frozen=True)
class BenchmarkResult:
    """Machine-readable result of one benchmark protocol."""

    benchmark: str
    dataset: str
    subgraph_provenance: dict[str, Any]
    n_trials: int
    duration_ms: float
    seeds: list[int]
    params_provenance: str
    per_trial: list[dict[str, Any]]
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "dataset": self.dataset,
            "subgraph_provenance": self.subgraph_provenance,
            "n_trials": self.n_trials,
            "duration_ms": self.duration_ms,
            "seeds": self.seeds,
            "params_provenance": self.params_provenance,
            "per_trial": self.per_trial,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkResult":
        return cls(**data)


PARAMS_PROVENANCE = (
    "fly.dynamics.lif.LIFParams defaults (Shiu et al. 2024 reference; "
    "verified in validation/reference/wp6_head_to_head.json)"
)


def _check_common(
    matrix: sparse.csr_matrix,
    node_ids: list[int],
    n_trials: int,
    duration_ms: float,
) -> None:
    if n_trials < 1:
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")
    if duration_ms <= 0:
        raise ValueError(f"duration_ms must be > 0, got {duration_ms}")
    if matrix.shape != (len(node_ids), len(node_ids)):
        raise ValueError(
            f"connectivity shape {matrix.shape} does not match {len(node_ids)} node ids"
        )


def _check_ids(node_ids: list[int], ids: list[int], what: str) -> None:
    known = set(node_ids)
    for value in ids:
        if value not in known:
            raise ValueError(f"{what} id {value!r} not in node_ids")


def _spike_stats(
    spike_times: dict[int, list[float]], duration_ms: float, n_neurons: int
) -> dict[str, Any]:
    n_spiking = len(spike_times)
    total = sum(len(v) for v in spike_times.values())
    rates = {nid: len(v) / (duration_ms / 1000.0) for nid, v in spike_times.items()}
    mean_rate = total / n_neurons / (duration_ms / 1000.0) if n_neurons else 0.0
    active_fraction = n_spiking / n_neurons if n_neurons else 0.0
    return {
        "total_spikes": total,
        "n_spiking": n_spiking,
        "mean_rate_hz": mean_rate,
        "active_fraction": active_fraction,
        "per_neuron_rates_hz": {str(k): v for k, v in rates.items()},
    }


def _summarize(per_trial: list[dict[str, Any]], fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in fields:
        values = [t[name] for t in per_trial if isinstance(t.get(name), (int, float))]
        if not values:
            continue
        arr = np.asarray(values, dtype=float)
        out[name] = {
            "mean": float(arr.mean()),
            "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
            "min": float(arr.min()),
            "max": float(arr.max()),
        }
    return out


def benchmark_spontaneous(
    matrix: sparse.csr_matrix,
    node_ids: list[int],
    n_trials: int = 30,
    duration_ms: float = 1000.0,
    seed_base: int = 0,
    params: LIFParams | None = None,
    dataset: str = "male-cns:v1.0",
    subgraph_provenance: dict[str, Any] | None = None,
) -> BenchmarkResult:
    """Spontaneous activity: run the network with no stimulation."""
    _check_common(matrix, node_ids, n_trials, duration_ms)
    params = params or LIFParams()
    per_trial = []
    for i in range(n_trials):
        run = simulate_lif(
            matrix, node_ids, params, duration_ms=duration_ms, seed=seed_base + i
        )
        trial = _spike_stats(run.spike_times, duration_ms, len(node_ids))
        trial["seed"] = seed_base + i
        per_trial.append(trial)
    summary = _summarize(
        per_trial, ["total_spikes", "n_spiking", "mean_rate_hz", "active_fraction"]
    )
    return BenchmarkResult(
        benchmark="spontaneous",
        dataset=dataset,
        subgraph_provenance=subgraph_provenance or {"unspecified": True},
        n_trials=n_trials,
        duration_ms=duration_ms,
        seeds=[seed_base + i for i in range(n_trials)],
        params_provenance=PARAMS_PROVENANCE,
        per_trial=per_trial,
        summary=summary,
    )


def benchmark_stimulus_response(
    matrix: sparse.csr_matrix,
    node_ids: list[int],
    stimulated: list[int],
    n_trials: int = 30,
    duration_ms: float = 1000.0,
    seed_base: int = 0,
    params: LIFParams | None = None,
    dataset: str = "male-cns:v1.0",
    subgraph_provenance: dict[str, Any] | None = None,
) -> BenchmarkResult:
    """Stimulus response: Poisson-drive a defined population, measure response."""
    _check_common(matrix, node_ids, n_trials, duration_ms)
    _check_ids(node_ids, stimulated, "stimulated")
    params = params or LIFParams()
    per_trial = []
    for i in range(n_trials):
        run = simulate_lif(
            matrix,
            node_ids,
            params,
            duration_ms=duration_ms,
            stimulated=stimulated,
            seed=seed_base + i,
        )
        trial = _spike_stats(run.spike_times, duration_ms, len(node_ids))
        stim_rates = [
            len(run.spike_times.get(s, [])) / (duration_ms / 1000.0) for s in stimulated
        ]
        stim_times = [run.spike_times.get(s, []) for s in stimulated]
        first_spike_overall = min(
            (times[0] for times in stim_times if times), default=None
        )
        all_times = [t for times in stim_times for t in times]
        peak_pop_rate = (
            max(
                _population_rate(run.spike_times, duration_ms)
            )
            if all_times
            else 0.0
        )
        trial["seed"] = seed_base + i
        trial["stimulated_rate_hz"] = float(np.mean(stim_rates)) if stim_rates else 0.0
        trial["first_stimulated_spike_ms"] = first_spike_overall
        trial["first_response_latency_ms"] = (
            first_spike_overall if first_spike_overall is not None else float("inf")
        )
        trial["peak_population_rate_hz"] = peak_pop_rate
        trial["recovery"] = None  # schema-stable placeholder; needs a paired off-stimulus window
        per_trial.append(trial)
    summary = _summarize(
        per_trial,
        [
            "total_spikes",
            "n_spiking",
            "mean_rate_hz",
            "active_fraction",
            "stimulated_rate_hz",
            "first_response_latency_ms",
            "peak_population_rate_hz",
        ],
    )
    return BenchmarkResult(
        benchmark="stimulus_response",
        dataset=dataset,
        subgraph_provenance=subgraph_provenance or {"unspecified": True},
        n_trials=n_trials,
        duration_ms=duration_ms,
        seeds=[seed_base + i for i in range(n_trials)],
        params_provenance=PARAMS_PROVENANCE,
        per_trial=per_trial,
        summary=summary,
    )


def _population_rate(spike_times: dict[int, list[float]], duration_ms: float, window_ms: float = 50.0) -> np.ndarray:
    """Population firing rate in 50 ms windows (Hz per active neuron)."""
    if not spike_times:
        return np.zeros(1)
    all_spikes = np.asarray([t for v in spike_times.values() for t in v], dtype=float)
    n_neurons_active = len(spike_times)
    window = max(window_ms, 1e-6)
    n_windows = int(np.ceil(duration_ms / window))
    counts, _ = np.histogram(all_spikes if all_spikes.size else [0.0], bins=n_windows, range=(0, duration_ms))
    return counts * (1000.0 / window) / n_neurons_active


def benchmark_circuit_propagation(
    matrix: sparse.csr_matrix,
    node_ids: list[int],
    stimulated: list[int],
    n_trials: int = 30,
    duration_ms: float = 1000.0,
    seed_base: int = 0,
    params: LIFParams | None = None,
    dataset: str = "male-cns:v1.0",
    subgraph_provenance: dict[str, Any] | None = None,
    depth: int = 2,
) -> BenchmarkResult:
    """Circuit propagation: causal activity map over synaptic hops."""
    _check_common(matrix, node_ids, n_trials, duration_ms)
    _check_ids(node_ids, stimulated, "stimulated")
    if depth < 1:
        raise ValueError(f"depth must be >= 1, got {depth}")
    params = params or LIFParams()

    index_of = {nid: i for i, nid in enumerate(node_ids)}
    stim_idx = [index_of[s] for s in stimulated]

    # BFS hop sets over the directed graph, seeded at the stimulated population
    hop_sets: list[list[int]] = [stim_idx]  # hop 0 = seeds
    visited = set(stim_idx)
    frontier = stim_idx
    for _ in range(depth):
        if not frontier:
            break
        targets: list[int] = []
        for i in frontier:
            row = matrix.getrow(i)
            for j in row.nonzero()[1]:
                if j not in visited:
                    visited.add(j)
                    targets.append(int(j))
        hop_sets.append(sorted(set(targets)))
        frontier = targets

    per_trial = []
    hop_labels = ["seeds"] + ["first_order", "second_order"] + [
        f"hop_{h}" for h in range(3, len(hop_sets))
    ]
    for i in range(n_trials):
        run = simulate_lif(
            matrix,
            node_ids,
            params,
            duration_ms=duration_ms,
            stimulated=stimulated,
            seed=seed_base + i,
        )
        trial: dict[str, Any] = {"seed": seed_base + i}
        hop_spiking: dict[str, int] = {}
        hop_first: dict[str, Any] = {}
        hop_rates: dict[str, float] = {}
        for h, members in enumerate(hop_sets):
            label = hop_labels[h]
            firsts = [run.spike_times[node_ids[j]][0] for j in members if run.spike_times.get(node_ids[j])]
            hop_spiking[label] = len(firsts)
            hop_first[label] = min(firsts) if firsts else None
            total_spikes = sum(len(run.spike_times.get(node_ids[j], [])) for j in members)
            hop_rates[label] = total_spikes / (duration_ms / 1000.0) if members else 0.0
        trial["hop_spiking"] = hop_spiking
        trial["hop_first_spike_ms"] = hop_first
        trial["hop_rate_hz"] = hop_rates
        # population-level totals for convenience
        trial["total_spikes"] = sum(len(v) for v in run.spike_times.values())
        trial["n_spiking"] = len(run.spike_times)
        per_trial.append(trial)

    # summary over trials: hop spiking counts and first-spike latencies
    summary: dict[str, Any] = {}
    for label in hop_labels[: len(hop_sets)]:
        counts = [t["hop_spiking"].get(label, 0) for t in per_trial]
        arr = np.asarray(counts, dtype=float)
        summary[f"hop_spiking_{label}"] = {
            "mean": float(arr.mean()),
            "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        }
        firsts = [
            t["hop_first_spike_ms"][label]
            for t in per_trial
            if t["hop_first_spike_ms"].get(label) is not None
        ]
        if firsts:
            arr2 = np.asarray(firsts, dtype=float)
            summary[f"hop_first_spike_ms_{label}"] = {
                "mean": float(arr2.mean()),
                "std": float(arr2.std(ddof=1)) if len(arr2) > 1 else 0.0,
            }
    return BenchmarkResult(
        benchmark="circuit_propagation",
        dataset=dataset,
        subgraph_provenance={
            **(subgraph_provenance or {"unspecified": True}),
            "hop_structure": {
                "seeds": len(hop_sets[0]),
                **{f"hop_{h}": len(hop_sets[h]) for h in range(1, len(hop_sets))},
            },
        },
        n_trials=n_trials,
        duration_ms=duration_ms,
        seeds=[seed_base + i for i in range(n_trials)],
        params_provenance=PARAMS_PROVENANCE,
        per_trial=per_trial,
        summary=summary,
    )
