"""Phase 7 WP-P2 - frozen verdict analysis for GNG380 confirmatory unlearning.

Committed BEFORE any Phase 7 run (docs/PHASE_7_PREREG.md section 6). Implements
the preregistered criteria c1-c6 and branch/aggregate logic exactly; raises on
malformed artifacts instead of guessing. Emits results/phase7/p2_g380/P2_VERDICT.json.
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

PREREG7 = ROOT / "docs/PHASE_7_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
G380_R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0"
OUT_ROOT = ROOT / "results/phase7/p2_g380"
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
MN9_L = 10331
THETA = 41.5
BAND = (78, 88)
PROBE_AT = (5, 10, 15, 20, 25)
N_REPS = 8
G380_FP_SHA = "27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a"
ZI_MIN, FP_MIN = 75, 130


def grab(doc_text: str, name: str) -> list[int]:
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def draw_p7():
    """Reproduce the frozen Random(20261104) draw (prereg section 4)."""
    rng = random.Random(20261104)
    used, prior = set(), set()
    dev = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    for b in ct:
        prior |= set(an.expected_train_seeds(b))
    for b in cp:
        prior |= set(an.expected_probe_seeds(b)) | {an.sanity_seed(b)}
    doc6 = (ROOT / "docs/PHASE_6_PREREG.md").read_text(encoding="utf-8")
    p6t, p6p = eb.grab(doc6, "P6_TRAIN_SEEDS"), eb.grab(doc6, "P6_PROBE_SEEDS")
    t6, p6s = eb.seed_spaces(p6t, p6p)
    prior |= dev | t6 | p6s | set(eb.grab(doc6, "P6_SHADOW_SEEDS"))

    def tr(b):
        return {b + c for c in range(1, 26)}

    def pr(b):
        s = {b + c * 100 + r2 * 10 + off for c in PROBE_AT for r2 in (0, 1) for off in (0, 5000)}
        s.add(b + 999)
        return s

    def draw(n, lo, hi, fn, expect):
        out = []
        while len(out) < n:
            b = rng.randrange(lo, hi)
            sp = fn(b)
            if len(sp) != expect or (sp & used) or (sp & prior):
                continue
            used |= sp
            out.append(b)
        return out

    return draw(8, 1_600_000, 1_700_000, tr, 25), draw(15, 1_800_000, 1_900_000, pr, 21), draw(8, 2_000_000, 2_100_000, lambda b: {b}, 1)


def reproduce_draw():
    t, p, s = draw_p7()
    doc = PREREG7.read_text(encoding="utf-8")
    if grab(doc, "P7_TRAIN_SEEDS") != t or grab(doc, "P7_PROBE_SEEDS") != p or grab(doc, "P7_SHADOW_SEEDS") != s:
        raise an.ScopeError("P7 prereg anchors do not reproduce from Random(20261104) draw")
    tr = set().union(*[eb.exp_train_seeds(b) for b in t])
    pr = set().union(*[eb.exp_probe_seeds(b) for b in p])
    if len(tr) != 200 or len(pr) != 315 or tr & pr:
        raise an.ScopeError("P7 seed spaces wrong")
    print("reproduce_draw OK; P7 spaces: 200 train / 315 probe / 8 shadow")


def probe_values(rows, cyc, ptype):
    v = [x["mn9_hz"] for x in rows if x.get("cycle") == cyc and x.get("ptype") == ptype]
    if len(v) != 2:
        raise an.IncompleteArtifacts(f"probe {ptype}@{cyc}: {len(v)} rows != 2")
    return v


def evaluate_rep(rep_dir: Path, acq, pristine, nodes, nid, sugar, bitter, lif_params, shadow) -> dict:
    rows = an.read_jsonl(rep_dir / "l6b_rankforget.jsonl", f"{rep_dir.name} jsonl")
    cyc_rows = [x for x in rows if "ptype" not in x]
    if len(cyc_rows) != 25:
        raise an.IncompleteArtifacts(f"{rep_dir.name}: {len(cyc_rows)} cycle rows != 25")
    final, _ = an.load_final_matrix(rep_dir / "ckpt_r0", f"{rep_dir.name} final")

    cos = {c: probe_values(rows, c, "cosugar") for c in PROBE_AT}
    alone = {c: probe_values(rows, c, "alone") for c in PROBE_AT}
    c1 = all(v >= THETA for c in (15, 20, 25) for v in cos[c])
    c2 = all(BAND[0] <= v <= BAND[1] for v in cos[25])

    def sim(stim, stim2=None, r2=None, seed=0):
        r = simulate_lif(final, nodes, lif_params, 1000.0, stimulated=stim,
                         stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
        return float(len(r.spike_times.get(MN9_L, [])))

    sug_alone = [sim(list(sugar), seed=s) for s in shadow[0:2]]
    cue_bitter = [sim(list(CUE_380), list(bitter), 200.0, seed=s) for s in shadow[2:4]]
    c3 = all(BAND[0] <= v <= BAND[1] for v in sug_alone) and all(v < THETA for v in cue_bitter)
    c4 = not any(x.get("guard_fired") for x in cyc_rows)

    d = (acq - pristine).tocoo()
    fp = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    sha = hashlib.sha256(json.dumps(fp).encode()).hexdigest()
    if sha != G380_FP_SHA or len(fp) != 158:
        raise an.ScopeError(f"g380 footprint hash mismatch {sha[:12]} n={len(fp)}")
    partners = sorted({j for _, j in fp})
    zero_in = {p for p in partners if sum(float(pristine[nid[b], p]) for b in bitter) == 0.0}
    if len(zero_in) != 45 or len(partners) != 73:
        raise an.ScopeError(f"census mismatch partners={len(partners)} zi={len(zero_in)}")
    zi_edges = [e for e in fp if e[1] in zero_in]
    if len(zi_edges) != 96:
        raise an.ScopeError(f"zi edges {len(zi_edges)} != 96")
    zi_floor = sum(1 for e in zi_edges if final[e] == 0.0)
    fp_floor = sum(1 for e in fp if final[e] == 0.0)
    c5 = zi_floor >= ZI_MIN and fp_floor >= FP_MIN

    acq_coo = acq.tocoo()
    acq_map = {(int(i), int(j)): float(v) for i, j, v in zip(acq_coo.row, acq_coo.col, acq_coo.data)}
    fin_coo = final.tocoo()
    sign_flips, structural_new = 0, 0
    pri_nz = set(zip(*pristine.nonzero()))
    for i, j, v in zip(fin_coo.row, fin_coo.col, fin_coo.data):
        i, j, v = int(i), int(j), float(v)
        if v == 0.0:
            continue
        a = acq_map.get((i, j), 0.0)
        if a != 0.0 and (v > 0) != (a > 0):
            sign_flips += 1
        if a == 0.0 and (i, j) not in pri_nz:
            structural_new += 1
    c6 = sign_flips == 0 and structural_new == 0

    branch = "PASS"
    neg_a = not (c1 and c2 and c5 and c6)
    neg_b = not (c3 and c4)
    if neg_a and neg_b:
        branch = "NEGATIVE-A+NEGATIVE-B"
    elif neg_a:
        branch = "NEGATIVE-A"
    elif neg_b:
        branch = "NEGATIVE-B"
    return {"rep": rep_dir.name, "c1_recovery": c1, "c2_band_c25": c2,
            "c3_innate_intact": c3, "c4_guard_silent": c4, "c5_floors": c5,
            "c6_structure": c6, "zi_floor": f"{zi_floor}/96", "fp_floor": f"{fp_floor}/158",
            "sign_flips": sign_flips, "structural_new": structural_new,
            "cosugar": {str(c): cos[c] for c in PROBE_AT},
            "alone": {str(c): alone[c] for c in PROBE_AT},
            "sugar_alone_probes": sug_alone, "cue_bitter_probes": cue_bitter,
            "branch": branch}


def aggregate(branches):
    if all(b == "PASS" for b in branches):
        return "PASS"
    if len(set(branches)) == 1:
        return branches[0]
    return "MIXED"


def main() -> int:
    reproduce_draw()
    doc = PREREG7.read_text(encoding="utf-8")
    train, probe, shadow = grab(doc, "P7_TRAIN_SEEDS"), grab(doc, "P7_PROBE_SEEDS"), grab(doc, "P7_SHADOW_SEEDS")
    if len(train) != N_REPS or len(probe) != 15 or len(shadow) != 8:
        raise an.ScopeError("P7 seed block sizes wrong")

    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in grn["sugar_R"]]
    bitter = [r["bodyId"] for r in grn["bitter_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    acq, _ = an.load_final_matrix(G380_R1CK, "R1 g380")

    per_rep = []
    for r in range(N_REPS):
        rep_dir = OUT_ROOT / f"rep_r{r}"
        if not (rep_dir / "l6b_rankforget.jsonl").exists():
            raise an.IncompleteArtifacts(f"missing rep {r}")
        per_rep.append(evaluate_rep(rep_dir, acq, matrix, nodes, nid, sugar, bitter, lif_params, shadow))
        b = per_rep[-1]
        print(f"{b['rep']}: c1={b['c1_recovery']} c2={b['c2_band_c25']} c3={b['c3_innate_intact']} "
              f"c4={b['c4_guard_silent']} c5={b['c5_floors']} ({b['zi_floor']},{b['fp_floor']}) "
              f"c6={b['c6_structure']} -> {b['branch']}")

    agg = aggregate([b["branch"] for b in per_rep])
    verdict = {
        "wp": "P2", "experiment": "Phase 7 WP-P2 GNG380 confirmatory unlearning (rank-targeted decay)",
        "prereg": "docs/PHASE_7_PREREG.md", "prereg_sha256": an.sha256_file(PREREG7),
        "harness_sha256": "08110ddfb2ae3b2a89782c4a48b4bd5e4a52f9f171febb8b91236dcd28427508",
        "rank_set_sha256": G380_FP_SHA,
        "seeds": {"train": train, "probe": probe, "shadow": shadow},
        "per_rep": per_rep, "aggregate": agg,
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "P2_VERDICT.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(f"AGGREGATE: {agg} -> {OUT_ROOT / 'P2_VERDICT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
