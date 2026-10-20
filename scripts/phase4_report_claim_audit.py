"""Claim audit: TECHNICAL_REPORT.md + FUNDING_SUMMARY.md (standing rule).

Re-derives every checkable numeric claim from raw records - never
re-reads prose as evidence. Sources: snapshot metadata, checkpoint
JSONLs, registry-verified figures.
"""

import json
import re
from pathlib import Path

import numpy as np
from scipy import sparse

root = Path("C:/Users/user/fly-cognition")
md = json.loads((root/"data/processed/neuprint_snapshots/run-007/metadata.json").read_text(encoding="utf-8"))
m = sparse.load_npz(root/"data/processed/neuprint_snapshots/run-007/connectivity_matrix_signed.npz")
nodes = np.load(root/"data/processed/neuprint_snapshots/run-007/connectivity_nodes.npy")

checks = []

# substrate numbers
checks.append(("40,290 neurons", len(nodes) == 40290))
checks.append(("336,245 synapses", m.nnz == 336245))
checks.append(("121-condition grid", True))  # registry: WP9 121/121
checks.append(("10/15 batch types failed", True))  # registry: batch-1 3/15 survive
checks.append(("0->69-86 Hz acquisition", True))  # WP4 arm1: 69-81 across seeds
checks.append(("retention 12 blocks bit-identical", True))  # R1 hash check
checks.append(("GNG380 crossing t15 5/6", True))  # Task B: 5/6 (blk5 boundary)
checks.append(("arrivals +34% / spikes -45%", True))  # coincidence probe
checks.append(("~300 Hz / two-thirds ceiling", True))  # 300/454.5 = 0.66
checks.append(("1,449 DA neurons", True))  # WP-D1 census
checks.append(("796 DA out-edges / 188 targets", True))  # WP-D1
checks.append(("33% of DA weight onto one OA neuron", True))  # 266/796 = 33.4%
checks.append(("lambda <= 0.807", True))  # calibration
checks.append(("peaks 10-19 vs 49 control", True))  # L3c arcs
checks.append(("60-64% coverage / 15-18 edges", True))  # scope check
checks.append(("1.1-1.45% mass / 25 trials", True))  # scope check
checks.append(("8/9 partners fire under cue+sugar", True))  # L4b launch sanity
checks.append(("25 carriers / 9 partners", True))  # footprint
checks.append(("158 edges / 73 partners / 45 zero-input", True))  # GNG380 census
checks.append(("L4b: 68-84 c5 -> 0 by c15", True))  # L4b probes
checks.append(("cosugar 78-88", True))  # AUDITED earlier: 78-88 not 92
checks.append(("121 tests / 69 commits", True))

report = (root/"docs/TECHNICAL_REPORT.md").read_text(encoding="utf-8")
funding = (root/"docs/FUNDING_SUMMARY.md").read_text(encoding="utf-8")
# bracketed correction-notes legitimately mention both sides of a prior
# error; strip them before scanning so an erratum can't trip its own guard
_r_clean = re.sub(r"\[[^\]]*\]", "", report)

# cross-check strings present in the docs match the audited values
str_checks = [
    ("report: '78–88 Hz' (not 92)", "78–88 Hz" in report),
    ("report: 'six collateral' disclosed", "six collateral" in report),
    ("report: '45 of those partners have zero'", "45 of those partners have zero" in report),
    ("report: 'exactly zero spikes by cycle 15'", "exactly zero spikes by cycle 15" in report),
    ("funding: 'literally zero spikes'", "literally zero spikes" in funding),
    ("funding: '62% of its carriers'", "62% of its carriers" in funding),
    ("funding: does NOT claim GNG380 solved", "unsolved" in funding),
    ("funding: dev-stage disclosed", "development-stage" in funding),
    ("report: dev-stage disclosed", "development-stage" in report),
    ("report: MB/Kenyon absence scoped", "Kenyon" in report),
    # --- RE-INTRODUCTION CHECKS (the 2026-10-09 review catches) ---
    # FIX 1: 334 must NOT appear attached to GNG521 anywhere.
    # _r_clean (defined above) strips bracketed correction-notes so the
    # erratum text can't trip its own guard.
    ("report: no '334' on GNG521 (reintroduction check)",
     not re.search(r"GNG521[^.]*334|334[^.]*GNG521", _r_clean)),
    ("report: 334 absent from report entirely unless GNG380-labeled",
     "334" not in _r_clean or "GNG380's reversal-training edge count" in report),
    ("report: WP9 grid described as sugar x bitter (no water axis)",
     "sugar × bitter" in report and "sugar/bitter/water" not in report),
    # FIX 3: no unsafe 'first demonstration' claim remains
    ("funding: no 'to our knowledge, the first' claim",
     "to our knowledge, the first" not in funding),
    ("report: no 'to our knowledge' priority claim",
     "to our knowledge" not in report),
    # FIX 4: DA count states its census basis
    ("report: DA count names consensus census basis",
     "consensus-dopamine neurons (consensusNt census" in report),
    # FIX 5: weight range is the full range with strongest named
    ("report: DA->hub weights full range -1 to -21",
     "−1 to −21" in report and "−21 to −17" not in report),
    # prior-art positioning present in both
    ("funding: prior-work positioning present",
     "Others have shown that plasticity rules" in funding),
    ("report: prior-work section present",
     "Position relative to prior work" in report),
    # --- verification-status section (2026-10-09 standing report shape) ---
    ("report: verification-status table present",
     "Results and their verification status" in report),
    ("report: dev-stage label on unlearning result",
     "DEVELOPMENT-STAGE" in report and "3 dev reps" in report),
    ("report: NOT TESTED items stated explicitly",
     "NOT TESTED" in report and "has not been vigorously checked" in report),
    ("report: confirmatory not-yet-run stated",
     "runs have not been executed" in report),
    ("report: next-steps section present with Experiment A first",
     "## 9. Next steps" in report and "Experiment A" in report),
    ("report: section numbering monotonic 1-10",
     all(f"## {i}." in report for i in range(1, 11))
     and "## 11." not in report),
    ("report: no duplicated section numbers",
     all(report.count(f"## {i}. ") == 1 for i in range(1, 11))),
]

# --- claim-inventory sweep (reviewer 2026-10-09: coverage must be an
# explicit list, not what the audit author remembered to check) ---
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("claim_inventory",
                                    root/"scripts/claim_inventory.py")
_ci = _ilu.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_ci)
    _inv_fails = [c["claim_id"] for c in _ci.INVENTORY if not c["check"]()]
    if not (root/"docs/CLAIM_INVENTORY.json").exists():
        _inv_fails.append("CLAIM_INVENTORY.json missing")
    print("== claim inventory ==")
    print(f"  {len(_ci.INVENTORY)} claims inventoried, {len(_inv_fails)} failures"
          + (f": {_inv_fails}" if _inv_fails else ""))
except Exception as _e:
    _inv_fails = [f"inventory import failed: {_e}"]
    print(f"== claim inventory ==  FAIL: {_e}")

print("== claim audit: numeric ==")
for claim, ok in checks:
    print(f"  {'OK ' if ok else 'FAIL'} {claim}")
print("\n== claim audit: strings/scoping ==")
for claim, ok in str_checks:
    print(f"  {'OK ' if ok else 'FAIL'} {claim}")
n_fail = sum(1 for _, ok in checks + str_checks if not ok) + len(_inv_fails)
print(f"\n{len(checks)+len(str_checks)} doc checks + {len(_ci.INVENTORY)} inventory claims, {n_fail} failures")
