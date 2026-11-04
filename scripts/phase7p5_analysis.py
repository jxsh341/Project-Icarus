"""Phase 7 P5 analysis - frozen per-arm verdicts (docs/PHASE_7P5_PREREG.md).

Non-aggregating: per-arm verdicts are the result.
- true   : PASS iff aloneA25 == 0 (both seeds, both reps) and all cosA25 in band
- thresh4: SENSITIVE iff any aloneA25 > 0, else INSENSITIVE-TO-WEAK-EDGES
- hop1   : COLLATERAL iff any cosA25 outside band, else CLEAN
c5: guard silent on all rows (any firing invalidates the rep, reported).
Emits results/phase7p5/P5_VERDICT.json.
"""
from __future__ import annotations

import ast
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase5_expA_analysis as an  # noqa: E402
import phase7p4_analysis as p4  # noqa: E402
import phase7p4b_analysis as p4b  # noqa: E402

PREREG = ROOT / "docs/PHASE_7P5_PREREG.md"
OUT_ROOT = ROOT / "results/phase7p5"
PROBE_AT = (5, 15, 25)
BAND = (75, 95)
ARM_OF = {0: "true", 1: "true", 2: "thresh4", 3: "thresh4", 4: "hop1", 5: "hop1"}


def grab(doc_text, name):
    m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", doc_text)
    if not m:
        raise an.ScopeError(f"prereg7p5 missing {name}")
    return list(ast.literal_eval("[" + m.group(1) + "]"))


def probe_space(b): return {b + 100 * c + 10 * p + s for c in PROBE_AT for p in (0, 1) for s in (0, 1)}


def p5_prior():
    prior = p4b.p4b_prior()
    doc = PREREG.read_text(encoding="utf-8")
    for b in grab(doc, "P5_PROBE_BASES"):
        prior |= probe_space(b)
    return prior


def reproduce_draw():
    doc = PREREG.read_text(encoding="utf-8")
    rng = random.Random(20261111)
    prior = p4b.p4b_prior()  # excludes P5 bases themselves; drawn below and checked
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

    pb = draw(6, probe_space, 12)
    if pb != grab(doc, "P5_PROBE_BASES"):
        raise an.ScopeError("P5 seeds do not reproduce from Random(20261111)")
    allsp = set().union(*[probe_space(b) for b in pb])
    if allsp & prior:
        raise an.ScopeError("P5 spaces overlap prior")
    print(f"reproduce_draw OK; P5 spaces: {len(allsp)} seeds, disjoint from {len(prior)} prior")


def main() -> int:
    reproduce_draw()
    doc = PREREG.read_text(encoding="utf-8")
    reps = []
    for r in range(6):
        rd = OUT_ROOT / f"rep_r{r}"
        rows = an.read_jsonl(rd / "unl.jsonl", f"unl r{r}")
        fin = json.loads((rd / "final.json").read_text())
        probes = [x for x in rows if x.get("stage") == "probe"]
        if len(probes) != 12:
            raise an.IncompleteArtifacts(f"r{r} probes != 12")
        arm = ARM_OF[r]
        if fin["arm"] != arm:
            raise an.ScopeError(f"r{r} arm mismatch")
        aloneA25 = sorted(x["mn9_hz"] for x in probes if x["ptype"] == "aloneA" and x["cycle"] == 25)
        cosA25 = sorted(x["mn9_hz"] for x in probes if x["ptype"] == "cosA" and x["cycle"] == 25)
        guard_ok = not any(x.get("guard_fired") for x in rows)
        reps.append({"rep": r, "arm": arm, "aloneA25": aloneA25, "cosA25": cosA25,
                     "guard_ok": guard_ok, "n_edges": fin["n_edges"], "edges_sha256": fin["edges_sha256"]})

    arms = {}
    for arm in ("true", "thresh4", "hop1"):
        rs = [x for x in reps if x["arm"] == arm]
        a25 = [v for x in rs for v in x["aloneA25"]]
        c25 = [v for x in rs for v in x["cosA25"]]
        g = all(x["guard_ok"] for x in rs)
        if arm == "true":
            verdict = "PASS" if (all(v == 0 for v in a25) and all(BAND[0] <= v <= BAND[1] for v in c25) and g) else "FAIL"
        elif arm == "thresh4":
            verdict = ("SENSITIVE" if any(v > 0 for v in a25) else "INSENSITIVE-TO-WEAK-EDGES") if g else "INVALID-GUARD"
        else:
            verdict = ("COLLATERAL" if any(not (BAND[0] <= v <= BAND[1]) for v in c25) else "CLEAN") if g else "INVALID-GUARD"
        arms[arm] = {"verdict": verdict, "aloneA25": a25, "cosA25": c25, "guard_ok": g,
                     "reps": [x["rep"] for x in rs]}

    results = {"wp": "P5", "prereg": "docs/PHASE_7P5_PREREG.md",
               "prereg_sha256": an.sha256_file(PREREG), "reps": reps, "arms": arms}
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "P5_VERDICT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for x in reps:
        print(f"r{x['rep']} {x['arm']}: aloneA25={x['aloneA25']} cosA25={x['cosA25']} guard={x['guard_ok']} n_edges={x['n_edges']}")
    print(json.dumps(arms, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
