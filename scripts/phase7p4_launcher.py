"""Phase 7 P4 launcher - selective removal, stages acq -> unlearn per rep.

Per docs/PHASE_7P4_PREREG.md. Harness FILE never modified; OUT/ACQ_BASE/
UNL_BASE injected in memory only, harness sha256 verified before/after EVERY
invocation. Rep shard via env PHASE7P4_SHARD="0" (one rep per process; run 4
in parallel).

Guards (raise, never warn): G1 harness sha, G2 injection keys only,
G3 seed spaces disjoint from all prior, G4 known artifacts only (complete
stages skipped, incomplete quarantined), G5 OUT never forbidden,
G6 prereg anchors reproduce Random(20261109), G7 cwd repo root.
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
import phase7p4_analysis as p4  # noqa: E402

HARNESS = ROOT / "scripts/phase7p4_harness.py"
PREREG = ROOT / "docs/PHASE_7P4_PREREG.md"
INJECT_KEYS = {"ACQ_BASE", "UNL_BASE", "OUT"}
FORBIDDEN = [an.DEV_OUT, an.CONF_ROOT] + [ROOT / f"results/{d}" for d in
             ("phase2", "phase4", "phase6", "phase7", "phase7b", "phase7e1", "phase7p3")]


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


def acq_complete(out_dir, base):
    try:
        rows = an.read_jsonl(out_dir / "acq.jsonl", "acq")
        if len([x for x in rows if x.get("stage") == "acq"]) != 8:
            return False, "trials != 8"
        if len([x for x in rows if x.get("stage") == "acq_probe"]) != 4:
            return False, "probes != 4"
        if sorted(x["seed"] for x in rows if x.get("stage") == "acq") != sorted(base + t for t in range(1, 9)):
            return False, "trial seeds wrong"
        return (out_dir / "combined.npz").exists() and (out_dir / "footprints.json").exists(), "ok"
    except Exception as ex:
        return False, f"{type(ex).__name__}: {ex}"


def unl_complete(out_dir, base):
    try:
        rows = an.read_jsonl(out_dir / "unl.jsonl", "unl")
        if len([x for x in rows if x.get("stage") == "probe"]) != 24:
            return False, "probes != 24"
        cfg = [x for x in rows if x.get("stage") == "unl_cfg"]
        if not cfg or cfg[0]["unl_base"] != base:
            return False, "cfg/base wrong"
        return (out_dir / "final.json").exists(), "ok"
    except Exception as ex:
        return False, f"{type(ex).__name__}: {ex}"


def main() -> int:
    t0 = time.time()
    r = int(os.environ.get("PHASE7P4_SHARD", "0"))
    print(f"Phase 7 P4 launcher rep {r} - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_g7()
    doc = PREREG.read_text(encoding="utf-8")
    m = re.search(r'HARNESS_SHA256\s*=\s*"([0-9a-f]{64})"', doc)
    if not m:
        raise GuardViolation("prereg7p4 missing HARNESS_SHA256")
    frozen_sha = m.group(1)
    guard_g1(frozen_sha)
    p4.reproduce_draw()  # G3 + G6
    print("G1/G3/G6/G7 guards passed", flush=True)
    ab = p4.grab(doc, "P4_ACQ_BASES")
    ub = p4.grab(doc, "P4_UNL_BASES")

    spec = importlib.util.spec_from_file_location("phase7p4_harness_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7p4_harness_frozen"] = mod
    spec.loader.exec_module(mod)

    out_root = ROOT / "results/phase7p4"
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "Phase 7 P4 selective removal", "rep": r,
                "harness_sha256": frozen_sha, "prereg": "docs/PHASE_7P4_PREREG.md",
                "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           capture_output=True, text=True).stdout.strip(),
                "stages": [], "created": datetime.now(timezone.utc).isoformat()}
    mpath = out_root / f"launcher_manifest_r{r}.json"
    mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = out_root / f"rep_r{r}"
    for stage, base, complete in (("acq", ab[r], acq_complete), ("unlearn", ub[r], unl_complete)):
        if (out_dir / (f"{stage[:3]}.jsonl")).exists() or (out_dir / "final.json").exists() and stage == "unlearn":
            ok, why = complete(out_dir, base)
            if ok:
                print(f"r{r} {stage}: pre-existing COMPLETE - skip", flush=True)
                continue
            q = out_root / "quarantine" / f"p4_r{r}_{stage}_{ts}"
            q.mkdir(parents=True, exist_ok=True)
            # quarantine only this stage's artifacts
            for f in out_dir.glob(f"{stage[:3]}*"):
                f.rename(q / f.name)
            if stage == "unlearn" and (out_dir / "final.json").exists():
                (out_dir / "final.json").rename(q / "final.json")
            print(f"r{r} {stage}: INCOMPLETE ({why}) - quarantined", flush=True)
        if any(out_dir.is_relative_to(f) for f in FORBIDDEN):
            raise GuardViolation(f"G5 OUT {out_dir} forbidden")
        out_dir.mkdir(parents=True, exist_ok=True)
        before = dict(vars(mod))
        mod.OUT = out_dir
        if stage == "acq":
            mod.ACQ_BASE = base
        else:
            mod.UNL_BASE = base
        guard_g2(before, dict(vars(mod)))
        os.environ["PHASE7P4_STAGE"] = stage
        print(f"=== r{r} stage={stage} base={base} ===", flush=True)
        t1 = time.time()
        mod.main()
        guard_g1(frozen_sha)
        ok, why = complete(out_dir, base)
        if not ok:
            raise RuntimeError(f"r{r} {stage}: incomplete after run: {why}")
        manifest["stages"].append({"stage": stage, "base": base, "wall_s": round(time.time() - t1, 1)})
        mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        print(f"r{r} {stage} complete in {(time.time() - t1) / 60:.1f} min", flush=True)
    print(f"rep {r} DONE ({(time.time() - t0) / 60:.1f} min) - verdict via "
          f"uv run python scripts/phase7p4_analysis.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
