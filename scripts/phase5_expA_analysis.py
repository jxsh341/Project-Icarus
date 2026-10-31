"""Phase 5 Experiment A - confirmatory analysis (pre-registered criteria).

Verdict authority for the confirmatory replication of the WP-L4b
unlearning result. Implements docs/PHASE_5_CONFIRMATORY_PREREG.md
exactly. Committed BEFORE any confirmatory run (preregistered
order). Fails loudly on incomplete or malformed artifacts and NEVER
emits a verdict from partial data.

Frozen criteria (verbatim intent from the preregistration):
  c1  cue-alone reaches literal 0 spikes by cycle <= 15, per rep
      (BOTH probe sims at the reaching cycle must read 0)
  c2  zero persists through cycle 25 (all probe sims at every
      probe cycle >= the reaching cycle)
  c3  every cosugar sim at every probe point within [78, 88]
  c4  guard silent on every trial of every rep (recorded
      guard_fired fields) AND no trial exceeds the guard's spike
      threshold (re-derived from per-trial total_spikes)
  c5  all 25 re-derived carrier edges and all 9 untouched-partner
      carrier edges at the V_CLIP floor (0.0) in the final matrix;
      no sign flips anywhere; no structural zero gains weight

Per-rep branches: PASS / NEGATIVE-A / NEGATIVE-B (a rep may hit
both A and B conditions - recorded as "NEGATIVE-A+B").
Aggregate: PASS only if all reps PASS; one identical non-PASS
branch across all reps is that branch; ANY split is MIXED (its own
verdict, non-aggregable - the dev result does not promote).

Seed mechanism (per-rep invocation design): rep r runs the frozen
harness once with REPS=1 and injected bases
TRAIN_SEED_BASE=CONF_TRAIN_SEEDS[r], PROBE_SEED_BASE=CONF_PROBE_
SEEDS[r] (first 8 of the frozen 15 in doc order; 7 reserved-
unused). Train seeds are artifact-verified from history.jsonl;
probe seeds are NOT recorded per-sim by the frozen harness and are
verified by derivation from the manifest bases + the sha-pinned
harness source (documented limit). The guard's spontaneous-rate
and E/I-drift criteria are in-run state not exported by the frozen
harness; the recorded guard_fired fields plus the re-derived spike
threshold cover what the artifacts carry.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fly.training import weight_matrix_hash  # noqa: E402

PREREG = ROOT / "docs" / "PHASE_5_CONFIRMATORY_PREREG.md"
HARNESS = ROOT / "scripts" / "phase4_wp_l4b_extinction.py"
FROZEN_HARNESS_SHA = "7fa1746b614316680270bb6e381e09617a7ec021ff62ea832a11a1a9b0ebfab0"
DEV_OUT = ROOT / "results" / "phase4" / "wp_l4b"
DEV_JSONL = DEV_OUT / "l4b_extinction.jsonl"
CONF_ROOT = ROOT / "results" / "phase4" / "wp_l4b_confirm"
VERDICT_PATH = CONF_ROOT / "CONFIRMATORY_VERDICT.json"

COSUGAR_BAND = (78, 88)
GUARD_MAX_SPIKES = 150_000
N_REPS = 8
PROBE_AT = (5, 10, 15, 20, 25)
N_CYCLES = 25
ZERO_BY_CYCLE = 15
CYCLE_ROWS_PER_REP = 25
PROBE_ROWS_PER_REP = 20
HIST_ROWS_PER_REP = 50
DRAW_SEED = 20261009


class IncompleteArtifacts(Exception):
    """Artifacts missing/malformed - refuse to emit any verdict."""


class ScopeError(Exception):
    """Re-derived scope contradicts the registration (fail loudly)."""


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_prereg_seeds(text: str | None = None) -> tuple[list[int], list[int]]:
    """Extract the frozen seed anchors from the preregistration doc."""
    text = PREREG.read_text(encoding="utf-8") if text is None else text

    def _grab(name: str) -> list[int]:
        m = re.search(rf"{name}\s*=\s*\[([^\]]*)\]", text)
        if not m:
            raise IncompleteArtifacts(f"prereg missing {name} block")
        return list(ast.literal_eval("[" + m.group(1) + "]"))

    train, probe = _grab("CONF_TRAIN_SEEDS"), _grab("CONF_PROBE_SEEDS")
    if len(train) != 8 or len(probe) != 15:
        raise ScopeError(
            f"prereg seeds: expected 8 train / 15 probe, got {len(train)}/{len(probe)}")
    return train, probe


def reproduce_draw(train: list[int], probe: list[int]) -> None:
    """The prereg documents Random(20261009) as the derivation; re-run it
    and require equality (stated-procedure-vs-executed-procedure).

    Order semantics, per Amendment A1: the probe list was sorted at draw
    time (sorted(rng.sample(...))) so it must match exactly; the train
    list is recorded in the doc in SORTED order while the generator emits
    it unsorted - so train equality is enforced as a SET (the freeze is
    the value set; per-rep assignment follows the doc's listed order)."""
    rng = random.Random(DRAW_SEED)
    t = [rng.randrange(860001, 860999) for _ in range(8)]
    p = sorted(rng.sample(range(970001, 970999), 15))
    if set(t) != set(train):
        raise ScopeError(
            "prereg train anchors do not reproduce from Random(20261009) - "
            "doc corrupted or derivation changed")
    if sorted(t) != sorted(train):
        raise ScopeError("train anchor multiset mismatch")
    if p != probe:
        raise ScopeError(
            "prereg probe anchors do not reproduce from Random(20261009) - "
            "doc corrupted or derivation changed")


def expected_train_seeds(base: int) -> set[int]:
    """Harness scheme: base + cyc*2 (sugar) / base + cyc*2 + 1 (bitter)."""
    return {base + c * 2 + ph for c in range(1, N_CYCLES + 1) for ph in (0, 1)}


def expected_probe_seeds(base: int) -> set[int]:
    """Harness scheme: base + cyc*100 + r2*10 + off (off 0=alone, 5000=cosugar)."""
    return {base + c * 100 + r2 * 10 + off
            for c in PROBE_AT for r2 in (0, 1) for off in (0, 5000)}


def sanity_seed(probe_base: int) -> int:
    return probe_base + 999  # harness launch-sanity sim


def dev_seed_space() -> set[int]:
    """Every seed the dev L4b run could have drawn (bases 160000/162000)."""
    s: set[int] = set()
    for rep in range(3):
        for c in range(1, N_CYCLES + 1):
            s |= {160_000 + rep * 1000 + c * 2, 160_000 + rep * 1000 + c * 2 + 1}
        for c in PROBE_AT:
            for r2 in (0, 1):
                for off in (0, 5000):
                    s.add(162_000 + rep * 10000 + c * 100 + r2 * 10 + off)
    s.add(162_000 + 999)
    return s


def read_jsonl(path: Path, what: str) -> list[dict]:
    if not path.exists():
        raise IncompleteArtifacts(f"missing {what}: {path}")
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise IncompleteArtifacts(f"malformed JSON in {what} line {n}: {e}")
    return rows


def load_final_matrix(ckpt_dir: Path, label: str) -> tuple[sparse.csr_matrix, dict]:
    """Load the latest weight snapshot; hash-verify against run_state."""
    state_p = ckpt_dir / "run_state.json"
    if not state_p.exists():
        raise IncompleteArtifacts(f"missing run_state.json for {label}")
    state = json.loads(state_p.read_text(encoding="utf-8"))
    wfiles = sorted(ckpt_dir.glob("weights_trial_*.npz"))
    if not wfiles:
        raise IncompleteArtifacts(f"no weight snapshots for {label}")
    mat = sparse.load_npz(wfiles[-1]).tocsr()
    actual = weight_matrix_hash(mat)
    if state.get("weight_hash") and actual != state["weight_hash"]:
        raise IncompleteArtifacts(
            f"{label}: weight hash mismatch ({wfiles[-1].name} "
            f"{actual} != run_state {state['weight_hash']})")
    return mat, state


def derive_carriers(
    pristine: sparse.csr_matrix, acquired: sparse.csr_matrix,
    cue_idx: set[int], untouched_idx: set[int],
) -> tuple[frozenset, frozenset]:
    """Carriers = edges that GREW during acquisition (acquired != pristine),
    must all be cue-incident; exactly 25, exactly 9 onto untouched partners."""
    d = (acquired - pristine).tocoo()
    changed = [(int(i), int(j)) for i, j, v in zip(d.row, d.col, d.data) if v != 0]
    if not changed:
        raise ScopeError("acquired-vs-pristine diff is EMPTY - no carriers derived")
    non_cue = [(i, j) for i, j in changed if i not in cue_idx]
    if non_cue:
        raise ScopeError(f"acquisition changed {len(non_cue)} non-cue-incident "
                         f"edges (scope surprise): {non_cue[:5]}")
    carriers = frozenset(changed)
    if len(carriers) != 25:
        raise ScopeError(f"carrier footprint is {len(carriers)}, registration says 25")
    unt = frozenset((i, j) for i, j in carriers if j in untouched_idx)
    if len(unt) != 9:
        raise ScopeError(f"untouched-partner carrier edges = {len(unt)}, registration says 9")
    return carriers, unt


def _probe_values(probe_rows: list[dict], cycle: int, ptype: str) -> list[int]:
    return [r["mn9_hz"] for r in probe_rows
            if r["cycle"] == cycle and r["ptype"] == ptype]


def evaluate_rep(
    r: int, rep_dir: Path, cfg: "AnalysisConfig",
    train_base: int, probe_base: int,
    carriers: frozenset, untouched_carriers: frozenset,
    acquired: sparse.csr_matrix,
) -> dict:
    if not rep_dir.exists():
        raise IncompleteArtifacts(f"rep {r}: missing run dir {rep_dir}")

    # --- training JSONL: cycle rows + probe rows, exact counts ---
    rows = read_jsonl(rep_dir / "l4b_extinction.jsonl", f"rep {r} results JSONL")
    cycle_rows = [x for x in rows if "ptype" not in x]
    probe_rows = [x for x in rows if "ptype" in x]
    if len(cycle_rows) != CYCLE_ROWS_PER_REP:
        raise IncompleteArtifacts(f"rep {r}: {len(cycle_rows)} cycle rows, expected 25")
    if len(probe_rows) != PROBE_ROWS_PER_REP:
        raise IncompleteArtifacts(f"rep {r}: {len(probe_rows)} probe rows, expected 20")
    if {x["cycle"] for x in cycle_rows} != set(range(1, N_CYCLES + 1)):
        raise IncompleteArtifacts(f"rep {r}: cycle rows do not cover cycles 1..25 exactly")
    want_probes = {(c, pt, r2) for c in PROBE_AT
                   for pt in ("alone", "cosugar") for r2 in (0, 1)}
    got_probes = {(x["cycle"], x["ptype"], x["rep2"]) for x in probe_rows}
    if got_probes != want_probes:
        raise IncompleteArtifacts(
            f"rep {r}: probe grid incomplete: missing={want_probes - got_probes} "
            f"extra={got_probes - want_probes}")
    if any(x.get("rep") != 0 for x in rows):
        raise IncompleteArtifacts(f"rep {r}: JSONL rep field != 0 (per-rep invocation "
                                  "expects rep=0 within each rep dir)")

    # --- history: artifact-backed train-seed verification ---
    hist = read_jsonl(rep_dir / "ckpt_r0" / "history.jsonl", f"rep {r} history")
    if len(hist) != HIST_ROWS_PER_REP:
        raise IncompleteArtifacts(f"rep {r}: {len(hist)} history rows, expected 50")
    actual_seeds = sorted(int(x["seed"]) for x in hist)
    want_seeds = sorted(expected_train_seeds(train_base))
    if actual_seeds != want_seeds:
        bad = set(actual_seeds) ^ set(want_seeds)
        raise IncompleteArtifacts(
            f"rep {r}: ACTUAL train seeds diverge from prereg-derived set "
            f"({len(bad)} differ, e.g. {sorted(bad)[:6]})")
    trials = sorted(int(x["trial"]) for x in hist)
    want_trials = sorted(c * 2 + ph for c in range(1, N_CYCLES + 1) for ph in (0, 1))
    if trials != want_trials:
        raise IncompleteArtifacts(
            f"rep {r}: trial numbering does not match the harness scheme "
            f"(2..{N_CYCLES * 2 + 1})")

    # --- final matrix integrity ---
    final, state = load_final_matrix(rep_dir / "ckpt_r0", f"rep {r}")
    if state.get("n_history") != HIST_ROWS_PER_REP:
        raise IncompleteArtifacts(f"rep {r}: run_state n_history={state.get('n_history')}")

    # c1/c2: cue-alone literal zero
    cycles_to_zero = None
    for c in PROBE_AT:
        vals = _probe_values(probe_rows, c, "alone")
        if vals and all(v == 0 for v in vals):
            cycles_to_zero = c
            break
    c1 = cycles_to_zero is not None and cycles_to_zero <= ZERO_BY_CYCLE
    persist_cycles = [c for c in PROBE_AT if cycles_to_zero is not None and c >= cycles_to_zero]
    c2 = cycles_to_zero is not None and all(
        all(v == 0 for v in _probe_values(probe_rows, c, "alone")) for c in persist_cycles)

    # c3: cosugar band
    cos_all = [v for c in PROBE_AT for v in _probe_values(probe_rows, c, "cosugar")]
    cos_min, cos_max = min(cos_all), max(cos_all)
    c3 = cos_min >= COSUGAR_BAND[0] and cos_max <= COSUGAR_BAND[1]
    below = [v for v in cos_all if v < COSUGAR_BAND[0]]
    above = [v for v in cos_all if v > COSUGAR_BAND[1]]

    # c4: guard silence (recorded fields) + spike-threshold re-derivation
    guard_fires = sum(1 for x in cycle_rows if x.get("guard_fired"))
    spike_viol = sum(1 for x in hist if int(x.get("total_spikes", 0)) >= GUARD_MAX_SPIKES)
    c4 = guard_fires == 0 and spike_viol == 0

    # c5 + NEGATIVE-B weight forensics: full-matrix scan of final vs acquired
    fcoo = final.tocoo()
    flips, struct_gains, changed = [], [], []
    for i, j, v in zip(fcoo.row, fcoo.col, fcoo.data):
        i, j = int(i), int(j)
        a = acquired[i, j]
        if v != 0:
            if a == 0:
                struct_gains.append((i, j, float(v)))
                continue
            if (a > 0 and v < 0) or (a < 0 and v > 0):
                flips.append((i, j, float(a), float(v)))
            if v != a:
                changed.append((i, j, float(v - a)))   # DELTA, not final value
    carriers_at_floor = sum(1 for (i, j) in carriers if final[i, j] == 0.0)
    untouched_at_floor = sum(1 for (i, j) in untouched_carriers if final[i, j] == 0.0)
    c5 = carriers_at_floor == 25 and untouched_at_floor == 9
    collateral = [(i, j, v) for (i, j, v) in changed if (i, j) not in carriers]

    a_fail = (not c1) or (not c2) or (not c5)
    b_fail = (not c3) or (not c4) or bool(flips) or bool(struct_gains)
    if not a_fail and not b_fail:
        branch = "PASS"
    else:
        branch = "+".join([b for b, f in (("NEGATIVE-A", a_fail), ("NEGATIVE-B", b_fail)) if f])

    return dict(
        rep=r, run_dir=str(rep_dir), train_base=train_base, probe_base=probe_base,
        seeds_verified=True, run_id=state.get("run_id"),
        cycles_to_zero=cycles_to_zero, zero_by_15=c1,
        zero_persists_c15_c25=c2,
        cosugar_by_point={str(c): _probe_values(probe_rows, c, "cosugar") for c in PROBE_AT},
        cosugar_min=cos_min, cosugar_max=cos_max, cosugar_in_band=c3,
        cosugar_below_band=below, cosugar_above_band=above,
        guard_fires=guard_fires, spike_threshold_violations=spike_viol, guard_silent=c4,
        carriers_at_floor=carriers_at_floor, untouched_at_floor=untouched_at_floor,
        floors=c5, sign_flips=flips, structural_zero_gains=struct_gains,
        collateral_count=len(collateral),
        collateral_max_abs_delta=max((abs(v) for _, _, v in collateral), default=0.0),
        collateral=collateral, branch=branch,
    )


def aggregate_verdict(branches: list[str]) -> str:
    uniq = set(branches)
    if uniq == {"PASS"}:
        return "PASS"
    if len(uniq) == 1:
        return branches[0]
    return "MIXED"


@dataclass
class AnalysisConfig:
    conf_root: Path
    pristine_path: Path
    r1ck_dir: Path
    dev_jsonl: Path
    manifest_path: Path
    prereg_path: Path = PREREG
    harness_path: Path = HARNESS
    nid: dict = field(default_factory=dict)          # body id -> matrix index
    cue: tuple = ()                                   # body ids
    untouched: tuple = ()                             # body ids
    n_reps: int = N_REPS
    probe_at: tuple = PROBE_AT


def evaluate_run(cfg: AnalysisConfig) -> dict:
    # 0. the code being analyzed must be the frozen implementation
    hsha = sha256_file(cfg.harness_path)
    if hsha != FROZEN_HARNESS_SHA:
        raise ScopeError(f"harness sha {hsha[:12]} != frozen {FROZEN_HARNESS_SHA[:12]}")

    # 1. prereg: parse anchors, reproduce the documented draw
    train_anchors, probe_anchors = parse_prereg_seeds(cfg.prereg_path.read_text(encoding="utf-8"))
    reproduce_draw(train_anchors, probe_anchors)

    # 2. launcher manifest must agree with the prereg anchors (first 8 probe
    #    anchors in doc order are the consumed bases; 7 reserved-unused)
    man_p = cfg.manifest_path
    if not man_p.exists():
        raise IncompleteArtifacts(f"missing launcher manifest: {man_p}")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    reps_man = man.get("reps", [])
    if len(reps_man) != cfg.n_reps:
        raise IncompleteArtifacts(f"manifest has {len(reps_man)} reps, expected {cfg.n_reps}")
    if [x["train_base"] for x in reps_man] != train_anchors:
        raise IncompleteArtifacts("manifest train bases != prereg CONF_TRAIN_SEEDS")
    if [x["probe_base"] for x in reps_man] != probe_anchors[:cfg.n_reps]:
        raise IncompleteArtifacts("manifest probe bases != prereg CONF_PROBE_SEEDS[:8]")

    # 3. seed-space verification: derived sets, global distinctness, dev disjoint
    train_sets = [expected_train_seeds(x["train_base"]) for x in reps_man]
    probe_sets = [expected_probe_seeds(x["probe_base"]) for x in reps_man]
    sanity = {sanity_seed(x["probe_base"]) for x in reps_man}
    all_seeds = set().union(*train_sets, *probe_sets, sanity)
    if len(all_seeds) != sum(len(s) for s in train_sets) + sum(len(s) for s in probe_sets) + len(sanity):
        raise ScopeError("confirmatory seed space has COLLISIONS across reps")
    dev = dev_seed_space()
    if all_seeds & dev:
        raise ScopeError(f"{len(all_seeds & dev)} confirmatory seeds collide with dev space")

    # 4. matrices + carrier re-derivation (scope guard)
    pristine = sparse.load_npz(cfg.pristine_path).tocsr()
    acquired, r1_state = load_final_matrix(cfg.r1ck_dir, "R1 acquired state")
    cue_idx = {cfg.nid[c] for c in cfg.cue}
    unt_idx = {cfg.nid[c] for c in cfg.untouched}
    carriers, unt_carriers = derive_carriers(pristine, acquired, cue_idx, unt_idx)

    # 5. per-rep evaluation
    per_rep = [evaluate_rep(x["rep"], Path(x["out_dir"]), cfg,
                            x["train_base"], x["probe_base"],
                            carriers, unt_carriers, acquired)
               for x in reps_man]

    # 6. aggregate + descriptives
    branches = [x["branch"] for x in per_rep]
    overall = aggregate_verdict(branches)
    dist = Counter(x["cycles_to_zero"] for x in per_rep)

    dev_rows = read_jsonl(cfg.dev_jsonl, "dev l4b JSONL")

    def _conf_probe_values(pt: str, c: int) -> list[int]:
        out = []
        for x in per_rep:
            rows = read_jsonl(Path(x["run_dir"]) / "l4b_extinction.jsonl",
                              f"rep {x['rep']} JSONL (drift)")
            out += [r["mn9_hz"] for r in rows
                    if r.get("ptype") == pt and r["cycle"] == c]
        return out

    drift = {}
    for pt in ("alone", "cosugar"):
        for c in cfg.probe_at:
            dv = [r["mn9_hz"] for r in dev_rows
                  if r.get("ptype") == pt and r["cycle"] == c]
            cv = _conf_probe_values(pt, c)
            drift[f"{pt}_c{c}"] = {
                "dev_n": len(dv), "dev_mean": round(sum(dv) / len(dv), 1) if dv else None,
                "dev_range": [min(dv), max(dv)] if dv else None,
                "conf_n": len(cv), "conf_mean": round(sum(cv) / len(cv), 1) if cv else None,
                "conf_range": [min(cv), max(cv)] if cv else None,
            }

    return dict(
        experiment="Phase 5 Experiment A - confirmatory replication of WP-L4b unlearning",
        prereg=str(cfg.prereg_path), prereg_sha256=sha256_file(cfg.prereg_path),
        harness=str(cfg.harness_path), harness_sha256=hsha,
        n_reps=cfg.n_reps, reserved_unused_probe_anchors=probe_anchors[cfg.n_reps:],
        per_rep=per_rep,
        criteria_verdicts={
            "c1_zero_by_15": [x["zero_by_15"] for x in per_rep],
            "c2_persist_through_25": [x["zero_persists_c15_c25"] for x in per_rep],
            "c3_cosugar_band": [x["cosugar_in_band"] for x in per_rep],
            "c4_guard_silent": [x["guard_silent"] for x in per_rep],
            "c5_floors": [x["floors"] for x in per_rep],
        },
        trials_to_zero_distribution={str(k): v for k, v in sorted(dist.items(), key=lambda kv: (kv[0] is None, kv[0]))},
        branches=branches, overall=overall,
        dev_vs_confirm_drift=drift,
        acquired_state_hash=r1_state.get("weight_hash"),
        notes=[
            "probe seeds not recorded per-sim by the frozen harness; verified by "
            "derivation from manifest bases + sha-pinned harness source",
            "guard spontaneous-rate and E/I-drift criteria are in-run state not "
            "exported by the frozen harness; recorded guard_fired (bitter-phase) "
            "plus re-derived per-trial spike threshold cover the artifact record",
            "cosugar band check enforces BOTH bounds [78, 88] per the PASS text; "
            "NEGATIVE-B text names <78 as the paradigmatic violation",
        ],
    )


def _probe_values_missing(x, c):  # alone values live in the rep JSONL, not the summary
    return [0]


def build_real_config() -> AnalysisConfig:
    spec = importlib.util.spec_from_file_location("phase4_wp_l4b_extinction_frozen", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase4_wp_l4b_extinction_frozen"] = mod  # dataclass-safe exec
    spec.loader.exec_module(mod)
    nodes = np.load(mod.BASE / "connectivity_nodes.npy").tolist()
    return AnalysisConfig(
        conf_root=CONF_ROOT, pristine_path=mod.BASE / "connectivity_matrix_signed.npz",
        r1ck_dir=mod.R1CK, dev_jsonl=DEV_JSONL,
        manifest_path=CONF_ROOT / "launcher_manifest.json",
        nid={n: i for i, n in enumerate(nodes)},
        cue=tuple(mod.CUE), untouched=tuple(mod.UNTOUCHED),
    )


def main() -> int:
    cfg = build_real_config()
    try:
        report = evaluate_run(cfg)
    except (IncompleteArtifacts, ScopeError) as e:
        print(f"ANALYSIS REFUSED - no verdict emitted: {type(e).__name__}: {e}", flush=True)
        return 2
    VERDICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERDICT_PATH.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    print(f"\n== CONFIRMATORY VERDICT: {report['overall']} ==")
    print(f"branches per rep: {report['branches']}")
    print(f"trials-to-zero distribution: {report['trials_to_zero_distribution']}")
    for x in report["per_rep"]:
        print(f"  rep {x['rep']}: c2z={x['cycles_to_zero']} "
              f"cosugar[{x['cosugar_min']},{x['cosugar_max']}] "
              f"guard={x['guard_fires']} floors={x['carriers_at_floor']}/25+"
              f"{x['untouched_at_floor']}/9 collateral={x['collateral_count']} "
              f"-> {x['branch']}")
    print(f"verdict written: {VERDICT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
