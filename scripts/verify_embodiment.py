"""Verify the embodiment MVP: open-loop equivalence + sensorimotor contingency demo.

Writes results/phase7_embodiment/verify_embodiment.json (untracked raw artifact)
and prints the summary. No learning is run here - closed-loop LEARNING is a
future preregistered experiment, not an assumption of this scaffold.
"""
from __future__ import annotations

import json
from pathlib import Path

from fly.embodiment import BodyState, SensorimotorLoop
from fly.embodiment.body_graph import CONTACT_THRESHOLD, MN9_FIRE_HZ

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "phase7_embodiment"


def main() -> int:
    loop = SensorimotorLoop()
    report = {"checks": {}, "episodes": {}}

    # A. contingency: sugar present, proboscis retracted vs extended
    r_re = loop.step(BodyState(cue_on=True, sugar_present=True, proboscis_extension=0.0), seed=777)
    r_ex = loop.step(BodyState(cue_on=True, sugar_present=True, proboscis_extension=1.0), seed=777)
    report["checks"]["contingency"] = {
        "retracted": {"sugar_rate_Hz": r_re["sugar_rate_Hz"], "mn9_hz": r_re["mn9_hz"]},
        "extended": {"sugar_rate_Hz": r_ex["sugar_rate_Hz"], "mn9_hz": r_ex["mn9_hz"],
                     "detected": r_ex["sugar_detected"]},
        "pass": r_re["sugar_rate_Hz"] == 0.0 and r_re["mn9_hz"] < r_ex["mn9_hz"]
                and r_ex["mn9_hz"] >= MN9_FIRE_HZ and r_ex["sugar_detected"],
    }

    # B. closed-loop episode, no experimenter help: cue+sugar, proboscis starts retracted
    ep1 = loop.run_episode(BodyState(cue_on=True, sugar_present=True, proboscis_extension=0.0),
                           6, episode_seed=2026)
    report["episodes"]["no_help"] = ep1
    report["checks"]["action_required"] = {
        "pass": all(not r["sugar_detected"] for r in ep1)
                 and all(r["proboscis_extension"] < CONTACT_THRESHOLD for r in ep1),
        "note": "with the body in the loop, sugar is never transduced unless the "
                "proboscis extends first - the open-loop 'free lunch' is gone",
    }

    # C. experimenter-extends episode: detection and MN9 firing follow
    ep2 = SensorimotorLoop().run_episode(
        BodyState(cue_on=True, sugar_present=True, proboscis_extension=1.0), 3, episode_seed=2026)
    report["episodes"]["experimenter_extended"] = ep2
    report["checks"]["innate_pathway_through_loop"] = {
        "pass": all(r["sugar_detected"] and r["mn9_hz"] >= MN9_FIRE_HZ for r in ep2),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verify_embodiment.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for k, v in report["checks"].items():
        print(f"{k}: {'PASS' if v['pass'] else 'FAIL'}")
    print("no_help trajectory:", [(r["mn9_hz"], r["proboscis_extension"], r["sugar_detected"]) for r in ep1])
    print("extended trajectory:", [(r["mn9_hz"], r["proboscis_extension"], r["sugar_detected"]) for r in ep2])
    return 0 if all(v["pass"] for v in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
