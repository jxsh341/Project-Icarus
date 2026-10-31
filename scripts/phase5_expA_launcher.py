"""Phase 5 Experiment A - confirmatory launcher (per-rep invocation design).

Amendment A1 design: rep r runs the FROZEN harness once with REPS=1 and
injected bases TRAIN_SEED_BASE=CONF_TRAIN_SEEDS[r],
PROBE_SEED_BASE=CONF_PROBE_SEEDS[r] (first 8 of the 15 frozen probe
anchors in doc order; 7 reserved-unused, recorded in the manifest).

The harness FILE is never modified: injection is via in-memory module
attributes only, and the file's sha256 is verified against the frozen
value before and after EVERY invocation. Outputs land in fresh per-rep
directories under results/phase4/wp_l4b_confirm/; the dev directory
(results/phase4/wp_l4b) is never written.

Runtime guards (raise, never warn - standing rule):
  G1 harness sha256 == frozen value, before and after every invocation
  G2 only the four injection keys differ after injection
  G3 confirmatory seed space collision-free AND disjoint from dev space
  G4 confirmatory output root is fresh (missing or empty)
  G5 injected OUT is never the dev OUT
  G6 prereg anchors reproduce from the documented generator
  G7 cwd is the repo root (harness paths are repo-relative)

Usage: uv run python scripts/phase5_expA_launcher.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase5_expA_analysis as an  # noqa: E402

HARNESS = an.HARNESS
CONF_ROOT = an.CONF_ROOT
MANIFEST = CONF_ROOT / "launcher_manifest.json"
INJECT_KEYS = {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT"}
N_REPS = an.N_REPS


class GuardViolation(Exception):
    """A pre-registered runtime guard refused to proceed."""


def guard_harness_sha(path: Path, expected: str) -> None:
    actual = an.sha256_file(path)
    if actual != expected:
        raise GuardViolation(
            f"G1 harness sha256 {actual[:12]} != frozen {expected[:12]} "
            f"({path.name}) - refusing to run against a modified implementation")


def guard_injection_keys(before: dict, after: dict, allowed: set) -> None:
    changed = {k for k in set(before) | set(after)
               if k not in before or k not in after or not _same(before.get(k), after.get(k))}
    unexpected = changed - allowed
    if unexpected:
        raise GuardViolation(
            f"G2 injection changed non-injection module keys: {sorted(unexpected)}")


def _same(a, b) -> bool:
    try:
        return bool(a == b) if not hasattr(a, "shape") else bool((a == b).all())
    except Exception:
        return a is b


def guard_seed_space(train_anchors: list[int], probe_anchors: list[int], n_reps: int) -> set:
    train_sets = [an.expected_train_seeds(b) for b in train_anchors[:n_reps]]
    probe_sets = [an.expected_probe_seeds(b) for b in probe_anchors[:n_reps]]
    sanity = {an.sanity_seed(b) for b in probe_anchors[:n_reps]}
    total = sum(len(s) for s in train_sets) + sum(len(s) for s in probe_sets) + len(sanity)
    union = set().union(*train_sets, *probe_sets, sanity)
    if len(union) != total:
        raise GuardViolation(
            f"G3 confirmatory seed space has {total - len(union)} COLLISIONS")
    dev = an.dev_seed_space()
    overlap = union & dev
    if overlap:
        raise GuardViolation(
            f"G3 {len(overlap)} confirmatory seeds overlap the dev space "
            f"(e.g. {sorted(overlap)[:4]})")
    if min(union) <= max(dev):
        raise GuardViolation("G3 confirmatory seed space is not strictly above the dev space")
    return union


def guard_fresh_out(root: Path) -> None:
    if root.exists() and any(root.iterdir()):
        raise GuardViolation(
            f"G4 confirmatory output root is not fresh: {root} is non-empty - "
            "quarantine superseded artifacts before relaunching (never resume stale)")


def guard_cwd() -> None:
    if Path.cwd().resolve() != ROOT:
        raise GuardViolation(f"G7 cwd {Path.cwd()} != repo root {ROOT} "
                             "(harness artifact paths are repo-relative)")


def _write_manifest(train_anchors, probe_anchors, reps_meta, status: str) -> None:
    CONF_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        head = None
    MANIFEST.write_text(json.dumps({
        "experiment": "Phase 5 Experiment A - confirmatory replication (Amendment A1)",
        "status": status,
        "design": "per-rep invocation; REPS=1 injected; bases = frozen anchors; "
                  "harness file unmodified (sha256 verified per invocation)",
        "harness": str(HARNESS.relative_to(ROOT)).replace("\\", "/"),
        "harness_sha256": an.FROZEN_HARNESS_SHA,
        "prereg": str(an.PREREG.relative_to(ROOT)).replace("\\", "/"),
        "prereg_sha256": an.sha256_file(an.PREREG),
        "git_head": head,
        "reserved_unused_probe_anchors": probe_anchors[N_REPS:],
        "created": datetime.now(timezone.utc).isoformat(),
        "reps": reps_meta,
    }, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    t_start = time.time()
    print(f"Phase 5 Experiment A launcher - {datetime.now(timezone.utc).isoformat()}",
          flush=True)

    # --- pre-registered runtime guards (all before any simulation) ---
    guard_cwd()
    train_anchors, probe_anchors = an.parse_prereg_seeds()
    an.reproduce_draw(train_anchors, probe_anchors)          # G6
    print(f"G6 prereg anchors reproduce: {len(train_anchors)} train, "
          f"{len(probe_anchors)} probe", flush=True)
    guard_harness_sha(HARNESS, an.FROZEN_HARNESS_SHA)         # G1
    print(f"G1 harness sha256 == frozen {an.FROZEN_HARNESS_SHA[:12]}", flush=True)
    guard_fresh_out(CONF_ROOT)                                 # G4
    union = guard_seed_space(train_anchors, probe_anchors, N_REPS)  # G3
    print(f"G3 seed space clean: {len(union)} distinct seeds, all above "
          f"dev space", flush=True)

    # --- load the FROZEN harness module (read-only import) ---
    spec = importlib.util.spec_from_file_location("phase4_wp_l4b_extinction_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase4_wp_l4b_extinction_frozen"] = mod
    spec.loader.exec_module(mod)

    reps_meta: list[dict] = []
    _write_manifest(train_anchors, probe_anchors, reps_meta, "launched")

    for r in range(N_REPS):
        out_dir = CONF_ROOT / f"rep_r{r}"
        out_dir.mkdir(parents=True, exist_ok=True)
        before = dict(vars(mod))
        mod.TRAIN_SEED_BASE = train_anchors[r]
        mod.PROBE_SEED_BASE = probe_anchors[r]
        mod.REPS = 1
        mod.OUT = out_dir
        guard_injection_keys(before, dict(vars(mod)), INJECT_KEYS)   # G2
        if mod.OUT == an.DEV_OUT:
            raise GuardViolation("G5 injected OUT equals the dev OUT directory")
        if mod.REPS != 1:
            raise GuardViolation("G2 REPS injection failed")

        print(f"\n=== rep {r}/{N_REPS - 1}: train_base={train_anchors[r]} "
              f"probe_base={probe_anchors[r]} out={out_dir.name} ===", flush=True)
        t0 = time.time()
        rc = mod.main()
        wall = time.time() - t0
        if rc != 0:
            raise RuntimeError(f"rep {r}: harness main() returned {rc}")
        guard_harness_sha(HARNESS, an.FROZEN_HARNESS_SHA)             # G1 after

        reps_meta.append({
            "rep": r, "out_dir": str(out_dir), "wall_s": round(wall, 1),
            "train_base": train_anchors[r], "probe_base": probe_anchors[r],
            "expected_train_seeds": sorted(an.expected_train_seeds(train_anchors[r])),
            "expected_probe_seeds": sorted(an.expected_probe_seeds(probe_anchors[r])),
            "sanity_seed": an.sanity_seed(probe_anchors[r]),
        })
        _write_manifest(train_anchors, probe_anchors, reps_meta, "running")
        print(f"rep {r} complete in {wall / 60:.1f} min", flush=True)

    _write_manifest(train_anchors, probe_anchors, reps_meta, "completed")
    total = time.time() - t_start
    print(f"\nALL {N_REPS} REPS COMPLETE in {total / 60:.1f} min", flush=True)
    print("VERDICT IS NOT EVALUATED HERE - run the frozen analysis: "
          "uv run python scripts/phase5_expA_analysis.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
