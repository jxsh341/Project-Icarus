# Subsystem API v1.0.0 — stable entry point (`fly/api.py`)

One facade over the foundational internals. **Additive only**: frozen
experiment harnesses never import `fly.api`; their sha-pinned behavior is
untouched (full suite still pins them). Everything below is versioned:
`API_VERSION = "1.0.0"`, `SCHEMA_VERSION = 1`. Any payload with a different
`schema_version` is rejected with `SchemaError` (no silent upgrades).

## Entry point

```python
from fly.api import FlySubstrate
sub = FlySubstrate.from_snapshot()          # run-007 frozen snapshot
# or: FlySubstrate(matrix, node_ids, lif_params=..., body_graph=..., readout_body_id=...)
```

`FlySubstrate` wraps one sparse weight matrix + node ids + LIF params +
optional `BodyGraph` (embodiment) + a `LearningController`.

## Inputs — versioned input/event schema

`InputEvent(schema_version=1, duration_ms, seed, ports, body)` with
`StimulusPort(name, body_ids, rate_hz, slot∈{1,2,3}, role∈{cue,drive,gate})`
and `BodyInput(cue_on, sugar_present, bitter_present)`. `slot` maps to the
`simulate_lif` stimulated/stimulated2/stimulated3 populations; `role="cue"`
ports receive plasticity observations. `body` wires the embodiment: the
body graph's sensors become stimulus ports per `BodyState`. Round-trip:
`InputEvent.from_dict(ev.to_dict()) == ev`; foreign versions raise.

## Outputs — standardised output contract

`Observation(schema_version=1, seed, duration_ms, spike_counts{body_id:int},
rates_hz{body_id:Hz}, n_spikes, trial_index, weight_hash, body|None)`.
JSON-serialisable (`to_dict` stringifies dict keys); `from_dict` validates
the version. `weight_hash` is `fly.training.weight_matrix_hash` (16-hex) so
observations are auditable against checkpoints.

## Learning — explicit learning-control interface

`sub.learning` is a `LearningController`: `arm(config=None)` (default =
frozen experiment config `PlasticityConfig(eta=1e-4, V_CLIP, w_max=766)`),
`disarm()`, `.enabled`, `.config_hash()`. **Disarmed by default.**
`sub.step(event)` never learns; `sub.run_trial(event)` applies rate-form
Hebbian observations on cue→1-hop structural edges only when armed (same
semantics as `TrainingRun`), then the stability guard — a fired guard
raises `LifecycleError`. Plasticity never creates edges.

## Persistence — documented runtime save/restore

`sub.save_checkpoint(dir)` writes `manifest.json` (api_version,
schema_version, weight_hash, file list), `weights.npz`, `nodes.npy`,
`state.json` (phase, trial_index, lif params, learning config, body).
`FlySubstrate.load_checkpoint(dir)` verifies both schema versions and the
weight hash against the manifest — tampered weights raise `SchemaError`.

## State exchange — defined import/export semantics

`sub.export_state()` → JSON-safe dict: matrix as COO triplets
(`{format:"coo", shape, row, col, data}`), node ids, all dataclasses as
plain dicts, learning config (semantics as its value), phase, trial_index,
weight_hash. `FlySubstrate.import_state(d)` validates schema_version and
the weight hash, then rebuilds. Import/export is lossless at the
weight-hash level (verified in tests).

## Lifecycle — initialize / pause / resume / reset / shutdown

State machine `Phase`: CREATED → INITIALIZED → RUNNING ⇄ PAUSED →
SHUTDOWN (terminal). `initialize()` snapshots the pristine matrix;
`reset()` restores it and zeroes `trial_index`; `pause()`/`resume()` gate
execution; `shutdown()` forbids everything. Illegal transitions raise
`LifecycleError`. `step`/`run_trial` require RUNNING.

## Verification

`tests/test_api.py` (10 tests): schema round-trips + version rejection,
determinism, lifecycle legality, learning on/off weight-hash deltas,
reset-to-pristine, checkpoint save/load incl. tamper detection, state
export/import losslessness, body wiring. Sanity-checked on the real
snapshot: pristine weight hash `384406e9278ae0c0` reproduced, 336,245
stored synapses exported.
