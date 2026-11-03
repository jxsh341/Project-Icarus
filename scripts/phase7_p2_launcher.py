"""Phase 7 WP-P2 - guarded launcher for GNG380 confirmatory unlearning.

Mirrors scripts/phase6_expB_launcher.py per docs/PHASE_7_PREREG.md. The L6b
harness FILE is never modified - REPS/OUT/TRAIN_SEED_BASE/PROBE_SEED_BASE are
injected in memory only; harness sha256 verified before and after EVERY rep.

Guards (raise, never warn):
  G1 harness sha256 == frozen, before and after every invocation
  G2 only the four injection keys differ after injection
  G3 P7 seed spaces collision-free AND disjoint from dev+confirm+Phase6
  G4 output root holds only known artifacts (complete reps skipped,
     incomplete quarantined, never deleted)
  G5 injected OUT is never a dev/confirm/phase4/phase6 output dir
  G6 prereg7 anchors reproduce from the Random(20261104) draw
  G7 cwd is the repo root

Usage: uv run python scripts/phase7_p2_launcher.py
"""
from __future__ import annotations

import importlib.util
import json
import os
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
import phase7_p2_analysis as p7  # noqa: E402

HARNESS = ROOT / "scripts" / "phase6_wp_l6b_rankforget.py"
FROZEN_HARNESS_SHA = "08110ddfb2ae3b2a89782c4a48b4bd5e4a52f9f171febb8b91236dcd28427508"
PREREG7 = ROOT / "docs/PHASE_7_PREREG.md"
OUT_ROOT = ROOT / "results/phase7/p2_g380"
INJECT_KEYS = {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT"}
FORBIDDEN_OUTS = {an.DEV_OUT, an.CONF_ROOT, ROOT / "results/phase4/wp_l4b",
                  ROOT / "results/phase2/taskB_r1", eb.L6B_ROOT, eb.G380_ROOT}
N_REPS = 8


class GuardViolation(Exception):
    pass


def guard_harness_sha() -> None:
    actual = an.sha256_file(HARNESS)
    if actual != FROZEN_HARNESS_SHA:
        raise GuardViolation(f"G1 harness sha256 {actual[:12]} != frozen")


def _same(a, b) -> bool:
    try:
        return bool(a == b) if not hasattr(a, "shape") else bool((a == b).all())
    except Exception:
        return a is b


def guard_injection_keys(before, after) -> None:
    changed = {k for k in set(before) | set(after)
               if k not in before or k not in after or not _same(before.get(k), after.get(k))}
    if changed - INJECT_KEYS:
        raise GuardViolation(f"G2 injection changed non-injection keys: {sorted(changed - INJECT_KEYS)}")


def guard_seed_space() -> None:
    doc = PREREG7.read_text(encoding="utf-8")
    train = p7.grab(doc, "P7_TRAIN_SEEDS")
    probe = p7.grab(doc, "P7_PROBE_SEEDS")
    shadow = set(p7.grab(doc, "P7_SHADOW_SEEDS"))
    tr = set().union(*[eb.exp_train_seeds(b) for b in train])
    pr = set().union(*[eb.exp_probe_seeds(b) for b in probe])
    all7 = tr | pr | shadow
    if len(all7) != 200 + 315 + 8:
        raise GuardViolation("G3 P7 seed space has internal collisions")
    dev = an.dev_seed_space()
    ct, cp = an.parse_prereg_seeds()
    conf = set()
    for b in ct:
        conf |= set(an.expected_train_seeds(b))
    for b in cp:
        conf |= set(an.expected_probe_seeds(b)) | {an.sanity_seed(b)}
    doc6 = (ROOT / "docs/PHASE_6_PREREG.md").read_text(encoding="utf-8")
    t6, p6s = eb.seed_spaces(eb.grab(doc6, "P6_TRAIN_SEEDS"), eb.grab(doc6, "P6_PROBE_SEEDS"))
    prior = dev | conf | t6 | p6s | set(eb.grab(doc6, "P6_SHADOW_SEEDS"))
    if all7 & prior:
        raise GuardViolation("G3 P7 seed space overlaps dev/confirm/Phase6 spaces")


def guard_output_root() -> None:
    if not OUT_ROOT.exists():
        return
    known = {"launcher_manifest.json"} | {f"rep_r{r}" for r in range(N_REPS)}
    unknown = [q.name for q in OUT_ROOT.iterdir() if q.name not in known]
    if unknown:
        raise GuardViolation(f"G4 unknown artifacts in {OUT_ROOT}: {unknown}")


def guard_cwd() -> None:
    if Path.cwd().resolve() != ROOT:
        raise GuardViolation(f"G7 cwd {Path.cwd()} != repo root")


def rep_complete(out_dir: Path, train_base: int) -> tuple[bool, str]:
    try:
        hist = an.read_jsonl(out_dir / "ckpt_r0" / "history.jsonl", "history")
        if len(hist) != 25:
            return False, f"history rows {len(hist)} != 25"
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
        if state.get("n_history") != 25:
            return False, f"n_history {state.get('n_history')}"
        return True, "complete"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def write_manifest(train, probe, reps_meta, status) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    (OUT_ROOT / "launcher_manifest.json").write_text(json.dumps({
        "experiment": "Phase 7 WP-P2 GNG380 confirmatory (rank-targeted decay)",
        "status": status, "harness": "scripts/phase6_wp_l6b_rankforget.py",
        "harness_sha256": FROZEN_HARNESS_SHA, "target": "g380", "n_reps": N_REPS,
        "prereg": "docs/PHASE_7_PREREG.md", "prereg_sha256": an.sha256_file(PREREG7),
        "git_head": head, "created": datetime.now(timezone.utc).isoformat(),
        "train_anchors": train, "probe_anchors": probe, "reps": reps_meta,
    }, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    t0 = time.time()
    print(f"Phase 7 WP-P2 launcher - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_cwd()                                   # G7
    p7.reproduce_draw()                           # G6
    guard_harness_sha()                           # G1
    guard_output_root()                           # G4
    guard_seed_space()                            # G3
    print("G1/G3/G4/G6/G7 guards passed", flush=True)

    doc = PREREG7.read_text(encoding="utf-8")
    train = p7.grab(doc, "P7_TRAIN_SEEDS")
    probe = p7.grab(doc, "P7_PROBE_SEEDS")

    spec = importlib.util.spec_from_file_location("phase6_wp_l6b_rankforget_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase6_wp_l6b_rankforget_frozen"] = mod
    spec.loader.exec_module(mod)
    os.environ["L6B_TARGET"] = "g380"

    reps_meta: list[dict] = []
    write_manifest(train, probe, reps_meta, "launched")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for r in range(N_REPS):
        out_dir = OUT_ROOT / f"rep_r{r}"
        meta = {"rep": r, "train_base": train[r], "probe_base": probe[r],
                "expected_train_seeds": sorted(eb.exp_train_seeds(train[r])),
                "expected_probe_seeds": sorted(eb.exp_probe_seeds(probe[r]))}
        if out_dir.exists():
            ok, why = rep_complete(out_dir, train[r])
            if ok:
                print(f"rep {r}: pre-existing COMPLETE - skipping", flush=True)
                reps_meta.append({**meta, "note": "pre-existing complete"})
                write_manifest(train, probe, reps_meta, "running")
                continue
            q = OUT_ROOT.parent / "quarantine" / f"p2_rep{r}_{ts}"
            q.mkdir(parents=True, exist_ok=True)
            out_dir.rename(q / f"rep_r{r}")
            print(f"rep {r}: INCOMPLETE ({why}) - quarantined", flush=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        before = dict(vars(mod))
        mod.TRAIN_SEED_BASE = train[r]
        mod.PROBE_SEED_BASE = probe[r]
        mod.REPS = 1
        mod.OUT = out_dir
        guard_injection_keys(before, dict(vars(mod)))          # G2
        if mod.OUT in FORBIDDEN_OUTS or any(mod.OUT.is_relative_to(p) for p in FORBIDDEN_OUTS):
            raise GuardViolation("G5 injected OUT is a forbidden directory")
        print(f"=== rep {r}/{N_REPS - 1}: train_base={train[r]} probe_base={probe[r]} ===", flush=True)
        t1 = time.time()
        mod.main()
        wall = time.time() - t1
        guard_harness_sha()                                    # G1 after
        ok, why = rep_complete(out_dir, train[r])
        if not ok:
            raise RuntimeError(f"rep {r}: artifacts incomplete after run: {why}")
        reps_meta.append({**meta, "wall_s": round(wall, 1)})
        write_manifest(train, probe, reps_meta, "running")
        print(f"rep {r} complete in {wall / 60:.1f} min", flush=True)
    write_manifest(train, probe, reps_meta, "completed")
    print(f"ALL {N_REPS} REPS COMPLETE - verdict via uv run python scripts/phase7_p2_analysis.py", flush=True)
    print(f"launcher total {((time.time() - t0) / 60):.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
