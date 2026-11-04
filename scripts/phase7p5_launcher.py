"""Phase 7 P5 launcher - footprint-estimation arms, one rep per shard.

Per docs/PHASE_7P5_PREREG.md. Harness FILE never modified; OUT/PROBE_BASE/ARM
injected in memory only, harness sha256 verified before/after EVERY invocation.
Rep via env PHASE7P5_SHARD="0".."5" (arm map in prereg section 2).

Guards (raise, never warn): G1 harness sha, G2 injection keys only,
G3 seed spaces disjoint from all prior, G4 known artifacts only (incomplete
quarantined), G5 OUT never forbidden, G6 prereg anchors reproduce
Random(20261111), G7 cwd repo root.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import phase5_expA_analysis as an  # noqa: E402
import phase7p5_analysis as p5  # noqa: E402

HARNESS = ROOT / "scripts/phase7p5_harness.py"
PREREG = ROOT / "docs/PHASE_7P5_PREREG.md"
INJECT_KEYS = {"PROBE_BASE", "OUT", "ARM"}
FORBIDDEN = [an.DEV_OUT, an.CONF_ROOT] + [ROOT / f"results/{d}" for d in
             ("phase2", "phase4", "phase6", "phase7", "phase7b", "phase7e1",
              "phase7p3", "phase7p4", "phase7p4b")]
ARM_OF = {0: "true", 1: "true", 2: "thresh4", 3: "thresh4", 4: "hop1", 5: "hop1"}


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


def complete(out_dir, base):
    try:
        rows = an.read_jsonl(out_dir / "unl.jsonl", "unl")
        if len([x for x in rows if x.get("stage") == "probe"]) != 12:
            return False, "probes != 12"
        cfg = [x for x in rows if x.get("stage") == "unl_cfg"]
        if not cfg or cfg[0]["probe_base"] != base:
            return False, "cfg/base wrong"
        return (out_dir / "final.json").exists(), "ok"
    except Exception as ex:
        return False, f"{type(ex).__name__}: {ex}"


def main() -> int:
    t0 = time.time()
    r = int(os.environ.get("PHASE7P5_SHARD", "0"))
    arm = ARM_OF[r]
    print(f"Phase 7 P5 launcher rep {r} arm={arm} - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_g7()
    doc = PREREG.read_text(encoding="utf-8")
    m = re.search(r'HARNESS_SHA256\s*=\s*"([0-9a-f]{64})"', doc)
    if not m:
        raise GuardViolation("prereg7p5 missing HARNESS_SHA256")
    frozen_sha = m.group(1)
    guard_g1(frozen_sha)
    p5.reproduce_draw()  # G3 + G6
    print("G1/G3/G6/G7 guards passed", flush=True)
    bases = p5.grab(doc, "P5_PROBE_BASES")

    spec = importlib.util.spec_from_file_location("phase7p5_harness_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7p5_harness_frozen"] = mod
    spec.loader.exec_module(mod)

    out_root = ROOT / "results/phase7p5"
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "Phase 7 P5 footprint-estimation sensitivity", "rep": r, "arm": arm,
                "harness_sha256": frozen_sha, "prereg": "docs/PHASE_7P5_PREREG.md",
                "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           capture_output=True, text=True).stdout.strip(),
                "created": datetime.now(timezone.utc).isoformat()}
    (out_root / f"launcher_manifest_r{r}.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = out_root / f"rep_r{r}"
    if (out_dir / "unl.jsonl").exists() or (out_dir / "final.json").exists():
        ok, why = complete(out_dir, bases[r])
        if ok:
            print(f"r{r}: pre-existing COMPLETE - skip", flush=True)
            return 0
        q = out_root / "quarantine" / f"p5_r{r}_{ts}"
        q.mkdir(parents=True, exist_ok=True)
        for f in out_dir.glob("*"):
            f.rename(q / f.name)
        print(f"r{r}: INCOMPLETE ({why}) - quarantined", flush=True)
    if any(out_dir.is_relative_to(f) for f in FORBIDDEN):
        raise GuardViolation(f"G5 OUT {out_dir} forbidden")
    out_dir.mkdir(parents=True, exist_ok=True)
    before = dict(vars(mod))
    mod.OUT = out_dir
    mod.PROBE_BASE = bases[r]
    mod.ARM = arm
    guard_g2(before, dict(vars(mod)))
    print(f"=== r{r} arm={arm} probe_base={bases[r]} ===", flush=True)
    mod.main()
    guard_g1(frozen_sha)
    ok, why = complete(out_dir, bases[r])
    if not ok:
        raise RuntimeError(f"r{r}: incomplete after run: {why}")
    print(f"rep {r} arm={arm} DONE ({(time.time() - t0) / 60:.1f} min) - verdict via "
          f"uv run python scripts/phase7p5_analysis.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
