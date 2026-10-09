"""WP-L4a: EligibilitySignRule - decoupled eligibility-then-sign mechanism.

Phase 4 design (registered 2026-10-09): the conflation check found
gate_on controlled coincidence-opening, application, AND sign.
This rule decouples them:

- ELIGIBILITY accumulates from whatever coincidence actually fires
  (sugar-recruited partners, per the reachability census - Q-B).
- SIGN is applied at apply() time as a scalar, from a separate
  source (the aversive phase / PPL pathway), to whatever
  eligibility is live.
- _pending persists across the phase boundary WITHIN a trial.

DECAY TIMEBASE (reviewer check, resolved by design): this rule has
NO decay term. The L3c lambda (per-trial, calibrated against Task
B's between-trial regression timing) does NOT carry over into this
rule - applying it between intra-trial phases would silently erode
eligibility on a timescale it was never calibrated for. Eligibility
survives the sugar->bitter phase gap fully intact (pinned by
test_no_decay_between_phases_within_trial). If a decay term is
ever needed here it must be calibrated against THIS design's own
measured data, per the standing rule.

Semantics: V_CLIP - negative deltas floor at zero, sign never
flips, stored zeros survive (the WP1 eliminate_zeros contract).

CLAIM BOUNDARY (reviewer note, on record): these tests verify
MECHANISM wiring on synthetic data. Real coverage of the 9
untouched partners is WP-L4b's empirical question - registered,
not claimed here.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from fly.plasticity import PlasticityConfig, Semantics


class EligibilitySignRule:
    """Eligibility-then-sign rule (Phase 4, decoupled).

    observe_rate_pair: accumulates eligibility (contrast), gated by
    nothing - whichever populations co-fire drive it.
    apply(weight, sign): applies eta * sign * accumulated contrast
    per edge with V_CLIP floors; flushes _pending.
    """

    def __init__(self, eta: float, w_max: float):
        self._base_cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_CLIP,
                                          w_max=w_max)
        self._pending: dict[tuple[int, int], float] = {}

    @property
    def config(self):
        return self._base_cfg

    def _has_structural_edge(self, w, pre, post):
        w = w.tocsr()
        return w[pre, post] != 0 or (pre, post) in self._zero_structural(w)

    def _zero_structural(self, w):
        coo = w.tocoo()
        return {(int(r), int(c)) for r, c, v in zip(coo.row, coo.col, coo.data)
                if v == 0.0}

    def observe_rate_pair(self, pre: int, post: int, weight: sparse.csr_matrix,
                          x_hz: float, y_hz: float) -> None:
        """Accumulate eligibility from a coincidence event. Structural
        edges only (fixed anatomy; stored zeros count as structure)."""
        w = weight.tocsr()
        coo = w.tocoo()
        present = (int(pre), int(post)) in {(int(r), int(c))
                                            for r, c in zip(coo.row, coo.col)}
        if not present:
            return
        key = (int(pre), int(post))
        self._pending[key] = self._pending.get(key, 0.0) + x_hz * y_hz

    def pending_count(self) -> int:
        return len(self._pending)

    def pending_edge(self, key: tuple[int, int]) -> float:
        return self._pending.get(key, 0.0)

    def apply(self, weight: sparse.csr_matrix, sign: int | None):
        """Apply sign * eta * eligibility per edge; V_CLIP floors.

        sign=None: eligibility NOT flushed - the phase boundary case
        (accumulation continues; the caller applies sign later).
        sign=+1/-1: apply and flush.
        """
        if sign is None:
            return weight
        if not self._pending:
            return weight
        cfg = self._base_cfg
        coo = weight.tocoo(copy=True)
        pos_of = {(int(r), int(c)): k for k, (r, c) in enumerate(zip(coo.row, coo.col))}
        data = coo.data.astype(float).copy()
        for (i, j), c in self._pending.items():
            dw = cfg.eta * sign * c
            k = pos_of.get((i, j))
            if k is None:
                continue
            w0 = float(data[k])
            new = w0 + dw
            # V_CLIP: floor at the zero crossing; zeroed edges stay dead
            if w0 == 0.0:
                new = 0.0
            elif w0 > 0 and new < 0:
                new = 0.0
            elif w0 < 0 and new > 0:
                new = 0.0
            new = float(np.clip(new, -cfg.w_max, cfg.w_max))
            data[k] = new
        self._pending = {}
        out = sparse.coo_matrix((data, (coo.row, coo.col)), shape=weight.shape).tocsr()
        out.sort_indices()
        return out
