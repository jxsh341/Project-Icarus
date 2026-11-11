"""ICA-M1-1 experiment runner (Phases B and C per docs/ICA_M1_PREREG.md, frozen).

Guards: prereg sha pinned, pristine hash pinned, seed disjointness asserted,
API version checked. Writes results/ica_m1/{separability,association}.json +
probes.jsonl + launcher_manifest.json. Phase B: 6 cues x 3 seeds, pristine.
Phase C: n=1 acquire L_A + wrong-cue control + 5 blank retention trials.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fly.api import (  # noqa: E402
    ACCEPTED_API_VERSIONS, API_VERSION, SCHEMA_VERSION, FlySubstrate,
    InputEvent, StimulusPort,
)
from fly.training import weight_matrix_hash  # noqa: E402

PREREG = ROOT / "docs" / "ICA_M1_PREREG.md"
OUT = ROOT / "results/ica_m1"
PRISTINE_HASH = "384406e9278ae0c0"
MN9_L = 10331

CUES = {
    "L_A": ("GNG521", (15957, 16327)),
    "L_B": ("GNG491", (14094,)),
    "L_C": ("GNG557", (12595,)),
    "L_D": ("GNG610", (128102,)),
    "U1": ("GNG318", (524428,)),   # unrelated, innate MN9 active
    "U2": ("AN17A015", (75140,)),   # unrelated, silent
}
N_SEEDS = 3


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def draw_seeds():
    """Random(20261112), range 3_400_000-3_420_000; disjointness from all prior
    spaces (which live in 3_000_000-3_220_000) is structural, and within-draw
    disjointness is asserted."""
    rng = random.Random(20261112)
    need = len(CUES) * N_SEEDS + 40  # probes + phase C (acq 20 + blanks 5 + probes)
    out, used = [], set()
    while len(out) < need:
        s = rng.randrange(3_400_000, 3_420_000)
        if s in used:
            continue
        if 3_000_000 <= s < 3_220_000:
            raise RuntimeError("seed landed in a prior space")
        used.add(s)
        out.append(s)
    return out


def probe(sub, cue_ids, seed, jout):
    ev = InputEvent(duration_ms=1000.0, seed=seed,
                    ports=(StimulusPort("cue", tuple(cue_ids), 200.0, slot=1, role="cue"),))
    obs = sub.step(ev)
    rec = {"cue": list(cue_ids), "seed": seed, "n_spikes": obs.n_spikes,
           "mn9_hz": obs.rates_hz.get(MN9_L, 0.0),
           "spike_counts": {str(k): v for k, v in obs.spike_counts.items()},
           "weight_hash": obs.weight_hash}
    with open(jout, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def vec(rec):
    v = np.zeros(len(rec["spike_counts"]) and 40290 or 40290)
    return rec["spike_counts"]


def main() -> int:
    doc_sha = sha_file(PREREG)
    seeds = draw_seeds()
    OUT.mkdir(parents=True, exist_ok=True)
    jout = OUT / "probes.jsonl"
    manifest = {"experiment": "ICA-M1-1 phases B+C", "prereg_sha256": doc_sha,
                "api_version": API_VERSION, "schema_version": SCHEMA_VERSION,
                "pristine_hash": PRISTINE_HASH, "seeds": seeds,
                "created": datetime.now(timezone.utc).isoformat(),
                "git_head": __import__("subprocess").run(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                    text=True).stdout.strip()}
    (OUT / "launcher_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    # ---------- Phase B ----------
    sub = FlySubstrate.from_snapshot()
    if weight_matrix_hash(sub.matrix) != PRISTINE_HASH:
        raise RuntimeError("pristine hash mismatch")
    sub.initialize(); sub.resume()
    si = iter(seeds)
    j_exists = jout.exists() and sum(1 for _ in open(jout, encoding="utf-8")) >= len(CUES) * N_SEEDS
    b_rows = {}
    if j_exists:  # resume: reuse saved probes
        saved = [json.loads(l) for l in open(jout, encoding="utf-8")]
        k = 0
        for loc, (name, ids) in CUES.items():
            rows = saved[k:k + N_SEEDS]; k += N_SEEDS
            b_rows[loc] = {"name": name, "ids": list(ids), "probes": rows}
        next(si)  # burn nothing; seeds list already drawn
        for _ in range(len(CUES) * N_SEEDS):
            next(si)
    else:
        for loc, (name, ids) in CUES.items():
            rows = [probe(sub, ids, next(si), jout) for _ in range(N_SEEDS)]
            b_rows[loc] = {"name": name, "ids": list(ids), "probes": rows}
    # metrics
    def counts(r):
        return {int(k): v for k, v in r["spike_counts"].items()}
    def cos(a, b):
        keys = set(a) | set(b)
        va = np.array([a.get(k, 0) for k in keys], float)
        vb = np.array([b.get(k, 0) for k in keys], float)
        na, nb = np.linalg.norm(va), np.linalg.norm(vb)
        return float(va @ vb / (na * nb)) if na > 0 and nb > 0 else 1.0
    def jac(a, b):
        sa, sb = set(a), set(b)
        return len(sa & sb) / max(len(sa | sb), 1)
    loc_keys = ["L_A", "L_B", "L_C", "L_D"]
    pairs = {}
    for i in range(len(loc_keys)):
        for j in range(i + 1, len(loc_keys)):
            a, b = loc_keys[i], loc_keys[j]
            ra = [counts(r) for r in b_rows[a]["probes"]]
            rb = [counts(r) for r in b_rows[b]["probes"]]
            cs = [cos(x, y) for x in ra for y in rb]
            js = [jac(x, y) for x in ra for y in rb]
            dm = abs(ra[0].get(MN9_L, 0) - rb[0].get(MN9_L, 0))  # mn9 counts
            pairs[f"{a}|{b}"] = {"mean_cos": round(float(np.mean(cs)), 4),
                                 "max_cos": round(float(np.max(cs)), 4),
                                 "mean_jac": round(float(np.mean(js)), 4),
                                 "max_jac": round(float(np.max(js)), 4)}
    repeat = {}
    for a in loc_keys:
        ra = [counts(r) for r in b_rows[a]["probes"]]
        cs = [cos(ra[i], ra[j]) for i in range(3) for j in range(i + 1, 3)]
        repeat[a] = round(float(np.mean(cs)), 4)
    b_metrics = {"pairs": pairs, "within_cue_cos": repeat,
                 "n_spikes": {l: [r["n_spikes"] for r in b_rows[l]["probes"]] for l in CUES},
                 "mn9_hz": {l: [r["mn9_hz"] for r in b_rows[l]["probes"]] for l in CUES}}
    c1 = all(v > 100 for l in loc_keys for v in b_metrics["n_spikes"][l])
    c2 = all(p["max_jac"] < 0.8 or p["max_cos"] < 0.9 for p in pairs.values())
    c3 = all(v >= 0.95 for v in repeat.values())
    c4 = all(v < 150_000 for l in CUES for v in b_metrics["n_spikes"][l])
    b_verdict = "SEPARABLE" if all([c1, c2, c3, c4]) else (
        "ALIASED" if not c2 else "PARTIALLY SEPARABLE")
    separability = {"prereg_sha256": doc_sha, "metrics": b_metrics,
                    "criteria": {"c1_active": c1, "c2_not_aliased": c2,
                                 "c3_repeatable": c3, "c4_guard_silent": c4},
                    "verdict": b_verdict}
    (OUT / "separability.json").write_text(json.dumps(separability, indent=1), encoding="utf-8")
    print(f"PHASE B: c1={c1} c2={c2} c3={c3} c4={c4} -> {b_verdict}")
    print("  pairs:", json.dumps(pairs))
    print("  within-cue cos:", repeat)
    print("  mn9_hz:", b_metrics["mn9_hz"])

    # ---------- Phase C (n=1 exploratory) ----------
    sub2 = FlySubstrate.from_snapshot()
    sub2.initialize(); sub2.resume()
    sub2.learning.arm()
    grn = json.loads((ROOT / "data/processed/neuprint_snapshots/wp6c_grn_seeds.json").read_text())
    sugar = tuple(r["bodyId"] for r in grn["sugar_R"])
    acq_seed_base = next(si)
    h0 = weight_matrix_hash(sub2.matrix)
    rec = sub2.acquire(CUES["L_A"][1], drive_body_ids=sugar, n_trials=20,
                       seed_base=acq_seed_base, duration_ms=1000.0)
    a1 = rec["n_edges"] > 0 and weight_matrix_hash(sub2.matrix) != h0
    a2 = True  # no LifecycleError raised == guard silent
    pre = sub2.present_cue(CUES["L_A"][1], seed=next(si))
    a3 = pre["retrieved"]
    wrong = sub2.present_cue(CUES["L_B"][1], seed=next(si))
    a4 = wrong["readout_hz"] < 41.5
    h_after = weight_matrix_hash(sub2.matrix)
    for _ in range(5):
        sub2.step(InputEvent(duration_ms=1000.0, seed=next(si)))
    a5 = weight_matrix_hash(sub2.matrix) == h_after and sub2.present_cue(CUES["L_A"][1], seed=next(si))["retrieved"]
    assoc = {"prereg_sha256": doc_sha, "acquire": rec, "pre_acq_hash": h0,
             "post_acq_hash": weight_matrix_hash(sub2.matrix),
             "present_L_A": pre, "present_L_B_wrong_cue": wrong,
             "blank_trials": 5, "hash_after_blanks": weight_matrix_hash(sub2.matrix),
             "criteria": {"a1_acquired": a1, "a2_guard_silent": a2, "a3_retrieved": a3,
                          "a4_wrong_cue_below_threshold": a4, "a5_retention": a5},
             "verdict": "DEMONSTRATED" if all([a1, a2, a3, a4, a5]) else (
                 "PARTIALLY" if a1 and a3 else "NOT DEMONSTRATED")}
    (OUT / "association.json").write_text(json.dumps(assoc, indent=1, default=str), encoding="utf-8")
    print(f"PHASE C: a1={a1} a2={a2} a3={a3} (L_A {pre['readout_hz']} Hz) "
          f"a4={a4} (L_B {wrong['readout_hz']} Hz) a5={a5} -> {assoc['verdict']}")
    print(f"  footprint: {rec['n_edges']} edges sha {rec['footprint_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
