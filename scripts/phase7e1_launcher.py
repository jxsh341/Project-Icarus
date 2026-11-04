"""Phase 7 E1 launcher - closed-loop conditioning, arms learn/control.

Per docs/PHASE_7E1_PREREG.md. Harness FILE never modified; OUT/REPS/
TASTE_BASE/PROBE_BASE injected in memory only, harness sha256 verified
before and after EVERY invocation.

Guards (raise, never warn):
  G1 harness sha256 == frozen (prereg), before/after every invocation
  G2 only injection keys differ after injection
  G3 E1 seed spaces disjoint from all prior spaces (dev/confirm/P6/P7/
     screen/P7B), whole-space collision check
  G4 output dirs hold only known artifacts (complete reps skipped,
     incomplete quarantined, never deleted)
  G5 injected OUT never a forbidden results dir
  G6 prereg anchors reproduce from Random(20261107)
  G7 cwd is repo root

Usage: uv run python scripts/phase7e1_launcher.py
"""
from __future__ import annotations

import hashlib
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
import phase7e1_analysis as e1  # noqa: E402

HARNESS = ROOT / "scripts/phase7e1_harness.py"
PREREG = ROOT / "docs/PHASE_7E1_PREREG.md"
INJECT_KEYS = {"TASTE_BASE", "PROBE_BASE", "REPS", "OUT"}
FORBIDDEN = [an.DEV_OUT, an.CONF_ROOT, ROOT / "results/phase2", ROOT / "results/phase4",
             ROOT / "results/phase6", ROOT / "results/phase7", ROOT / "results/phase7b"]
N_REPS = 4


class GuardViolation(Exception):
    pass


def harness_sha():
    return hashlib.sha256(HARNESS.read_bytes()).hexdigest()


def guard_g1(frozen):
    actual = harness_sha()
    if actual != frozen:
        raise GuardViolation(f"G1 harness sha {actual[:12]} != frozen {frozen[:12]}")


def guard_g2(before, after):
    changed = {k for k in set(before) | set(after)
               if k not in before or k not in after or before.get(k) != after.get(k)}
    if changed - INJECT_KEYS:
        raise GuardViolation(f"G2 non-injection keys changed: {sorted(changed - INJECT_KEYS)}")


def guard_g7():
    if Path.cwd().resolve() != ROOT:
        raise GuardViolation(f"G7 cwd {Path.cwd()} != {ROOT}")


def stage_complete(out_dir: Path, arm: str, tb: int, pb: int) -> tuple[bool, str]:
    try:
        rows = an.read_jsonl(out_dir / f"{arm}.jsonl", "jsonl")
        if len([x for x in rows if x.get("phase") == "taste"]) != 24:
            return False, "taste rows != 24"
        if len([x for x in rows if x.get("phase") == "probe"]) != 12:
            return False, "probe rows != 12"
        post = [x for x in rows if x.get("phase") == "post_taste"]
        if len(post) != 1 or post[0]["train_base"] != tb or post[0]["probe_base"] != pb:
            return False, "post_taste row/seeds wrong"
        exp_taste = sorted(tb + t for t in range(1, 25))
        if sorted(x["seed"] for x in rows if x.get("phase") == "taste") != exp_taste:
            return False, "taste seeds != expected"
        if not (out_dir / "footprint_r0.json").exists():
            return False, "footprint missing"
        return True, "complete"
    except Exception as ex:
        return False, f"{type(ex).__name__}: {ex}"


def main() -> int:
    import hashlib as _h, re as _re
    t0 = time.time()
    print(f"Phase 7 E1 launcher - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_g7()
    doc = PREREG.read_text(encoding="utf-8")
    m = _re.search(r'HARNESS_SHA256\s*=\s*"([0-9a-f]{64})"', doc)
    if not m:
        raise GuardViolation("prereg7e1 missing HARNESS_SHA256")
    frozen_sha = m.group(1)
    guard_g1(frozen_sha)
    e1.reproduce_draw()  # G3 + G6
    print("G1/G3/G6/G7 guards passed", flush=True)

    tb = e1.grab(doc, "E1_TASTE_BASES")
    pb = e1.grab(doc, "E1_PROBE_BASES")

    spec = importlib.util.spec_from_file_location("phase7e1_harness_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7e1_harness_frozen"] = mod
    spec.loader.exec_module(mod)

    (ROOT / "results/phase7e1").mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "Phase 7 E1 closed-loop conditioning",
                "harness_sha256": frozen_sha, "prereg": "docs/PHASE_7E1_PREREG.md",
                "prereg_sha256": _h.sha256(PREREG.read_bytes()).hexdigest(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           capture_output=True, text=True).stdout.strip(),
                "reps": [], "created": datetime.now(timezone.utc).isoformat()}
    mpath = ROOT / "results/phase7e1/launcher_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for arm in ("learn", "control"):
        for r in range(N_REPS):
            out_dir = ROOT / "results/phase7e1" / arm / f"rep_r{r}"
            if out_dir.exists():
                ok, why = stage_complete(out_dir, arm, tb[r], pb[r])
                if ok:
                    print(f"{arm} r{r}: pre-existing COMPLETE - skip", flush=True)
                    continue
                q = ROOT / "results/phase7e1/quarantine" / f"e1_{arm}_r{r}_{ts}"
                q.mkdir(parents=True, exist_ok=True)
                out_dir.rename(q / out_dir.name)
                print(f"{arm} r{r}: INCOMPLETE ({why}) - quarantined", flush=True)
            if any(out_dir.is_relative_to(f) for f in FORBIDDEN):
                raise GuardViolation(f"G5 OUT {out_dir} forbidden")
            out_dir.mkdir(parents=True, exist_ok=True)
            before = dict(vars(mod))
            mod.TASTE_BASE = tb[r]
            mod.PROBE_BASE = pb[r]
            mod.REPS = 1
            mod.OUT = out_dir
            guard_g2(before, dict(vars(mod)))
            os.environ["PHASE7E1_ARM"] = arm
            print(f"=== {arm} r{r} taste_base={tb[r]} probe_base={pb[r]} ===", flush=True)
            t1 = time.time()
            mod.main()
            guard_g1(frozen_sha)
            ok, why = stage_complete(out_dir, arm, tb[r], pb[r])
            if not ok:
                raise RuntimeError(f"{arm} r{r}: incomplete after run: {why}")
            manifest["reps"].append({"arm": arm, "rep": r, "taste_base": tb[r],
                                     "probe_base": pb[r], "wall_s": round(time.time() - t1, 1)})
            mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
            print(f"{arm} r{r} complete in {(time.time() - t1) / 60:.1f} min", flush=True)
    print(f"ALL DONE - verdict via uv run python scripts/phase7e1_analysis.py "
          f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
