"""Task B R2 reversal report: two-state classification + trials-to-criterion.

Per docs/TASK_B_DESIGN.md (registered criteria + corrections):
- Unlearning = OLD response gone WITHOUT the competing drive:
    GNG521 (feed->withhold): cue-ALONE < theta  (old feed response)
    GNG380 (withhold->feed): cue+COSUGAR >= theta (old suppression gone)
- Relearning = new direction achieved:
    GNG521: cosugar < theta;  GNG380: cue-alone >= theta
- Two-state gate (final probes, pt=6 after trial 25):
    GNG521: REVERSED = alone<th AND cosugar<th | MASKED = alone>=th AND cosugar<th
            NOT REVERSED = alone>=th AND cosugar>=th | ERASED/PARTIAL = alone<th AND cosugar>=th
    GNG380: REVERSED = cosugar>=th AND alone>=th | MASKED = cosugar<th AND alone>=th
            NOT REVERSED = cosugar<th AND alone<th | ERASED/PARTIAL = cosugar>=th AND alone<th
- Trials-to-criterion: earliest probe point where BOTH reps satisfy the
  criterion metric; computed separately for unlearning and relearning.
"""

import json
from pathlib import Path

R2 = Path("results/phase2/taskB_r2")
THETA = 41.5
PROBE_TRIALS = (0, 1, 2, 4, 9, 14, 24)  # probe points after train trial t (pt 0-6)


def load(cue_tag, k, mode):
    pp = R2 / f"{mode}_{cue_tag}_blk{k}.jsonl"
    if not pp.exists():
        return {}
    out = {}
    for l in pp.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r["ptype"] in ("alone", "cosugar"):
            out.setdefault((r["cue"], r["trial"], r["ptype"]), []).append(r["readout_hz"])
    return out


def firsts(vals_by_trial, side):
    """Earliest train-trial where BOTH reps are on `side` of theta."""
    for t in PROBE_TRIALS:
        vs = vals_by_trial.get(t)
        if not vs or len(vs) < 2:
            continue
        if side == "ge" and all(v >= THETA for v in vs):
            return t + 1
        if side == "lt" and all(v < THETA for v in vs):
            return t + 1
    return None


def classify(alone_final, cosugar_final, cue):
    a, c = alone_final, cosugar_final
    if cue == "GNG521":
        if a < THETA and c < THETA:
            return "REVERSED"
        if a >= THETA and c < THETA:
            return "TWO-ASSOCIATION (masked)"
        if a >= THETA and c >= THETA:
            return "NOT REVERSED"
        return "ERASED/PARTIAL"
    else:
        if c >= THETA and a >= THETA:
            return "REVERSED"
        if c < THETA and a >= THETA:
            return "TWO-ASSOCIATION (masked)"
        if c < THETA and a < THETA:
            return "NOT REVERSED"
        return "ERASED/PARTIAL"


def main():
    print("== R2 REVERSAL VERDICT (L1, n=6 blocks each) ==\n")
    summary = {}
    for tag, cue in (("gng521_rev", "GNG521"), ("gng380_rev", "GNG380")):
        classes, unl_ttt, rel_ttt, finals = [], [], [], []
        for k in range(6):
            d = load(tag, k, "l1")
            if not d:
                print(f"  {tag} blk{k}: MISSING")
                continue
            alone = {t: d.get((cue, t, "alone"), []) for t in PROBE_TRIALS}
            cosu = {t: d.get((cue, t, "cosugar"), []) for t in PROBE_TRIALS}
            af = alone[24][:2]
            cf = cosu[24][:2]
            cls = classify(af[0] if af else None, cf[0] if cf else None, cue)
            # trials-to-criterion: unlearning vs relearning sides per cue
            if cue == "GNG521":
                unl = firsts(alone, "lt")   # old feed gone (alone < theta)
                rel = firsts(cosu, "lt")    # new withhold (cosugar < theta)
            else:
                unl = firsts(cosu, "ge")    # old suppression gone (cosugar >= theta)
                rel = firsts(alone, "ge")   # new feed (alone >= theta)
            classes.append(cls)
            unl_ttt.append(unl)
            rel_ttt.append(rel)
            finals.append((af, cf))
            print(f"  {tag} blk{k}: alone@25={af} cosugar@25={cf} -> {cls} | "
                  f"unlearn-ttt={unl} relearn-ttt={rel}")
        summary[tag] = {"classes": classes, "unl": unl_ttt, "rel": rel_ttt, "finals": finals}

    print("\n== class counts ==")
    for tag, s in summary.items():
        from collections import Counter
        print(f"  {tag}: {dict(Counter(s['classes']))}")

    print("\n== L0-R control (same retained start, no plasticity) ==")
    for tag, cue in (("gng521_rev", "GNG521"), ("gng380_rev", "GNG380")):
        for k in range(6):
            d = load(tag, k, "l0")
            if not d:
                continue
            alone = [d.get((cue, 24, "alone"), [])]
            cosu = [d.get((cue, 24, "cosugar"), [])]
            print(f"  {tag} l0 blk{k}: alone@25={alone[0][:2]} cosugar@25={cosu[0][:2]}")

    fires = 0
    for f in R2.glob("*.jsonl"):
        for l in f.open(encoding="utf-8"):
            if json.loads(l).get("guard_fired"):
                fires += 1
    print(f"\nguard fires: {fires}")

    (R2 / "r2_verdict_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("wrote r2_verdict_summary.json")


if __name__ == "__main__":
    main()
