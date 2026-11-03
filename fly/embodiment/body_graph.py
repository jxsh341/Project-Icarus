"""Body morphology graph for the SEZ embodiment MVP.

Discrete body state (per the plan's risk mitigation: start discrete, no
continuous physics). Sensors transduce world+body state into Poisson drive
rates for their connectome GRN populations; the actuator maps MN9_L firing
to proboscis extension.

Sensorimotor contingency (the core of the plan): sugar/bitter are only
transduced when the proboscis is extended to contact (extension >= 0.5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DRIVE_HZ = 200.0                 # drive rate when a stimulus is transduced
CONTACT_THRESHOLD = 0.5          # proboscis extension needed for contact
MN9_FIRE_HZ = 41.5               # innate feeding boundary (TECHNICAL_REPORT: MN9_L >= 41.5 Hz iff sugar & no bitter)
CUE_GRNS = [15957, 16327]        # GNG521_L/R (phase2 taskB cue)
MN9_L = 10331                    # traced motor neuron, readout == proboscis actuator
EXT_STEP_GAIN = 0.5              # first-order extension update per 1 s step

SNAP = Path(__file__).resolve().parents[2] / "data" / "processed" / "neuprint_snapshots"


@dataclass
class BodyState:
    cue_on: bool = False
    sugar_present: bool = False
    bitter_present: bool = False
    proboscis_extension: float = 0.0
    sugar_detected: bool = field(default=False)
    bitter_detected: bool = field(default=False)

    def contact(self) -> bool:
        return self.proboscis_extension >= CONTACT_THRESHOLD


@dataclass
class Sensor:
    sensor_id: str
    modality: str            # 'cue' | 'sugar' | 'bitter'
    neuron_ids: list[int]


@dataclass
class Actuator:
    actuator_id: str
    modality: str            # 'proboscis_extension'
    neuron_id: int           # MN9_L


class BodyGraph:
    def __init__(self, sensors: list[Sensor], actuators: list[Actuator]):
        self.sensors = {s.modality: s for s in sensors}
        self.actuators = {a.modality: a for a in actuators}

    def sensor_rates(self, state: BodyState) -> dict[str, float]:
        """World+body state -> Poisson drive rate per sensor modality."""
        c = state.contact()
        return {
            "cue": DRIVE_HZ if state.cue_on else 0.0,
            "sugar": DRIVE_HZ if (state.sugar_present and c) else 0.0,
            "bitter": DRIVE_HZ if (state.bitter_present and c) else 0.0,
        }

    def detected(self, state: BodyState) -> tuple[bool, bool]:
        c = state.contact()
        return state.sugar_present and c, state.bitter_present and c

    def apply_actuators(self, state: BodyState, motor_hz: dict[int, float]) -> BodyState:
        """MN9_L firing drives proboscis extension (first-order, damped, clamped)."""
        ext = state.proboscis_extension
        target = 1.0 if motor_hz.get(MN9_L, 0.0) >= MN9_FIRE_HZ else 0.0
        ext = min(1.0, max(0.0, ext + (target - ext) * EXT_STEP_GAIN))
        state.proboscis_extension = ext
        state.sugar_detected, state.bitter_detected = self.detected(state)
        return state


def default_body_graph() -> BodyGraph:
    grn = json.loads((SNAP / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    bitter = [r["bodyId"] for r in grn["bitter_R"]]
    sensors = [
        Sensor("cue_gng521", "cue", CUE_GRNS),
        Sensor("labellum_sugar", "sugar", sugar),
        Sensor("labellum_bitter", "bitter", bitter),
    ]
    actuators = [Actuator("proboscis", "proboscis_extension", MN9_L)]
    return BodyGraph(sensors, actuators)
