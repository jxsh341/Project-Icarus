"""Phase 7 P4 - frozen analysis: selective removal of GNG521 memory while
GNG491 memory persists. Committed BEFORE any P4 run (docs/PHASE_7P4_PREREG.md).
Emits results/phase7p4/P4_VERDICT.json.

4 reps. Per rep: acq (R1CK + 8 cueB+sugar trials) then fast rank-decay of
cue-A's 25 solo edges (tau=1, 25 cycles, analytic), probes at (5,15,25) x
{aloneA, aloneB, cosA, cosB} x 2 seeds.
Criteria (frozen):
  c0 both memories acquired: acq probes aloneA >= 41.5 AND aloneB >= 41.5
  c1 selective erasure: aloneA mn9 == 0 at cycle 25 (both seeds)
  c2 memory B survives: aloneB mn9 >= 41.5 at cycle 25 in >= 3/4 reps
  c3 structure: A-solo edges at exact floor == analytic f_pred(25); B-added
     edges bit-unchanged after decay (b_unchanged True)
  c4 innate intact: cosA and cosB at 25 within [75, 95] (both seeds)
  c5 guard silent on all rows
Aggregate PASS iff c0-c5; MIXED non-aggregating otherwise.
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase5_expA_analysis as an  # noqa: E402
import phase7p3_analysis as p3  # noqa: E402

PREREG = ROOT / "docs/PHASE_7P4_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng521_feed_0"
OUT_ROOT = ROOT / "results/phase7p4"
MN9_FIRE_HZ = 41.5
N_CYCLES = 25
PROBE_AT = (5, 15, 25)
PTYPES = ("aloneA", "aloneB", "cosA", "cosB")
N_REPS = 4
BAND = (75, 95)
W_EPS = 1e-9
TAU = 1.0
RANK_A_SHA256 = "43313db60de5c3faad5ed932a5c0fe31649a21628fbfbf7444a230acdf9f2589"


def grab(doc_text, name):
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7p4 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def p4_prior():
    prior = p3.p3_prior()
    d3 = (ROOT / "docs/PHASE_7P3_PREREG.md").read_text(encoding="utf-8")
    for b in p3.grab(d3, "P3_PROBE_BASES"):
        prior |= p3.probe_space(b)
    return prior


def acq_space(b): return {b + t for t in range(1, 9)} | {b + 100 + s for s in (0, 1)}
def unl_space(b): return {b + 1000 + 100 * c + 10 * p + s for c in PROBE_AT for p in range(4) for s in (0, 1)}


def reproduce_draw():
    doc = PREREG.read_text(encoding="utf-8")
    rng = random.Random(20261109)
    prior = p4_prior()
    used = set()

    def draw(n, fn, expect):
        out = []
        while len(out) < n:
            b = rng.randrange(3_200_000, 3_220_000)
            sp = fn(b)
            if len(sp) != expect or (sp & used) or (sp & prior):
                continue
            used.update(sp)
            out.append(b)
        return out

    ab = draw(4, acq_space, 10)
    ub = draw(4, unl_space, 24)
    if ab != grab(doc, "P4_ACQ_BASES") or ub != grab(doc, "P4_UNL_BASES"):
        raise an.ScopeError("P4 seeds do not reproduce from Random(20261109)")
    allsp = set().union(*[acq_space(b) for b in ab], *[unl_space(b) for b in ub])
    if allsp & prior:
        raise an.ScopeError("P4 spaces overlap prior")
    print(f"reproduce_draw OK; P4 spaces: {len(allsp)} seeds, disjoint from {len(prior)} prior")


def main() -> int:
    reproduce_draw()
    doc = PREREG.read_text(encoding="utf-8")
    ab = grab(doc, "P4_ACQ_BASES")
    ub = grab(doc, "P4_UNL_BASES")
    import numpy as np
    from scipy import sparse
    from fly.training import TrainingRun
    from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
    pristine = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    rule = HebbianRule(PlasticityConfig(eta=1e-4, semantics=Semantics.V_CLIP, w_max=766.0))
    g = PlasticityGuard(StabilityThresholds(150_000, 5.0, 0.20))
    base_m = TrainingRun.load(R1CK, pristine, nodes, rule, g, 10331).matrix.copy()
    d = (base_m - pristine).tocoo()
    rank_a = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    rsha = hashlib.sha256(json.dumps(rank_a).encode()).hexdigest()
    if rsha != RANK_A_SHA256:
        raise an.ScopeError("RANK_A sha mismatch")
    w0 = {e: float(base_m[e]) for e in rank_a}
    f_pred25 = sum(1 for e in rank_a if w0[e] * math.exp(-N_CYCLES / TAU) < W_EPS) / len(rank_a)

    results = {"rank_a_n": len(rank_a), "f_pred25": f_pred25, "reps": [], "aggregate": None}
    c0_n = c2_n = 0
    c3_ok = c4_ok = c5_ok = True
    for r in range(N_REPS):
        rd = OUT_ROOT / f"rep_r{r}"
        arows = an.read_jsonl(rd / "acq.jsonl", f"acq r{r}")
        urows = an.read_jsonl(rd / "unl.jsonl", f"unl r{r}")
        fp = json.loads((rd / "footprints.json").read_text())
        fin = json.loads((rd / "final.json").read_text())
        if len([x for x in arows if x.get("stage") == "acq"]) != 8:
            raise an.IncompleteArtifacts(f"r{r} acq trials != 8")
        if len([x for x in urows if x.get("stage") == "probe"]) != 24:
            raise an.IncompleteArtifacts(f"r{r} probes != 24")
        if fp["rank_a_sha256"] != RANK_A_SHA256 or fp["overlap_a_b"] != 0:
            raise an.ScopeError(f"r{r} rank/overlap mismatch")
        guard_ok = not any(x.get("guard_fired") for x in arows + urows)
        c5_ok = c5_ok and guard_ok
        ap = {x["ptype"]: x["mn9_hz"] for x in arows if x.get("stage") == "acq_probe"}
        # acq probes: aloneA seeds +100,+101 ; aloneB same seeds - logged per ptype
        aloneA_acq = sorted(x["mn9_hz"] for x in arows if x.get("stage") == "acq_probe" and x["ptype"] == "aloneA")
        aloneB_acq = sorted(x["mn9_hz"] for x in arows if x.get("stage") == "acq_probe" and x["ptype"] == "aloneB")
        c0 = all(v >= MN9_FIRE_HZ for v in aloneA_acq + aloneB_acq) and guard_ok
        if c0:
            c0_n += 1
        up = [x for x in urows if x.get("stage") == "probe"]
        aloneA25 = sorted(x["mn9_hz"] for x in up if x["ptype"] == "aloneA" and x["cycle"] == 25)
        aloneB25 = sorted(x["mn9_hz"] for x in up if x["ptype"] == "aloneB" and x["cycle"] == 25)
        cosA25 = sorted(x["mn9_hz"] for x in up if x["ptype"] == "cosA" and x["cycle"] == 25)
        cosB25 = sorted(x["mn9_hz"] for x in up if x["ptype"] == "cosB" and x["cycle"] == 25)
        c1 = all(v == 0 for v in aloneA25)
        if all(v >= MN9_FIRE_HZ for v in aloneB25):
            c2_n += 1
        f_meas = sum(1 for v in fin["rank_a_final_weights"].values() if v == 0.0) / len(rank_a)
        c3 = abs(f_meas - f_pred25) < 1e-12 and fin["b_unchanged"]
        c3_ok = c3_ok and c3
        c4 = all(BAND[0] <= v <= BAND[1] for v in cosA25 + cosB25)
        c4_ok = c4_ok and c4
        results["reps"].append({
            "rep": r, "c0_acquired_both": c0, "aloneA_acq": aloneA_acq, "aloneB_acq": aloneB_acq,
            "aloneA25": aloneA25, "aloneB25": aloneB25, "cosA25": cosA25, "cosB25": cosB25,
            "f_meas25": round(f_meas, 4), "b_unchanged": fin["b_unchanged"],
            "b_added_n": fp["b_added_n"], "overlap": fp["overlap_a_b"],
            "c1": c1, "c3": c3, "c4": c4, "guard_ok": guard_ok})
    results["criteria"] = {
        "c0": {"reps": c0_n, "of": 4, "pass": c0_n == 4},
        "c1_erasure_A": {"pass": all(r["c1"] for r in results["reps"])},
        "c2_B_survives": {"reps": c2_n, "of": 4, "pass": c2_n >= 3},
        "c3_structure": {"pass": c3_ok},
        "c4_innate": {"pass": c4_ok},
        "c5_guard": {"pass": c5_ok},
    }
    c = results["criteria"]
    results["aggregate"] = "PASS" if all(v["pass"] for v in c.values()) else "MIXED"
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "P4_VERDICT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for r in results["reps"]:
        print(f"r{r['rep']}: acqA={r['aloneA_acq']} acqB={r['aloneB_acq']} A25={r['aloneA25']} B25={r['aloneB25']} "
              f"cosA={r['cosA25']} cosB={r['cosB25']} f={r['f_meas25']} b_unch={r['b_unchanged']}")
    print(json.dumps(results["criteria"], indent=1))
    print(f"AGGREGATE: {results['aggregate']} -> {OUT_ROOT / 'P4_VERDICT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
