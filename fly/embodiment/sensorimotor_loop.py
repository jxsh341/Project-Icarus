"""Closed sensorimotor loop: body state -> sensory drive -> SEZ LIF -> MN9_L -> body state.

One step = one 1000 ms LIF trial (matching the phase-2/4/5/6 trial granularity).
The frozen simulate_lif is used unmodified: cue on the `stimulated` port,
sugar on `stimulated2`, bitter on `stimulated3`, each with its own rate.
Deterministic per (episode_seed, step).
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from .body_graph import (CUE_GRNS, DRIVE_HZ, MN9_L, BodyGraph, BodyState,
                         default_body_graph)

BASE = Path(__file__).resolve().parents[2] / "data" / "processed" / "neuprint_snapshots" / "run-007"
EPISODE_MS = 1000.0


class SensorimotorLoop:
    def __init__(self, body: BodyGraph | None = None,
                 matrix=None, nodes=None, params: LIFParams | None = None):
        self.body = body or default_body_graph()
        if matrix is None:
            matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
        if nodes is None:
            nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
        self.matrix, self.nodes = matrix, nodes
        # cue port rate = DRIVE_HZ, matching phase5 cosugar trials
        self.params = params or dataclasses.replace(LIFParams(), r_poisson_Hz=DRIVE_HZ)

    def step(self, state: BodyState, seed: int) -> dict:
        rates = self.body.sensor_rates(state)
        res = simulate_lif(
            self.matrix, self.nodes, self.params, EPISODE_MS,
            stimulated=CUE_GRNS if rates["cue"] > 0 else None,
            stimulated2=self.body.sensors["sugar"].neuron_ids if rates["sugar"] > 0 else None,
            r_poisson2_Hz=rates["sugar"] if rates["sugar"] > 0 else None,
            stimulated3=self.body.sensors["bitter"].neuron_ids if rates["bitter"] > 0 else None,
            r_poisson3_Hz=rates["bitter"] if rates["bitter"] > 0 else None,
            seed=seed,
        )
        mn9_hz = float(len(res.spike_times.get(MN9_L, []))) / (EPISODE_MS / 1000.0)
        self.body.apply_actuators(state, {MN9_L: mn9_hz})
        return {
            "seed": seed, "cue_on": state.cue_on,
            "sugar_present": state.sugar_present, "sugar_rate_Hz": rates["sugar"],
            "bitter_present": state.bitter_present, "bitter_rate_Hz": rates["bitter"],
            "mn9_hz": mn9_hz, "proboscis_extension": round(state.proboscis_extension, 6),
            "sugar_detected": state.sugar_detected, "bitter_detected": state.bitter_detected,
        }

    def run_episode(self, state: BodyState, n_steps: int, episode_seed: int) -> list[dict]:
        traj = []
        for k in range(n_steps):
            traj.append(self.step(state, seed=episode_seed + k))
        return traj
