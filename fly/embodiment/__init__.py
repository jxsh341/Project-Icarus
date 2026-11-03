"""Embodiment layer: closed sensorimotor loop around the SEZ connectome.

MVP scope (2026-11-03 embodiment plan, phase "minimum viable embodiment"):
3 sensor modalities (cue GNG521, sugar GRNs, bitter GRNs) gated by body
state, 1 connectome-grounded actuator (proboscis extension via MN9_L=10331,
a traced motor neuron). Leg/head actuators are NOT grounded in the SEZ
closure and are out of scope. No harness changes: the loop drives the frozen
simulate_lif via its stimulated/stimulated2/stimulated3 ports.
"""
from .body_graph import BodyGraph, BodyState, default_body_graph
from .sensorimotor_loop import SensorimotorLoop

__all__ = ["BodyGraph", "BodyState", "SensorimotorLoop", "default_body_graph"]
