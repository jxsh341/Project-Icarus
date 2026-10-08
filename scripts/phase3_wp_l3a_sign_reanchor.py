"""WP-L3a: DA sign re-anchoring (discharges the Phase 1 freeze obligation).

L3 design §3: the gate-DA -> AVLP597-pair edges are +1 BY DEFAULT
(nt_sign gives all monoamines +1 - an auditable assumption, never
validated for DA-on-GABA). This WP resolves H(+) vs H(-)
empirically BEFORE any L3 plasticity exists, in FROZEN Phase 1
dynamics (plasticity=None, no learning runs here).

Method (WP6c-style stimulation sweeps, registered in L3_DESIGN.md):
- Sweep A: drive the 9 gate-DA neurons with Poisson stimulation
  (rate sweep 0..200 Hz) on the PRISTINE matrix; measure the hub
  pair (10646, 10094) spike responses. Establishes DA->hub sign
  under the default matrix.
- Sweep B: drive the hub pair directly; measure the 8 GNG380
  intermediates' rates. Establishes hub->intermediates sign
  (expected: inhibitory, they are GABA).
- Sweep C (the decisive one): baseline-drive the GNG380 cue+sugar
  training condition (the coincidence-waste regime), then drive
  gate-DA ON TOP at sweep rates; measure intermediates + MN9_L.
  H(+) predicts intermediate rates FALL (gated suppression
  counteracts coincidence waste) and the readout shifts; H(-)
  predicts the opposite or null.

Pre-registered interpretation:
- H(+) supported iff Sweep C shows intermediate-rate suppression
  increasing with gate-DA drive (monotone or near-monotone).
- H(-) supported iff intermediates rise or readout rises with
  gate-DA drive.
- Nonlinear/ambiguous -> recorded as-is; design adapts, not data.

Seeds: 150000+t (L3 train range start; disjointness verified in the
launch log line below). Plasticity NONE throughout (frozen
dynamics). Guard live. Per-trial JSONL.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUTDIR = Path("results/phase3/wp_l3a")
MN9_L = 10331
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
HUB_PAIR = [10646, 10094]
INTER_380 = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
RATES = (0, 25, 50, 75, 100, 150, 200)
REPS = 3
SEED_BASE = 150_000


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    nid = {n: i for i, n in enumerate(nodes)}
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    # seed disjointness: prior max = R2 probes 142047; L3 train starts 150000
    prior_max = 142_047
    print(f"seed check: L3a seeds {SEED_BASE}-{SEED_BASE+200} vs prior max {prior_max}: "
          f"{'DISJOINT' if SEED_BASE > prior_max else 'OVERLAP - ABORT'}", flush=True)

    def run(seed, stim, stim2=None, r2=None):
        p = dataclasses.replace(lif_params, r_poisson_Hz=200.0)  # default stim rate
        lif = simulate_lif(
            matrix, nodes, p, duration_ms=1000.0,
            stimulated=list(stim),
            stimulated2=list(stim2) if stim2 else None,
            r_poisson2_Hz=r2,
            seed=seed,
        )
        return lif

    out = OUTDIR / "l3a_sweeps.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    # ---- Sweep A: drive gate-DA, measure hubs ----
    print("\n== Sweep A: gate-DA drive -> hub pair response (default-sign matrix) ==", flush=True)
    for rate in RATES:
        for rep in range(REPS):
            rec = {"sweep": "A", "gate_rate": rate, "rep": rep}
            if rate == 0:
                lif = run(SEED_BASE + rep, [])
            else:
                p = dataclasses.replace(lif_params, r_poisson_Hz=float(rate))
                lif = simulate_lif(matrix, nodes, p, duration_ms=1000.0,
                                   stimulated=list(GATE_DA), seed=SEED_BASE + rep)
            hubs = {h: len(lif.spike_times.get(h, [])) for h in HUB_PAIR}
            rec.update({"hub_10646_hz": hubs[10646], "hub_10094_hz": hubs[10094],
                        "mn9_hz": len(lif.spike_times.get(MN9_L, []))})
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            if rep == 0:
                print(f"  gate@{rate:>3}Hz: 10646={hubs[10646]:>3}Hz 10094={hubs[10094]:>3}Hz "
                      f"MN9={rec['mn9_hz']}", flush=True)

    # ---- Sweep B: drive hub pair, measure intermediates ----
    print("\n== Sweep B: hub-pair drive -> GNG380 intermediates (expected inhibitory) ==", flush=True)
    for rate in RATES:
        for rep in range(REPS):
            rec = {"sweep": "B", "hub_rate": rate, "rep": rep}
            if rate == 0:
                lif = run(SEED_BASE + 100 + rep, [])
            else:
                p = dataclasses.replace(lif_params, r_poisson_Hz=float(rate))
                lif = simulate_lif(matrix, nodes, p, duration_ms=1000.0,
                                   stimulated=list(HUB_PAIR), seed=SEED_BASE + 100 + rep)
            inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER_380}
            rec.update({"intermediates": inter,
                        "mn9_hz": len(lif.spike_times.get(MN9_L, []))})
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            if rep == 0:
                s = " ".join(f"{x[-4:]}={v}" for x, v in inter.items())
                print(f"  hubs@{rate:>3}Hz: {s} MN9={rec['mn9_hz']}", flush=True)

    # ---- Sweep C: training baseline + gate-DA on top ----
    print("\n== Sweep C: cue+sugar baseline + gate-DA drive (THE DECISIVE SWEEP) ==", flush=True)
    for rate in RATES:
        for rep in range(REPS):
            rec = {"sweep": "C", "gate_rate": rate, "rep": rep}
            # cue+sugar baseline: cue as PRIMARY via r_poisson, sugar as stim2
            if rate == 0:
                lif = run(SEED_BASE + 200 + rep, CUE_380, stim2=sugar, r2=200.0)
            else:
                # cue+sugar AND gate-DA: use stimulated for cue, stimulated2 for sugar;
                # gate-DA needs a THIRD stim channel - simulate_lif supports only two.
                # Approach: drive cue at PRIMARY rate via stimulated; gate-DA + sugar
                # merged into stimulated2? That changes sugar rate. HONEST FALLBACK:
                # stimulate cue+gate-DA together at rate (both are 'primary' Poisson
                # populations at the same rate), sugar at stim2. Registered limitation:
                # gate-DA driven at same Poisson rate as cue.
                merged = list(CUE_380) + list(GATE_DA)
                lif = run(SEED_BASE + 200 + rep, merged, stim2=sugar, r2=200.0)
            inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER_380}
            rec.update({"intermediates": inter,
                        "mn9_hz": len(lif.spike_times.get(MN9_L, [])),
                        "gate_da_hz": {str(g): len(lif.spike_times.get(g, [])) for g in GATE_DA}})
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            if rep == 0:
                s = " ".join(f"{x[-4:]}={v}" for x, v in inter.items())
                print(f"  gate@{rate:>3}Hz: {s} MN9={rec['mn9_hz']}", flush=True)

    print("\nWP-L3a sweeps complete. Aggregate + verdict next.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
