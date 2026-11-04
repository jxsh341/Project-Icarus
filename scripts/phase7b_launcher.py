"""Phase 7b P1 launcher - held-out circuits, stages acquire -> l6b -> l4b.

Per docs/PHASE_7B_PREREG.md. The harness FILE is never modified; OUT/R1CK/CUE/
TRAIN_SEED_BASE/PROBE_SEED_BASE/REPS injected in memory only, harness sha256
verified before and after EVERY invocation.

Guards (raise, never warn):
  G1 harness sha256 == frozen, before/after every invocation
  G2 only injection keys differ after injection
  G3 all P7B seed spaces (+ screen seeds) collision-free and disjoint from
     dev+confirm+P6+P7 spaces
  G4 output roots hold only known artifacts (complete reps skipped,
     incomplete quarantined, never deleted)
  G5 injected OUT never a dev/confirm/phase2/4/6/7 output dir
  G6 prereg anchors reproduce (Random(20261105) screen + Random(20261106) runs)
  G7 cwd is repo root

Usage: uv run python scripts/phase7b_launcher.py
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
import phase7b_analysis as p1  # noqa: E402

HARNESS = ROOT / "scripts" / "phase7b_harness.py"
PREREG = ROOT / "docs/PHASE_7B_PREREG.md"
INJECT_KEYS = {"TRAIN_SEED_BASE", "PROBE_SEED_BASE", "REPS", "OUT", "R1CK", "CUE"}
FORBIDDEN = [an.DEV_OUT, an.CONF_ROOT, ROOT / "results/phase2", ROOT / "results/phase4",
             ROOT / "results/phase6", ROOT / "results/phase7"]
PAIRS = p1.PAIRS
N_REPS = 2


class GuardViolation(Exception):
    pass


def harness_sha():
    import hashlib
    return hashlib.sha256(HARNESS.read_bytes()).hexdigest()


def guard_g1(frozen):
    actual = harness_sha()
    if actual != frozen:
        raise GuardViolation(f"G1 harness sha {actual[:12]} != frozen {frozen[:12]}")


def _same(a, b):
    try:
        return bool(a == b) if not hasattr(a, "shape") else bool((a == b).all())
    except Exception:
        return a is b


def guard_g2(before, after):
    changed = {k for k in set(before) | set(after)
               if k not in before or k not in after or not _same(before.get(k), after.get(k))}
    if changed - INJECT_KEYS:
        raise GuardViolation(f"G2 non-injection keys changed: {sorted(changed - INJECT_KEYS)}")


def guard_g3():
    p1.reproduce_draw()  # raises on any collision/overlap; also checks screen seeds


def guard_g4(root: Path, known: set[str]):
    if not root.exists():
        return
    unknown = [q.name for q in root.iterdir() if q.name not in known]
    if unknown:
        raise GuardViolation(f"G4 unknown artifacts in {root}: {unknown}")


def guard_g7():
    if Path.cwd().resolve() != ROOT:
        raise GuardViolation(f"G7 cwd {Path.cwd()} != {ROOT}")


def stage_complete(out_dir: Path, stage: str, train_base: int, n_reps=1) -> tuple[bool, str]:
    try:
        hist = an.read_jsonl(out_dir / "ckpt_r0" / "history.jsonl", "history")
        n_exp = 20 if stage == "acquire" else (25 if stage == "l6b" else 50)
        if len(hist) != n_exp:
            return False, f"history {len(hist)} != {n_exp}"
        if stage == "acquire":
            exp = sorted(p1.acq_train(train_base))
        elif stage == "l6b":
            exp = sorted(p1.unl_train(train_base))
        else:
            exp = sorted(p1.l4b_train(train_base))
        if sorted(int(x["seed"]) for x in hist) != exp:
            return False, "history seeds != expected"
        jname = "acq.jsonl" if stage == "acquire" else f"{stage}.jsonl"
        rows = an.read_jsonl(out_dir / jname, "jsonl")
        n_probe_exp = 32 if stage == "acquire" else 20
        if len([x for x in rows if "ptype" in x]) != n_probe_exp:
            return False, "probe row count wrong"
        return True, "complete"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    t0 = time.time()
    print(f"Phase 7b P1 launcher - {datetime.now(timezone.utc).isoformat()}", flush=True)
    guard_g7()
    doc = PREREG.read_text(encoding="utf-8")
    frozen_sha = re_search_sha(doc)
    guard_g1(frozen_sha)
    guard_g3()
    print("G1/G3/G6/G7 guards passed", flush=True)

    acq_t = p1.grab(doc, "P7B_ACQ_TRAIN"); acq_p = p1.grab(doc, "P7B_ACQ_PROBE")
    l6t = p1.grab(doc, "P7B_L6B_TRAIN"); l6p = p1.grab(doc, "P7B_L6B_PROBE")
    l4t = p1.grab(doc, "P7B_L4B_TRAIN"); l4p = p1.grab(doc, "P7B_L4B_PROBE")

    spec = importlib.util.spec_from_file_location("phase7b_harness_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7b_harness_frozen"] = mod
    spec.loader.exec_module(mod)

    manifest = {"experiment": "Phase 7b P1 held-out circuits",
                "harness_sha256": frozen_sha, "prereg": "docs/PHASE_7B_PREREG.md",
                "prereg_sha256": an.sha256_file(PREREG),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           capture_output=True, text=True).stdout.strip(),
                "pairs": sorted(PAIRS), "reps": [],
                "created": datetime.now(timezone.utc).isoformat()}
    (ROOT / "results/phase7b").mkdir(parents=True, exist_ok=True)
    mpath = ROOT / "results/phase7b/launcher_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for pi, pair in enumerate(sorted(PAIRS)):
        cue = PAIRS[pair]
        for r in range(N_REPS):
            k = pi * N_REPS + r
            acq_dir = ROOT / "results/phase7b/acq" / pair / f"rep_r{r}"
            l6b_dir = ROOT / "results/phase7b/l6b" / pair / f"rep_r{r}"
            l4b_dir = ROOT / "results/phase7b/l4b" / pair / f"rep_r{r}"
            guard_g4(ROOT / "results/phase7b/acq" / pair, {"launcher_manifest.json"} | {f"rep_r{i}" for i in range(N_REPS)})
            for stage, out_dir, tbase, pbase, r1ck in (
                ("acquire", acq_dir, acq_t[k], acq_p[k], None),
                ("l6b", l6b_dir, l6t[k], l6p[k], acq_dir / "ckpt_r0"),
                ("l4b", l4b_dir, l4t[k], l4p[k], acq_dir / "ckpt_r0"),
            ):
                if out_dir.exists():
                    ok, why = stage_complete(out_dir, stage, tbase)
                    if ok:
                        print(f"{pair} r{r} {stage}: pre-existing COMPLETE - skip", flush=True)
                        continue
                    q = ROOT / "results/phase7b/quarantine" / f"p1_{pair}_r{r}_{stage}_{ts}"
                    q.mkdir(parents=True, exist_ok=True)
                    out_dir.rename(q / out_dir.name)
                    print(f"{pair} r{r} {stage}: INCOMPLETE ({why}) - quarantined", flush=True)
                if any(out_dir.is_relative_to(f) for f in FORBIDDEN):
                    raise GuardViolation(f"G5 OUT {out_dir} is forbidden")
                out_dir.mkdir(parents=True, exist_ok=True)
                before = dict(vars(mod))
                mod.TRAIN_SEED_BASE = tbase
                mod.PROBE_SEED_BASE = pbase
                mod.REPS = 1
                mod.OUT = out_dir
                mod.CUE = list(cue)
                if r1ck is not None:
                    mod.R1CK = r1ck
                guard_g2(before, dict(vars(mod)))
                os.environ["PHASE7B_STAGE"] = stage
                os.environ["PHASE7B_PAIR"] = pair
                print(f"=== {pair} r{r} stage={stage} train_base={tbase} probe_base={pbase} ===", flush=True)
                t1 = time.time()
                mod.main()
                guard_g1(frozen_sha)
                ok, why = stage_complete(out_dir, stage, tbase)
                if not ok:
                    raise RuntimeError(f"{pair} r{r} {stage}: incomplete after run: {why}")
                manifest["reps"].append({"pair": pair, "rep": r, "stage": stage,
                                         "train_base": tbase, "probe_base": pbase,
                                         "wall_s": round(time.time() - t1, 1)})
                mpath.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
                print(f"{pair} r{r} {stage} complete in {(time.time() - t1) / 60:.1f} min", flush=True)
    print(f"ALL DONE - verdict via uv run python scripts/phase7b_analysis.py "
          f"(total {((time.time() - t0) / 60):.1f} min)", flush=True)
    return 0


def re_search_sha(doc: str) -> str:
    import re as _re
    m = _re.search(r'HARNESS_SHA256\s*=\s*"([0-9a-f]{64})"', doc)
    if not m:
        raise GuardViolation("prereg7b missing HARNESS_SHA256")
    return m.group(1)


if __name__ == "__main__":
    raise SystemExit(main())
