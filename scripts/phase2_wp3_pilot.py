"""FLY-LEARN-001 WP3: L1 acquisition pilot (pre-registered design).

Registry section "WP3 L1 acquisition pilot — pre-registered design"
(2026-09-25) is the authority for every choice here. Read it before
editing this script.

Stages:
  A  Confirmatory baseline, n=10 fresh seeds (30000-30009) per cue x
     {alone, cosugar}. HALT (exit 2) if the frozen pair's baseline
     facts do not hold.
  B  Eta range-finder: GNG521 only, eta in {1e-5, 1e-4, 1e-3},
     10 training trials + 1 cue-alone probe. eta* = smallest eta with
     probe expression and no guard fire; else largest eta with no
     guard fire; halt if all fire.
  C  L1 pilot: 3 seeds x 2 cues x 20 training trials, cue-alone
     probes after trials 5/10/15/20, V_MAG, w_max=766, guard live.
  D  L0 control: identical schedule, plasticity=None.

All runs checkpointed per trial to JSONL; resumable; explicit 200 Hz
everywhere; cue = PRIMARY population, sugar = SECONDARY (identical
wiring to the group probes).
"""

from __future__ import annotations

import dataclasses
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif
from fly.plasticity import HebbianRule, PlasticityConfig, PlasticityGuard, Semantics, StabilityThresholds
from fly.training import TrainingRun, TrialSpec, weight_matrix_hash

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUTDIR = Path("results/phase2/wp3_pilot")
MN9_L = 10331
W_MAX = 766.0
THRESH = 41.5
CUES = {
    "GNG521": [15957, 16327],
    "PRW043": [25250, 26891, 37670, 39767, 69045],
}
ETA_GRID = [1e-5, 1e-4, 1e-3]


def load_world():
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    return matrix, node_ids, sugar


def guard():
    return PlasticityGuard(StabilityThresholds(
        max_spikes_per_trial=150_000, spontaneous_rate_hz=5.0,
        inh_weight_drift_frac=0.20))


def trial(params_matrix, node_ids, stim, stim2, r2, seed, duration=1000.0):
    params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    t0 = time.time()
    r = simulate_lif(params_matrix, node_ids, params, duration_ms=duration,
                      stimulated=stim, stimulated2=stim2, r_poisson2_Hz=r2, seed=seed)
    return r, round(time.time() - t0, 1)


def append(out: Path, rec: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def done_keys(out: Path) -> set:
    if not out.exists():
        return set()
    keys = set()
    for line in out.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            keys.add(tuple(sorted([(k, str(v)) for k, v in r.items()
                                   if k not in ("mn9_l_hz", "total_spikes", "n_spiking", "wall_s")])))
    return keys


def seen(out: Path, **kw) -> bool:
    if not out.exists():
        return False
    probe = {k: str(v) for k, v in kw.items()}
    for line in out.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        got = {k: str(r.get(k)) for k in probe}
        if all(got.get(k) == v for k, v in probe.items()):
            return True
    return False


# ---------------------------------------------------------------- Stage A

def stage_a(matrix, node_ids, sugar) -> bool:
    out = OUTDIR / "stage_a_baseline.jsonl"
    print("== Stage A: confirmatory baseline, n=10 fresh seeds ==", flush=True)
    ok = True
    for cue, ids in CUES.items():
        alone, co = [], []
        for seed in range(30_000, 30_010):
            if not seen(out, stage="A", cue=cue, arm="alone", seed=seed):
                r, w = trial(matrix, node_ids, ids, None, None, seed)
                append(out, {"stage": "A", "cue": cue, "arm": "alone", "seed": seed,
                             "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
                             "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
                             "wall_s": w})
            rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
            rec = [r for r in rows if r.get("cue") == cue and r.get("arm") == "alone" and r.get("seed") == seed]
            alone.append(rec[-1]["mn9_l_hz"])
            if not seen(out, stage="A", cue=cue, arm="cosugar", seed=seed):
                r, w = trial(matrix, node_ids, sugar, ids, 200.0, seed)
                append(out, {"stage": "A", "cue": cue, "arm": "cosugar", "seed": seed,
                             "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
                             "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
                             "wall_s": w})
            rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
            rec = [r for r in rows if r.get("cue") == cue and r.get("arm") == "cosugar" and r.get("seed") == seed]
            co.append(rec[-1]["mn9_l_hz"])
        c_ok, d_ok = max(alone) == 0, min(co) >= THRESH
        ok = ok and c_ok and d_ok
        print(f"  {cue}: alone={alone} cosugar={co} -> "
              f"(c){'PASS' if c_ok else 'FAIL'} (d){'PASS' if d_ok else 'FAIL'}", flush=True)
    print(f"Stage A verdict: {'PASS - baseline facts hold at n=10' if ok else 'HALT - baseline facts FAILED at n=10'}",
          flush=True)
    return ok


# ---------------------------------------------------------------- Stage B

def stage_b(matrix, node_ids, sugar) -> float:
    out = OUTDIR / "stage_b_eta.jsonl"
    print("== Stage B: eta range-finder (GNG521 only) ==", flush=True)
    eta_star = None
    for eta in ETA_GRID:
        fired = False
        probe_hz = None
        for t in range(10):
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"b_{eta}", OUTDIR / f"ckpt_b_{eta}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            spec = TrialSpec(trial=t, seed=31_300 + t, cue_body_ids=tuple(CUES["GNG521"]),
                             drive_body_ids=tuple(sugar), drive2_body_ids=(),
                             r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
            rec = run.run_trial(spec)
            append(out, {"stage": "B", "eta": eta, "trial": t,
                         "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                         "guard_fired": rec.get("guard_fired")})
            if rec.get("guard_fired"):
                fired = True
                break
        if not fired:
            # probe: cue alone, NO plasticity applied (probe trial)
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"b_{eta}", OUTDIR / f"ckpt_b_{eta}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            spec = TrialSpec(trial=10, seed=31_350, cue_body_ids=tuple(CUES["GNG521"]),
                             drive_body_ids=(), drive2_body_ids=(),
                             r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0, is_probe=True)
            rec = run.run_trial(spec)
            probe_hz = rec["readout_hz"]
            append(out, {"stage": "B", "eta": eta, "trial": 10, "probe": True,
                         "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                         "guard_fired": rec.get("guard_fired")})
        print(f"  eta={eta}: guard={'FIRED' if fired else 'ok'} probe_MN9_L={probe_hz}",
              flush=True)
        if not fired and probe_hz is not None and probe_hz > 0 and eta_star is None:
            eta_star = eta
    if eta_star is None:
        # no eta expressed; choose largest eta with no guard fire
        for eta in reversed(ETA_GRID):
            rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
            recs = [r for r in rows if r.get("eta") == eta]
            if recs and not any(r.get("guard_fired") for r in recs):
                eta_star = eta
                break
    if eta_star is None:
        print("Stage B verdict: HALT - all eta fired the guard", flush=True)
        sys.exit(3)
    print(f"Stage B verdict: eta* = {eta_star}", flush=True)
    return eta_star


# ---------------------------------------------------------------- Stage C

def stage_c(matrix, node_ids, sugar, eta) -> None:
    out = OUTDIR / "stage_c_pilot.jsonl"
    print(f"== Stage C: L1 pilot, 3 seeds x 2 cues x 20 trials, eta={eta} ==", flush=True)
    for cue, ids in CUES.items():
        for blk, base_seed in enumerate((31_000, 31_100, 31_200)):
            cfg = PlasticityConfig(eta=eta, semantics=Semantics.V_MAG, w_max=W_MAX)
            run = TrainingRun(matrix, node_ids, HebbianRule(cfg), guard(), MN9_L,
                              f"c_{cue}_{blk}", OUTDIR / f"ckpt_c_{cue}_{blk}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            for t in range(20):
                spec = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(ids),
                                 drive_body_ids=tuple(sugar), drive2_body_ids=(),
                                 r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(spec)
                append(out, {"stage": "C", "cue": cue, "seed_block": blk, "trial": t,
                             "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                             "n_spiking": rec["n_spiking"],
                             "weight_diff": rec.get("weight_diff"),
                             "guard_fired": rec.get("guard_fired")})
                if rec.get("guard_fired"):
                    print(f"  GUARD FIRE {cue} blk{blk} trial {t}: {rec['guard_fired']}", flush=True)
                    return
                if (t + 1) in (5, 10, 15, 20):
                    pspec = TrialSpec(trial=t, seed=base_seed + 500, cue_body_ids=tuple(ids),
                                       drive_body_ids=(), drive2_body_ids=(),
                                       r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                    prec = run.run_trial(pspec)
                    append(out, {"stage": "C", "cue": cue, "seed_block": blk, "trial": t,
                                  "probe": True, "readout_hz": prec["readout_hz"],
                                  "total_spikes": prec["total_spikes"],
                                  "weight_hash": prec["weight_hash"],
                                  "guard_fired": prec.get("guard_fired")})
                    print(f"  {cue} blk{blk} trial {t + 1}: probe MN9_L = {prec['readout_hz']} Hz",
                          flush=True)


# ---------------------------------------------------------------- Stage D

def stage_d(matrix, node_ids, sugar) -> None:
    out = OUTDIR / "stage_d_l0_control.jsonl"
    print("== Stage D: L0 control (plasticity=None), same schedule ==", flush=True)
    for cue, ids in CUES.items():
        for blk, base_seed in enumerate((33_000, 33_100, 33_200)):
            run = TrainingRun(matrix, node_ids, None, guard(), MN9_L,
                              f"d_{cue}_{blk}", OUTDIR / f"ckpt_d_{cue}_{blk}",
                              lif_params=dataclasses.replace(LIFParams(), r_poisson_Hz=200.0))
            for t in range(20):
                spec = TrialSpec(trial=t, seed=base_seed + t, cue_body_ids=tuple(ids),
                                 drive_body_ids=tuple(sugar), drive2_body_ids=(),
                                 r_cue_hz=200.0, r_drive_hz=200.0, r_drive2_hz=0.0)
                rec = run.run_trial(spec)
                append(out, {"stage": "D", "cue": cue, "seed_block": blk, "trial": t,
                             "readout_hz": rec["readout_hz"], "total_spikes": rec["total_spikes"],
                             "n_spiking": rec["n_spiking"]})
                if (t + 1) in (5, 10, 15, 20):
                    pspec = TrialSpec(trial=t, seed=base_seed + 500, cue_body_ids=tuple(ids),
                                       drive_body_ids=(), drive2_body_ids=(),
                                       r_cue_hz=200.0, r_drive_hz=0.0, r_drive2_hz=0.0,
                                       is_probe=True)
                    prec = run.run_trial(pspec)
                    append(out, {"stage": "D", "cue": cue, "seed_block": blk, "trial": t,
                                  "probe": True, "readout_hz": prec["readout_hz"],
                                  "total_spikes": prec["total_spikes"]})
                    print(f"  {cue} blk{blk} trial {t + 1}: L0 probe = {prec['readout_hz']} Hz",
                          flush=True)


def main() -> int:
    matrix, node_ids, sugar = load_world()
    if not stage_a(matrix, node_ids, sugar):
        return 2
    eta = stage_b(matrix, node_ids, sugar)
    stage_c(matrix, node_ids, sugar, eta)
    stage_d(matrix, node_ids, sugar)
    print("\nWP3 pilot complete. Aggregation: see wp3_pilot_report.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
