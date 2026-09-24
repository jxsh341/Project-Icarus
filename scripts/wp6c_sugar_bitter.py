"""WP6c: sugar/bitter feeding experiment on the MaleCNS signed connectome.

Reproduces the directional prediction of Shiu et al. 2024 Fig 3a:
  bitter GRN co-stimulation SUPPRESSES sugar-driven MN9 firing.

Protocol (from figures.ipynb cells 23-25):
  - sugar GRNs (LB3b/LB3c, right hemisphere) driven at r_poi
  - bitter GRNs (LB1a-d, right hemisphere) driven at r_poi2
  - readout: MN9 firing rate (proboscis-extension motor neuron)
  - grid: sugar in {200, 180} Hz x bitter in {0, 50, 100, 150, 200} Hz

Discriminating control: rerun the same conditions with the NT-sign
convention ABLATED (all-positive weights) and with glutamate-only
ablation (gaba inhibitory, glutamate excitatory). If MN9 suppression
by bitter requires GABA/glutamate inhibition, the all-positive arm must
fail to reproduce the paper's directionality.
"""

from __future__ import annotations

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


def mn9_rate(result, node_ids, mn9_ids, duration_ms):
    idx = {n: i for i, n in enumerate(node_ids)}
    rates = []
    for m in mn9_ids:
        spikes = result.spike_times.get(m, [])
        rates.append(len(spikes) / (duration_ms / 1000.0))
    return float(np.mean(rates)) if rates else 0.0


def run_condition(matrix, node_ids, sugar_ids, bitter_ids, f_sugar, f_bitter, n=N_TRIALS):
    """Drive sugar at f_sugar and bitter at f_bitter; return per-trial MN9 rates.

    simulate_lif drives `stimulated` at r_poisson_Hz; for two populations at
    different rates we need a two-rate drive. Simplest faithful approach:
    drive each population in separate simulate_lif calls is WRONG (needs
    simultaneous). Instead: patch params per call so the combined drive is
    applied - here we approximate by driving the UNION at the sugar rate
    only when f_bitter == 0, and otherwise run two-source drive via
    repeated single-population calls summed? No - implement a tiny local
    two-rate Poisson loop on top of simulate_lif's primitives instead.
    """
    raise NotImplementedError


def main() -> int:
    raise SystemExit("replaced by inline run; see scripts/wp6c_run.py")


if __name__ == "__main__":
    raise SystemExit(main())
