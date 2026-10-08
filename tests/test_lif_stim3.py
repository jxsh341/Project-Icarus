"""Tests: third Poisson stimulation channel (stimulated3) for L3.

L3's gate-DA drive needs a THIRD independent stimulation rate on top
of cue (stimulated) and sugar (stimulated2). The WP-L3a Sweep C bug
(the swept rate never entered the sim; the sweep degenerated to a
2-point contrast) is what this extension exists to fix.

Requirements pinned here:
1. Default-off: simulate_lif WITHOUT stimulated3 is bit-identical to
   the pre-extension behavior (same seed -> same spikes).
2. stimulated3 drives: targets fire at the given rate, rfc=0
   semantics (same as the other Poisson populations).
3. The three populations run at INDEPENDENT rates.
"""

import dataclasses
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

_N = 6
_ROWS = [0, 1, 2, 3, 4]
_COLS = [5, 5, 5, 5, 5]
_DATA = [10.0, 10.0, 10.0, -10.0, 10.0]


def _matrix():
    m = sparse.csr_matrix((_DATA, (_ROWS, _COLS)), shape=(_N, _N))
    m.sort_indices()
    return m


def _nodes():
    return list(range(100, 100 + _N))


def test_stimulated3_default_off_bit_identical():
    """No stimulated3 -> identical results to the 2-channel form."""
    m, nodes = _matrix(), _nodes()
    params = LIFParams()
    a = simulate_lif(m, nodes, params, 200.0, stimulated=[100], seed=42)
    b = simulate_lif(m, nodes, params, 200.0, stimulated=[100], stimulated3=[], seed=42)
    assert a.spike_times == b.spike_times
    assert a.n_spikes == b.n_spikes


def test_stimulated3_drives_targets():
    """stimulated3 at 200 Hz drives its targets to fire."""
    m, nodes = _matrix(), _nodes()
    params = LIFParams()
    r = simulate_lif(m, nodes, params, 1000.0,
                     stimulated3=[104], r_poisson3_Hz=200.0, seed=7)
    assert len(r.spike_times.get(104, [])) > 100  # ~0.9x of 200


def test_stimulated3_independent_rate():
    """cue at 200 + sugar2 at 0 + stim3 at 50 -> stim3 targets fire
    ~50 Hz while the primary runs its own rate."""
    m, nodes = _matrix(), _nodes()
    params = LIFParams()
    r = simulate_lif(m, nodes, params, 1000.0,
                     stimulated=[100], stimulated2=[101], stimulated3=[104],
                     r_poisson2_Hz=0.0, r_poisson3_Hz=50.0, seed=9)
    n3 = len(r.spike_times.get(104, []))
    n1 = len(r.spike_times.get(100, []))
    assert 30 < n3 < 80   # ~50 Hz (0.9x)
    assert n1 > 130       # primary unaffected: ~145 = 0.97x of its 150 Hz default rate
