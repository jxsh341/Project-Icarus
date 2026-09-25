"""Phase 2 pre-WP0 probe: innate valence of candidate neutral cues (D1 check).

The redesigned Task A uses water GRNs (LB3a) and IR94e GRNs (LB1e) as
'neutral' cues. Review flag: water-seeking is a plausible innate drive
independent of the sugar/bitter axis; IR94e may carry its own documented
valence. Literature + this probe decide whether the cue choice stands.

Arms (n=5 seeds each, 200 Hz explicit, 1 s, checkpointed):
  water_only   - LB3a_R driven: does the substrate innately FEED on water?
  ir94e_only   - LB1e_R driven: any MN9_L expression?
  ir94e_cosugar- sugar_R@200 + LB1e_R@200 co-drive: does IR94e SUPPRESS
                 the sugar-driven feed program (innate aversive valence)?
  sugar_only   - positive control (expect MN9_L ~81 Hz)
  bitter_only  - aversive control (expect MN9_L 0, aversive-state activity)

Also computed: 1-hop downstream target overlap (Jaccard) between cue
populations - the discriminability precondition for any cue pair.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
SEEDS_FILE = Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json")
OUT = Path("results/phase2/wp0_cue_valence_probe.jsonl")
MN9_L, MN9_R = 10331, 16949
DURATION_MS = 1000.0


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    idx = {n: i for i, n in enumerate(node_ids)}

    seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]
    water, ir94e = [], []
    for p in sorted(BASE.glob("neurons_batch_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            if r.get("type") == "LB3a" and r.get("rootSide") == "R":
                water.append(r["bodyId"])
            elif r.get("type") == "LB1e" and r.get("rootSide") == "R":
                ir94e.append(r["bodyId"])
    print(f"populations: water(LB3a_R) n={len(water)}, ir94e(LB1e_R) n={len(ir94e)}, "
          f"sugar n={len(sugar)}, bitter n={len(bitter)}", flush=True)

    # discriminability precondition: 1-hop downstream target overlap
    def one_hop(ids):
        s = set()
        for b in ids:
            s.update(matrix.getrow(idx[b]).nonzero()[1].tolist())
        return s

    tw, ti, ts, tb = one_hop(water), one_hop(ir94e), one_hop(sugar), one_hop(bitter)
    def jac(a, b):
        return round(len(a & b) / len(a | b), 3)
    print(f"1-hop target sets: water {len(tw)}, ir94e {len(ti)}, sugar {len(ts)}, bitter {len(tb)}", flush=True)
    print(f"Jaccard: water-ir94e {jac(tw, ti)} | water-sugar {jac(tw, ts)} | "
          f"ir94e-sugar {jac(ti, ts)} | water-bitter {jac(tw, tb)} | ir94e-bitter {jac(ti, tb)}", flush=True)

    arms = [
        ("water_only", water, None, None),
        ("ir94e_only", ir94e, None, None),
        ("ir94e_cosugar", sugar, ir94e, 200.0),
        ("sugar_only", sugar, None, None),
        ("bitter_only", bitter, None, None),
    ]

    done = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done.add((rec["arm"], rec["seed"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    p200 = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)
    with OUT.open("a", encoding="utf-8") as fh:
        for arm_name, stim, stim2, r2 in arms:
            for i in range(5):
                seed = 20_000 + i
                if (arm_name, seed) in done:
                    continue
                t0 = time.time()
                r = simulate_lif(matrix, node_ids, p200, duration_ms=DURATION_MS,
                                 stimulated=stim, stimulated2=stim2,
                                 r_poisson2_Hz=r2, seed=seed)
                rec = {"arm": arm_name, "seed": seed,
                       "mn9_l_hz": len(r.spike_times.get(MN9_L, [])),
                       "mn9_r_hz": len(r.spike_times.get(MN9_R, [])),
                       "total_spikes": r.n_spikes, "n_spiking": len(r.spike_times),
                       "wall_s": round(time.time() - t0, 1)}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print(f"[{arm_name}] seed={seed} MN9_L={rec['mn9_l_hz']} Hz "
                      f"total={rec['total_spikes']} n_spiking={rec['n_spiking']} ({rec['wall_s']}s)",
                      flush=True)
    print("probe complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
