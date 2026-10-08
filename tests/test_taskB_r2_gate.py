"""Tests: Task B R2 retention gate (the two gate bugs, pinned).

Bug 1 (caught 2026-10-03): the gate read the probe set WITHOUT a cue
filter - both cues' probes exist at every point (cross-direction
leakage by design), so mixing the untrained cue's values (0 by
construction) into the criterion made every block read FAIL ->
all-R2-N/A.

Bug 2 (caught 2026-10-08 pre-launch): the gate read trial==10, an
ACQUISITION-phase probe in R1 v2's as-run schedule (acq = trials
0-14; retention = 15-29; retention-phase probes at 15/20/25; t=30
never fires). The registered criterion is the FINAL retention-phase
point that actually fired: t=25.

These tests pin the corrected gate semantics against synthetic R1
record sets.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase2_taskB_r2_reversal import R2_COND, r1_retained  # noqa: E402


def _write_r1(tmp_path, cond, k, records):
    d = tmp_path / "taskB_r1"
    d.mkdir(exist_ok=True)
    (d / f"l1_{cond}_blk{k}.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def _records(cue, ptype, ok_vals):
    """Probe records for `cue`/`ptype` at retention points 15/20/25
    (2 reps each), plus OTHER-cue contamination at the same points
    (the Bug-1 poison: 0s)."""
    other = "GNG380" if cue == "GNG521" else "GNG521"
    recs = []
    for i, t in enumerate((15, 20, 25)):
        for rep, v in enumerate(ok_vals[i]):
            recs.append({"cue": cue, "trial": t, "ptype": ptype, "rep": rep,
                         "readout_hz": v})
            # contamination: the other cue, same point, 0 Hz
            recs.append({"cue": other, "trial": t, "ptype": ptype, "rep": rep,
                          "readout_hz": 0})
    return recs


def test_gate_filters_by_cue(tmp_path, monkeypatch):
    """With contamination present, a properly retained feed block must
    still pass (Bug 1: the unfiltered gate failed it)."""
    import phase2_taskB_r2_reversal as r2mod
    monkeypatch.setattr(r2mod, "R1DIR", tmp_path / "taskB_r1")
    cdef = R2_COND["gng521_rev"]  # r1_cond=gng521_feed, cue=GNG521, metric=alone
    recs = _records("GNG521", "alone", [[80, 81], [79, 82], [81, 86]])
    _write_r1(tmp_path, "gng521_feed", 0, recs)
    ok, vals = r2mod.r1_retained(cdef, 0)
    assert ok is True
    assert vals == [81, 86]  # final point (t=25), own-cue only


def test_gate_reads_final_retention_point(tmp_path, monkeypatch):
    """A block retained at 15/20 but DECAYED at t=25 must FAIL (Bug 2:
    the t=10/t=15 gate passed it). Also verifies t=25 is the point
    actually read."""
    import phase2_taskB_r2_reversal as r2mod
    monkeypatch.setattr(r2mod, "R1DIR", tmp_path / "taskB_r1")
    cdef = R2_COND["gng521_rev"]
    # t=15 fine, t=20 fine, t=25 BELOW theta -> decayed by the final point
    recs = _records("GNG521", "alone", [[80, 81], [79, 82], [12, 8]])
    _write_r1(tmp_path, "gng521_feed", 0, recs)
    ok, vals = r2mod.r1_retained(cdef, 0)
    assert ok is False
    assert vals == [12, 8]


def test_gate_withhold_side(tmp_path, monkeypatch):
    """GNG380-withhold reversal gate: cosugar metric, PASS side is
    < theta at t=25."""
    import phase2_taskB_r2_reversal as r2mod
    monkeypatch.setattr(r2mod, "R1DIR", tmp_path / "taskB_r1")
    cdef = R2_COND["gng380_rev"]  # r1_cond=gng380_withhold, cue=GNG380, metric=cosugar
    recs = _records("GNG380", "cosugar", [[3, 2], [1, 4], [2, 1]])
    _write_r1(tmp_path, "gng380_withhold", 0, recs)
    ok, vals = r2mod.r1_retained(cdef, 0)
    assert ok is True
    assert vals == [2, 1]


def test_gate_missing_file(tmp_path, monkeypatch):
    import phase2_taskB_r2_reversal as r2mod
    monkeypatch.setattr(r2mod, "R1DIR", tmp_path / "taskB_r1")
    (tmp_path / "taskB_r1").mkdir(exist_ok=True)
    ok, vals = r2mod.r1_retained(R2_COND["gng521_rev"], 0)
    assert ok is False and vals == []
