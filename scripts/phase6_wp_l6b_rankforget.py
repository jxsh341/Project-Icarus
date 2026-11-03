"""WP-L6b: rank-targeted multiplicative forgetting (FNN top-N port) - Phase 6.

Frozen by docs/PHASE_6_PREREG.md section 3. Starts from the acquired R1
checkpoint (no re-acquisition). Protocol per cycle: ONE cue-alone unlearning
trial @ 200 Hz (no drive - drive-independent by construction). After each
trial the rule applies, on every RANK_SET edge, w <- w*exp(-1/TAU0), then
w < W_EPS snaps to 0.0 (V_CLIP exact-floor semantics preserved).

RANK_SET = acquisition footprint (acquired != pristine), content-hash-pinned:
  g521: 25 edges  sha256 43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589
  g380: 158 edges sha256 27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a
Hash mismatch at launch -> halt (no run).

Module globals REPS / OUT / TRAIN_SEED_BASE / PROBE_SEED_BASE are injected by
phase6_expB_launcher.py (same pattern as the Phase 5 launcher); this file is
byte-stable once committed (sha-pinned by the launcher).

Target switch: L6B_TARGET=g521 (default) | g380.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import (HebbianRule, PlasticityConfig, PlasticityGuard,
                            Semantics, StabilityThresholds)
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
R1CK_521 = Path("results/phase2/taskB_r1/ckpt_l1_gng521_feed_0")
R1CK_380 = Path("results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0")
OUT = Path("results/phase6/wp_l6b")
JSONL_NAME = "l6b_rankforget.jsonl"
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
TAU0 = 1.0
W_EPS = 1e-9
CUE_521 = [15957, 16327]
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
UNTOUCHED = [13510, 18474, 12364, 14803, 14953, 66802, 516493, 524078, 555850]
N_CYCLES = 25
PROBE_AT = (5, 10, 15, 20, 25)
REPS = 3
TRAIN_SEED_BASE = 1_200_000
PROBE_SEED_BASE = 1_300_000
RANK_SHA_521 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"
RANK_SHA_380 = "27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a"


class RankDecayRule:
    """apply(matrix): multiplicative decay on RANK_SET edges only.

    observe_rate_pair is a NO-OP: decay is not coincidence-gated - that is
    the entire point of L6b (FNN-style direct weight decay vs L4b's
    eligibility-then-sign). V_CLIP floor preserved via the W_EPS snap.
    """

    def __init__(self, rank_edges, tau0=TAU0, w_eps=W_EPS, w_max=W_MAX):
        self.rank = list(rank_edges)
        self.tau0 = tau0
        self.w_eps = w_eps
        self._cfg = PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=w_max)

    @property
    def config(self):
        return self._cfg

    def observe_rate_pair(self, pre, post, weight, x_hz, y_hz):
        pass

    def apply(self, weight):
        coo = weight.tocoo()
        idx = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(coo.row, coo.col))}
        f = math.exp(-1.0 / self.tau0)
        data = coo.data.copy()
        for e in self.rank:
            k = idx.get(e)
            if k is None:
                continue
            v = float(data[k]) * f
            data[k] = 0.0 if v < self.w_eps else v
        out = sparse.coo_matrix((data, (coo.row, coo.col)), shape=coo.shape).tocsr()
        out.sum_duplicates()
        return out


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def main() -> int:
    target = os.environ.get("L6B_TARGET", "g521")
    if target == "g521":
        r1ck, cue, rank_sha, n_rank = R1CK_521, CUE_521, RANK_SHA_521, 25
    else:
        r1ck, cue, rank_sha, n_rank = R1CK_380, CUE_380, RANK_SHA_380, 158

    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    base_rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
    retained = TrainingRun.load(r1ck, matrix, nodes, base_rule, guard(), MN9_L)
    acquired = retained.matrix.copy()

    d = (acquired - matrix).tocoo()
    rank = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    sha = hashlib.sha256(json.dumps(rank).encode()).hexdigest()
    if sha != rank_sha or len(rank) != n_rank:
        raise RuntimeError(f"RANK_SET mismatch for {target}: {sha} n={len(rank)}")
    print(f"RANK_SET ok ({target}): {len(rank)} edges sha256={sha[:16]}...", flush=True)

    if target == "g521":
        chk = simulate_lif(acquired, nodes, lif_params, 1000.0,
                           stimulated=list(cue), stimulated2=list(sugar),
                           r_poisson2_Hz=200.0, seed=PROBE_SEED_BASE + 999)
        firing = {str(p): len(chk.spike_times.get(p, [])) for p in UNTOUCHED}
        print(f"LAUNCH SANITY: untouched partners firing under cue+sugar: "
              f"{sum(1 for v in firing.values() if v > 0)}/9", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / JSONL_NAME

    for rep in range(REPS):
        rule = RankDecayRule(rank)
        run = TrainingRun(acquired.copy(), nodes, rule, guard(), MN9_L,
                          f"l6b_{target}_r{rep}", OUT / f"ckpt_r{rep}",
                          lif_params=lif_params)
        for cyc in range(1, N_CYCLES + 1):
            seed = TRAIN_SEED_BASE + cyc
            spec = TrialSpec(trial=cyc, seed=seed, cue_body_ids=tuple(cue),
                             drive_body_ids=(), drive2_body_ids=(),
                             r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0)
            rec = run.run_trial(spec)
            run.save()
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"rep": rep, "cycle": cyc, "seed": seed,
                                     "readout_hz": rec["readout_hz"],
                                     "guard_fired": rec.get("guard_fired")}) + "\n")
            if cyc in PROBE_AT:
                for ptype, off in (("alone", 0), ("cosugar", 5000)):
                    for r2 in range(2):
                        pseed = PROBE_SEED_BASE + cyc * 100 + r2 * 10 + off
                        lif = simulate_lif(
                            run.matrix, nodes, lif_params, 1000.0,
                            stimulated=list(cue),
                            stimulated2=(list(sugar) if ptype == "cosugar" else None),
                            r_poisson2_Hz=(200.0 if ptype == "cosugar" else None),
                            seed=pseed)
                        mn9 = len(lif.spike_times.get(MN9_L, []))
                        with out.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"rep": rep, "cycle": cyc,
                                                 "ptype": ptype, "rep2": r2,
                                                 "mn9_hz": mn9}) + "\n")
        print(f"rep {rep} done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
