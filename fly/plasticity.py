"""FLY-LEARN-001 WP1: experience-dependent plasticity rules.

The ONLY learning mechanism Phase 2 may add to the frozen substrate.
L0 (no plasticity) is the identity rule: a run with plasticity disabled
must be bit-identical to Phase 1 dynamics.

Design decisions (docs/FLY_LEARN_001_DECISIONS.md, registry v2):
- D3: three NAMED semantics for composing Hebbian updates with signed
  weights, because the protocol's `dw = eta * x_i * y_j` is ambiguous
  on a signed matrix. V_MAG (default) grows |w| and preserves sign -
  the NT->sign mapping is a validated per-presynaptic property
  (WP6b/WP6c) and LTP must not silently override it. V_SIGNED adds to
  the signed value and may cross zero (an inhibitory synapse can turn
  excitatory) - biologically aggressive, registered-arm only.
  V_CLIP adds to the signed value but freezes at the zero crossing.
- D5: PlasticityConfig has NO defaults on the read side; construction
  with any field unset raises, and every field is captured in the
  content hash so a config is fully identified by its hash.
- D6: StabilityThresholds carry the pre-registered stability limits
  (spike ceiling, spontaneous-rate ceiling, inhibitory-drift ceiling);
  PlasticityGuard.check() returns None on a healthy trial and a
  reason string naming the crossed threshold otherwise.

Units: eta is per-(pre,post) coincidence event; a potentiation event
contributes eta * x * y where x, y are the pre/post firing rates in
spikes/s observed at the event. Weights are synapse-count scale
(median 2, p99 78, max 766 on run-007).
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import sparse


class Semantics(enum.Enum):
    """How a Hebbian update composes with a signed weight."""

    V_MAG = "v_mag"      # |w| <- |w| + eta*x*y ; sign preserved (default)
    V_SIGNED = "v_signed"  # w <- w + eta*x*y ; zero-crossing allowed
    V_CLIP = "v_clip"    # w <- w + eta*x*y ; frozen at zero crossing


@dataclasses.dataclass(frozen=True)
class PlasticityConfig:
    """Full specification of one plasticity rule instance.

    No read-side defaults (D5): every field is required. Frozen dataclass;
    clone via dataclasses.replace(cfg, ...).
    """

    eta: float
    semantics: Semantics
    w_max: float

    def __post_init__(self) -> None:
        # Validate on construction: fail fast on nonsense configs.
        if self.eta <= 0:
            raise ValueError(f"eta must be > 0, got {self.eta}")
        if self.w_max <= 0:
            raise ValueError(f"w_max must be > 0, got {self.w_max}")
        if not isinstance(self.semantics, Semantics):
            raise ValueError(f"semantics must be a Semantics member, got {self.semantics!r}")

    def content_hash(self) -> str:
        payload = {
            "eta": repr(self.eta),
            "semantics": self.semantics.value,
            "w_max": repr(self.w_max),
        }
        blob = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self) | {"semantics": self.semantics.value}, sort_keys=True)


@dataclasses.dataclass(frozen=True)
class StabilityThresholds:
    """D6: pre-registered stability limits (Phase 1 anchors).

    max_spikes_per_trial: 150_000 = 4x the signed-run maximum
      (37,560 on run-007 at (200,200) driven), 4x below the all-pos
      epileptiform reference (618k).
    spontaneous_rate_hz: 5.0 - Phase 1 spontaneous is 0 spikes across
      30 trials; anything above 5 Hz mean population rate in a no-drive
      trial is runaway.
    inh_weight_drift_frac: 0.20 - inhibitory |w| mass moving more than
      20% from baseline without a compensating mechanism is instability.
    """

    max_spikes_per_trial: int
    spontaneous_rate_hz: float
    inh_weight_drift_frac: float


@dataclasses.dataclass
class PlasticityGuard:
    """Halts a training run when a pre-registered threshold is crossed."""

    thresholds: StabilityThresholds

    def check(
        self,
        trial_spikes: int,
        spontaneous_rate_hz: Optional[float] = None,
        inh_weight_drift_frac: Optional[float] = None,
    ) -> Optional[str]:
        if trial_spikes > self.thresholds.max_spikes_per_trial:
            return f"max_spikes_per_trial exceeded: {trial_spikes} > {self.thresholds.max_spikes_per_trial}"
        if spontaneous_rate_hz is not None and spontaneous_rate_hz > self.thresholds.spontaneous_rate_hz:
            return f"spontaneous_rate_hz exceeded: {spontaneous_rate_hz} > {self.thresholds.spontaneous_rate_hz}"
        if inh_weight_drift_frac is not None and inh_weight_drift_frac > self.thresholds.inh_weight_drift_frac:
            return f"inh_weight_drift_frac exceeded: {inh_weight_drift_frac} > {self.thresholds.inh_weight_drift_frac}"
        return None


class HebbianRule:
    """Pairwise Hebbian plasticity with named signed-weight semantics.

    The rule ACCUMULATES pending updates from observed (pre, post)
    coincidences and applies them to a sparse weight matrix on
    ``apply()``. Updates live on EXISTING structural edges only -
    plasticity cannot create edges (no structural growth in Phase 2),
    it can only modify existing synapse weights, matching the
    connectome's fixed anatomy.
    """

    def __init__(self, config: PlasticityConfig) -> None:
        if not isinstance(config, PlasticityConfig):
            raise TypeError(f"config must be PlasticityConfig, got {type(config)!r}")
        self.config = config
        # pending[abs_edge_index] -> accumulated delta in eta*x*y units
        # keys are (row, col) so the rule is matrix-object independent
        self._pending: dict[tuple[int, int], float] = {}

    # -- observation --------------------------------------------------------

    @staticmethod
    def _has_structural_edge(w: sparse.csr_matrix, pre: int, post: int) -> bool:
        """True iff (pre, post) is stored in the matrix STRUCTURE.

        Deliberately value-blind: under V_SIGNED an edge can transiently
        hold exactly 0.0, and that edge must remain learnable - a stored
        zero is a synapse that exists with no weight, not a missing
        synapse. Only the indptr/indices structure is authoritative.
        """
        lo, hi = w.indptr[pre], w.indptr[pre + 1]
        return post in w.indices[lo:hi]

    def observe(self, pre: int, post: int, weight: sparse.csr_matrix) -> None:
        """Record one coincidence event between pre and post.

        The (pre, post) edge must exist structurally in the current
        weight matrix; x=y=1 spike is the unit event. Deltas accumulate
        in config.eta units per event and compose at apply() time.
        """
        w = weight.tocsr()
        if not self._has_structural_edge(w, pre, post):
            # plasticity cannot create a structural edge (fixed anatomy)
            return
        key = (int(pre), int(post))
        self._pending[key] = self._pending.get(key, 0.0) + self.config.eta

    def observe_rate_pair(self, pre: int, post: int, weight: sparse.csr_matrix,
                          x_hz: float, y_hz: float) -> None:
        """Rate-form Hebbian: one update of eta * x * y per call.

        Used by simulation drivers that track pre/post firing rates
        rather than individual coincidences. Same structural-edge
        restriction.
        """
        w = weight.tocsr()
        if not self._has_structural_edge(w, pre, post):
            return
        key = (int(pre), int(post))
        self._pending[key] = self._pending.get(key, 0.0) + self.config.eta * x_hz * y_hz

    # -- application --------------------------------------------------------

    def apply(self, weight: sparse.csr_matrix) -> sparse.csr_matrix:
        """Fold accumulated deltas into the weight matrix.

        Returns a NEW matrix; the input is never mutated. Semantics per
        config.semantics (D3). All updates respect w_max on magnitude.
        """
        if not self._pending:
            return weight
        cfg = self.config
        # Operate on COO data arrays directly: no scalar CSR assignment
        # (whose stored-zero semantics are version-dependent) and NO
        # eliminate_zeros() - stored zeros are part of the structure and
        # must survive so V_SIGNED can potentiate through them.
        coo = weight.tocoo(copy=True)
        pos_of = {(int(r), int(c)): k for k, (r, c) in enumerate(zip(coo.row, coo.col))}
        new_data = coo.data.copy()
        for (row, col), delta in self._pending.items():
            pos = pos_of.get((row, col))
            if pos is None:
                continue  # edge vanished from this matrix version; drop
            w0 = float(coo.data[pos])
            if cfg.semantics is Semantics.V_MAG:
                new = np.sign(w0) * min(abs(w0) + delta, cfg.w_max)
            elif cfg.semantics is Semantics.V_SIGNED:
                new = np.clip(w0 + delta, -cfg.w_max, cfg.w_max)
            elif cfg.semantics is Semantics.V_CLIP:
                if w0 == 0.0:
                    new = 0.0  # a zeroed edge is dead; stays dead
                else:
                    new = w0 + delta
                    if w0 < 0 and new > 0:
                        new = 0.0
                    elif w0 > 0 and new < 0:
                        new = 0.0
                    new = float(np.clip(new, -cfg.w_max, cfg.w_max))
            else:  # pragma: no cover - enum exhaustiveness
                raise ValueError(f"unknown semantics {cfg.semantics}")
            new_data[pos] = float(new)
        self._pending.clear()
        out = sparse.coo_matrix((new_data, (coo.row, coo.col)), shape=coo.shape).tocsr()
        return out

    # -- checkpointing ------------------------------------------------------

    def pending(self) -> dict[tuple[int, int], float]:
        return dict(self._pending)

    def checkpoint(self) -> str:
        """Lossless state for resume-after-interrupt."""
        return json.dumps(
            {
                "config": self.config.to_json(),
                "pending": {f"{r},{c}": d for (r, c), d in self._pending.items()},
            },
            sort_keys=True,
        )

    @classmethod
    def from_checkpoint(cls, state: str) -> "HebbianRule":
        blob = json.loads(state)
        raw = json.loads(blob["config"])
        semantics = Semantics(raw["semantics"])
        cfg = PlasticityConfig(eta=raw["eta"], semantics=semantics,
                               w_max=raw["w_max"])
        rule = cls(cfg)
        for key, delta in blob["pending"].items():
            r, c = (int(v) for v in key.split(","))
            rule._pending[(r, c)] = delta
        return rule
