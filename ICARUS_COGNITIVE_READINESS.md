# ICARUS_COGNITIVE_READINESS.md — WP2 Cognitive Substrate Readiness Audit

**Audit type:** read-only capability and evidence audit of Project Icarus (the `fly-cognition` repository).
**Repo state audited:** commit `7657c5e` (clean tree). **No code was modified for this audit.**
**Method:** every classification below cites source files, tests, verdict JSONs, and preregistrations in this repo. Verdicts are read from `results/**/*VERDICT*.json`, not from prose. Where evidence is negative or bounded, it is reported as such.

---

## A. Executive assessment

Icarus is a **validated spiking-neural substrate with one fully demonstrated cognitive primitive: associative learning with located, certifiable retention and erasure on a real connectome-derived microcircuit**, plus a closed-loop embodied conditioning demonstration (E1) and a versioned subsystem API (v1.0.0). It is **not** a memory system in the general sense, has **no demonstrated multi-step reasoning**, no planner/goals/reward-driven action selection, and no full-simulation-state resume (membrane/RNG state is per-call by design). Its strongest, most defensible contribution to SiR M1 is as the **adaptive sensorimotor association + selective memory-editing substrate inside a coordinator-owned loop** — not as a reasoning or planning owner.

---

## B. Capability inventory

| # | Investigation area | Classification | One-line justification |
|---|---|---|---|
| 1 | Internal neural state | **PARTIALLY DEMONSTRATED** | Synaptic weights persist and are hash-verified (R1, 12/12 bit-identical); membrane/refractory/activity are per-call by design (`lif.py:141`); segmented-vs-continuous equivalence untested |
| 2 | Memory & retention | **DEMONSTRATED (bounded)** | Learned persistent memory: acquisition + hash-level retention + cue-only retrieval; certified forgetting (L6a 11/11, A3 44/44); interference mapped (P4/P4b). Duration tested only to ~30 trials / 25 cycles |
| 3 | Retrieval & representation | **PARTIALLY DEMONSTRATED** | Cue-selective retrieval demonstrated (aloneA vs cosA separation, all verdicts); post-erasure state provably *not* decodable as "member" (oracle PASS = negative leak result); single readout (MN9_L); aliasing under interference not systematically tested |
| 4 | Adaptive learning & plasticity | **DEMONSTRATED (bounded)** | Hebbian V_CLIP, rate-form, cue→1-hop; acquisition in a characterized narrow regime (P2 confirm 8/8); reversal *fails* (coincidence waste, traced); unlearning/graded/selective all measured (L6b, P2, P3 16/16, P4b PASS 4/4); transfer weak (P1 NEGATIVE-ACQUISITION) |
| 5 | Multi-step computation & reasoning | **PARTIALLY DEMONSTRATED (computation) / ABSENT (reasoning)** | Multi-input conjunction and history-dependent non-monotonic responses demonstrated; one-step closed loop (E1 PASS); no compositional/multi-hop reasoning battery exists |
| 6 | Continuity, persistence, recovery | **PARTIALLY DEMONSTRATED** | Weight+config+learning-state checkpoint save/restore is hash-verified incl. cross-process load and tamper detection (API tests); full simulation state (membrane, RNG, time) is *not* saved — `simulate_lif` is stateless per call; segmented-vs-continuous equivalence UNTESTED |
| 7 | External interfaces & integration readiness | **DEMONSTRATED** | `fly/api.py` v1.0.0: versioned input/output schemas, learning control, checkpointing, state export/import, lifecycle state machine — 10 contract tests; plus raw `simulate_lif`/`TrainingRun`/`SensorimotorLoop` |

---

## C. Evidence register

### Investigation 1 — Internal neural state

- **Membrane potentials / refractory / activity:** defined in `fly/dynamics/lif.py` (`LIFParams`, `simulate_lif`, `LIFRun`). `v` is initialized fresh every call (`lif.py:141`: `v = np.full(n, params.v0_mV if init_v_mV is None else ...)`). **Does not persist across `simulate_lif` calls**; `init_v_mV` allows manual injection (tested in `tests/test_lif.py:147,171,192` for injection behavior, *not* for segmented-vs-continuous equivalence).
- **Synaptic weights:** persist in the CSR matrix object; hash = `fly/training.py:68 weight_matrix_hash`. Persistence **independently tested at hash level**: R1 retention, 12/12 blocks bit-identical end-acq → end-retention with the plasticity rule active (`docs/TASK_B_CLOSEOUT.md` §R1).
- **Plasticity-related state:** `HebbianRule._pending` accumulates until `apply()` (`fly/plasticity.py:125+`); persists across trials within a `TrainingRun`; not serialized separately.
- **Buffers:** none beyond `LIFRun` return values. **RNG:** per-call `seed` parameter; deterministic per (matrix, seed); no RNG state carried between calls.
- **Segmented vs continuous equivalence:** **UNTESTED** — no test runs N short calls vs one long call over the same total simulated time. Flagged as a gap, not assumed.

### Investigation 2 — Memory and information retention

Three categories distinguished as required:

1. **Transient activity:** demonstrated — probe responses differ by stimulus (alone vs cosugar) in every verdict JSON.
2. **Persistent neural state (weights):** DEMONSTRATED — R1: 30 no-stimulus trials with rule live, 12/12 weight-hash-identical; spontaneous dynamics separately verified silent. Tested duration: 15 acq + 15 retention trials (~15 s simulated each); longer horizons untested.
3. **Learned persistent memory:** DEMONSTRATED — GNG521 acquisition (cue+sugar → MN9 82–87 Hz), confirmatory P2 PASS 8/8 (`results/phase7/p2_g380/P2_VERDICT.json`); **retrieval without re-presenting the original drive**: cue-alone probes (aloneA) at 76–89 Hz post-acquisition (`TASK_B_CLOSEOUT.md` R1). Different histories → distinguishable states: alone vs cosugar separation in all reps. **Interference:** P4 MIXED (8-trial dose) → P4b PASS 4/4 at 20-trial dose — A erased to literal 0 with B intact 69–77 Hz, disjoint footprints, B edges bit-unchanged (`results/phase7p4b/P4B_VERDICT.json`). **Forgetting certified, not assumed:** membership-oracle FR 11/11 (`oracle_report.json`) and wide 49-feature oracle FR 44/44, LOO 1.000 (`oracle_report_wide_A3.json`). **Retention curve endpoint:** information unavailable (readout 0) by cycle 15–25 under unlearning protocols (P3 16/16). Distractor robustness: only disjoint-footprint case tested (P4/P4b); overlapping-footprint interference untested.

### Investigation 3 — Retrieval and representation

- Encoding is firing-rate based at a single readout population (MN9_L = 10331), cue-selective: aloneA vs cosA bands disjoint across all experiments.
- **Decodability probe with negative control:** WP-L6a membership oracle — after unlearning, substrates are indistinguishable from never-learned (FR 11/11; wide-oracle 44/44). This is a *negative* identifiability result, reported as PASS for "no inferable leak", i.e. residual synaptic edges do **not** encode retrievable membership information.
- Representational aliasing under interfering inputs: not systematically probed (P4 covers disjoint footprints only). Classification: PARTIALLY DEMONSTRATED.

### Investigation 4 — Adaptive learning and plasticity

- **Rule:** rate-form Hebbian, `eta·x·y` per coincidence, cue→1-hop structural edges only, V_CLIP semantics, `w_max=766`, stability guard (`fly/plasticity.py`). No external supervision; local.
- **Acquisition:** DEMONSTRATED in a narrow characterized regime — WP2 screen of 15 candidate types under frozen seeds; GNG521 class acquires; confirmatory P2 8/8. Held-out prediction (P1): NEGATIVE-ACQUISITION — accessibility predictor held 4/6, broke on the tiny-footprint GNG557 (`results/phase7b/P1_VERDICT.json`). Transfer to new inputs is therefore **weak/unproven**.
- **Reversal:** NEGATIVE — coincidence waste, traced spike-level (arrivals +34%, spikes −45%; ~300 Hz onset boundary), GNG521 stable at 2.75× crossing dose (`TASK_B_CLOSEOUT.md` R2).
- **Unlearning:** DEMONSTRATED and certified — rank-targeted decay (L6b 25/25+9/9 floors 8/8; P2 GNG380 8/8 incl. 77/96 zero-input partners), graded dose dial (P3 PASS 16/16, floor fraction == analytic exactly), selective multi-memory removal (P4b PASS 4/4). Footprint-estimation sensitivity measured (P5): robust to both under- and over-estimation.
- **Reproducibility:** frozen seed spaces (Random(2026xxxx) draws, disjointness guarded), harness sha-pins, preregistrations frozen pre-run, 198 tests, programmatic claim audit (50 doc checks + 18 claims, 0 failures at `7657c5e`).

### Investigation 5 — Multi-step computation and reasoning readiness

- Multi-population integration: DEMONSTRATED (cue × sugar conjunction; cosugar band 75–95 Hz preserved across all erasure protocols).
- History dependence: DEMONSTRATED and non-monotonic (coincidence waste — response depends on preceding drive history, not just current input).
- Intermediate-state maintenance across dependent steps: only one-step (E1 closed loop, PASS 4/4 learn + 4/4 control bit-pristine, `results/phase7e1/E1_VERDICT.json`). Two-hop *structural* expressibility was screened (P1 G2 gate) but that is anatomy, not computation.
- Compositional / multi-hop inference / reasoning: **ABSENT** — no registered reasoning battery exists. Smallest non-presupposing test: a delayed-match-to-sample or two-hop dependency chain (cue → intermediate → readout) on the existing closure with preregistered readout criteria, control = scrambled intermediate mapping.

### Investigation 6 — Continuity, persistence, recovery

- **Saving weights/params:** DEMONSTRATED — `TrainingRun.save` (`fly/training.py:220+`), API `save_checkpoint`/`load_checkpoint` hash-verified incl. tamper detection (`tests/test_api.py`).
- **Saving learning state:** DEMONSTRATED — `LearningController` serialized in checkpoints; rule `_pending` is transient within a trial.
- **Saving full simulation state (membrane, refractory, RNG, time):** **ABSENT by design** — `simulate_lif` reinitializes `v` each call; no RNG state object exists.
- **Cross-process restore:** DEMONSTRATED for weights+config (load_checkpoint verifies hash; behavioral determinism per seed is tested in `test_lif.py`).
- **Segmented = continuous:** **UNTESTED** (see Inv. 1). **Resume an ongoing task mid-simulation:** NOT POSSIBLE currently (only mid-run *between trials*, via trial_index/history).

### Investigation 7 — External interfaces

- **`fly/api.py` (API v1.0.0, schema v1)** — DEMONSTRATED, 10 contract tests (`tests/test_api.py`): versioned `InputEvent`/`Observation` (reject foreign schema versions), `LearningController` (arm/disarm; disarmed default), checkpoint save/load, COO `export_state`/`import_state`, lifecycle `initialize/pause/resume/reset/shutdown` with illegal-transition errors. Verified on the real snapshot: pristine hash `384406e9278ae0c0` reproduced.
- Raw interfaces: `simulate_lif(matrix, node_ids, params, duration_ms, stimulated…, seed)` — stateless, deterministic per seed; `TrainingRun` — trial loop + guard + checkpointing; `SensorimotorLoop` — embodiment step/episode.
- Restrictions: fixed-structure matrix (plasticity never creates edges); experiments use one readout (MN9_L), 1000 ms episodes, explicit seeds; guard halts on threshold breach.
- **Hybrid-repo caveat honored:** no Hybrid reference patch is assumed adopted; everything above is in this repo at `7657c5e`.

---

## D. Capability gaps (ranked by importance to SiR M1)

1. **No full-simulation-state persistence** (membrane/RNG/time) — blocks "resume an ongoing cognitive process", a core M1 continuity requirement. Only weights/trial-level resume exists.
2. **No demonstrated multi-step / compositional reasoning** — only one-step closed-loop conditioning (E1) and history-dependent single-step responses.
3. **No goal representation, planner, or reward-driven action selection** — ABSENT entirely (no code, no experiments).
4. **No persistent episodic memory store** — "memory" here is synaptic weights of associations; nothing stores/retrieves arbitrary episode content.
5. **Weak transfer/generalization of learning** — P1 accessibility prediction NEGATIVE-ACQUISITION (4/6); learnability regime narrow and not yet predictively characterized.
6. **Segmented-vs-continuous equivalence untested** — a correctness risk for any coordinator that steps the substrate in chunks.
7. **Single-task embodiment** — one actuator (proboscis), one cue class.

## E. Minimum requirements for Icarus to contribute to M1

- **Reliability (small, test-only):** add a segmented-vs-continuous equivalence test (N short calls with carried `init_v_mV`/spike carryover vs one long call) — experiment, not code redesign, since the simulator is per-call stateless by design.
- **Expose existing capabilities:** adopt `fly/api.py` as the coordinator-facing surface (already versioned and tested); expose weight-hash + trial_index in every `Observation` (done).
- **New-capability experiments (preregistered):** (a) delayed-match-to-sample retrieval on the closure; (b) two-hop dependency chain for multi-step computation; (c) full-state checkpoint (membrane + RNG + time) if M1 truly needs mid-simulation resume — otherwise trial-level resume suffices and should be stated as the contract.
- **Architectural (research, not engineering):** goals/planner/reward-driven action selection and an episodic store are absent; they require new research, not patches. Do not assign these to Icarus yet.

## F. Recommended development sequence

1. Segmented-vs-continuous equivalence test (low complexity, low risk, closes a correctness gap; independent).
2. Coordinator adoption of `fly/api.py` v1 with the trial-level resume contract stated explicitly (low complexity; depends on nothing).
3. Delayed-match-to-sample + two-hop chain preregistrations (medium complexity, medium uncertainty; establishes whether multi-step computation exists).
4. Full-simulation-state checkpoint *only if* M1 spec requires mid-simulation resume (medium complexity; low scientific uncertainty).
5. Learnability-regime characterization (what predicts acquisition/erasure across the 15 candidate types) — high scientific value (P1 failed; the open scientific question), medium complexity.
6. Goals/planner/episodic store — architectural research; highest uncertainty; not M1-blocking if the coordinator owns planning.

## G. Final assessment

1. **Three strongest demonstrated capabilities:** (a) associative acquisition + hash-verified retention + certified, selective, graded erasure on a real connectome microcircuit (P2 8/8, P3 16/16, P4b 4/4, L6a/A3 oracle-clean); (b) closed-loop embodied conditioning that closes autonomously with a bit-pristine control (E1 PASS); (c) a versioned, hash-verified subsystem API with lifecycle and persistence contracts (198 tests, audit 0 failures).
2. **Three largest gaps:** no full-simulation-state resume (membrane/RNG/time) and untested segmented equivalence; no multi-step/compositional reasoning evidence; no goals/planner/reward-driven action selection or episodic memory store.
3. **Most appropriate initial role in SiR:** the **adaptive spiking association-and-memory-editing substrate** inside a coordinator-owned loop — providing temporal dynamics, history-dependent responses, learned cue→actuator mappings, and selective unlearning — interfaced via `fly/api.py`.
4. **Capabilities Icarus should NOT yet own:** reasoning/planning, goal management, episodic memory, mid-simulation process continuity, or any claim of general intelligence.
5. **Most important unresolved scientific question:** what structural property of a cue circuit predicts learnability *and* erasability — the held-out accessibility predictor failed (P1, 4/6), so the current regime boundary (footprint size / zero-input-partner fraction / cue-incident edges) is measured but not yet predictive.

---
*Audit evidence base: `docs/TECHNICAL_REPORT.md`, `docs/FLY_LEARN_001_DECISIONS.md`, `docs/TASK_B_CLOSEOUT.md`, preregs `docs/PHASE_*_PREREG.md`, verdicts `results/**/*VERDICT*.json`, `tests/` (198 tests at `7657c5e`), audit `scripts/phase4_report_claim_audit.py` (50 checks + 18 claims, 0 failures).*
