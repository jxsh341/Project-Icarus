"""fly.api stable subsystem entry point: contract tests (synthetic 6-node net)."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fly.api import (  # noqa: E402
    API_VERSION, SCHEMA_VERSION, BodyInput, BodyObservation, FlySubstrate,
    InputEvent, LifecycleError, LearningController, Observation, Phase,
    SchemaError, StimulusPort,
)
from fly.plasticity import PlasticityConfig, Semantics  # noqa: E402
from fly.training import weight_matrix_hash  # noqa: E402


def tiny_net():
    # 0,1 = cue; 2 = target; 3 = readout(MN9 stand-in id irrelevant here); 4,5 = spare
    row = [0, 0, 1, 2, 3]
    col = [2, 3, 3, 3, 2]
    data = [40.0, 30.0, 50.0, 25.0, 20.0]
    m = sparse.coo_matrix((data, (row, col)), shape=(6, 6)).tocsr()
    return m, [100, 101, 102, 103, 104, 105]


def make_sub():
    m, nodes = tiny_net()
    s = FlySubstrate(m, nodes, readout_body_id=103)
    s.initialize()
    s.resume()
    return s


def cue_event(seed=7):
    return InputEvent(duration_ms=200.0, seed=seed,
                      ports=(StimulusPort("cue", (100, 101), 200.0, slot=1, role="cue"),))


def test_schema_versions_pinned():
    assert SCHEMA_VERSION == 1 and API_VERSION == "1.1.0"


def test_event_roundtrip_and_version_rejection():
    ev = cue_event()
    d = ev.to_dict()
    assert InputEvent.from_dict(d) == ev
    bad = dict(d, schema_version=99)
    with pytest.raises(SchemaError):
        InputEvent.from_dict(bad)


def test_observation_roundtrip_and_version_rejection():
    s = make_sub()
    obs = s.step(cue_event())
    assert isinstance(obs, Observation)
    d = obs.to_dict()
    json.dumps(d)  # JSON-serialisable contract
    assert Observation.from_dict(json.loads(json.dumps(d))) == obs
    with pytest.raises(SchemaError):
        Observation.from_dict(dict(d, schema_version=2))


def test_step_requires_running_and_is_deterministic():
    s = make_sub()
    s.pause()
    with pytest.raises(LifecycleError):
        s.step(cue_event())
    s.resume()
    o1 = s.step(cue_event(seed=3))
    o2 = s.step(cue_event(seed=3))
    assert o1.spike_counts == o2.spike_counts and o1.weight_hash == o2.weight_hash
    assert sum(o1.spike_counts.values()) == o1.n_spikes


def test_lifecycle_transitions():
    m, nodes = tiny_net()
    s = FlySubstrate(m, nodes)
    with pytest.raises(LifecycleError):
        s.resume()          # CREATED -> cannot resume
    s.initialize()
    with pytest.raises(LifecycleError):
        s.initialize()      # no double init
    s.resume()
    s.pause()
    s.resume()
    s.shutdown()
    with pytest.raises(LifecycleError):
        s.step(cue_event())  # shut down
    with pytest.raises(LifecycleError):
        s.shutdown()


def test_reset_restores_pristine():
    s = make_sub()
    h0 = weight_matrix_hash(s.matrix)
    s.learning.arm(PlasticityConfig(eta=1e-3, semantics=Semantics.V_CLIP, w_max=766.0))
    s.run_trial(cue_event())
    assert weight_matrix_hash(s.matrix) != h0
    s.reset()
    assert weight_matrix_hash(s.matrix) == h0
    assert s.trial_index == 0 and s.phase == Phase.INITIALIZED


def test_learning_control_explicit():
    s = make_sub()
    assert not s.learning.enabled
    h0 = weight_matrix_hash(s.matrix)
    s.run_trial(cue_event())   # disarmed: probe semantics, no weight change
    assert weight_matrix_hash(s.matrix) == h0
    s.learning.arm(PlasticityConfig(eta=1e-3, semantics=Semantics.V_CLIP, w_max=766.0))
    assert s.learning.enabled
    s.run_trial(cue_event())
    assert weight_matrix_hash(s.matrix) != h0
    s.learning.disarm()
    h1 = weight_matrix_hash(s.matrix)
    s.run_trial(cue_event())
    assert weight_matrix_hash(s.matrix) == h1


def test_checkpoint_save_load_roundtrip(tmp_path):
    s = make_sub()
    s.learning.arm(PlasticityConfig(eta=1e-3, semantics=Semantics.V_CLIP, w_max=766.0))
    s.run_trial(cue_event())
    s.pause()
    p = s.save_checkpoint(tmp_path / "ck")
    man = json.loads((p / "manifest.json").read_text())
    assert man["api_version"] == API_VERSION and man["schema_version"] == SCHEMA_VERSION
    s2 = FlySubstrate.load_checkpoint(p)
    assert weight_matrix_hash(s2.matrix) == weight_matrix_hash(s.matrix)
    assert s2.trial_index == s.trial_index and s2.phase == Phase.PAUSED
    assert s2.learning.enabled
    # tamper detection
    m = sparse.load_npz(p / "weights.npz").tocsr()
    m = m + sparse.coo_matrix(([1.0], ([0], [0])), shape=m.shape).tocsr()
    sparse.save_npz(p / "weights.npz", m)
    with pytest.raises(SchemaError):
        FlySubstrate.load_checkpoint(p)


def test_state_export_import_roundtrip():
    s = make_sub()
    s.run_trial(cue_event())
    d = s.export_state()
    json.dumps(d)
    s2 = FlySubstrate.import_state(json.loads(json.dumps(d)))
    assert weight_matrix_hash(s2.matrix) == weight_matrix_hash(s.matrix)
    assert s2.trial_index == s.trial_index and s2.phase == s.phase
    with pytest.raises(SchemaError):
        FlySubstrate.import_state(dict(d, schema_version=42))


def test_body_input_wiring_and_observation():
    from fly.embodiment.body_graph import Actuator, BodyGraph, BodyState, Sensor, MN9_L
    m, nodes = tiny_net()
    nodes = [100, 101, 102, MN9_L, 104, 105]  # readout = MN9_L so the actuator engages
    bg = BodyGraph(
        sensors=[Sensor("s_cue", "cue", [100, 101]), Sensor("s_sugar", "sugar", [102]),
                 Sensor("s_bitter", "bitter", [104])],
        actuators=[Actuator("a_ext", "proboscis_extension", MN9_L)],
    )
    s = FlySubstrate(m, nodes, body_graph=bg, readout_body_id=MN9_L)
    s.initialize()
    s.resume()
    ev = InputEvent(duration_ms=200.0, seed=1, body=BodyInput(cue_on=True, sugar_present=True))
    obs = s.step(ev)
    assert obs.body is not None and isinstance(obs.body, BodyObservation)
    assert s.body_state is not None
