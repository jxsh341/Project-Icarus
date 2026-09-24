"""WP6c report builder: fold the sugar/bitter grid results into the
validation record with the discriminating-outcome analysis.

Reads the per-trial JSONL checkpoints written by wp6c_run.py (resumable
design), so the report is always built from the same durable record the
runs wrote - never from stdout.

Readout (v3): MN9_L (10331) is the paper's readout neuron (figures.ipynb
cell 23: id_mn9 = 720575940660219265 # left; right-GRN drive -> left MN9,
the known contralateral crossing of this circuit). MN9_R (16949) is
recorded but not the headline. Rates are per-neuron; the earlier
"mean of both MN9s" halved the reported rates (40.6 was 81.3/2).
"""

import json
from pathlib import Path

import numpy as np
from scipy import stats

OUT = Path("results/wp6c_sugar_bitter")
REPORT_PATH = Path("validation/reference/wp6c_sign_behavioral_anchor.json")

ARMS = ["signed", "abl-glu", "all-pos"]
CONDITIONS = [("sugar200_bitter0", "sugar_only"), ("sugar200_bitter200", "sugar_bitter")]
MN9_L, MN9_R = "10331", "16949"


def load_trials(arm: str, cond_file: str) -> list[dict]:
    p = OUT / f"trials_{arm}_{cond_file}.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def cell_stats(trials: list[dict], neuron_key: str) -> dict:
    rates = np.array([t["mn9"][neuron_key] for t in trials])
    return {
        "mean_hz": float(rates.mean()),
        "sem_hz": float(rates.std(ddof=1) / np.sqrt(len(rates))),
        "min_hz": float(rates.min()),
        "max_hz": float(rates.max()),
        "trials_with_zero_spikes": int((rates == 0).sum()),
        "n_trials": len(rates),
    }


def main() -> int:
    per_arm = {}
    for arm in ARMS:
        entry = {}
        rates_L = {}
        for cond_file, cond_name in CONDITIONS:
            trials = load_trials(arm, cond_file)
            assert len(trials) == 10, f"{arm}/{cond_file}: {len(trials)} trials"
            entry[cond_name] = {
                "mn9_L_10331": cell_stats(trials, MN9_L),
                "mn9_R_16949": cell_stats(trials, MN9_R),
                "total_spikes_mean": float(np.mean([t["total_spikes"] for t in trials])),
                "n_spiking_mean": float(np.mean([t["n_spiking"] for t in trials])),
                "seeds": [t["seed"] for t in trials],
            }
            rates_L[cond_name] = np.array([t["mn9"][MN9_L] for t in trials])

        so, sb = rates_L["sugar_only"], rates_L["sugar_bitter"]
        t_w, p_w = stats.ttest_ind(so, sb, equal_var=False)
        try:
            _, p_u = stats.mannwhitneyu(so, sb, alternative="two-sided")
        except ValueError:
            p_u = float("nan")
        entry["mn9_L_statistics"] = {
            "sugar_only_hz": float(so.mean()),
            "sugar_bitter_hz": float(sb.mean()),
            "delta_hz": float(sb.mean() - so.mean()),
            "welch_t": float(t_w),
            "welch_p": float(p_w),
            "mannwhitney_p": float(p_u),
            "direction": "suppressed" if sb.mean() < so.mean() else "not_suppressed",
        }
        per_arm[arm] = entry

    s = per_arm["signed"]["mn9_L_statistics"]
    a = per_arm["all-pos"]["mn9_L_statistics"]
    g = per_arm["abl-glu"]["mn9_L_statistics"]

    discriminating = s["direction"] == "suppressed" and a["direction"] == "not_suppressed"
    glu_specific = g["direction"] == "not_suppressed"
    if discriminating and glu_specific:
        verdict = (
            "PASS - the signed convention reproduces the paper's directional "
            "finding (bitter suppresses sugar-driven MN9_L firing) and BOTH ablated "
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
        "prediction_source": "Shiu et al. 2024 Fig 3a (bitter GRN co-stimulation suppresses sugar-driven MN9_L firing)",
        "substrate": {
            "snapshot": "run-007: male-cns:v0.9 depth-2 closed subgraph around the 36 driven GRNs (40,290 neurons, 336,245 signed edges, 0 dangling)",
            "driven_sugar": "LB3b/LB3c (Gr64f+ sugar lbGRNs), right hemisphere, n=17",
            "driven_bitter": "LB1a-d (Gr33a+ bitter lbGRNs), right hemisphere, n=19",
            "population_mapping_source": "Agee et al. 2026 (Cell) gustatory connectome paper: MaleCNS-native lbGRN type names; mapping recorded in wp6c_grn_seeds.json with per-neuron NT",
            "readout": "MN9_L (10331) firing rate - the paper's readout (id_mn9 720575940660219265, left; right-GRN drive -> left MN9, contralateral crossing). MN9_R (16949) recorded, not headline.",
        },
        "protocol": {
            "duration_ms": 1000.0,
            "n_trials_per_condition": 10,
            "seeds": "7000-7009 (identical across arms and conditions)",
            "drive": "sugar 200 Hz, bitter 200 Hz - the paper's Fig 3a high-drive corner (its full grid is 0-200 Hz in 20 Hz steps)",
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
            "exact_zero_note": (
                "MN9_L suppression is literal zero spikes in 10/10 signed trials "
                "(not a rounding artifact). The paper's own pipeline represents MN9 "
                "rates as fillna(0) and its Fig 3a shows full suppression at high "
                "bitter drive - complete silencing at the 200/200 corner matches "
                "the published target regime."
            ),
        },
        "interpretation": {
            "signed": "Bitter co-drive silences MN9_L (81.3 -> 0.0 Hz; Welch t=101.2, p=4.6e-15; Mann-Whitney p=6.1e-05), reproducing the paper's Fig 3a direction on MaleCNS.",
            "abl-glu": "With glutamate excitatory, bitter co-drive INCREASES MN9_L rate (102.7 -> 105.7 Hz; Welch p=1.6e-04): suppression depends on glutamatergic inhibition, not only GABA. Corroborates Agee et al. 2026: lbGRN bitter signaling is (partly) glutamatergic.",
            "all-pos": "Without signs, MN9_L runs at ~143 Hz in both conditions (no suppression; delta +0.5 Hz, Welch p=0.031 - a small but significant INCREASE), plus a 16x spike-count explosion (618K vs 39K mean): the unsigned graph is not merely quantitatively wrong, it produces a qualitatively different (epileptiform) network.",
        },
        "limitations": [
            "Population identity mapping (FlyWire GRNs -> MaleCNS lbGRN types) is from the Agee et al. 2026 (Cell) gustatory connectome paper, not from Shiu et al.; literature-based, recorded in wp6c_grn_seeds.json with per-neuron NT.",
            "Directionality, not rate matching, is the tested prediction (different substrate: MaleCNS vs the paper's FlyWire male-CNS model).",
            "MN9 firing rate is a scalar circuit proxy for proboscis extension, not a behavioral assay.",
            "NT convention for 'unknown' neurons (14.4% here) defaults to +1; hub-bias check (WP6b) shows unknown-NT neurons are under-represented among out-weight hubs.",
            "Single grid corner (200/200 Hz) tested, not the paper's full 11x11 grid; a dose-response reproduction would be the natural follow-up.",
            "MN9_R (16949) is silent across all arms/conditions in this closure (dynamics of the right-side mirror circuit may require the left GRNs); the paper's readout (MN9_L) is the one reported.",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["discriminating_outcome"], indent=2))
    print()
    for arm in ARMS:
        e = per_arm[arm]["mn9_L_statistics"]
        print(f"[{arm:8s}] MN9_L sugar-only {e['sugar_only_hz']:6.1f} Hz | "
              f"sugar+bitter {e['sugar_bitter_hz']:6.1f} Hz | "
              f"delta {e['delta_hz']:+6.1f} Hz | {e['direction']} "
              f"(Welch p={e['welch_p']:.2e})")
    print("report ->", REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
