"""GNG557 full-diligence steps 2+3 (registry, pre-registered 2026-09-25).

Step 2 — full original suite (c)-(f) at group level, n=10 fresh seeds
(33600-33609), cue driven PRIMARY, explicit 200 Hz:
  census (nt/status/hops/in-out/leg-2 max), cue-alone (c: max==0),
  cue-cosugar (d: min>=41.5), aggregate target Jaccard vs GNG521 (f).

Step 3 — eta* range-finder under FROZEN 1-hop L1, grid {1e-5,1e-4,1e-3},
10 accumulated trials + probe per eta, seeds 33700-33709 / probe 33750.

Verdicts printed and checkpointed; freeze requires suite PASS AND
acquisition OPEN (probe > 0 at some eta, no guard fire).
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from collections import deque

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUTDIR = Path("results/phase2/wp3_pilot")
MN9_L = 10331
THRESH = 41.5
W_MAX = 766.0
ETAS = [1e-5, 1e-4, 1e-3]
GNG521 = [15957, 16327]


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


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


def probe_arm(W, nodes, stim, stim2, r2, label, typ, seed, out):
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

    gng557 = [b for b, r in meta.items() if r.get("type") == "GNG557"]
    print(f"GNG557 members: {gng557}", flush=True)
    in_closure = [b for b in gng557 if b in idx]
    if len(in_closure) != len(gng557):
        print(f"WARNING: {len(gng557) - len(in_closure)} member(s) outside closure", flush=True)

    # ---- Step 2: census ----
    print("\n== Step 2 census (a)/(b') ==", flush=True)
    into_mn9 = {int(r): float(w) for r, w in zip(W[:, mn9].tocoo().row, W[:, mn9].tocoo().data)}
    census = []
    for b in in_closure:
        i = idx[b]
        row = W.getrow(i)
        legs2 = [(int(t), into_mn9.get(int(t), 0.0)) for t in row.indices]
        max_l2 = max((w for _, w in legs2 if w > 0), default=0.0)
        hops = bfs_exc_hops(W, i, mn9)
        r = meta[b]
        census.append({"bodyId": b, "nt": r.get("predictedNt"), "status": r.get("status"),
                       "in_deg": int(W[:, i].nnz), "out_deg": int(W[i, :].nnz),
                       "hops": hops, "max_leg2": max_l2})
        print(f"  {b}: nt={r.get('predictedNt')} status={r.get('status')} "
              f"in={census[-1]['in_deg']} out={census[-1]['out_deg']} hops={hops} max_leg2={max_l2}",
              flush=True)

    # ---- Step 2: (f) Jaccard vs GNG521 ----
    t557 = set()
    for b in in_closure:
        t557.update(W[idx[b], :].nonzero()[1].tolist())
    t521 = set()
    for b in GNG521:
        t521.update(W[idx[b], :].nonzero()[1].tolist())
    jac = len(t557 & t521) / max(1, len(t557 | t521))
    print(f"  (f) Jaccard(GNG557, GNG521) = {jac:.3f}", flush=True)

    # ---- Step 2: group probes (c)/(d), n=10 ----
    print("\n== Step 2 group probes, n=10 (seeds 33600-33609) ==", flush=True)
    out = Path("results/phase2/wp2_cue_probe_gng557.jsonl")
    alone, co = [], []
    for seed in range(33_600, 33_610):
        r = probe_arm(W, nodes, in_closure, None, None, "cue_alone", "GNG557", seed, out)
        alone.append(r["mn9_l_hz"])
        r = probe_arm(W, nodes, sugar, in_closure, 200.0, "cue_cosugar", "GNG557", seed, out)
        co.append(r["mn9_l_hz"])
    c_ok, d_ok = max(alone) == 0, min(co) >= THRESH
    suite_pass = c_ok and d_ok
    print(f"  alone={alone} cosugar={co} -> (c){'PASS' if c_ok else 'FAIL'} (d){'PASS' if d_ok else 'FAIL'}",
          flush=True)

    # ---- Step 3: eta* range-finder ----
    print("\n== Step 3 eta* range-finder, frozen 1-hop L1 ==", flush=True)
    outb = OUTDIR / "stage_b_gng557.jsonl"
    matrix0 = W
    eta_star = None
    for eta in ETAS:
        rows = []
        if outb.exists():
            rows = [json.loads(l) for l in outb.read_text(encoding="utf-8").splitlines() if l.strip()]
        if any(r.get("eta") == eta for r in rows):
            continue
        cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
        run = TrainingRun(matrix0, nodes, HebbianRule(cfg), guard(), MN9_L,
                          f"b4_{eta}", OUTDIR / f"ckpt_b4_{eta}",
                          lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
        fired = None
        for t in range(10):
            s = TrialSpec(trial=t, seed=33_700 + t, cue_body_ids=tuple(in_closure),
                          drive_body_ids=tuple(sugar), drive2_body_ids=(),
                          r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(s)
            if rec.get("guard_fired"):
                fired = rec["guard_fired"]
                break
        probe_hz = None
        if not fired:
            ps = TrialSpec(trial=10, seed=33_750, cue_body_ids=tuple(in_closure),
                           drive_body_ids=(), drive2_body_ids=(),
                           r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0, is_probe=True)
            probe_hz = run.run_trial(ps)["readout_hz"]
            sparse.save_npz(OUTDIR / f"weights_b4_{eta}.npz", run.matrix)
        with outb.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"eta": eta, "guard": fired, "probe_hz": probe_hz}) + "\n")
            fh.flush()
        print(f"  eta={eta}: guard={'FIRED' if fired else 'ok'} probe={probe_hz}", flush=True)
        if not fired and probe_hz and probe_hz > 0 and eta_star is None:
            eta_star = eta
    if eta_star is None:
        rows = [json.loads(l) for l in outb.read_text(encoding="utf-8").splitlines() if l.strip()]
        for r in reversed(rows):
            if not r["guard"]:
                eta_star = r["eta"]
                break

    gate_open = eta_star is not None
    # verify eta_star actually expressed
    rows = [json.loads(l) for l in outb.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        if r["eta"] == eta_star and not (r["probe_hz"] or 0) > 0:
            gate_open = False

    verdict = {"census": census, "jaccard_vs_521": jac, "alone": alone, "cosugar": co,
               "c_pass": c_ok, "d_pass": d_ok, "eta_star": eta_star,
               "suite_pass": suite_pass, "gate_open": gate_open,
               "freeze": bool(suite_pass and gate_open)}
    Path("results/phase2/wp2_gng557_verdict.json").write_text(json.dumps(verdict, indent=2),
                                                              encoding="utf-8")
    print(f"\neta* = {eta_star}; suite {'PASS' if suite_pass else 'FAIL'}; "
          f"gate {'OPEN' if gate_open else 'CLOSED'}; "
          f"FREEZE: {'YES - pair v3 = GNG521+GNG557' if verdict['freeze'] else 'NO'}", flush=True)
    return 0 if verdict["freeze"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
