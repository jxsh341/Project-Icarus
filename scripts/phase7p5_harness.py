"""Phase 7 P5 harness - footprint-estimation sensitivity (arms true/thresh4/hop1).

Per docs/PHASE_7P5_PREREG.md. Loads frozen R1CK, builds the arm's edge set
deterministically from pristine + R1CK, checks its sha256 against the prereg
pins, then fast analytic rank-decay (tau=1.0, 25 cycles) + probes
(cycles 5/15/25 x {aloneA, cosA} x 2 seeds). OUT/PROBE_BASE/ARM injected by
the launcher in memory only; harness FILE never modified.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fly.dynamics.lif import LIFParams, simulate_lif  # noqa: E402
from fly.training import TrainingRun  # noqa: E402
from fly.plasticity import (  # noqa: E402
    HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds,
)
from phase7p4_harness import decay_to  # noqa: E402  pure function, bit-identity tested

BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng521_feed_0"
PREREG = ROOT / "docs/PHASE_7P5_PREREG.md"
CUE_A = [15957, 16327]
MN9_L = 10331
TAU = 1.0
N_CYCLES = 25
PROBE_AT = (5, 15, 25)
PTYPES = ("aloneA", "cosA")
RANK_TRUE_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"

OUT = Path("results/phase7p5/unset")
PROBE_BASE = 0
ARM = "unset"


def esha(edges):
    return hashlib.sha256(json.dumps(sorted(edges)).encode()).hexdigest()


def log(path, rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def arm_edges(arm, pristine, base_m, nid):
    if arm == "true":
        d = (base_m - pristine).tocoo()
        edges = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    elif arm == "thresh4":
        w1 = sparse.load_npz(R1CK / "weights_trial_0001.npz").tocsr()
        w30 = sparse.load_npz(R1CK / "weights_trial_0030.npz").tocsr()
        d = (w30 - w1).tocoo()
        edges = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if abs(v) >= 4.0)
    elif arm == "hop1":
        ci = {nid[c] for c in CUE_A}
        coo = pristine.tocoo()
        edges = sorted((int(i), int(j)) for i, j in zip(coo.row, coo.col) if i in ci or j in ci)
    else:
        raise RuntimeError(f"unknown arm {arm}")
    return edges


def probe(matrix, nodes, params, sugar, cue, pseed, ptype):
    if ptype == "aloneA":
        r = simulate_lif(matrix, nodes, params, 1000.0, stimulated=list(cue), seed=pseed)
    else:
        r = simulate_lif(matrix, nodes, params, 1000.0, stimulated=list(cue),
                         stimulated2=list(sugar), r_poisson2_Hz=200.0, seed=pseed)
    return float(len(r.spike_times.get(MN9_L, [])))


def main() -> int:
    doc = PREREG.read_text(encoding="utf-8")
    pins = dict(re.findall(r'(RANK_\w+_SHA256)\s*=\s*"([0-9a-f]{64})"', doc))
    pristine = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    rule = HebbianRule(PlasticityConfig(eta=1e-4, semantics=Semantics.V_CLIP, w_max=766.0))
    g = PlasticityGuard(StabilityThresholds(150_000, 5.0, 0.20))
    base_m = TrainingRun.load(R1CK, pristine, nodes, rule, g, MN9_L).matrix.copy()

    edges = arm_edges(ARM, pristine, base_m, nid)
    sha = esha(edges)
    key = {"true": "RANK_TRUE_SHA256", "thresh4": "RANK_THRESH4_SHA256", "hop1": "RANK_HOP1_SHA256"}[ARM]
    expect = pins.get(key, RANK_TRUE_SHA256 if ARM == "true" else None)
    if expect is None or sha != expect:
        raise RuntimeError(f"arm {ARM} edge-set sha {sha[:12]} != prereg pin {str(expect)[:12]}")
    print(f"arm={ARM} n_edges={len(edges)} sha={sha[:12]} OK", flush=True)

    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "unl.jsonl"
    log(jout, {"stage": "unl_cfg", "arm": ARM, "probe_base": PROBE_BASE, "tau": TAU,
               "n_cycles": N_CYCLES, "n_edges": len(edges), "edges_sha256": sha})

    m = base_m.copy()
    for c in range(1, N_CYCLES + 1):
        m = decay_to(m, edges, 1, TAU)
        if c in PROBE_AT:
            for p, ptype in enumerate(PTYPES):
                for s in (0, 1):
                    pseed = PROBE_BASE + 100 * c + 10 * p + s
                    hz = probe(m, nodes, params, sugar, CUE_A, pseed, ptype)
                    rec = {"stage": "probe", "arm": ARM, "cycle": c, "ptype": ptype,
                           "seed": pseed, "mn9_hz": hz}
                    try:
                        tr = simulate_lif(m, nodes, params, 1000.0, seed=pseed)
                        rec["guard_fired"] = bool(g.check(trial_spikes=len(tr.spike_times.get(MN9_L, []))))
                    except Exception:
                        rec["guard_fired"] = True
                    log(jout, rec)

    final = {"arm": ARM, "edges_sha256": sha, "n_edges": len(edges),
             "final_weights": {f"{i},{j}": float(m[i, j]) for i, j in edges}}
    (OUT / "final.json").write_text(json.dumps(final), encoding="utf-8")
    print(f"p5 arm={ARM} done base={PROBE_BASE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
