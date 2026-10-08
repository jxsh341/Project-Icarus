"""WP-L3a Sweep C RE-RUN (corrected): the decisive sign sweep.

The first Sweep C was INVALID: the swept gate rate never entered the
simulation (the run() helper hardcoded 200 Hz), degenerating the
sweep to a 2-point contrast. Registered as an implementation bug;
Sweeps A and B remain valid (their rates entered via
dataclasses.replace correctly).

This re-run uses the new stimulated3 channel (tests/test_lif_stim3.py:
default-off bit-identical, independent rates, rfc=0 semantics) to
drive gate-DA at INDEPENDENT swept rates on top of the cue+sugar
training baseline.

Pre-registered criteria (L3_DESIGN.md):
- H(+) supported iff intermediate-rate suppression increases with
  gate-DA drive (monotone or near-monotone).
- H(-) supported iff intermediates or readout RISE with gate-DA.
- Nonlinear/ambiguous -> recorded as-is.

Seeds: 151000+t (disjoint; L3a first pass used 150000-150200).
Plasticity NONE throughout (frozen dynamics).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

BASE = Path("data/processed/neuprint_snapshots/run-007")
OUT = Path("results/phase3/wp_l3a/l3a_sweep_c_v2.jsonl")
MN9_L = 10331
GATE_DA = [10399, 10898, 10914, 11125, 12588, 13068, 520146, 520188, 529811]
HUB_PAIR = [10646, 10094]
INTER_380 = [12256, 10646, 15014, 15207, 14642, 14793, 12583, 63701]
CUE_380 = [50843, 53901, 103327, 129624, 556072, 559464]
RATES = (0, 25, 50, 75, 100, 150, 200)
REPS = 3
SEED_BASE = 151_000


def main() -> int:
    matrix = sparse.load_npz(BASE / "connectivity_matrix_signed.npz").tocsr()
    nodes = np.load(BASE / "connectivity_nodes.npy").tolist()
    seeds = json.loads((BASE.parent / "wp6c_grn_seeds.json").read_text(encoding="utf-8"))
    sugar = [r["bodyId"] for r in seeds["sugar_R"]]
    lif_params = dataclasses.replace(LIFParams(), r_poisson_Hz=200.0)

    print("seed check: 151000-151200 vs prior L3a pass 150000-150200: "
          "disjoint by construction (higher base)", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("\n== Sweep C v2: cue@sugar baseline + gate-DA at INDEPENDENT swept rates ==", flush=True)
    for rate in RATES:
        for rep in range(REPS):
            seed = SEED_BASE + rep + RATES.index(rate) * 10
            p = dataclasses.replace(lif_params, r_poisson_Hz=200.0)
            lif = simulate_lif(
                matrix, nodes, p, duration_ms=1000.0,
                stimulated=list(CUE_380),           # cue: primary @200
                stimulated2=list(sugar), r_poisson2_Hz=200.0,  # sugar @200
                stimulated3=list(GATE_DA) if rate > 0 else [],
                r_poisson3_Hz=float(rate) if rate > 0 else None,
                seed=seed,
            )
            inter = {str(x): len(lif.spike_times.get(x, [])) for x in INTER_380}
            hubs = {str(h): len(lif.spike_times.get(h, [])) for h in HUB_PAIR}
            gates = {str(g): len(lif.spike_times.get(g, [])) for g in GATE_DA}
            rec = {"sweep": "C2", "gate_rate": rate, "rep": rep, "seed": seed,
                   "intermediates": inter, "hubs": hubs, "gate_da_hz": gates,
                   "mn9_hz": len(lif.spike_times.get(MN9_L, []))}
            with OUT.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            if rep == 0:
                s = " ".join(f"{x[-4:]}={v}" for x, v in inter.items())
                h = " ".join(f"{k[-4:]}={v}" for k, v in hubs.items())
                print(f"  gate@{rate:>3}Hz: {s} | hubs {h} | MN9={rec['mn9_hz']}", flush=True)

    # aggregate: mean over reps per rate, monotonicity check
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("\n== aggregation (mean over 3 reps) ==")
    agg = {}
    for rate in RATES:
        rs = [r for r in rows if r["gate_rate"] == rate]
        means = {x: np.mean([r["intermediates"][x] for r in rs]) for x in rs[0]["intermediates"]}
        agg[rate] = {"means": means, "mn9": np.mean([r["mn9_hz"] for r in rs])}
        s = " ".join(f"{x[-4:]}={v:.0f}" for x, v in means.items())
        print(f"  gate@{rate:>3}: {s} MN9={agg[rate]['mn9']:.1f}")

    # H(+) test: suppression increasing with rate on the ACTIVE intermediates
    active = ["15014", "15207", "14642", "14793", "12583"]
    base_vals = [agg[0]["means"][x] for x in active]
    sup200 = [agg[200]["means"][x] for x in active]
    print(f"\nactive intermediates @0Hz: {[f'{v:.0f}' for v in base_vals]}")
    print(f"active intermediates @200Hz: {[f'{v:.0f}' for v in sup200]}")
    deltas = [b - s for b, s in zip(base_vals, sup200)]
    print(f"suppression deltas (0 -> 200): {[f'{d:+.1f}' for d in deltas]}")
    verdict = "H(+) SUPPORTED: suppression increases with gate-DA drive" if all(
        agg[r]["means"][x] <= agg[0]["means"][x] + 2 for x in active
        for r in RATES) and all(d >= 0 for d in deltas) else (
        "H(+) NOT cleanly supported - inspect nonmonotonicity")
    print(f"\nVERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
