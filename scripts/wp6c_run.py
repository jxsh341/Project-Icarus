"""WP6c: sugar/bitter feeding experiment on the MaleCNS signed connectome.

Reproduces the directional prediction of Shiu et al. 2024 (Fig 3a):
  bitter GRN co-stimulation SUPPRESSES sugar-driven MN9 firing.

Driven populations (Cell 2026 gustatory connectome mapping, right
hemisphere, male-cns:v0.9 bodyIds in wp6c_grn_seeds.json):
  sugar = LB3b/LB3c (Gr64f+), bitter = LB1a-d (Gr33a+)
Readout: MN9 (proboscis-extension motor neuron; 16949=R primary).

Arms (one process per arm, checkpointed per trial to JSONL):
  signed   - the pipeline's NT convention (gaba, glutamate -> -1)
  abl-glu  - glutamate treated as excitatory (gaba still inhibitory)
  all-pos  - all weights positive (sign convention removed entirely)

If the paper's directionality (bitter suppresses MN9) reproduces under
`signed` but not under `all-pos`, the NT-sign convention is doing real,
load-bearing work - that is the discriminating outcome WP6c exists to
test.

Checkpoint discipline: every trial is appended to
results/wp6c_sugar_bitter/trials_<arm>_<sugar>_<bitter>.jsonl the moment
it completes, so an interrupted run resumes instead of restarting
(the WP6c orphan incident: a Hermes restart killed an uncheckpointed
60-trial run with only stdout as the record).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
SEEDS_FILE = Path("data/processed/neuprint_snapshots/wp6c_grn_seeds.json")
OUT = Path("results/wp6c_sugar_bitter")
N_TRIALS = 10
SEED_BASE = 7000
DURATION_MS = 1000.0
MN9_IDS = [16949, 10331]  # MN9_R primary readout; MN9_L recorded too


def mn9_rates(result, duration_ms):
    rates = {}
    for m in MN9_IDS:
        spikes = result.spike_times.get(m, [])
        rates[str(m)] = len(spikes) / (duration_ms / 1000.0)
    rates["mean"] = float(np.mean(list(rates.values())))
    return rates


def load_matrix(arm: str, node_ids: list[int]):
    matrix_signed = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    if arm == "signed":
        return matrix_signed
    if arm == "all-pos":
        m = matrix_signed.copy()
        m.data = np.abs(m.data)
        return m
    if arm == "abl-glu":
        m = matrix_signed.copy()
        nt_lookup = {}
        for p in sorted(BASE.glob("neurons_batch_*.json")):
            for r in json.loads(p.read_text(encoding="utf-8")):
                nt_lookup[r["bodyId"]] = r.get("predictedNt")
        idx = {n: i for i, n in enumerate(node_ids)}
        flip = np.zeros(len(node_ids), dtype=bool)
        for nid, nt in nt_lookup.items():
            if nid in idx and (nt or "").lower() == "glutamate":
                flip[idx[nid]] = True
        coo = m.tocoo()
        mask = flip[coo.row]
        new_data = np.where(mask, np.abs(coo.data), coo.data)
        m = sparse.csr_matrix((new_data, (coo.row, coo.col)), shape=m.shape)
        print(f"glutamatergic edges flipped positive for abl-glu: {int(mask.sum())}")
        return m
    raise ValueError(f"unknown arm {arm}")


def run_condition(matrix, node_ids, sugar, bitter, arm, f_sugar, f_bitter):
    """One (arm, condition) cell; appends each trial to its checkpoint."""
    ckpt = OUT / f"trials_{arm}_sugar{int(f_sugar)}_bitter{int(f_bitter)}.jsonl"
    done = set()
    if ckpt.exists():
        for line in ckpt.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["seed"])
    with ckpt.open("a", encoding="utf-8") as fh:
        for i in range(N_TRIALS):
            seed = SEED_BASE + i
            if seed in done:
                continue
            t0 = time.time()
            r = simulate_lif(
                matrix, node_ids, LIFParams(),
                duration_ms=DURATION_MS,
                stimulated=sugar,
                stimulated2=bitter if f_bitter > 0 else None,
                r_poisson2_Hz=f_bitter if f_bitter > 0 else None,
                seed=seed,
            )
            rec = {
                "arm": arm, "f_sugar": f_sugar, "f_bitter": f_bitter,
                "seed": seed,
                "mn9": mn9_rates(r, DURATION_MS),
                "total_spikes": r.n_spikes,
                "n_spiking": len(r.spike_times),
                "wall_s": round(time.time() - t0, 1),
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[{arm} sugar={int(f_sugar)} bitter={int(f_bitter)}] seed={seed} "
                  f"mn9={rec['mn9']['mean']:.1f} Hz total={rec['total_spikes']} "
                  f"({rec['wall_s']}s)", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["signed", "abl-glu", "all-pos"])
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    node_ids = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    bitter = [r["bodyId"] for r in seeds["bitter_R"]]

    matrix = load_matrix(args.arm, node_ids)
    run_condition(matrix, node_ids, sugar, bitter, args.arm, 200.0, 0.0)
    run_condition(matrix, node_ids, sugar, bitter, args.arm, 200.0, 200.0)
    print(f"arm {args.arm} complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
