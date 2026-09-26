"""GNG611 + GNG622 full probe suite — the COMPLETE original criteria set,
re-run from scratch per the IR94e lesson (a candidate can clear the
currently-focused check and fail one you weren't looking at).

Criteria (a)-(f), frozen 2026-09-25 (registry):
  (a) excitatory NT
  (b) structural path to readout <= 3 hops -> AMENDED: hop PARITY <= 2
      for BOTH cues (the PRW043 lesson)
  (c) probe-verified zero baseline MN9_L expression, cue-alone
  (d) no suppression of innate sugar-feed under co-stimulation
  (e) no literature-documented / NT-mediated state-conditional valence
      (literature check done; uncharacterized != neutral -> probes decide)
  (f) target-set overlap between cues neither ~1.0 nor ~0

Arms (n=10, seeds 32000-32009, explicit 200 Hz, cue driven PRIMARY
exactly as training will drive it):
  cue_alone / cue_cosugar per type-group (all members in closure).
PASS = (c) max(alone)==0 AND (d) min(cosugar)>=41.5, both groups.

This script runs the GROUP-level probe (the freeze-gate level used
for GNG521+PRW043). Structural census + (f) computed from the frozen
matrix. Results checkpointed per trial.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from collections import deque

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase2/wp2_cue_probe_gng611_gng622.jsonl")
MN9_L = 10331
THRESH = 41.5
SEEDS = range(32_000, 32_010)


def bfs_exc_hops(W, src, dst):
    seen = {src: 0}
    q = deque([src])
    while q:
        c = q.popleft()
        if c == dst:
            return seen[c]
        row = W.getrow(c)
        for t, w in zip(row.indices, row.data):
            if w <= 0:
                continue
            if t not in seen:
                seen[t] = seen[c] + 1
                q.append(t)
    return None


def run_arm(W, nodes, stim, stim2, r2, label, typ, seed, out):
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("label") == label and r.get("type") == typ and r.get("seed") == seed:
                return r
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    t0 = time.time()
    res = simulate_lif(W, nodes, params, duration_ms=1000.0,
                       stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    rec = {"label": label, "type": typ, "seed": seed,
           "mn9_l_hz": len(res.spike_times.get(MN9_L, [])),
           "total_spikes": res.n_spikes, "n_spiking": len(res.spike_times),
           "wall_s": round(time.time() - t0, 1)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
    return rec


def main() -> int:
    W = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(nodes)}
    mn9 = idx[MN9_L]
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]

    meta = {}
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            meta[r["bodyId"]] = r

    groups = {}
    for t in ("GNG611", "GNG622"):
        groups[t] = [b for b, r in meta.items() if r.get("type") == t]
    print("== (a)+(b) structural census ==", flush=True)
    census = {}
    for t, ids in groups.items():
        rows = []
        for b in ids:
            if b not in idx:
                rows.append({"bodyId": b, "in_closure": False})
                continue
            i = idx[b]
            r = meta[b]
            hops = bfs_exc_hops(W, i, mn9)
            rows.append({"bodyId": b, "in_closure": True,
                         "nt": r.get("predictedNt"), "status": r.get("status"),
                         "side": r.get("rootSide"),
                         "in_deg": int(W[:, i].nnz), "out_deg": int(W[i, :].nnz),
                         "exc_hops_to_mn9": hops})
        census[t] = rows
        for r in rows:
            print(f"  {t} {r['bodyId']}: nt={r.get('nt')} status={r.get('status')} "
                  f"in={r.get('in_deg')} out={r.get('out_deg')} hops={r.get('exc_hops_to_mn9')}",
                  flush=True)

    # (f) target Jaccard between the two groups' aggregate target sets
    ta = set()
    tb = set()
    for b in groups["GNG611"]:
        if b in idx:
            ta.update(W[idx[b], :].nonzero()[1].tolist())
    for b in groups["GNG622"]:
        if b in idx:
            tb.update(W[idx[b], :].nonzero()[1].tolist())
    jac = len(ta & tb) / max(1, len(ta | tb))
    print(f"  (f) aggregate target Jaccard = {jac:.3f}", flush=True)

    print("\n== (c)+(d) group probes, n=10 each ==", flush=True)
    verdict = {"census": census, "target_jaccard": jac}
    ok = True
    for t, ids in groups.items():
        in_closure = [b for b in ids if b in idx]
        alone, co = [], []
        for seed in SEEDS:
            r = run_arm(W, nodes, in_closure, None, None, "cue_alone", t, seed, OUT)
            alone.append(r["mn9_l_hz"])
            r = run_arm(W, nodes, sugar, in_closure, 200.0, "cue_cosugar", t, seed, OUT)
            co.append(r["mn9_l_hz"])
        c_ok, d_ok = max(alone) == 0, min(co) >= THRESH
        ok = ok and c_ok and d_ok
        print(f"  {t}: alone={alone} cosugar={co} -> (c){'PASS' if c_ok else 'FAIL'} "
              f"(d){'PASS' if d_ok else 'FAIL'}", flush=True)
        verdict[t] = {"alone": alone, "cosugar": co, "c_pass": c_ok, "d_pass": d_ok}

    verdict["overall"] = "PASS" if ok else "FAIL"
    Path("results/phase2/wp2_gng611_gng622_verdict.json").write_text(
        json.dumps(verdict, indent=2), encoding="utf-8")
    print(f"\nOVERALL: {verdict['overall']}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
