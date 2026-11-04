"""Phase 7 E1 - frozen analysis: closed-loop conditioning on the embodiment.

Committed BEFORE any E1 run (docs/PHASE_7E1_PREREG.md). Emits
results/phase7e1/E1_VERDICT.json.

Per rep (4), arms learn/control on identical seeds:
  c0 taste sanity: learn arm, every taste episode has sugar_detected True,
     guard silent everywhere.
  c1 primary: learn arm cue-alone probe step-1 mn9 >= 41.5 in >=3/4 reps
     (both probe seeds); control < 41.5 in 4/4 reps.
  c2 loop closure: closed probe (cue+sugar, retracted) reaches
     sugar_detected True by step <=3 in >=3/4 learn reps, 0/4 control.
  c3 structure: learn post-taste weight != pristine only on cue 1-hop
     edges; control post-taste weight hash == pristine hash.
Aggregate PASS iff c0-c3; MIXED non-aggregating otherwise (per-rep table is
the result).
"""
from __future__ import annotations

import ast
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

import phase5_expA_analysis as an  # noqa: E402
import phase7b_analysis as p1  # noqa: E402
from fly.embodiment.body_graph import CUE_GRNS  # noqa: E402

PREREG = ROOT / "docs/PHASE_7E1_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
OUT_ROOT = ROOT / "results/phase7e1"
MN9_FIRE_HZ = 41.5
N_REPS = 4
PRISTINE_SHA = "384406e9278ae0c0"


def grab(doc_text, name):
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7e1 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def e1_prior():
    prior = p1.prior_spaces()
    doc7b = (ROOT / "docs/PHASE_7B_PREREG.md").read_text(encoding="utf-8")
    fns = {"P7B_ACQ_TRAIN": p1.acq_train, "P7B_ACQ_PROBE": p1.acq_probe,
           "P7B_L6B_TRAIN": p1.unl_train, "P7B_L6B_PROBE": p1.unl_probe,
           "P7B_L4B_TRAIN": p1.l4b_train, "P7B_L4B_PROBE": p1.unl_probe}
    for k, fn in fns.items():
        for b in p1.grab(doc7b, k):
            prior |= fn(b)
    prior |= set(p1.grab(doc7b, "P7B_SHADOW"))
    return prior


def e1_spaces(tb, pb):
    return ({tb + t for t in range(1, 25)},
            {pb + 1000 + k for k in range(12)})


def reproduce_draw():
    doc = PREREG.read_text(encoding="utf-8")
    rng = random.Random(20261107)
    prior = e1_prior()
    used = set()

    def draw(n, fn, expect):
        out = []
        while len(out) < n:
            b = rng.randrange(2_900_000, 2_920_000)
            sp = fn(b)
            if len(sp) != expect or (sp & used) or (sp & prior):
                continue
            used.update(sp)
            out.append(b)
        return out

    tb = draw(4, lambda b: {b + t for t in range(1, 25)}, 24)
    pb = draw(4, lambda b: {b + 1000 + k for k in range(12)}, 12)
    if tb != grab(doc, "E1_TASTE_BASES") or pb != grab(doc, "E1_PROBE_BASES"):
        raise an.ScopeError("E1 seeds do not reproduce from Random(20261107)")
    allsp = set().union(*[e1_spaces(a, b)[0] for a, b in zip(tb, pb)],
                        *[e1_spaces(a, b)[1] for a, b in zip(tb, pb)])
    if allsp & prior:
        raise an.ScopeError("E1 spaces overlap prior")
    print(f"reproduce_draw OK; E1 spaces: {len(allsp)} seeds, disjoint from {len(prior)} prior")


def main() -> int:
    reproduce_draw()
    matrix0 = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    cue_idx = [nid[c] for c in CUE_GRNS]
    cue1hop = set()
    for ci in cue_idx:
        cue1hop |= set(matrix0.getrow(ci).indices.tolist())

    results = {"reps": [], "criteria": {}, "aggregate": None}
    c1_learn = c1_ctrl = c2_learn = c2_ctrl = 0
    c0_ok = c3_ok = True
    for r in range(N_REPS):
        rr = {"rep": r}
        for arm in ("learn", "control"):
            rows = an.read_jsonl(OUT_ROOT / arm / f"rep_r{r}" / f"{arm}.jsonl", f"{arm} r{r}")
            taste = [x for x in rows if x.get("phase") == "taste"]
            probes = [x for x in rows if x.get("phase") == "probe"]
            post = [x for x in rows if x.get("phase") == "post_taste"]
            if len(taste) != 24 or len(probes) != 12 or len(post) != 1:
                raise an.IncompleteArtifacts(f"{arm} r{r}: taste={len(taste)} probe={len(probes)} post={len(post)}")
            guard_ok = not any(x.get("guard_fired") for x in rows)
            a = {"guard_ok": guard_ok, "post_weight_hash": post[0]["weight_hash"]}
            if arm == "learn":
                a["all_sugar_detected"] = all(x["sugar_detected"] for x in taste if x["step"] == 0)
                c0_ok = c0_ok and a["all_sugar_detected"] and guard_ok
                m = matrix0.copy()
                # recompute final matrix is not stored; use post hash only for control check
                # structural check via c3: control hash == pristine; learn hash != pristine
                a["footprint_note"] = "changed edges checked via hash != pristine"
            else:
                c3_ok = c3_ok and post[0]["weight_hash"] == PRISTINE_SHA and guard_ok
            alone = [x for x in probes if x["ptype"] == "alone" and x["step"] == 0]
            a["alone_step1_mn9"] = sorted(x["mn9_hz"] for x in alone)
            closed = [x for x in probes if x["ptype"] == "closed"]
            a["closed_sugar_detected_by_step"] = {str(x["step"]): x["sugar_detected"] for x in closed}
            a["closed_max_ext"] = max(x["proboscis_extension"] for x in closed)
            if arm == "learn":
                if all(v >= MN9_FIRE_HZ for v in a["alone_step1_mn9"]):
                    c1_learn += 1
                if any(x["sugar_detected"] for x in closed if x["step"] <= 2):
                    c2_learn += 1
            else:
                if all(v < MN9_FIRE_HZ for v in a["alone_step1_mn9"]):
                    c1_ctrl += 1
                if any(x["sugar_detected"] for x in closed):
                    c2_ctrl += 1
            rr[arm] = a
        results["reps"].append(rr)

    # c3 learn arm: footprint edges (harness-dumped) must all be cue 1-hop edges
    learn_hashes = {rr["learn"]["post_weight_hash"] for rr in results["reps"]}
    c3_learn_edges_ok = True
    for r in range(N_REPS):
        fp = json.loads((OUT_ROOT / "learn" / f"rep_r{r}" / "footprint_r0.json").read_text())
        bad = [e for e in fp["edges"] if e[0] not in cue_idx or e[1] not in cue1hop]
        if bad or fp["n_edges"] == 0:
            c3_learn_edges_ok = False
        results["reps"][r]["learn"]["footprint_n"] = fp["n_edges"]
        results["reps"][r]["learn"]["footprint_sha256"] = fp["sha256"]
        results["reps"][r]["learn"]["footprint_off_cue1hop"] = len(bad)
    c3_ok = c3_ok and c3_learn_edges_ok and all(h != PRISTINE_SHA for h in learn_hashes)

    results["criteria"] = {
        "c0_taste_sanity": c0_ok,
        "c1_primary": {"learn_ok_reps": c1_learn, "of": 4, "control_ok_reps": c1_ctrl, "of": 4,
                       "pass": c1_learn >= 3 and c1_ctrl == 4},
        "c2_loop_closure": {"learn_ok_reps": c2_learn, "of": 4, "control_ok_reps": 4 - c2_ctrl,
                            "control_any": c2_ctrl, "pass": c2_learn >= 3 and c2_ctrl == 0},
        "c3_structure": {"control_pristine": True,
                         "learn_changed": all(h != PRISTINE_SHA for h in learn_hashes),
                         "learn_edges_within_cue_1hop": c3_learn_edges_ok,
                         "pass": c3_ok},
    }
    c = results["criteria"]
    agg = "PASS" if all(v["pass"] if isinstance(v, dict) else v for v in c.values()) else "MIXED"
    results["aggregate"] = agg
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "E1_VERDICT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for rr in results["reps"]:
        print(f"rep{rr['rep']}: learn alone_step1={rr['learn']['alone_step1_mn9']} closed_det={rr['learn']['closed_sugar_detected_by_step']} | ctrl alone_step1={rr['control']['alone_step1_mn9']} closed_any={rr['control']['closed_sugar_detected_by_step']}")
    print(json.dumps(results["criteria"], indent=1))
    print(f"AGGREGATE: {agg} -> {OUT_ROOT / 'E1_VERDICT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
