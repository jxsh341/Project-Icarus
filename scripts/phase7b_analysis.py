"""Phase 7b P1 - frozen analysis: does footprint accessibility predict
unlearnability on held-out circuits? Committed BEFORE any Phase 7b run
(docs/PHASE_7B_PREREG.md). Emits results/phase7b/P1_VERDICT.json.

Pairs (frozen by screening, prereg section 3): GNG557 [12595], GNG610
[128102], GNG491 [14094] - feed direction. Per pair x rep (2): acquire ->
census -> l6b + l4b. Predictions: P1a |f_l4b - (1 - z_edges)| <= 0.15 in
>=5/6 reps; P1b f_l6b >= 0.9 in >=5/6 reps; behavioral c1 (cue-alone zero by
cycle 15, persists to 25), c2 (cosugar in [78,88] at cycle 25), c3 guard
silent - per rep, both mechanisms. Aggregate PREDICTIVE-PASS iff >=2 pairs
acquired AND P1a AND P1b AND all behavioral criteria on evaluated reps;
MIXED non-aggregating otherwise.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from fly.dynamics.lif import LIFParams, simulate_lif  # noqa: E402
import phase5_expA_analysis as an  # noqa: E402
import phase6_expB_analysis as eb  # noqa: E402

PREREG = ROOT / "docs/PHASE_7B_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
OUT_ROOT = ROOT / "results/phase7b"
MN9_L = 10331
THETA = 41.5
BAND = (78, 88)
UNL_PROBE_AT = (5, 10, 15, 20, 25)
ACQ_PROBE_AT = (1, 2, 3, 4, 5, 10, 15, 20)
PAIRS = {"GNG557": [12595], "GNG610": [128102], "GNG491": [14094]}
N_REPS = 2
TOL = 0.15
F_MIN = 0.9


def grab(doc_text, name):
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7b missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


# ---- seed space functions (frozen formulas; shared with the launcher) ----
def acq_train(b): return {b + t for t in range(1, 21)}
def acq_probe(b):
    s = {b + t * 100 + r2 * 10 + off for t in ACQ_PROBE_AT for r2 in (0, 1) for off in (0, 5000)}
    s.add(b + 999)
    return s
def unl_train(b): return {b + c for c in range(1, 26)}
def l4b_train(b): return {b + c * 2 + ph for c in range(1, 26) for ph in (0, 1)}
def unl_probe(b):
    s = {b + c * 100 + r2 * 10 + off for c in UNL_PROBE_AT for r2 in (0, 1) for off in (0, 5000)}
    s.add(b + 999)
    return s


def prior_spaces():
    prior = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    for b in ct:
        prior |= set(an.expected_train_seeds(b))
    for b in cp:
        prior |= set(an.expected_probe_seeds(b)) | {an.sanity_seed(b)}
    for docname, pre in (("PHASE_6_PREREG.md", "P6"), ("PHASE_7_PREREG.md", "P7")):
        doc = (ROOT / "docs" / docname).read_text(encoding="utf-8")
        t, p = eb.grab(doc, f"{pre}_TRAIN_SEEDS"), eb.grab(doc, f"{pre}_PROBE_SEEDS")
        a, b_ = eb.seed_spaces(t, p)
        prior |= a | b_ | set(eb.grab(doc, f"{pre}_SHADOW_SEEDS"))
    prior |= set(grab(PREREG.read_text(encoding="utf-8"), "P7B_SCREEN_SEEDS"))
    return prior


def draw_p7b():
    rng = random.Random(20261106)
    prior = prior_spaces()
    used = set()

    def draw(n, lo, hi, fn, expect):
        out = []
        while len(out) < n:
            b = rng.randrange(lo, hi)
            sp = fn(b)
            if len(sp) != expect or (sp & used) or (sp & prior):
                continue
            used.update(sp)
            out.append(b)
        return out

    return (draw(6, 2_400_000, 2_420_000, acq_train, 20),
            draw(6, 2_400_000, 2_420_000, acq_probe, 33),
            draw(6, 2_500_000, 2_520_000, unl_train, 25),
            draw(6, 2_500_000, 2_520_000, unl_probe, 21),
            draw(6, 2_600_000, 2_620_000, l4b_train, 50),
            draw(6, 2_600_000, 2_620_000, unl_probe, 21),
            draw(4, 2_800_000, 2_820_000, lambda b: {b}, 1))


def reproduce_draw():
    doc = PREREG.read_text(encoding="utf-8")
    # screen seeds
    rng = random.Random(20261105)
    prior = prior_spaces()
    prior -= set(grab(doc, "P7B_SCREEN_SEEDS"))
    scr, used = [], set()
    while len(scr) < 45:
        s = rng.randrange(2_200_000, 2_300_000)
        if s in prior or s in used:
            continue
        used.add(s)
        scr.append(s)
    if scr != grab(doc, "P7B_SCREEN_SEEDS"):
        raise an.ScopeError("P7B screen seeds do not reproduce")
    a_t, a_p, l6t, l6p, l4t, l4p, sh = draw_p7b()
    got = [a_t, a_p, l6t, l6p, l4t, l4p, sh]
    want = [grab(doc, k) for k in ("P7B_ACQ_TRAIN", "P7B_ACQ_PROBE", "P7B_L6B_TRAIN",
                                   "P7B_L6B_PROBE", "P7B_L4B_TRAIN", "P7B_L4B_PROBE", "P7B_SHADOW")]
    if got != want:
        raise an.ScopeError("P7B run seeds do not reproduce from Random(20261106)")
    allsp = set().union(*[acq_train(b) for b in a_t], *[acq_probe(b) for b in a_p],
                        *[unl_train(b) for b in l6t], *[unl_probe(b) for b in l6p],
                        *[l4b_train(b) for b in l4t], *[unl_probe(b) for b in l4p],
                        *[{b} for b in sh])
    if allsp & prior_spaces():
        raise an.ScopeError("P7B spaces overlap prior spaces")
    print(f"reproduce_draw OK; P7B spaces: {len(allsp)} seeds, disjoint")


def probe_vals(rows, cyc, ptype, stage):
    v = [x["mn9_hz"] for x in rows if x.get("cycle", x.get("trial")) == cyc and x.get("ptype") == ptype]
    if len(v) != 2:
        raise an.IncompleteArtifacts(f"{stage} probe {ptype}@{cyc}: {len(v)} != 2")
    return v


def main() -> int:
    reproduce_draw()
    doc = PREREG.read_text(encoding="utf-8")
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    results = {"pairs": {}, "predictions": {}, "aggregate": None}
    n_eval = 0
    p1a_ok = p1b_ok = beh_ok = 0
    for pi, (pair, cue) in enumerate(sorted(PAIRS.items())):
        acq_reps, acquired = [], False
        for r in range(N_REPS):
            adir = OUT_ROOT / "acq" / pair / f"rep_r{r}"
            rows = an.read_jsonl(adir / "acq.jsonl", f"{pair} acq r{r}")
            cyc_rows = [x for x in rows if "ptype" not in x]
            if len(cyc_rows) != 20:
                raise an.IncompleteArtifacts(f"{pair} acq r{r}: {len(cyc_rows)} trials != 20")
            guard_ok = not any(x.get("guard_fired") for x in cyc_rows)
            a20 = probe_vals(rows, 20, "alone", "acq")
            acq_ok = guard_ok and all(v >= THETA for v in a20)
            acq_reps.append({"rep": r, "cue_alone_t20": a20, "guard_ok": guard_ok, "acquired": acq_ok})
            acquired = acquired or acq_ok
            # census on this rep's acquired matrix
            m, _ = an.load_final_matrix(adir / "ckpt_r0", f"{pair} acq r{r}")
            d = (m - matrix).tocoo()
            fp = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
            fp_sha = hashlib.sha256(json.dumps(fp).encode()).hexdigest()
            partners = sorted({j for _, j in fp})
            zi = {p for p in partners if sum(float(matrix[nid[b], p]) for b in sugar) == 0.0}
            zi_edges = [e for e in fp if e[1] in zi]
            z_e = len(zi_edges) / len(fp)
            rep_res = {"acq": acq_reps[-1], "footprint": len(fp), "footprint_sha256": fp_sha,
                       "partners": len(partners), "zero_input_edges": len(zi_edges), "z_edges": round(z_e, 4)}
            for stage in ("l6b", "l4b"):
                sdir = OUT_ROOT / stage / pair / f"rep_r{r}"
                srows = an.read_jsonl(sdir / f"{stage}.jsonl", f"{pair} {stage} r{r}")
                scyc = [x for x in srows if "ptype" not in x]
                n_exp = 25 if stage == "l6b" else 50
                if len(scyc) != n_exp:
                    raise an.IncompleteArtifacts(f"{pair} {stage} r{r}: {len(scyc)} != {n_exp}")
                g_ok = not any(x.get("guard_fired") for x in scyc)
                fm, _ = an.load_final_matrix(sdir / "ckpt_r0", f"{pair} {stage} r{r} final")
                f_floor = sum(1 for e in fp if fm[e] == 0.0) / len(fp)
                alone = {c: probe_vals(srows, c, "alone", stage) for c in UNL_PROBE_AT}
                cos = {c: probe_vals(srows, c, "cosugar", stage) for c in UNL_PROBE_AT}
                c1 = all(v == 0 for c in (15, 20, 25) for v in alone[c])
                c2 = all(BAND[0] <= v <= BAND[1] for v in cos[25])
                c3 = g_ok
                rep_res[stage] = {"f_floor": round(f_floor, 4), "c1_zero_by_15": c1,
                                  "c2_band_c25": c2, "c3_guard_silent": c3,
                                  "alone": {str(c): alone[c] for c in UNL_PROBE_AT},
                                  "cosugar_c25": cos[25]}
                if stage == "l4b":
                    rep_res["p1a_dev"] = round(abs(f_floor - (1 - z_e)), 4)
                    if abs(f_floor - (1 - z_e)) <= TOL:
                        p1a_ok += 1
                else:
                    if f_floor >= F_MIN:
                        p1b_ok += 1
                if c1 and c2 and c3:
                    beh_ok += 1
                n_eval += 1
            results["pairs"].setdefault(pair, []).append(rep_res)
        results["pairs"][pair + "_acquired"] = acquired

    n_pairs_acq = sum(1 for p in PAIRS if results["pairs"].get(p + "_acquired"))
    results["predictions"] = {
        "P1a_l4b_accessibility": {"ok_reps": p1a_ok, "of": 6, "tol": TOL,
                                  "pass": p1a_ok >= 5},
        "P1b_l6b_universal": {"ok_reps": p1b_ok, "of": 6, "f_min": F_MIN,
                              "pass": p1b_ok >= 5},
        "behavioral_c1_c3": {"ok_reps": beh_ok, "of": n_eval, "pass": beh_ok == n_eval},
        "pairs_acquired": {"n": n_pairs_acq, "of": 3},
    }
    p = results["predictions"]
    if n_pairs_acq >= 2 and p["P1a_l4b_accessibility"]["pass"] and p["P1b_l6b_universal"]["pass"] and p["behavioral_c1_c3"]["pass"]:
        agg = "PREDICTIVE-PASS"
    elif n_pairs_acq <= 1:
        agg = "NEGATIVE-ACQUISITION"
    else:
        agg = "MIXED"
    results["aggregate"] = agg
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "P1_VERDICT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for pair, reps in results["pairs"].items():
        if pair.endswith("_acquired"):
            continue
        for rr in reps:
            print(f"{pair} r{rr['acq']['rep']}: fp={rr['footprint']} z_e={rr['z_edges']} "
                  f"acq={rr['acq']['acquired']} | l6b f={rr['l6b']['f_floor']} c1={rr['l6b']['c1_zero_by_15']} "
                  f"| l4b f={rr['l4b']['f_floor']} dev={rr.get('p1a_dev')} c1={rr['l4b']['c1_zero_by_15']}")
    print(json.dumps(results["predictions"], indent=1))
    print(f"AGGREGATE: {agg} -> {OUT_ROOT / 'P1_VERDICT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
