"""Tests for delayed second-population onset (WP9 staggered-onset protocol).

WP9's suppression-latency protocol needs bitter GRNs to start firing 200
ms into a sugar trial. simulate_lif gains ``stim2_start_ms``: Poisson
events for ``stimulated2`` are suppressed for t < start (None/0 = drive
from t=0, exactly the previous semantics).
"""

import dataclasses

import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif


def _matrix(n):
    m = sparse.csr_matrix((n, n))
    return m


def test_no_kicks_before_start() -> None:
    # lone neuron driven only via stimulated2, start at 800 ms of a 1000 ms
    # trial: all spikes must land at/after 800 ms
    r = simulate_lif(
        _matrix(1), [10], LIFParams(), duration_ms=1000.0,
        stimulated2=[10], r_poisson2_Hz=300.0, stim2_start_ms=800.0, seed=7,
    )
    spikes = r.spike_times.get(10, [])
    assert spikes, "delayed drive should still fire the neuron after start"
    assert min(spikes) >= 799.9
    assert max(spikes) <= 1000.0


def test_start_zero_equals_none() -> None:
    # regression: explicit 0 ms start must reproduce the default semantics
    a = simulate_lif(
        _matrix(1), [10], LIFParams(), duration_ms=500.0,
        stimulated2=[10], r_poisson2_Hz=200.0, stim2_start_ms=0.0, seed=3,
    )
    b = simulate_lif(
        _matrix(1), [10], LIFParams(), duration_ms=500.0,
        stimulated2=[10], r_poisson2_Hz=200.0, seed=3,
    )
    assert a.spike_times == b.spike_times
    assert a.n_spikes == b.n_spikes


def test_start_requires_stimulated2() -> None:
    with pytest.raises(ValueError, match="stim2_start_ms"):
        simulate_lif(
            _matrix(1), [10], LIFParams(), duration_ms=100.0,
            stim2_start_ms=200.0,
        )


def test_start_beyond_duration_means_no_drive() -> None:
    r = simulate_lif(
        _matrix(1), [10], LIFParams(), duration_ms=500.0,
        stimulated2=[10], r_poisson2_Hz=100_000.0, stim2_start_ms=1500.0, seed=1,
    )
    assert r.spike_times.get(10, []) == []
