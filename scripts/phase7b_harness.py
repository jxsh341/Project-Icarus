"""Phase 7b P1 harness - held-out circuits: stages acquire | l6b | l4b.

Frozen by docs/PHASE_7B_PREREG.md. Stage via env PHASE7B_STAGE, pair via
PHASE7B_PAIR. Module globals OUT/R1CK/CUE/TRAIN_SEED_BASE/PROBE_SEED_BASE/REPS
are injected in memory only by phase7b_launcher.py (sha-pinned, guard G1).

acquire: from PRISTINE, 20 trials cue+sugar @200 Hz (feed direction),
         probes after trials (1,2,3,4,5,10,15,20) x {alone, cosugar} x 2 seeds.
l6b:     rank-targeted multiplicative decay (identical rule+constants to
         phase6_wp_l6b_rankforget.RankDecayRule: w<-w*e^(-1/TAU0), TAU0=1.0,
         W_EPS=1e-9 snap) from the acquired ckpt, 25 cycles cue-alone @200,
         probes at cycles 5/10/15/20/25 x {alone, cosugar} x 2.
l4b:     eligibility-then-sign (phase4_eligibility_sign_rule, identical
         protocol to phase4_wp_l4b_extinction) from the acquired ckpt:
         per cycle sugar phase (sign None) then bitter phase (sign -1),
         probes same as l6b.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import (HebbianRule, PlasticityConfig, PlasticityGuard,
                            Semantics, StabilityThresholds)
from fly.training import TrainingRun, TrialSpec

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase4_eligibility_sign_rule import EligibilitySignRule  # noqa: E402

BASE = Path("data/processed/neuprint_snapshots/run-007")
MN9_L = 10331
THETA = 41.5
W_MAX = 766.0
ETA = 1e-4
TAU0 = 1.0
W_EPS = 1e-9
N_ACQ_TRIALS = 20
ACQ_PROBE_AT = (1, 2, 3, 4, 5, 10, 15, 20)
N_CYCLES = 25
UNL_PROBE_AT = (5, 10, 15, 20, 25)
PPL_TRIO = [11618, 11900, 529516]

# injected by launcher
OUT = Path("results/phase7b/unset")
R1CK = Path("results/phase7b/unset")
CUE: list[int] = []
TRAIN_SEED_BASE = 0
PROBE_SEED_BASE = 0
REPS = 1


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def world():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    bitter = [r["bodyId"] for r in grn["bitter_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    return matrix, nodes, sugar, bitter, lif_params


def log(path: Path, rec: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def probe(run_matrix, nodes, lif_params, cue, sugar, pseed, ptype):
    lif = simulate_lif(run_matrix, nodes, lif_params, 1000.0,
                       stimulated=list(cue),
                       stimulated2=(list(sugar) if ptype == "cosugar" else None),
                       r_poisson2_Hz=(200.0 if ptype == "cosugar" else None),
                       seed=pseed)
    return len(lif.spike_times.get(MN9_L, []))


def stage_acquire() -> int:
    matrix, nodes, sugar, bitter, lif_params = world()
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "acq.jsonl"
    for rep in range(REPS):
        rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
        run = TrainingRun(matrix.copy(), nodes, rule, guard(), MN9_L,
                          f"p7b_acq_r{rep}", OUT / f"ckpt_r{rep}", lif_params=lif_params)
        for t in range(1, N_ACQ_TRIALS + 1):
            spec = TrialSpec(trial=t, seed=TRAIN_SEED_BASE + t, cue_body_ids=tuple(CUE),
                             drive_body_ids=tuple(sugar), drive2_body_ids=(),
                             r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(spec)
            run.save()
            log(jout, {"rep": rep, "trial": t, "seed": TRAIN_SEED_BASE + t,
                       "readout_hz": rec["readout_hz"], "guard_fired": rec.get("guard_fired")})
            if t in ACQ_PROBE_AT:
                for ptype, off in (("alone", 0), ("cosugar", 5000)):
                    for r2 in range(2):
                        pseed = PROBE_SEED_BASE + t * 100 + r2 * 10 + off
                        mn9 = probe(run.matrix, nodes, lif_params, CUE, sugar, pseed, ptype)
                        log(jout, {"rep": rep, "trial": t, "ptype": ptype, "rep2": r2, "mn9_hz": mn9})
        print(f"acquire rep {rep} done", flush=True)
    return 0


class RankDecayRule:
    """Identical rule+constants to phase6_wp_l6b_rankforget.RankDecayRule."""

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


def _load_acquired(matrix, nodes):
    base_rule = HebbianRule(PlasticityConfig(eta=ETA, semantics=Semantics.V_CLIP, w_max=W_MAX))
    retained = TrainingRun.load(R1CK, matrix, nodes, base_rule, guard(), MN9_L)
    return retained.matrix.copy()


def _unlearn_loop(stage: str) -> int:
    matrix, nodes, sugar, bitter, lif_params = world()
    acquired = _load_acquired(matrix, nodes)
    d = (acquired - matrix).tocoo()
    rank = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / f"{stage}.jsonl"
    n_hist = N_CYCLES if stage == "l6b" else N_CYCLES * 2
    for rep in range(REPS):
        if stage == "l6b":
            rule = RankDecayRule(rank)
        else:
            inner = EligibilitySignRule(ETA, W_MAX)
            rule = PhaseDriverRule(inner)
        run = TrainingRun(acquired.copy(), nodes, rule, guard(), MN9_L,
                          f"p7b_{stage}_r{rep}", OUT / f"ckpt_r{rep}", lif_params=lif_params)
        for cyc in range(1, N_CYCLES + 1):
            if stage == "l6b":
                spec = TrialSpec(trial=cyc, seed=TRAIN_SEED_BASE + cyc, cue_body_ids=tuple(CUE),
                                 drive_body_ids=(), drive2_body_ids=(),
                                 r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0)
                rec = run.run_trial(spec)
                run.save()
                log(jout, {"rep": rep, "cycle": cyc, "seed": TRAIN_SEED_BASE + cyc,
                           "readout_hz": rec["readout_hz"], "guard_fired": rec.get("guard_fired")})
            else:
                rule.sign = None
                s_spec = TrialSpec(trial=cyc * 2, seed=TRAIN_SEED_BASE + cyc * 2,
                                   cue_body_ids=tuple(CUE), drive_body_ids=tuple(sugar),
                                   drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(s_spec)
                run.save()
                log(jout, {"rep": rep, "cycle": cyc, "phase": "sugar", "seed": TRAIN_SEED_BASE + cyc * 2,
                           "readout_hz": rec["readout_hz"], "guard_fired": rec.get("guard_fired")})
                rule.sign = -1
                b_spec = TrialSpec(trial=cyc * 2 + 1, seed=TRAIN_SEED_BASE + cyc * 2 + 1,
                                   cue_body_ids=tuple(CUE), drive_body_ids=tuple(bitter),
                                   drive2_body_ids=(), r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(b_spec)
                run.save()
                log(jout, {"rep": rep, "cycle": cyc, "phase": "bitter", "seed": TRAIN_SEED_BASE + cyc * 2 + 1,
                           "readout_hz": rec["readout_hz"], "guard_fired": rec.get("guard_fired")})
            if cyc in UNL_PROBE_AT:
                for ptype, off in (("alone", 0), ("cosugar", 5000)):
                    for r2 in range(2):
                        pseed = PROBE_SEED_BASE + cyc * 100 + r2 * 10 + off
                        mn9 = probe(run.matrix, nodes, lif_params, CUE, sugar, pseed, ptype)
                        log(jout, {"rep": rep, "cycle": cyc, "ptype": ptype, "rep2": r2, "mn9_hz": mn9})
        print(f"{stage} rep {rep} done (rank={len(rank)})", flush=True)
    return 0


class PhaseDriverRule:
    def __init__(self, inner):
        self.inner = inner
        self.sign = None

    @property
    def config(self):
        return self.inner.config

    def observe_rate_pair(self, pre, post, weight, x_hz, y_hz):
        self.inner.observe_rate_pair(pre, post, weight, x_hz=x_hz, y_hz=y_hz)

    def apply(self, weight):
        return self.inner.apply(weight, sign=self.sign)


def main() -> int:
    stage = os.environ["PHASE7B_STAGE"]
    if stage == "acquire":
        return stage_acquire()
    if stage in ("l6b", "l4b"):
        return _unlearn_loop(stage)
    raise RuntimeError(f"unknown stage {stage}")


if __name__ == "__main__":
    raise SystemExit(main())
