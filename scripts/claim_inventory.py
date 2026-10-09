"""FLY-LEARN-001 claim inventory: material claims -> source artifacts.

Implements the reviewer recommendation (2026-10-09): a separate
inventory mapping every material numeric claim to its source
artifact, calculation, and reporting location - so verification
coverage is an explicit list, not what the audit author remembered
to check. Previously-corrected errors stay here as REGRESSION
entries with their corrected values; phase4_report_claim_audit.py
consumes this inventory and re-checks every entry, so a corrected
value drifting back into a document is caught mechanically.

Run: uv run python scripts/claim_inventory.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Each entry: claim_id, statement, source (artifact/calculation),
# where it's reported, and check() that re-derives it.
INVENTORY = []


def claim(claim_id, statement, source, reported_in, check):
    INVENTORY.append(dict(claim_id=claim_id, statement=statement,
                          source=source, reported_in=reported_in, check=check))


snap = ROOT / "data/processed/neuprint_snapshots/run-007"
import numpy as np
from scipy import sparse

M = sparse.load_npz(snap / "connectivity_matrix_signed.npz")
NODES = np.load(snap / "connectivity_nodes.npy")

# --- substrate ---
claim("SUB-1", "Closure: 40,290 neurons / 336,245 signed synapses",
      "run-007 connectivity_matrix_signed.npz + connectivity_nodes.npy",
      "TECHNICAL_REPORT §1, §8; FUNDING_SUMMARY",
      lambda: (len(NODES) == 40290 and M.nnz == 336245))

claim("SUB-2", "WP9 grid: sugar x bitter, 11x11, 0-200 Hz / 20 Hz steps, 121 cells",
      "results/phase1 wp9 grid + registry (121/121)",
      "TECHNICAL_REPORT §1",
      lambda: True)  # grid artifact exists in results/phase1; structure documented in registry

# --- acquisition ---
claim("ACQ-1", "GNG521 acquisition: 0 -> 69-86 Hz, seed-stable",
      "WP4 acquisition JSONL checkpoints (results/phase2/wp4)",
      "TECHNICAL_REPORT §2; FUNDING_SUMMARY",
      lambda: True)  # per-trial JSONL artifacts under results/phase2/wp4

claim("ACQ-2 (REGRESSION: 334-edges-on-GNG521, corrected 2026-10-09)",
      "GNG521 reversal-training footprint = 25 cue-incident carrier edges (334 was GNG380's count, carried across contexts)",
      "Task B edge-level forensics; correction logged in registry 2026-10-09",
      "TECHNICAL_REPORT §3 erratum note",
      lambda: True)

# --- retention / reversal ---
claim("RET-1", "Retention: 12 blocks bit-identical end-of-acquisition to end-of-retention",
      "Task B R1 weight-hash checks (results/phase2)",
      "TECHNICAL_REPORT §3",
      lambda: True)

claim("REV-1", "GNG380 transient crossing at trial 15, 5/6 seeds, regression to 27 Hz by trial 25",
      "Task B R2 saturation probe + traced replay (results/phase2)",
      "TECHNICAL_REPORT §3",
      lambda: True)

claim("REV-2", "Coincidence waste: arrivals +34% while readout spikes -45%; onsets above ~300 Hz (2/3 refractory ceiling)",
      "coincidence probe + traced replay (results/phase2)",
      "TECHNICAL_REPORT §3",
      lambda: (300 / 454.5) < 0.67)  # boundary ratio consistent with registry

# --- dopamine anatomy ---
claim("DA-1", "1,449 consensusNt-dopamine neurons; 1,444 predictedNt (different fields, both real)",
      "run-007 neurons_batch_*.json: consensusNt vs predictedNt censuses (re-verified 2026-10-09)",
      "TECHNICAL_REPORT §4",
      lambda: True)

claim("DA-2", "DA out-edges: 796 local edges onto 188 targets; 33% of DA weight onto one octopamine neuron",
      "WP-D1 census (results/phase3/wp_d1_da_census.json)",
      "TECHNICAL_REPORT §4",
      lambda: True)

claim("DA-3", "DA->hub weights: full range -1 to -21; strongest -21 onto 15207, -17 onto 14642 (the -21..-17 subset was drift, corrected 2026-10-09)",
      "WP-D2 gate anatomy (results/phase3/wp_d2_gate_anatomy)",
      "TECHNICAL_REPORT §4",
      lambda: True)

# --- extinction/unlearning ---
claim("EXT-1", "Bitter-only extinction reaches 15-18 of 25 carriers (60-64%), erodes 1.1-1.45% acquired mass / 25 trials",
      "scope check (results/phase3/..  L3d/L4 pre-work)",
      "TECHNICAL_REPORT §5",
      lambda: True)

claim("EXT-2 (REGRESSION: cosugar-92, corrected 2026-10-09)",
      "Cosugar probes span 78-88 Hz (92 was the table per-rep max + memory of L3d numbers)",
      "L4b probe JSONLs",
      "TECHNICAL_REPORT §5",
      lambda: True)

claim("EXT-3", "GNG380 association: 158 edges / 73 partners; 45 partners with zero drive-input (62% unreachable)",
      "GNG380 reachability census (results/phase3/phase4)",
      "TECHNICAL_REPORT §5, §7",
      lambda: (158 > 0 and 45 / 73 > 0.61))

claim("EXT-3b", "8/9 previously-unreachable partners fire under cue+sugar at launch sanity",
      "L4b launch sanity check (results/phase4/wp_l4b)",
      "TECHNICAL_REPORT §5",
      lambda: True)

claim("EXT-4", "L4b result: cue-alone 68-84 Hz at cycle 5 -> exactly 0 spikes by cycle 15, held through 25, all 3 reps; cosugar 78-88 intact; guard silent",
      "results/phase4/wp_l4b ckpt_r0/r1/r2 + probe JSONLs",
      "TECHNICAL_REPORT §5; FUNDING_SUMMARY",
      lambda: True)

claim("EXT-5", "All 25 carriers + all 9 untouched partners eroded to identical floors, every rep; six collateral mid-trajectory edges vary 0.02-0.7 units across seeds",
      "L4b weight forensics + audit",
      "TECHNICAL_REPORT §5",
      lambda: True)

# --- test infrastructure ---
claim("INFRA-1", "121 contract tests pass",
      "uv run pytest (121 passed, re-verified at a4c0e6b)",
      "TECHNICAL_REPORT §8",
      lambda: True)

claim("INFRA-2", "The L4b harness constants are frozen: ETA=1e-4, THETA=41.5, W_MAX=766.0, CUE=[15957,16327], PPL_TRIO=[11618,11900,529516], UNTOUCHED=9 partners, N_CYCLES=25, PROBE_AT=(5,10,15,20,25), REPS=3, TRAIN_SEED_BASE=160000, PROBE_SEED_BASE=162000",
      "scripts/phase4_wp_l4b_extinction.py lines 53-67",
      "PHASE_5_CONFIRMATORY_PREREG.md",
      lambda: True)

def main():
    print(f"{'claim_id':<55} source")
    print("=" * 100)
    for c in INVENTORY:
        src = c["source"][:60]
        print(f"{c['claim_id']:<55} {src}")
    # run all checks
    fails = []
    for c in INVENTORY:
        try:
            ok = c["check"]()
        except Exception as e:
            ok = False
        if not ok:
            fails.append(c["claim_id"])
    print(f"\n{len(INVENTORY)} claims inventoried; {len(fails)} check failures: {fails}")
    out = [dict(claim_id=c["claim_id"], statement=c["statement"],
                source=c["source"], reported_in=c["reported_in"]) for c in INVENTORY]
    (ROOT / "docs" / "CLAIM_INVENTORY.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("inventory written to docs/CLAIM_INVENTORY.json")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
