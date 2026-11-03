"""Phase 6 Experiment B - guarded launcher for WP-L6b (rank-targeted forgetting).

Mirrors the Phase 5 launcher (scripts/phase5_expA_launcher.py) per the Phase 6
prereg (docs/PHASE_6_PREREG.md section 5, execution step 2). Per-rep invocation:
the L6b harness FILE is never modified - REPS/OUT/TRAIN_SEED_BASE/PROBE_SEED_BASE
are injected in memory only, and the harness sha256 is verified against the
frozen value before and after EVERY invocation.

Runtime guards (raise, never warn):
  G1 harness sha256 == frozen value, before and after every invocation
  G2 only the four injection keys differ after injection
  G3 Phase 6 seed spaces collision-free AND disjoint from dev+confirm+shadow
  G4 output root holds only known artifacts (idempotent relaunch: complete
     rep dirs skipped, incomplete quarantined, never deleted)
  G5 injected OUT is never a dev/confirm/phase4 output dir
  G6 prereg anchors reproduce from the Amendment-A1 draw algorithm
  G7 cwd is the repo root

Usage: uv run python scripts/phase6_expB_launcher.py [g521|g380|both]
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
import phase6_expB_analysis as eb  # noqa: E402

HARNESS = ROOT / "scripts" / "phase6_wp_l6b_rankforget.py"
FROZEN_HARNESS_SHA = "08110ddfb2ae3b2a89782c4a48b4bd5e4a52f9f171febb8b91236dcd28427508"
PREREG6 = ROOT / "docs" / "PHASE_6_PREREG.md"
INJECT_KEYS = {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT"}
FORBIDDEN_OUTS = {an.DEV_OUT, an.CONF_ROOT, ROOT / "results/phase4/wp_l4b",
                  ROOT / "results/phase2/taskB_r1"}


class GuardViolation(Exception):
    """A pre-registered runtime guard refused to proceed."""


def guard_harness_sha() -> None:
    actual = an.sha256_file(HARNESS)
    if actual != FROZEN_HARNESS_SHA:
        raise GuardViolation(f"G1 harness sha256 {actual[:12]} != frozen "
                             f"{FROZEN_HARNESS_SHA[:12]} - refusing to run")


def _same(a, b) -> bool:
    try:
        return bool(a == b) if not hasattr(a, "shape") else bool((a == b).all())
    except Exception:
        return a is b


def guard_injection_keys(before: dict, after: dict) -> None:
    changed = {k for k in set(before) | set(after)
               if k not in before or k not in after or not _same(before.get(k), after.get(k))}
    unexpected = changed - INJECT_KEYS
    if unexpected:
        raise GuardViolation(f"G2 injection changed non-injection keys: {sorted(unexpected)}")


def guard_seed_space(train_anchors, probe_anchors, n_reps) -> set:
    tr, pr = eb.seed_spaces(train_anchors[:n_reps], probe_anchors[:n_reps])
    all6 = tr.union(pr)
    if len(all6) != len(tr) + len(pr):
        raise GuardViolation("G3 P6 seed space has internal collisions")
    dev = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    conf = set()
    for b in ct:
        conf = conf.union(an.expected_train_seeds(b))
    for b in cp:
        conf = conf.union(an.expected_probe_seeds(b))
        conf.add(an.sanity_seed(b))
    shadow = set(eb.grab(PREREG6.read_text(encoding="utf-8"), "P6_SHADOW_SEEDS"))
    if all6.intersection(dev.union(conf)):
        raise GuardViolation("G3 P6 seed space overlaps dev/confirm spaces")
    if shadow.intersection(all6.union(dev).union(conf)):
        raise GuardViolation("G3 shadow seeds overlap run spaces")
    return all6


def guard_output_root(root: Path, n_reps: int) -> None:
    if not root.exists():
        return
    known = {"launcher_manifest.json"} | {f"rep_r{r}" for r in range(n_reps)}
    unknown = [q.name for q in root.iterdir() if q.name not in known]
    if unknown:
        raise GuardViolation(f"G4 unknown artifacts in {root}: {unknown}")


def guard_cwd() -> None:
    if Path.cwd().resolve() != ROOT:
        raise GuardViolation(f"G7 cwd {Path.cwd()} != repo root {ROOT}")


def rep_complete(out_dir: Path, train_base: int) -> tuple[bool, str]:
    """Artifact-level completion: 25 history rows with prereg-derived seeds;
    25 cycle + 20 probe JSONL rows; cycle-row seeds match; weight hash ok."""
    try:
        hist = an.read_jsonl(out_dir / "ckpt_r0" / "history.jsonl", "history")
        if len(hist) != eb.N_CYCLES:
            return False, f"history rows {len(hist)} != {eb.N_CYCLES}"
        if sorted(int(x["seed"]) for x in hist) != sorted(eb.exp_train_seeds(train_base)):
            return False, "history seeds != prereg-derived set"
        rows = an.read_jsonl(out_dir / "l6b_rankforget.jsonl", "jsonl")
        cyc = [x for x in rows if "ptype" not in x]
        probe = [x for x in rows if "ptype" in x]
        if len(cyc) != 25 or len(probe) != 20:
            return False, f"JSONL {len(cyc)} cycle / {len(probe)} probe"
        if sorted(int(x["seed"]) for x in cyc) != sorted(eb.exp_train_seeds(train_base)):
            return False, "cycle-row seeds != prereg-derived set"
        _m, state = an.load_final_matrix(out_dir / "ckpt_r0", "final")
        if state.get("n_history") != eb.N_CYCLES:
            return False, f"n_history {state.get('n_history')}"
        return True, "complete"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def write_manifest(root: Path, target: str, train_anchors, probe_anchors, reps_meta, status: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    (root / "launcher_manifest.json").write_text(json.dumps({
        "experiment": f"Phase 6 Experiment B (WP-L6b) target={target}",
        "status": status,
        "harness": "scripts/phase6_wp_l6b_rankforget.py",
        "harness_sha256": FROZEN_HARNESS_SHA,
        "prereg": "docs/PHASE_6_PREREG.md", "prereg_sha256": an.sha256_file(PREREG6),
        "git_head": head, "created": datetime.now(timezone.utc).isoformat(),
        "train_anchors": train_anchors, "probe_anchors": probe_anchors,
        "reps": reps_meta,
    }, indent=1) + "\n", encoding="utf-8")


def run_target(target: str) -> int:
    n_reps = eb.N_REPS if target == "g521" else 2
    root = eb.L6B_ROOT if target == "g521" else eb.G380_ROOT
    print(f"\n########## target={target} root={root} n_reps={n_reps} ##########", flush=True)
    guard_cwd()
    doc = PREREG6.read_text(encoding="utf-8")
    train = eb.grab(doc, "P6_TRAIN_SEEDS")[:n_reps]
    probe = eb.grab(doc, "P6_PROBE_SEEDS")[:n_reps]
    eb.reproduce_draw(eb.grab(doc, "P6_TRAIN_SEEDS"), eb.grab(doc, "P6_PROBE_SEEDS"),
                      eb.grab(doc, "P6_SHADOW_SEEDS"))          # G6
    guard_harness_sha()                                          # G1
    guard_output_root(root, n_reps)                              # G4
    guard_seed_space(eb.grab(doc, "P6_TRAIN_SEEDS"), eb.grab(doc, "P6_PROBE_SEEDS"), n_reps)  # G3
    print("G1/G3/G4/G6/G7 guards passed", flush=True)

    spec = importlib.util.spec_from_file_location("phase6_wp_l6b_rankforget_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase6_wp_l6b_rankforget_frozen"] = mod
    spec.loader.exec_module(mod)
    import os
    os.environ["L6B_TARGET"] = target

    reps_meta: list[dict] = []
    write_manifest(root, target, train, probe, reps_meta, "launched")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for r in range(n_reps):
        out_dir = root / f"rep_r{r}"
        meta = {"rep": r, "train_base": train[r], "probe_base": probe[r],
                "expected_train_seeds": sorted(eb.exp_train_seeds(train[r])),
                "expected_probe_seeds": sorted(eb.exp_probe_seeds(probe[r]))}
        if out_dir.exists():
            ok, why = rep_complete(out_dir, train[r])
            if ok:
                print(f"rep {r}: pre-existing COMPLETE - skipping (idempotent)", flush=True)
                reps_meta.append({**meta, "note": "pre-existing complete"})
                write_manifest(root, target, train, probe, reps_meta, "running")
                continue
            q = root.parent / "quarantine" / f"expB_{target}_rep{r}_{ts}"
            q.mkdir(parents=True, exist_ok=True)
            out_dir.rename(q / f"rep_r{r}")
            print(f"rep {r}: INCOMPLETE ({why}) - quarantined, re-running", flush=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        before = dict(vars(mod))
        mod.TRAIN_SEED_BASE = train[r]
        mod.PROBE_SEED_BASE = probe[r]
        mod.REPS = 1
        mod.OUT = out_dir
        guard_injection_keys(before, dict(vars(mod)))            # G2
        if mod.OUT in FORBIDDEN_OUTS or mod.OUT.is_relative_to(ROOT / "results/phase4"):
            raise GuardViolation("G5 injected OUT is a forbidden (dev/phase4) directory")
        print(f"=== rep {r}/{n_reps - 1}: train_base={train[r]} probe_base={probe[r]} ===", flush=True)
        t0 = time.time()
        mod.main()
        wall = time.time() - t0
        guard_harness_sha()                                      # G1 after
        ok, why = rep_complete(out_dir, train[r])
        if not ok:
            raise RuntimeError(f"rep {r}: artifacts incomplete after run: {why}")
        reps_meta.append({**meta, "wall_s": round(wall, 1)})
        write_manifest(root, target, train, probe, reps_meta, "running")
        print(f"rep {r} complete in {wall / 60:.1f} min", flush=True)
    write_manifest(root, target, train, probe, reps_meta, "completed")
    print(f"target {target}: ALL {n_reps} REPS COMPLETE - verdict via "
          f"uv run python scripts/phase6_expB_analysis.py", flush=True)
    return 0


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    t0 = time.time()
    print(f"Phase 6 Experiment B launcher - {datetime.now(timezone.utc).isoformat()}", flush=True)
    if which in ("g521", "both"):
        run_target("g521")
    if which in ("g380", "both"):
        run_target("g380")
    print(f"launcher total {((time.time() - t0) / 60):.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
