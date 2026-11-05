"""fly/api.py — STABLE SUBSYSTEM ENTRY POINT (API v1.0.0, schema v1).

One facade over the foundational internals (fly.dynamics.lif.simulate_lif,
fly.embodiment, fly.plasticity, fly.training.weight_matrix_hash). Additive
only: frozen experiment harnesses do NOT import this module and are
unaffected.

Contracts (all versioned, SCHEMA_VERSION = 1):
  inputs    : InputEvent / StimulusPort / BodyInput   (versioned event schema)
  outputs   : Observation / BodyObservation           (standardised contract)
  learning  : LearningController (arm/disarm, explicit) (learning-control iface)
  persistence: FlySubstrate.save_checkpoint / load_checkpoint (documented fmt)
  state     : export_state / import_state              (defined semantics)
  lifecycle : initialize / pause / resume / reset / shutdown (state machine)
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, LIFRun, simulate_lif
from fly.embodiment.body_graph import BodyGraph, BodyState, default_body_graph, MN9_L
from fly.plasticity import (  # noqa: E402
    HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds,
)

FROZEN_PLASTICITY = PlasticityConfig(eta=1e-4, semantics=Semantics.V_CLIP, w_max=766.0)
from fly.training import weight_matrix_hash

API_VERSION = "1.0.0"
SCHEMA_VERSION = 1
BASE = Path(__file__).resolve().parents[1] / "data/processed/neuprint_snapshots/run-007"


class SchemaError(ValueError):
    """Raised when a payload's schema_version is unsupported or malformed."""


class LifecycleError(RuntimeError):
    """Raised on an illegal lifecycle transition."""


# --------------------------------------------------------------------------
# Inputs: versioned input/event schema
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class StimulusPort:
    """One named stimulus population. slot: 1/2/3 -> simulate_lif stimulated/
    stimulated2/stimulated3. role: 'cue' ports get plasticity observations
    (cue -> 1-hop, rate-form); 'drive'/'gate' are non-plastic."""
    name: str
    body_ids: tuple[int, ...]
    rate_hz: float
    slot: int = 1
    role: str = "drive"

    def to_dict(self) -> dict:
        return {"name": self.name, "body_ids": list(self.body_ids),
                "rate_hz": self.rate_hz, "slot": self.slot, "role": self.role}

    @classmethod
    def from_dict(cls, d: dict) -> "StimulusPort":
        if d.get("slot") not in (1, 2, 3):
            raise SchemaError(f"bad slot {d.get('slot')!r}")
        if d.get("role") not in ("cue", "drive", "gate"):
            raise SchemaError(f"bad role {d.get('role')!r}")
        return cls(name=str(d["name"]), body_ids=tuple(int(x) for x in d["body_ids"]),
                   rate_hz=float(d["rate_hz"]), slot=int(d["slot"]), role=str(d["role"]))


@dataclass(frozen=True)
class BodyInput:
    """Body/environment state attached to an event (embodiment wiring)."""
    cue_on: bool = False
    sugar_present: bool = False
    bitter_present: bool = False

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BodyInput":
        return cls(bool(d.get("cue_on", False)), bool(d.get("sugar_present", False)),
                   bool(d.get("bitter_present", False)))


@dataclass(frozen=True)
class InputEvent:
    """Versioned input/event schema. schema_version MUST be 1."""
    duration_ms: float = 1000.0
    seed: int = 0
    ports: tuple[StimulusPort, ...] = ()
    body: Optional[BodyInput] = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "duration_ms": self.duration_ms,
                "seed": self.seed, "ports": [p.to_dict() for p in self.ports],
                "body": self.body.to_dict() if self.body else None}

    @classmethod
    def from_dict(cls, d: dict) -> "InputEvent":
        v = d.get("schema_version")
        if v != SCHEMA_VERSION:
            raise SchemaError(f"InputEvent schema_version {v!r} != {SCHEMA_VERSION}")
        return cls(duration_ms=float(d.get("duration_ms", 1000.0)), seed=int(d.get("seed", 0)),
                   ports=tuple(StimulusPort.from_dict(p) for p in d.get("ports", [])),
                   body=BodyInput.from_dict(d["body"]) if d.get("body") else None,
                   schema_version=v)


# --------------------------------------------------------------------------
# Outputs: standardised output contract
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class BodyObservation:
    proboscis_extension: float = 0.0
    sugar_detected: bool = False
    bitter_detected: bool = False

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BodyObservation":
        return cls(float(d.get("proboscis_extension", 0.0)),
                   bool(d.get("sugar_detected", False)), bool(d.get("bitter_detected", False)))


@dataclass(frozen=True)
class Observation:
    """Standardised output contract: spike counts + rates + body + provenance."""
    seed: int
    duration_ms: float
    spike_counts: dict[int, int]          # body_id -> spike count
    rates_hz: dict[int, float]            # body_id -> Hz
    n_spikes: int
    trial_index: int
    weight_hash: str
    body: Optional[BodyObservation] = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "seed": self.seed,
                "duration_ms": self.duration_ms,
                "spike_counts": {str(k): int(v) for k, v in self.spike_counts.items()},
                "rates_hz": {str(k): float(v) for k, v in self.rates_hz.items()},
                "n_spikes": self.n_spikes, "trial_index": self.trial_index,
                "weight_hash": self.weight_hash,
                "body": self.body.to_dict() if self.body else None}

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        v = d.get("schema_version")
        if v != SCHEMA_VERSION:
            raise SchemaError(f"Observation schema_version {v!r} != {SCHEMA_VERSION}")
        return cls(seed=int(d["seed"]), duration_ms=float(d["duration_ms"]),
                   spike_counts={int(k): int(v2) for k, v2 in d["spike_counts"].items()},
                   rates_hz={int(k): float(v2) for k, v2 in d["rates_hz"].items()},
                   n_spikes=int(d["n_spikes"]), trial_index=int(d["trial_index"]),
                   weight_hash=str(d["weight_hash"]),
                   body=BodyObservation.from_dict(d["body"]) if d.get("body") else None,
                   schema_version=v)


# --------------------------------------------------------------------------
# Learning: explicit learning-control interface
# --------------------------------------------------------------------------

class LearningController:
    """Explicit learning control. Disarmed by default: probes never learn."""

    def __init__(self, guard: Optional[PlasticityGuard] = None):
        self.rule: Optional[HebbianRule] = None
        self.guard = guard or PlasticityGuard(StabilityThresholds(150_000, 5.0, 0.20))

    @property
    def enabled(self) -> bool:
        return self.rule is not None

    def arm(self, config: Optional[PlasticityConfig] = None) -> None:
        self.rule = HebbianRule(config or FROZEN_PLASTICITY)

    def disarm(self) -> None:
        self.rule = None

    def config_hash(self) -> str:
        if self.rule is None:
            return "disarmed"
        return self.rule.config.content_hash()

    def to_dict(self) -> dict:
        cfg = None
        if self.rule is not None:
            c = self.rule.config
            cfg = {"eta": c.eta, "semantics": c.semantics.value, "w_max": c.w_max}
        return {"armed": self.enabled, "config": cfg, "config_hash": self.config_hash()}

    @classmethod
    def from_dict(cls, d: dict, guard: Optional[PlasticityGuard] = None) -> "LearningController":
        lc = cls(guard)
        if d.get("armed"):
            c = d["config"]
            lc.arm(PlasticityConfig(eta=float(c["eta"]), semantics=Semantics(c["semantics"]),
                                    w_max=float(c["w_max"])))
        return lc


# --------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------

class Phase(Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTDOWN = "shutdown"


# --------------------------------------------------------------------------
# The subsystem
# --------------------------------------------------------------------------

class FlySubstrate:
    """Stable entry point: callable LIF + embodiment over one weight matrix."""

    def __init__(self, matrix: sparse.csr_matrix, node_ids: list[int],
                 lif_params: Optional[LIFParams] = None,
                 body_graph: Optional[BodyGraph] = None,
                 readout_body_id: int = MN9_L):
        self.matrix = matrix.tocsr()
        self.node_ids = list(node_ids)
        self.lif_params = lif_params or LIFParams()
        self.body_graph = body_graph
        self.readout_body_id = readout_body_id
        self.learning = LearningController()
        self.body_state: Optional[BodyState] = None
        self.phase = Phase.CREATED
        self.trial_index = 0
        self._pristine: Optional[sparse.csr_matrix] = None

    @classmethod
    def from_snapshot(cls, run_dir: Path | str = BASE, **kw) -> "FlySubstrate":
        run_dir = Path(run_dir)
        m = sparse.load_npz(run_dir / "connectivity_matrix_signed.npz").tocsr()
        nodes = np.load(run_dir / "connectivity_nodes.npy").tolist()
        return cls(m, nodes, **kw)

    # -- lifecycle ------------------------------------------------------------

    def initialize(self) -> None:
        if self.phase != Phase.CREATED:
            raise LifecycleError(f"initialize() from {self.phase.value}")
        self._pristine = self.matrix.copy()
        if self.body_graph is not None:
            self.body_state = BodyState()
        self.phase = Phase.INITIALIZED

    def _require(self, *allowed: Phase) -> None:
        if self.phase == Phase.SHUTDOWN:
            raise LifecycleError("subsystem is shut down")
        if self.phase not in allowed:
            raise LifecycleError(f"operation requires { [p.value for p in allowed] }, in {self.phase.value}")

    def pause(self) -> None:
        self._require(Phase.RUNNING)
        self.phase = Phase.PAUSED

    def resume(self) -> None:
        self._require(Phase.PAUSED, Phase.INITIALIZED)
        self.phase = Phase.RUNNING

    def reset(self) -> None:
        """Restore the post-initialize weight matrix and body; trial_index -> 0."""
        self._require(Phase.INITIALIZED, Phase.RUNNING, Phase.PAUSED)
        assert self._pristine is not None
        self.matrix = self._pristine.copy()
        if self.body_graph is not None:
            self.body_state = BodyState()
        self.trial_index = 0
        self.phase = Phase.INITIALIZED

    def shutdown(self) -> None:
        if self.phase == Phase.SHUTDOWN:
            raise LifecycleError("already shut down")
        self.phase = Phase.SHUTDOWN

    # -- execution ------------------------------------------------------------

    def _ports_from_body(self, body_in: BodyInput) -> list[StimulusPort]:
        assert self.body_graph is not None
        st = BodyState(cue_on=body_in.cue_on, sugar_present=body_in.sugar_present,
                       bitter_present=body_in.bitter_present)
        rates = self.body_graph.sensor_rates(st)
        ports = []
        for modality in ("cue", "sugar", "bitter"):
            if rates[modality] > 0:
                ids = self.body_graph.sensors[modality].neuron_ids
                slot = {"cue": 1, "sugar": 2, "bitter": 3}[modality]
                role = "cue" if modality == "cue" else "drive"
                ports.append(StimulusPort(modality, tuple(ids), rates[modality], slot, role))
        return ports

    def _run(self, event: InputEvent) -> LIFRun:
        ports = list(event.ports)
        if event.body is not None:
            if self.body_graph is None:
                raise SchemaError("event carries body input but subsystem has no body_graph")
            ports += self._ports_from_body(event.body)
        by_slot: dict[int, list[int]] = {1: [], 2: [], 3: []}
        rate: dict[int, float] = {}
        for p in ports:
            if p.rate_hz <= 0:
                continue
            by_slot[p.slot].extend(p.body_ids)
            rate[p.slot] = p.rate_hz
        params = dataclasses.replace(self.lif_params, r_poisson_Hz=rate.get(1, self.lif_params.r_poisson_Hz))
        return simulate_lif(
            self.matrix, self.node_ids, params, event.duration_ms,
            stimulated=by_slot[1] or None,
            stimulated2=by_slot[2] or None, r_poisson2_Hz=rate.get(2),
            stimulated3=by_slot[3] or None, r_poisson3_Hz=rate.get(3),
            seed=event.seed,
        )

    def _observe(self, event: InputEvent, result: LIFRun) -> Observation:
        counts = {nid: len(ts) for nid, ts in result.spike_times.items()}
        dur_s = event.duration_ms / 1000.0
        body_obs = None
        if event.body is not None and self.body_state is not None:
            assert self.body_graph is not None
            self.body_graph.apply_actuators(
                self.body_state, {self.readout_body_id: counts.get(self.readout_body_id, 0) / dur_s})
            body_obs = BodyObservation(self.body_state.proboscis_extension,
                                       self.body_state.sugar_detected, self.body_state.bitter_detected)
        return Observation(seed=event.seed, duration_ms=event.duration_ms,
                           spike_counts=counts,
                           rates_hz={k: v / dur_s for k, v in counts.items()},
                           n_spikes=result.n_spikes, trial_index=self.trial_index,
                           weight_hash=weight_matrix_hash(self.matrix), body=body_obs)

    def step(self, event: InputEvent) -> Observation:
        """Pure simulation step (no plasticity, regardless of learning state)."""
        self._require(Phase.RUNNING)
        if event.schema_version != SCHEMA_VERSION:
            raise SchemaError(f"InputEvent schema_version {event.schema_version!r}")
        obs = self._observe(event, self._run(event))
        self.trial_index += 1
        return obs

    def run_trial(self, event: InputEvent) -> Observation:
        """Learning step: like step(), but if learning is armed, cue-port
        coincidences (cue -> 1-hop targets, rate-form) update the weights."""
        self._require(Phase.RUNNING)
        if event.schema_version != SCHEMA_VERSION:
            raise SchemaError(f"InputEvent schema_version {event.schema_version!r}")
        result = self._run(event)
        if self.learning.enabled and self.learning.rule is not None:
            idx_of = {n: i for i, n in enumerate(self.node_ids)}
            dur_s = event.duration_ms / 1000.0
            rates = {n: len(ts) / dur_s for n, ts in result.spike_times.items()}
            cue_ports = [p for p in event.ports if p.role == "cue" and p.rate_hz > 0]
            coo = self.matrix.tocoo()
            targets: dict[int, list[int]] = {}
            for cue_id in (cid for p in cue_ports for cid in p.body_ids):
                if cue_id in idx_of:
                    ci = idx_of[cue_id]
                    lo, hi = self.matrix.indptr[ci], self.matrix.indptr[ci + 1]
                    targets[ci] = [int(self.matrix.indices[k]) for k in range(lo, hi)]
            for ci, tgts in targets.items():
                pre_id = self.node_ids[ci]
                if rates.get(pre_id, 0.0) <= 0:
                    continue
                for tj in tgts:
                    if rates.get(self.node_ids[tj], 0.0) > 0:
                        self.learning.rule.observe_rate_pair(ci, tj, self.matrix,
                                                             rates[self.node_ids[ci]],
                                                             rates[self.node_ids[tj]])
            self.matrix = self.learning.rule.apply(self.matrix).tocsr()
        obs = self._observe(event, result)
        fired = self.learning.guard.check(trial_spikes=result.n_spikes)
        if fired is not None:
            raise LifecycleError(f"stability guard fired: {fired}")
        self.trial_index += 1
        return obs

    # -- persistence: documented runtime save/restore -------------------------
    # Format (dir): manifest.json + weights.npz + nodes.npy + state.json
    # manifest pins api_version, schema_version, weight_hash; load verifies.

    def save_checkpoint(self, path: Path | str) -> Path:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        wh = weight_matrix_hash(self.matrix)
        sparse.save_npz(path / "weights.npz", self.matrix)
        np.save(path / "nodes.npy", np.array(self.node_ids, dtype=np.int64))
        (path / "state.json").write_text(json.dumps({
            "schema_version": SCHEMA_VERSION, "trial_index": self.trial_index,
            "phase": self.phase.value, "weight_hash": wh,
            "lif_params": dataclasses.asdict(self.lif_params),
            "learning": self.learning.to_dict(),
            "body": dataclasses.asdict(self.body_state) if self.body_state else None,
            "readout_body_id": self.readout_body_id,
        }, indent=1), encoding="utf-8")
        (path / "manifest.json").write_text(json.dumps({
            "api_version": API_VERSION, "schema_version": SCHEMA_VERSION,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "weight_hash": wh, "n_nodes": len(self.node_ids),
            "files": ["weights.npz", "nodes.npy", "state.json"],
        }, indent=1), encoding="utf-8")
        return path

    @classmethod
    def load_checkpoint(cls, path: Path | str) -> "FlySubstrate":
        path = Path(path)
        man = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if man.get("schema_version") != SCHEMA_VERSION:
            raise SchemaError(f"checkpoint schema_version {man.get('schema_version')!r}")
        if man.get("api_version") != API_VERSION:
            raise SchemaError(f"checkpoint api_version {man.get('api_version')!r}")
        st = json.loads((path / "state.json").read_text(encoding="utf-8"))
        if st.get("schema_version") != SCHEMA_VERSION:
            raise SchemaError("state.json schema_version mismatch")
        m = sparse.load_npz(path / "weights.npz").tocsr()
        nodes = np.load(path / "nodes.npy").tolist()
        wh = weight_matrix_hash(m)
        if wh != man.get("weight_hash") or wh != st.get("weight_hash"):
            raise SchemaError(f"weight hash mismatch on load: {wh}")
        sub = cls(m, nodes, lif_params=LIFParams(**st["lif_params"]),
                  readout_body_id=int(st["readout_body_id"]))
        sub.learning = LearningController.from_dict(st["learning"])
        sub.trial_index = int(st["trial_index"])
        sub.phase = Phase(st["phase"]) if Phase(st["phase"]) != Phase.SHUTDOWN else Phase.INITIALIZED
        sub.initialize() if sub.phase == Phase.CREATED else None
        if st.get("body"):
            sub.body_state = BodyState(**st["body"])
            sub.body_graph = sub.body_graph or default_body_graph()
        return sub

    # -- state exchange: defined import/export semantics ----------------------

    def export_state(self) -> dict:
        """Full serialisable state: matrix as COO triplets + all dataclasses as
        plain dicts. schema_version-tagged; import_state validates."""
        coo = self.matrix.tocoo()
        return {
            "schema_version": SCHEMA_VERSION, "api_version": API_VERSION,
            "matrix": {"format": "coo", "shape": list(self.matrix.shape),
                       "row": coo.row.tolist(), "col": coo.col.tolist(), "data": coo.data.tolist()},
            "node_ids": list(self.node_ids),
            "lif_params": dataclasses.asdict(self.lif_params),
            "learning": self.learning.to_dict(),
            "body": dataclasses.asdict(self.body_state) if self.body_state else None,
            "readout_body_id": self.readout_body_id,
            "trial_index": self.trial_index, "phase": self.phase.value,
            "weight_hash": weight_matrix_hash(self.matrix),
        }

    @classmethod
    def import_state(cls, d: dict) -> "FlySubstrate":
        if d.get("schema_version") != SCHEMA_VERSION:
            raise SchemaError(f"state schema_version {d.get('schema_version')!r} != {SCHEMA_VERSION}")
        md = d["matrix"]
        if md.get("format") != "coo":
            raise SchemaError(f"matrix format {md.get('format')!r} != 'coo'")
        m = sparse.coo_matrix((md["data"], (md["row"], md["col"])),
                              shape=tuple(md["shape"])).tocsr()
        sub = cls(m, [int(x) for x in d["node_ids"]], lif_params=LIFParams(**d["lif_params"]),
                  readout_body_id=int(d["readout_body_id"]))
        if weight_matrix_hash(sub.matrix) != d.get("weight_hash"):
            raise SchemaError("weight_hash mismatch on import")
        sub.learning = LearningController.from_dict(d["learning"])
        sub.trial_index = int(d["trial_index"])
        sub.phase = Phase(d["phase"]) if Phase(d["phase"]) != Phase.SHUTDOWN else Phase.INITIALIZED
        if d.get("body"):
            sub.body_state = BodyState(**d["body"])
            sub.body_graph = default_body_graph()
        return sub


__all__ = [
    "API_VERSION", "SCHEMA_VERSION", "SchemaError", "LifecycleError",
    "StimulusPort", "BodyInput", "InputEvent",
    "BodyObservation", "Observation",
    "LearningController", "Phase", "FlySubstrate",
]
