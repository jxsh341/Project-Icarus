# ICA-M1-1 Phase A — Location Encoding Audit (read-only)

**Scope:** how environmental location information from M1-GRIDFETCH *could* enter
the existing Icarus substrate through its current input pathway. No internals were
modified for this audit. Repo state: `be845c0`.

## 1. How a cue enters the substrate today

`fly/api.py` v1.1.0 `InputEvent` → `StimulusPort(name, body_ids, rate_hz, slot,
role)` → `simulate_lif(stimulated=...)` — a Poisson drive at `rate_hz` onto the
listed body ids (slot 1 = primary `r_poisson_Hz` population; slots 2/3 = the
sugar/bitter drive populations). **The cue is an arbitrary set of connectome
body ids; the API accepts any of them without touching Icarus internals.** The
GNG521 reference cue is `[15957, 16327]` at 200 Hz (`docs/PHASE_7B_PREREG.md`
screen table; Hybrid probe §1).

## 2. Which populations participate

- Cue candidates that passed the frozen Stage-0 gates (G1 innate silence, G2
  two-hop expressibility): GNG521 [15957,16327] (pair C=291+... ), GNG491
  [14094], GNG557 [12595], GNG610 [128102], GNG611 [25821], GNG622 [32179],
  AN17A015 [75140], AN17A024 [51068], IN05B094 [800555]. GNG380/GNG521 were
  excluded from the held-out screen as already-used.
- Failing/unrelated types (measured): GNG318 [524428] (G1+G2 FAIL, but innate
  cue-alone MN9 64–83 Hz), ANXXX255/ANXXX462a/dorsal_tpGRN (G1 FAIL, innate MN9
  active), PRW043/pIP1 (G2 FAIL, silent).
- Drive: `sugar_R` = 17 bodies (`wp6c_grn_seeds.json`), 200 Hz, slot 2.
- Readout: MN9_L = 10331, frozen behavioural threshold 41.5 Hz.

## 3. Answers to the Phase-A questions

1. **GNG521 representation:** two body ids driven directly by Poisson kicks
   (refractory disabled for Poisson targets, per `simulate_lif` docstring).
2. **Distinguishable activation patterns:** measured in Phase B
   (`ICA_M1_REPRESENTATIONAL_SEPARABILITY.md`) — population spike sets, not
   identifiers.
3. **API accepts cue info without internals changes:** YES — any body-id set is a
   valid `StimulusPort`; no code change needed.
4. **Association ↔ external location id:** the API registry keys associations by
   cue tuple (`assoc_<footprint_sha>`); the location→cue binding is caller-side
   metadata (Hybrid keeps `location_id -> cue body_ids`). `present_cue` returns
   the association ids whose cue matches, so a returned id can be mapped back to
   a location by the caller. No internals change needed.
5. **Distinguishing multiple associations:** **LIMITED** — there is ONE readout
   (MN9_L). Two associations are distinguishable only by *which cue was
   presented* (cue-selective retrieval), not by different output channels.
   The response is a single scalar rate; it cannot encode "which location" by
   itself — the location identity must be read from the cue/association id in
   the contract, and the neural readout only signals "retrieved / not".

## 4. Mapping proposal (location → cue)

GRIDFETCH grid cell (x,y) → hash to one of the gate-passing cue populations
(e.g. 4 locations → GNG521/GNG491/GNG557/GNG610) → `acquire(cue, sugar_R)` →
`present_cue(cue)` returns `{associations: [id], retrieved, confidence}` → Hybrid
maps id back to (x,y). Constraints measured in WP2 and binding here: acquisition
works only inside the characterized regime (P1 NEGATIVE-ACQUISITION for
arbitrary held-out cues), reversal is NEGATIVE, and the readout is single.

## 5. Limitations of the existing encoding (documented before any new system)

- Single readout channel (see 5 above); no population-coded output.
- Cue populations are fixed anatomy — a location mapping is a *choice* of which
  existing GRN population stands for the location; learnability of that choice
  is NOT predictable a priori (P1 predictor failed 4/6).
- Stimulus strength is bounded by the stability envelope (guard at 150k
  spikes/trial); Hybrid attempt A (whole sugar_R as cue) fired the guard — do
  not broaden stimuli.
- No per-neuron drive channel yet (REQ-ICA-2, phase-2); rates only.
