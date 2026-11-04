"""Phase 7 P4b (Amendment B1): frozen-logic contract tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7p4b_analysis as p4b  # noqa: E402


def test_reproduce_draw_matches_prereg():
    p4b.reproduce_draw()


def test_spaces_sized():
    assert len(p4b.acq_space(3_200_000)) == 22
    assert len(p4b.unl_space(3_200_000)) == 24


def test_decay_to_matches_iterated():
    """One-shot analytic decay == 25 iterated single-cycle decays (P3 math)."""
    import numpy as np
    from scipy import sparse
    import phase7p4b_harness as h
    m = sparse.random(50, 50, density=0.1, format="csr",
                      random_state=1, data_rvs=lambda k: np.full(k, 20.0))
    rank = sorted((int(i), int(j)) for i, j in list(zip(*m.nonzero()))[:25])
    one = h.decay_to(m, rank, 25, 1.0)
    step = m.copy()
    for _ in range(25):
        step = h.decay_to(step, rank, 1, 1.0)
    assert (one != step).nnz == 0


def test_harness_b1_trials_20():
    import phase7p4b_harness as h
    assert h.N_ACQ_TRIALS == 20
