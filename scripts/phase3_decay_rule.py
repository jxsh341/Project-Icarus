"""WP-L3c: DecayHebbianRule - eligibility-decay variant of the frozen L1 rule.

D-4 (registered): consolidation re-scoped to the rule. Per-edge
eligibility trace with per-trial decay lam (CALIBRATED band
[0.70, 0.807] from Task B's own measured timing; gamma pinned = 1):

    e <- lam * e + c_t     (c_t = this trial's per-edge contrast, in eta*x*y units)
    dw  = eta * e_t        (per-trial increment = the full trace value)

Closed form vs frozen L1: L1's dw = eta * c_t per trial (weight
after t trials = eta * sum c_k). Here each trial adds eta * e_t, so
trial 1 (e=0 start) produces IDENTICAL dw to L1 (pinned by test) and
subsequent increments grow sub-linearly as e saturates toward
c/(1-lam).

The frozen L1 rule is UNTOUCHED. The wrapper proxies the base
rule's config (eta/semantics/w_max) and its structural-edge filter,
holds its own pending contrasts + trace, and applies trace-based
deltas itself. TrainingRun's flow (observe_rate_pair -> apply) is
satisfied by the same signatures as the base rule.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from fly.plasticity import HebbianRule


class DecayHebbianRule:
    """Eligibility-decay wrapper around the frozen L1 HebbianRule.

    lam = per-trial trace decay (registry D-4: band [0.70, 0.807],
    gamma pinned = 1). First trial identical to L1; later trials
    update from the decayed, saturating trace.
    """

    def __init__(self, base_rule: HebbianRule, lam: float):
        if not 0.0 < lam < 1.0:
            raise ValueError(f"lam must lie in (0,1), got {lam}")
        self.base = base_rule
        self.lam = lam
        self.trace: dict[tuple[int, int], float] = {}
        self._pending: dict[tuple[int, int], float] = {}

    # proxied config surface (TrainingRun reads .config for eta/semantics)
    @property
    def config(self):
        return self.base.config

    def observe_rate_pair(self, pre: int, post: int, weight: sparse.csr_matrix,
                          x_hz: float, y_hz: float) -> None:
        """Record this trial's contrast per edge (same structural-edge
        restriction as the base rule, via its filter)."""
        w = weight.tocsr()
        if not self.base._has_structural_edge(w, pre, post):
            return
        key = (int(pre), int(post))
        self._pending[key] = self._pending.get(key, 0.0) + x_hz * y_hz

    def apply(self, weight: sparse.csr_matrix) -> sparse.csr_matrix:
        """Fold age-discounted deltas into the matrix (returns NEW matrix).

        Registered semantics (D-4, THE mechanism): the per-trial
        increment for an edge is its current contrast discounted by
        the edge's consecutive-observation age:

            dw_t = eta * lam^(n-1) * c_t     (n = observation count)

        Properties (pinned by tests): trial 1 (discount=1) identical
        to L1; cumulative growth = eta * sum_k lam^(k-1) * c =
        eta*c*(1-lam^n)/(1-lam), BOUNDED by eta*c/(1-lam) - strictly
        sub-linear vs L1's eta*c*n; weights never decrease
        (potentiative-only, V_MAG-compatible); the incremental
        contribution at observation n is lam^(n-1) of contrast -
        <5% by n=15 for lam<=0.807, exactly the calibrated
        consolidation criterion. NOTE: the alternative 'apply the
        full accumulated trace every trial' (dw = eta*e_t) was
        implemented first and REFUTED BY TEST - it outgrows L1
        quadratically (each trial re-adds the whole trace); the
        test caught it before any real run.
        """
        if not self._pending:
            return weight
        cfg = self.base.config
        coo = weight.tocoo(copy=True)
        pos_of = {(int(r), int(c)): k for k, (r, c) in enumerate(zip(coo.row, coo.col))}
        data = coo.data.astype(float).copy()
        for (i, j), c in self._pending.items():
            prev = self.trace.get((i, j))
            if prev is None:
                self.trace[(i, j)] = {"c": c, "n": 1}
                discount = 1.0
            else:
                prev["n"] += 1
                discount = self.lam ** (prev["n"] - 1)
            dw = cfg.eta * discount * c
            k = pos_of.get((i, j))
            if k is None:
                continue
            w_new = data[k] + dw
            if abs(w_new) > cfg.w_max:
                w_new = cfg.w_max if w_new > 0 else -cfg.w_max
            data[k] = w_new
        self._pending = {}
        out = sparse.coo_matrix((data, (coo.row, coo.col)), shape=weight.shape).tocsr()
        out.sort_indices()
        return out
