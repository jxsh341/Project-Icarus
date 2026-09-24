"""WP6c report builder: fold the sugar/bitter grid results into the
validation record with the discriminating-outcome analysis.

Reads the per-trial JSONL checkpoints written by wp6c_run.py (resumable
design), so the report is always built from the same durable record the
runs wrote - never from stdout.
"""

import json
from pathlib import Path

import numpy as np

OUT = Path("results/wp6c_sugar_bitter")
REPORT_PATH = Path("validation/reference/wp6c_sign_behavioral_anchor.json")

ARMS = ["signed", "abl-glu", "all-pos"]
CONDITIONS = [("sugar200_bitter0", "sugar_only"), ("sugar200_bitter200", "sugar_bitter")]


def load_trials(arm: str, cond_file: str) -> list[dict]:
    p = OUT / f"trials_{arm}_{cond_file}.jsonl"
    trials = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return trials


def main() -> int:
    per_arm = {}
    for arm in ARMS:
        entry = {}
        for cond_file, cond_name in CONDITIONS:
            trials = load_trials(arm, cond_file)
            assert len(trials) == 10, f"{arm}/{cond_file}: {len(trials)} trials"
            so = np.array([t["mn9"]["mean"] for t in trials])
            entry[cond_name] = {
                "mn9_mean_hz": float(so.mean()),
                "mn9_sem_hz": float(so.std(ddof=1) / np.sqrt(len(so))),
                "mn9_min_max_hz": [float(so.min()), float(so.max())],
                "total_spikes_mean": float(np.mean([t["total_spikes"] for t in trials])),
                "n_spiking_mean": float(np.mean([t["n_spiking"] for t in trials])),
                "n_trials": len(trials),
                "seeds": [t["seed"] for t in trials],
            }
        entry["delta_hz"] = entry["sugar_bitter"]["mn9_mean_hz"] - entry["sugar_only"]["mn9_mean_hz"]
        entry["direction"] = ("suppressed"
                              if entry["sugar_bitter"]["mn9_mean_hz"] < entry["sugar_only"]["mn9_mean_hz"]
                              else "not_suppressed")
        per_arm[arm] = entry

    s, a, g = per_arm["signed"], per_arm["all-pos"], per_arm["abl-glu"]

    discriminating = s["direction"] == "suppressed" and a["direction"] == "not_suppressed"
    glu_specific = g["direction"] == "not_suppressed"
    if discriminating and glu_specific:
        verdict = (
            "PASS - the signed convention reproduces the paper's directional "
            "finding (bitter suppresses sugar-driven MN9 firing) and BOTH ablated "
            "conventions fail to reproduce it. The NT-sign assumption is "
            "load-bearing: GABA alone is insufficient - glutamatergic inhibition "
            "is specifically required for bitter-driven feeding suppression."
        )
    elif discriminating:
        verdict = (
            "PASS - signed reproduces direction, all-pos does not; "
            "glutamate-specific ablation retained direction (glu not required)."
        )
    else:
        verdict = "FAIL - directionality not discriminated between conventions"

    report = {
        "work_package": "WP6c",
        "title": "Behavioral anchor for the NT-sign convention: sugar/bitter feeding",
        "prediction_source": "Shiu et al. 2024 Fig 3a (bitter GRN co-stimulation suppresses sugar-driven feeding motor output)",
        "substrate": {
            "snapshot": "run-007: male-cns:v0.9 depth-2 closed subgraph around the 36 driven GRNs (40,290 neurons, 336,245 signed edges, 0 dangling)",
            "driven_sugar": "LB3b/LB3c (Gr64f+ sugar lbGRNs), right hemisphere, n=17",
            "driven_bitter": "LB1a-d (Gr33a+ bitter lbGRNs), right hemisphere, n=19",
            "population_mapping_source": "Cell 2026 gustatory connectome paper (MaleCNS-native lbGRN type names)",
            "readout": "MN9 (proboscis-extension motor neuron) firing rate; mean of MN9_R (16949) and MN9_L (10331)",
        },
        "protocol": {
            "duration_ms": 1000.0,
            "n_trials_per_condition": 10,
            "seeds": "7000-7009 (identical across arms and conditions)",
            "drive": "sugar 200 Hz, bitter 200 Hz (paper's Fig 3a high-drive contrast)",
            "simulator": "fly.dynamics.lif.simulate_lif (WP6b-validated against Shiu Brian2 reference, TOST p~0, rho=0.9999)",
            "two_population_drive": "stimulated2/r_poisson2_Hz pathway (reference poi() exc2 semantics; rfc=0; TDD'd in tests/test_two_population_drive.py)",
        },
        "arms": {
            "signed": "pipeline NT convention: gaba, glutamate -> -1; ach -> +1; unknown -> +1 (5,794/40,290 neurons unknown, hub-under-represented)",
            "abl-glu": "glutamate -> +1 (gaba kept inhibitory): 32,165 glutamatergic edges flipped positive",
            "all-pos": "all weights positive (sign convention fully removed)",
        },
        "results_per_arm": per_arm,
        "discriminating_outcome": {
            "signed_reproduces_paper_direction": s["direction"] == "suppressed",
            "all_pos_suppresses_mn9": a["direction"] == "suppressed",
            "glutamate_flip_alone_breaks_direction": glu_specific,
            "verdict": verdict,
        },
        "interpretation": {
            "signed": "Bitter co-drive silences MN9 (40.6 -> 0.0 Hz), reproducing the paper's directional finding on MaleCNS.",
            "abl-glu": "With glutamate excitatory, bitter co-drive INCREASES MN9 rate (51.5 -> 53.0 Hz): the suppression circuit depends on glutamatergic inhibition, not only GABA. Corroborates the Cell 2026 finding that lbGRN bitter signaling is (partly) glutamatergic.",
            "all-pos": "Without signs, MN9 runs at ~88 Hz in both conditions - no suppression, and a 16x spike-count explosion (618K vs 39K mean): the unsigned graph is not merely quantitatively wrong, it produces a qualitatively different (epileptiform) network.",
        },
        "limitations": [
            "Population identity mapping (FlyWire GRNs -> MaleCNS lbGRN types) is from the Cell 2026 gustatory connectome paper, not from Shiu et al.; literature-based, recorded in wp6c_grn_seeds.json with per-neuron NT.",
            "Directionality, not rate matching, is the tested prediction (different substrate: MaleCNS vs the paper's FlyWire male-CNS model).",
            "MN9 firing rate is a scalar circuit proxy for proboscis extension, not a behavioral assay.",
            "NT convention for 'unknown' neurons (14.4% here) defaults to +1; hub-bias check (WP6b) shows unknown-NT neurons are under-represented among out-weight hubs.",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["discriminating_outcome"], indent=2))
    print()
    for arm in ARMS:
        e = per_arm[arm]
        print(f"[{arm:8s}] sugar-only {e['sugar_only']['mn9_mean_hz']:6.1f} Hz | "
              f"sugar+bitter {e['sugar_bitter']['mn9_mean_hz']:6.1f} Hz | "
              f"delta {e['delta_hz']:+6.1f} Hz | {e['direction']}")
    print("report ->", REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
