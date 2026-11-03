"""Contract tests for the embodiment MVP (closed sensorimotor loop)."""
import dataclasses

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.embodiment import BodyState, SensorimotorLoop, default_body_graph
from fly.embodiment.body_graph import (CUE_GRNS, CONTACT_THRESHOLD, DRIVE_HZ,
                                      MN9_FIRE_HZ, MN9_L)
from fly.embodiment.sensorimotor_loop import BASE, EPISODE_MS


def _loop():
    return SensorimotorLoop()


def test_sensor_rate_gating():
    body = default_body_graph()
    s = BodyState(cue_on=True, sugar_present=True, bitter_present=True,
                  proboscis_extension=0.0)
    r = body.sensor_rates(s)
    assert r == {"cue": DRIVE_HZ, "sugar": 0.0, "bitter": 0.0}  # no contact -> no transduction
    s.proboscis_extension = CONTACT_THRESHOLD
    r = body.sensor_rates(s)
    assert r["sugar"] == DRIVE_HZ and r["bitter"] == DRIVE_HZ
    s.sugar_present = False
    assert body.sensor_rates(s)["sugar"] == 0.0  # absent stimulus -> no drive even in contact


def test_open_loop_equivalence_bit_identical():
    """Forced-extended closed-loop step must equal the direct phase-5-style call."""
    loop = _loop()
    state = BodyState(cue_on=True, sugar_present=True, bitter_present=False,
                      proboscis_extension=1.0)
    row = loop.step(state, seed=4242)
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=DRIVE_HZ)
    sugar = loop.body.sensors["sugar"].neuron_ids
    direct = simulate_lif(loop.matrix, loop.nodes, params, EPISODE_MS,
                          stimulated=CUE_GRNS, stimulated2=sugar,
                          r_poisson2_Hz=DRIVE_HZ, seed=4242)
    direct_hz = float(len(direct.spike_times.get(MN9_L, []))) / (EPISODE_MS / 1000.0)
    assert row["mn9_hz"] == direct_hz


def test_contingency_no_taste_without_extension():
    loop = _loop()
    retracted = loop.step(BodyState(cue_on=True, sugar_present=True,
                                    proboscis_extension=0.0), seed=777)
    extended = loop.step(BodyState(cue_on=True, sugar_present=True,
                                   proboscis_extension=1.0), seed=777)
    assert retracted["sugar_rate_Hz"] == 0.0 and extended["sugar_rate_Hz"] == DRIVE_HZ
    assert retracted["mn9_hz"] < extended["mn9_hz"]
    assert extended["mn9_hz"] >= MN9_FIRE_HZ  # innate boundary holds through the loop


def test_actuator_drives_extension_and_detection():
    loop = _loop()
    state = BodyState(cue_on=True, sugar_present=True, proboscis_extension=0.0)
    # first step: no contact -> MN9 low -> extension stays 0
    r0 = loop.step(state, seed=99)
    assert r0["proboscis_extension"] == 0.0 and not r0["sugar_detected"]
    # experimenter extends the proboscis -> contact -> sugar transduced -> MN9 fires
    state.proboscis_extension = 1.0
    r1 = loop.step(state, seed=100)
    assert r1["sugar_detected"] and r1["mn9_hz"] >= MN9_FIRE_HZ


def test_episode_deterministic():
    a = _loop().run_episode(BodyState(cue_on=True, sugar_present=True), 5, episode_seed=1234)
    b = _loop().run_episode(BodyState(cue_on=True, sugar_present=True), 5, episode_seed=1234)
    assert a == b and len(a) == 5
