"""Tests for two-population Poisson drive (WP6c sugar/bitter requirement).

The Shiu reference's poi() creates TWO PoissonInput classes (r_poi for
`exc`, r_poi2 for `exc2`) - both targeting v with weight w_syn*f_poi,
both with rfc=0. simulate_lif needs an equivalent stimulated2/r2 pathway
to run the sugar x bitter grid.
"""

import dataclasses

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif


def _matrix(rows, cols, data, n):
    m = sparse.csr_matrix((np.asarray(data, float), (rows, cols)), shape=(n, n))
    m.sum_duplicates()
    m.sort_indices()
    return m


def test_second_population_drives_at_its_own_rate() -> None:
    # two isolated neurons, each with its own Poisson population
    counts = _matrix([], [], [], 2)
    base = LIFParams()
    p1 = dataclasses.replace(base, r_poisson_Hz=50.0)
    p2 = dataclasses.replace(base, r_poisson_Hz=300.0)

    r = simulate_lif(
        counts, [10, 20], p1,
        duration_ms=2000.0,
        stimulated=[10],
        stimulated2=[20],
        r_poisson2_Hz=300.0,
        seed=3,
    )
    rate1 = len(r.spike_times.get(10, [])) / 2.0
    rate2 = len(r.spike_times.get(20, [])) / 2.0
    # driven neuron 1 at 50 Hz -> effective ~50 Hz (low rate, minimal
    # same-step destruction); neuron 2 at 300 Hz -> below nominal
    assert 30 <= rate1 <= 75
    assert rate2 > rate1  # higher drive -> higher rate
    assert 150 <= rate2 <= 320


def test_second_population_also_has_refractory_disabled() -> None:
    # stimulated2 neurons must get rfc=0 like stimulated (reference poi()
    # sets neu[i].rfc = 0 for BOTH loops)
    counts = _matrix([], [], [], 1)
    p = LIFParams()
    # drive hard: rfc=0 lets the neuron fire above what 2.2ms refractory
    # would cap (~455 Hz); with rfc enforced it could not exceed ~450 Hz
    r = simulate_lif(
        counts, [10], p,
        duration_ms=500.0,
        stimulated2=[10],
        r_poisson2_Hz=100_000.0,
        seed=1,
    )
    rate = len(r.spike_times.get(10, [])) / 0.5
    assert rate > 460  # exceeds the refractory cap -> rfc was disabled


def test_stimulated2_requires_r2() -> None:
    counts = _matrix([], [], [], 2)
    with pytest.raises(ValueError, match="r_poisson2"):
        simulate_lif(counts, [10, 20], LIFParams(), duration_ms=10.0,
                     stimulated2=[20])  # no r_poisson2_Hz given


def test_second_population_unknown_id_rejected() -> None:
    counts = _matrix([], [], [], 2)
    with pytest.raises(ValueError, match="stimulated2"):
        simulate_lif(counts, [10, 20], LIFParams(), duration_ms=10.0,
                     stimulated2=[99], r_poisson2_Hz=100.0)
