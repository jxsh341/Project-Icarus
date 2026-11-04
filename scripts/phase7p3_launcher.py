"""Phase 7 P3 launcher - graded decay dose sweep, fast mode, sharded reps.

Per docs/PHASE_7P3_PREREG.md. Harness FILE never modified; OUT/REPS/
PROBE_BASE/TAU injected in memory only, harness sha256 verified before and
after EVERY invocation. Rep shard via env PHASE7P3_SHARD="0-3" (4 shards of 4
reps run as parallel processes; manifests per shard).

Guards (raise, never warn): G1 harness sha, G2 injection keys only,
G3 seed spaces disjoint from all prior (dev/confirm/P6/P7/screen/P7B/E1),
G4 known artifacts only (complete reps skipped, incomplete quarantined),
G5 OUT never forbidden, G6 prereg anchors reproduce Random(20261108),
G7 cwd repo root.
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
import phase7p3_analysis as p3  # noqa: E402

HARNESS = ROOT / "scripts/phase7p3_harness.py"
PREREG = ROOT / "docs/PHASE_7P3_PREREG.md"
INJECT_KEYS = {"PROBE_BASE", "REPS", "OUT", "TAU", "MODE"}
FORBIDDEN = [an.DEV_OUT, an.CONF_ROOT] + [ROOT / f"results/{d}" for d in
             ("phase2", "phase4", "phase6", "phase7", "phase7b", "phase7e1")]
TAU_LEVELS = p3.TAU_LEVELS


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


def stage_complete(out_dir: Path, tau: float, base: int) -> tuple[bool, str]:
    try:
        rows = an.read_jsonl(out_dir / "p3.jsonl", "jsonl")
        cfg = [x for x in rows if x.get("phase") == "config"]
        probes = [x for x in rows if x.get("phase") == "probe"]
        if len(cfg) != 1 or cfg[0]["tau"] != tau or cfg[0]["probe_base"] != base or cfg[0]["mode"] != "fast":
            return False, "config mismatch"
        if len(probes) != 8:
            return False, f"probes {len(probes)} != 8"
        if not (out_dir / "footprint_final.json").exists():
            return False, "footprint missing"
        return True, "complete"
    except Exception as ex:
        return False, f"{type(ex).__name__}: {ex}"


def main() -> int:
    t0 = time.time()
    shard = os.environ.get("PHASE7P3_SHARD", "0-15")
    lo, hi = (int(x) for x in shard.split("-"))
    reps = list(range(lo, hi + 1))
    print(f"Phase 7 P3 launcher shard {shard} - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_g7()
    doc = PREREG.read_text(encoding="utf-8")
    m = re.search(r'HARNESS_SHA256\s*=\s*"([0-9a-f]{64})"', doc)
    if not m:
        raise GuardViolation("prereg7p3 missing HARNESS_SHA256")
    frozen_sha = m.group(1)
    guard_g1(frozen_sha)
    p3.reproduce_draw()  # G3 + G6
    print("G1/G3/G6/G7 guards passed", flush=True)
    bases = p3.grab(doc, "P3_PROBE_BASES")

    spec = importlib.util.spec_from_file_location("phase7p3_harness_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7p3_harness_frozen"] = mod
    spec.loader.exec_module(mod)

    out_root = ROOT / "results/phase7p3"
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "Phase 7 P3 graded decay", "shard": shard,
                "harness_sha256": frozen_sha, "prereg": "docs/PHASE_7P3_PREREG.md",
                "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           capture_output=True, text=True).stdout.strip(),
                "reps": [], "created": datetime.now(timezone.utc).isoformat()}
    mpath = out_root / f"launcher_manifest_{shard.replace('-', '_')}.json"
    mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for r in reps:
        tau = TAU_LEVELS[r % 4]
        out_dir = out_root / f"rep_r{r}"
        if out_dir.exists():
            ok, why = stage_complete(out_dir, tau, bases[r])
            if ok:
                print(f"r{r}: pre-existing COMPLETE - skip", flush=True)
                continue
            q = out_root / "quarantine" / f"p3_r{r}_{ts}"
            q.mkdir(parents=True, exist_ok=True)
            out_dir.rename(q / out_dir.name)
            print(f"r{r}: INCOMPLETE ({why}) - quarantined", flush=True)
        if any(out_dir.is_relative_to(f) for f in FORBIDDEN):
            raise GuardViolation(f"G5 OUT {out_dir} forbidden")
        out_dir.mkdir(parents=True, exist_ok=True)
        before = dict(vars(mod))
        mod.PROBE_BASE = bases[r]
        mod.REPS = 1
        mod.OUT = out_dir
        mod.TAU = tau
        mod.MODE = "fast"
        guard_g2(before, dict(vars(mod)))
        os.environ["PHASE7P3_MODE"] = "fast"
        print(f"=== r{r} tau={tau} probe_base={bases[r]} ===", flush=True)
        t1 = time.time()
        mod.main()
        guard_g1(frozen_sha)
        ok, why = stage_complete(out_dir, tau, bases[r])
        if not ok:
            raise RuntimeError(f"r{r}: incomplete after run: {why}")
        manifest["reps"].append({"rep": r, "tau": tau, "probe_base": bases[r],
                                 "wall_s": round(time.time() - t1, 1)})
        mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        print(f"r{r} complete in {(time.time() - t1) / 60:.1f} min", flush=True)
    print(f"shard {shard} DONE ({(time.time() - t0) / 60:.1f} min) - verdict via "
          f"uv run python scripts/phase7p3_analysis.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
