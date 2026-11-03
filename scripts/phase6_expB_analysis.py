"""Phase 6 Experiment B - frozen analysis for WP-L6b (rank-targeted forgetting).

Frozen by docs/PHASE_6_PREREG.md section 3 BEFORE any L6b run. Emits
results/phase6/wp_l6b/EXP_B_VERDICT.json only from complete artifacts;
missing/malformed artifacts -> loud failure, no verdict.

L6b seed scheme (harness writes the seed into every cycle row):
  train seed rep r, cycle c   = P6_TRAIN_SEEDS[r]  + r*1000 + c        (c=1..25)
  probe seed rep r, cycle cyc, rep2, off
                              = P6_PROBE_SEEDS[r]  + r*10000 + cyc*100 + rep2*10 + off
  sanity seed                 = P6_PROBE_SEEDS[r] + 999
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

PREREG6 = ROOT / "docs" / "PHASE_6_PREREG.md"
BASE = ROOT / "data/processed/neuprint_snapshots/run-007"
R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng521_feed_0"
G380_R1CK = ROOT / "results/phase2/taskB_r1/ckpt_l1_gng380_withhold_0"
L6B_ROOT = ROOT / "results/phase6/wp_l6b"
G380_ROOT = ROOT / "results/phase6/wp_l6b_g380"
VERDICT_PATH = L6B_ROOT / "EXP_B_VERDICT.json"

CUE = [15957, 16327]
G380_CUE = [50843, 53901, 103327, 129624, 556072, 559464]
UNTOUCHED = [13510, 18474, 12364, 14803, 14953, 66802, 516493, 524078, 555850]
N_CYCLES, PROBE_AT, N_REPS = 25, (5, 10, 15, 20, 25), 8
COSUGAR_BAND = (78, 88)
ZERO_BY_CYCLE = 15
G380_FP_SHA = "27517364b713c339e51927804896f269cb621791edba62f54a7679fb57eb5a3a"
DRAW_SEED = 20261103


def grab(doc_text: str, name: str) -> list[int]:
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg6 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def reproduce_draw(train: list[int], probe: list[int], shadow: list[int]) -> None:
    """Re-run the documented draw (Random(20261103), blocks 1.2M/1.3M/1.4M,
    sorted, excluding all dev+confirm seeds) and require exact equality."""
    dev = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    used = set(dev)
    for b in ct:
        used |= an.expected_train_seeds(b)
    for b in cp:
        used |= an.expected_probe_seeds(b)
        used.add(an.sanity_seed(b))
    rng = random.Random(DRAW_SEED)

    def draw(lo: int, hi: int, n: int) -> list[int]:
        out, seen = [], set()
        while len(out) < n:
            v = rng.randrange(lo, hi)
            if v not in seen and v not in used:
                seen.add(v)
                out.append(v)
        return sorted(out)

    if draw(1_200_000, 1_210_000, 8) != train:
        raise an.ScopeError("P6 train anchors do not reproduce from Random(20261103)")
    if draw(1_300_000, 1_310_000, 15) != probe:
        raise an.ScopeError("P6 probe anchors do not reproduce from Random(20261103)")
    if draw(1_400_000, 1_410_000, 8) != shadow:
        raise an.ScopeError("P6 shadow anchors do not reproduce from Random(20261103)")


def exp_train_seeds(base: int, rep: int) -> set[int]:
    return {base + rep * 1000 + c for c in range(1, N_CYCLES + 1)}


def exp_probe_seeds(base: int, rep: int) -> set[int]:
    s = {base + rep * 10000 + c * 100 + r2 * 10 + off
         for c in PROBE_AT for r2 in (0, 1) for off in (0, 5000)}
    s.add(base + 999)
    return s


def seed_spaces(train: list[int], probe: list[int]) -> tuple[set[int], set[int]]:
    tr: set[int] = set()
    for r in range(N_REPS):
        tr |= exp_train_seeds(train[r], r)
    pr: set[int] = set()
    for r in range(N_REPS):
        pr |= exp_probe_seeds(probe[r], r)
    return tr, pr


def evaluate_rep(r: int, train_base: int, probe_base: int,
                 carriers: frozenset, unt: frozenset,
                 acquired: sparse.csr_matrix, pristine: sparse.csr_matrix) -> dict:
    rep_dir = L6B_ROOT / f"rep_r{r}"
    rows = an.read_jsonl(rep_dir / "l6b_rankforget.jsonl", f"L6b rep {r} JSONL")
    cyc_rows = [x for x in rows if "ptype" not in x]
    probe_rows = [x for x in rows if "ptype" in x]
    if len(cyc_rows) != N_CYCLES:
        raise an.IncompleteArtifacts(f"rep {r}: {len(cyc_rows)} cycle rows, expected {N_CYCLES}")
    if len(probe_rows) != 20:
        raise an.IncompleteArtifacts(f"rep {r}: {len(probe_rows)} probe rows, expected 20")
    got_seeds = sorted(int(x["seed"]) for x in cyc_rows)
    if got_seeds != sorted(exp_train_seeds(train_base, r)):
        raise an.IncompleteArtifacts(f"rep {r}: cycle-row seeds != prereg-derived set")
    want_probes = {(c, pt, r2) for c in PROBE_AT for pt in ("alone", "cosugar") for r2 in (0, 1)}
    if {(x["cycle"], x["ptype"], x["rep2"]) for x in probe_rows} != want_probes:
        raise an.IncompleteArtifacts(f"rep {r}: probe grid incomplete")

    def vals(cyc, pt):
        return [x["mn9_hz"] for x in probe_rows if x["cycle"] == cyc and x["ptype"] == pt]

    alone = {c: vals(c, "alone") for c in PROBE_AT}
    cosg = {c: vals(c, "cosugar") for c in PROBE_AT}
    zero_cycles = [c for c in PROBE_AT if all(v == 0 for v in alone[c])]
    t2z = zero_cycles[0] if zero_cycles else None
    c1 = t2z is not None and t2z <= ZERO_BY_CYCLE
    c2 = all(all(v == 0 for v in alone[c]) for c in (15, 20, 25))
    cosg_all = [v for c in PROBE_AT for v in cosg[c]]
    c3 = all(COSUGAR_BAND[0] <= v <= COSUGAR_BAND[1] for v in cosg_all)
    c4 = not any(x.get("guard_fired") for x in cyc_rows)

    final, _ = an.load_final_matrix(rep_dir / "ckpt_r0", f"L6b rep {r} final")
    d = (final - acquired).tocoo()
    changed = {(int(i), int(j)): float(v) for i, j, v in zip(d.row, d.col, d.data) if v != 0}
    floors = sum(1 for e in carriers if final[e] == 0.0)
    unt_floors = sum(1 for e in unt if final[e] == 0.0)
    sign_flips = [e for e in carriers if final[e] < 0]
    d0 = (acquired - pristine).tocoo()
    acquired_edges = {(int(i), int(j)) for i, j, v in zip(d0.row, d0.col, d0.data) if v != 0}
    structural_new = [e for e in changed if e not in acquired_edges
                      and final[e] != 0 and acquired[e] == 0]
    c5 = floors == len(carriers) and unt_floors == len(unt) and not sign_flips and not structural_new

    branch = "PASS"
    if not (c1 and c2 and c5):
        branch = "NEGATIVE-A"
    if not (c3 and c4) or sign_flips or structural_new:
        branch = "NEGATIVE-A+NEGATIVE-B" if branch == "NEGATIVE-A" else "NEGATIVE-B"
    return {"rep": r, "trials_to_zero": t2z, "c1_zero_by_15": c1, "c2_persist": c2,
            "c3_cosugar_band": c3, "cosugar_min": min(cosg_all), "cosugar_max": max(cosg_all),
            "c4_guard_silent": c4, "c5_floors": c5, "carriers_at_floor": floors,
            "untouched_at_floor": unt_floors, "sign_flips": len(sign_flips),
            "structural_new": len(structural_new), "branch": branch,
            "alone_traj": {str(c): alone[c] for c in PROBE_AT}}


def evaluate_g380() -> dict:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    grn = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    bitter = [r["bodyId"] for r in grn["bitter_R"]]
    pristine = matrix
    acq, _ = an.load_final_matrix(G380_R1CK, "R1 gng380")
    d = (acq - pristine).tocoo()
    fp = sorted((int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0.0)
    fp_sha = hashlib.sha256(json.dumps(fp).encode()).hexdigest()
    if fp_sha != G380_FP_SHA or len(fp) != 158:
        raise an.ScopeError(f"GNG380 footprint hash/size mismatch: {fp_sha} {len(fp)}")
    partners = sorted({j for _, j in fp})
    zero_in = {p for p in partners
               if sum(float(matrix[nid[b], p]) for b in bitter) == 0.0}
    if len(zero_in) != 45 or len(partners) != 73:
        raise an.ScopeError(f"GNG380 census mismatch: partners {len(partners)}, zero-input {len(zero_in)}")
    zi_edges = [e for e in fp if e[1] in zero_in]

    out = {"footprint_edges": len(fp), "partners": len(partners),
           "zero_input_partners": len(zero_in), "zero_input_edges": len(zi_edges), "reps": []}
    boundary = False
    for r in range(2):
        rep_dir = G380_ROOT / f"rep_r{r}"
        rows = an.read_jsonl(rep_dir / "l6b_rankforget.jsonl", f"G380 rep {r} JSONL")
        guard_ok = not any(x.get("guard_fired") for x in rows if "ptype" not in x)
        final, _ = an.load_final_matrix(rep_dir / "ckpt_r0", f"G380 rep {r} final")
        zi_floor = sum(1 for e in zi_edges if final[e] == 0.0)
        fp_floor = sum(1 for e in fp if final[e] == 0.0)
        out["reps"].append({"rep": r, "guard_silent": guard_ok,
                            "zero_input_edges_at_floor": f"{zi_floor}/{len(zi_edges)}",
                            "footprint_at_floor": f"{fp_floor}/{len(fp)}"})
        if guard_ok and zi_floor >= 1:
            boundary = True
    out["boundary_verdict"] = "POSITIVE-BOUNDARY" if boundary else "NEGATIVE-BOUNDARY"
    return out


def aggregate(branches: list[str]) -> str:
    if all(b == "PASS" for b in branches):
        return "PASS"
    if len(set(branches)) == 1:
        return branches[0]
    return "MIXED"


def main() -> int:
    doc = PREREG6.read_text(encoding="utf-8")
    train = grab(doc, "P6_TRAIN_SEEDS")
    probe = grab(doc, "P6_PROBE_SEEDS")
    shadow = grab(doc, "P6_SHADOW_SEEDS")
    if len(train) != N_REPS or len(probe) != 15 or len(shadow) != 8:
        raise an.ScopeError("prereg6 seed block sizes wrong")
    reproduce_draw(train, probe, shadow)

    tr_space, pr_space = seed_spaces(train, probe)
    dev = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    conf = set()
    for b in ct:
        conf |= an.expected_train_seeds(b)
    for b in cp:
        conf |= an.expected_probe_seeds(b)
        conf.add(an.sanity_seed(b))
    all6 = tr_space | pr_space
    if len(all6) != len(tr_space) + len(pr_space):
        raise an.ScopeError("P6 seed space has internal collisions")
    if all6 & (dev | conf):
        raise an.ScopeError("P6 seed space overlaps dev/confirm spaces")

    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    acquired, _ = an.load_final_matrix(R1CK, "R1 gng521")
    cue_idx = {nid[c] for c in CUE}
    unt_idx = {nid[p] for p in UNTOUCHED}
    carriers, unt = an.derive_carriers(matrix, acquired, cue_idx, unt_idx)

    reps = [evaluate_rep(r, train[r], probe[r], carriers, unt, acquired, matrix)
            for r in range(N_REPS)]
    g380 = evaluate_g380()
    verdict = {
        "experiment": "Phase 6 Experiment B (WP-L6b rank-targeted forgetting)",
        "prereg": "docs/PHASE_6_PREREG.md", "prereg_sha256": an.sha256_file(PREREG6),
        "seeds": {"train": train, "probe": probe, "shadow_reserved": shadow,
                  "train_space": len(tr_space), "probe_space": len(pr_space),
                  "overlap_dev_confirm": 0},
        "per_rep": reps, "aggregate": aggregate([x["branch"] for x in reps]),
        "g380_probe": g380,
    }
    L6B_ROOT.mkdir(parents=True, exist_ok=True)
    VERDICT_PATH.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    for x in reps:
        print(f"rep {x['rep']}: t2z={x['trials_to_zero']} floors={x['carriers_at_floor']}/25"
              f"+{x['untouched_at_floor']}/9 cosugar=[{x['cosugar_min']},{x['cosugar_max']}]"
              f" guard_ok={x['c4_guard_silent']} -> {x['branch']}")
    print(f"GNG380 probe: {g380['boundary_verdict']} "
          f"(zero-input edges at floor: {[x['zero_input_edges_at_floor'] for x in g380['reps']]})")
    print(f"AGGREGATE: {verdict['aggregate']}  -> {VERDICT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
