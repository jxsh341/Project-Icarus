"""Phase 7 P3 - frozen analysis: graded rank-decay dose sweep on GNG521.

Committed BEFORE any P3 run (docs/PHASE_7P3_PREREG.md). Emits
results/phase7p3/P3_VERDICT.json.

16 reps: tau in (0.5, 1.0, 2.0, 4.0) x 4 reps (rep r -> level r%4). Predictions
are analytic and exact (decay is deterministic, sim-independent):
  f_pred(c) = fraction of rank edges with w0 * e^(-c/tau) < W_EPS at cycle c
Criteria per rep:
  c1 weight hashes at every probe cycle == hash of analytic decay (exact)
  c2 alone mn9 at cycle 25 == 0 (both seeds); alone mn9 non-increasing in c
  c3 cosugar mn9 at cycle 25 within [75, 95] (both seeds)
  c4 guard silent on all probe sims
  c5 f_floor(final) == f_pred(25) exactly
Aggregate PASS iff all 16 reps pass; MIXED non-aggregating otherwise.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase5_expA_analysis as an  # noqa: E402
import phase7b_analysis as p1  # noqa: E402
import phase7e1_analysis as e1  # noqa: E402

PREREG = ROOT / "docs/PHASE_7P3_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng521_feed_0"
OUT_ROOT = ROOT / "results/phase7p3"
W_EPS = 1e-9
N_CYCLES = 25
ALONE_AT = (5, 15, 25)
TAU_LEVELS = (0.5, 1.0, 2.0, 4.0)
N_REPS = 16
BAND = (75, 95)
RANK_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"


def grab(doc_text, name):
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7p3 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def p3_prior():
    prior = e1.e1_prior()
    d7b = (ROOT / "docs/PHASE_7B_PREREG.md").read_text(encoding="utf-8")
    fns = {"P7B_ACQ_TRAIN": p1.acq_train, "P7B_ACQ_PROBE": p1.acq_probe,
           "P7B_L6B_TRAIN": p1.unl_train, "P7B_L6B_PROBE": p1.unl_probe,
           "P7B_L4B_TRAIN": p1.l4b_train, "P7B_L4B_PROBE": p1.unl_probe}
    for k, fn in fns.items():
        for b in p1.grab(d7b, k):
            prior |= fn(b)
    prior |= set(p1.grab(d7b, "P7B_SHADOW"))
    d7e1 = (ROOT / "docs/PHASE_7E1_PREREG.md").read_text(encoding="utf-8")
    for tb, pb in zip(e1.grab(d7e1, "E1_TASTE_BASES"), e1.grab(d7e1, "E1_PROBE_BASES")):
        t, p = e1.e1_spaces(tb, pb)
        prior |= t | p
    return prior


def probe_space(b):
    return ({b + 100 * c + s for c in ALONE_AT for s in (0, 1)}
            | {b + 1000 + s for s in (0, 1)})


def reproduce_draw():
    doc = PREREG.read_text(encoding="utf-8")
    rng = random.Random(20261108)
    prior = p3_prior()
    used = set()
    out = []
    while len(out) < 16:
        b = rng.randrange(3_000_000, 3_020_000)
        sp = probe_space(b)
        if len(sp) != 8 or (sp & used) or (sp & prior):
            continue
        used.update(sp)
        out.append(b)
    if out != grab(doc, "P3_PROBE_BASES"):
        raise an.ScopeError("P3 seeds do not reproduce from Random(20261108)")
    allsp = set().union(*[probe_space(b) for b in out])
    if allsp & prior:
        raise an.ScopeError("P3 spaces overlap prior")
    print(f"reproduce_draw OK; P3 spaces: {len(allsp)} seeds, disjoint from {len(prior)} prior")


def analytic(matrix, rank, cycles, tau):
    coo = matrix.tocoo()
    idx = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(coo.row, coo.col))}
    f = math.exp(-cycles / tau)
    data = coo.data.copy()
    for e in rank:
        k = idx.get(e)
        if k is None:
            continue
        v = float(data[k]) * f
        data[k] = 0.0 if v < W_EPS else v
    out = sparse.coo_matrix((data, (coo.row, coo.col)), shape=coo.shape).tocsr()
    out.sum_duplicates()
    return out


def whash(m):
    from fly.training import weight_matrix_hash
    return weight_matrix_hash(m)


def main() -> int:
    reproduce_draw()
    doc = PREREG.read_text(encoding="utf-8")
    bases = grab(doc, "P3_PROBE_BASES")
    pristine = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    from fly.training import TrainingRun
    from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
    rule = HebbianRule(PlasticityConfig(eta=1e-4, semantics=Semantics.V_CLIP, w_max=766.0))
    g = PlasticityGuard(StabilityThresholds(150_000, 5.0, 0.20))
    acquired = TrainingRun.load(R1CK, pristine, nodes, rule, g, 10331).matrix.copy()
    d = (acquired - pristine).tocoo()
    rank = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rsha = hashlib.sha256(json.dumps(rank).encode()).hexdigest()
    if rsha != RANK_SHA256:
        raise an.ScopeError(f"RANK_SET sha {rsha} != pinned")
    w0 = {e: float(acquired[e]) for e in rank}

    results = {"rank_n": len(rank), "rank_sha256": rsha, "reps": [], "aggregate": None}
    n_pass = 0
    for r in range(N_REPS):
        tau = TAU_LEVELS[r % 4]
        b = bases[r]
        rows = an.read_jsonl(OUT_ROOT / f"rep_r{r}" / "p3.jsonl", f"p3 r{r}")
        cfg = [x for x in rows if x.get("phase") == "config"]
        probes = [x for x in rows if x.get("phase") == "probe"]
        if len(cfg) != 1 or cfg[0]["tau"] != tau or cfg[0]["probe_base"] != b:
            raise an.ScopeError(f"r{r}: config mismatch (tau/probe_base)")
        if len(probes) != 8:
            raise an.IncompleteArtifacts(f"r{r}: {len(probes)} probe rows != 8")
        guard_ok = not any(x.get("guard_fired") for x in rows)
        # expected probe seeds
        exp = {b + 100 * c + s for c in ALONE_AT for s in (0, 1)} | {b + 1000 + s for s in (0, 1)}
        if {x["seed"] for x in probes} != exp:
            raise an.ScopeError(f"r{r}: probe seeds != expected space")
        rep = {"rep": r, "tau": tau, "c": {}}
        ok = guard_ok
        # c1: weight hash == analytic
        for cyc in ALONE_AT:
            m = analytic(acquired, rank, cyc, tau)
            for x in [x for x in probes if x["ptype"] == "alone" and x["cycle"] == cyc]:
                if x["weight_hash"] != whash(m):
                    ok = False
                rep["c"].setdefault(f"alone@{cyc}", []).append(x["mn9_hz"])
        m25 = analytic(acquired, rank, N_CYCLES, tau)
        for x in [x for x in probes if x["ptype"] == "cosugar"]:
            if x["weight_hash"] != whash(m25):
                ok = False
        # c2: extinction by 25 + monotone alone
        alone = {c: sorted(v for x in probes if x["ptype"] == "alone" and x["cycle"] == c
                           for v in [x["mn9_hz"]]) for c in ALONE_AT}
        rep["alone"] = {str(c): alone[c] for c in ALONE_AT}
        if not all(v == 0 for v in alone[25]):
            ok = False
        if not all(alone[5][i] >= alone[15][i] >= alone[25][i] for i in (0, 1)):
            ok = False
        # c3: cosugar band
        cos = sorted(x["mn9_hz"] for x in probes if x["ptype"] == "cosugar")
        rep["cosugar25"] = cos
        if not all(BAND[0] <= v <= BAND[1] for v in cos):
            ok = False
        # c5: floor fraction exact (Amendment P3-A1: rank-edge-zero fraction in
        # the hash-verified final matrix, read from rank_final_weights)
        f_pred = sum(1 for e in rank if w0[e] * math.exp(-N_CYCLES / tau) < W_EPS) / len(rank)
        fp = json.loads((OUT_ROOT / f"rep_r{r}" / "footprint_final.json").read_text())
        rw = fp["rank_final_weights"]
        f_meas = sum(1 for e in rank if rw[f"{e[0]},{e[1]}"] == 0.0) / len(rank)
        rep["f_pred25"] = round(f_pred, 4)
        rep["f_meas25"] = round(f_meas, 4)
        if abs(f_pred - f_meas) > 1e-12:
            ok = False
        rep["pass"] = bool(ok and guard_ok)
        n_pass += rep["pass"]
        results["reps"].append(rep)
    results["aggregate"] = "PASS" if n_pass == N_REPS else "MIXED"
    results["reps_pass"] = f"{n_pass}/{N_REPS}"
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "P3_VERDICT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for rep in results["reps"]:
        print(f"r{rep['rep']} tau={rep['tau']}: alone={rep['alone']} cos25={rep['cosugar25']} "
              f"f_pred={rep['f_pred25']} f_meas={rep['f_meas25']} pass={rep['pass']}")
    print(f"AGGREGATE: {results['aggregate']} ({results['reps_pass']}) -> {OUT_ROOT / 'P3_VERDICT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
