"""Phase 7 E1 analysis: frozen-logic contract tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase7e1_analysis as e1  # noqa: E402


def test_reproduce_draw_matches_prereg():
    e1.reproduce_draw()  # raises ScopeError on any mismatch


def test_c1_threshold_boundary():
    assert e1.MN9_FIRE_HZ == 41.5
    assert 41.5 >= e1.MN9_FIRE_HZ and 41.4 < e1.MN9_FIRE_HZ


def test_e1_spaces_sized():
    t, p = e1.e1_spaces(2_900_000, 2_900_100)
    assert len(t) == 24 and len(p) == 12
    assert not (t & p)


def test_prereg_lists_present():
    doc = (ROOT / "docs/PHASE_7E1_PREREG.md").read_text(encoding="utf-8")
    assert len(e1.grab(doc, "E1_TASTE_BASES")) == 4
    assert len(e1.grab(doc, "E1_PROBE_BASES")) == 4


def test_step_once_bit_identical_to_embodiment_loop():
    """Harness step wiring must match SensorimotorLoop.step exactly (no plasticity)."""
    import dataclasses
    import numpy as np
    from scipy import sparse
    from fly.dynamics.lif import LIFParams
    from fly.embodiment.body_graph import BodyState, default_body_graph
    from fly.embodiment.sensorimotor_loop import SensorimotorLoop
    import phase7e1_harness as h

    base = ROOT / "data/processed/neuprint_snapshots/run-007"
    matrix = sparse.load_npz(base / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(base / "connectivity_nodes.npy").tolist()
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    body = default_body_graph()
    loop = SensorimotorLoop(body=default_body_graph(), matrix=matrix.copy(), nodes=nodes, params=params)
    s1 = BodyState(cue_on=True, sugar_present=True, proboscis_extension=1.0)
    s2 = BodyState(cue_on=True, sugar_present=True, proboscis_extension=1.0)
    seed = 2999999
    ref = loop.step(s1, seed)
    rec, res = h.step_once(matrix, nodes, params, body, s2, seed)
    assert rec["mn9_hz"] == ref["mn9_hz"]
    assert rec["proboscis_extension"] == ref["proboscis_extension"]
    assert rec["sugar_detected"] == ref["sugar_detected"]
    assert rec["n_spikes"] == res.n_spikes
