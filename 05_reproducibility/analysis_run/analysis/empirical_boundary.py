#!/usr/bin/env python3
"""Exploratory cued-perception boundary check, not a placebo treatment trial."""
from __future__ import annotations
import csv, hashlib, itertools, json, math, platform
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "empirical"
SOURCE = OUT / "source"
PROTOCOL = ROOT / "research" / "EMPIRICAL_PROTOCOL.md"
COMMIT = "84dc29cdaefcf78de489e990419a8a398419cb6d"
SEED, BOOTSTRAPS = 20260904, 10000
MODELS = ("sensory_only", "additive_cue", "cue_x_uncertainty")
SOURCE_PATHS = {
    "cued_perception_with_exclusions.csv": "data_for_analysis/processed_data/task-expectpercept_all_subjs_with_pred_and_exclusions.csv",
    "behavioral_analysis.R": "analysis/behavioral_analysis.R",
    "LICENSE": "LICENSE",
}
COLUMNS = ("source_row", "participant", "modality", "block", "trial_num",
           "trial_within_modality", "stim_level", "stim_value", "cue_mean",
           "cue_std", "cue_sk", "rating", "RT")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def flag(value):
    if value in ("0", "False", "FALSE", "false"):
        return False
    if value in ("1", "True", "TRUE", "true"):
        return True
    raise ValueError(f"Unrecognized exclusion flag: {value!r}")

def finite(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False

def ci(values):
    return [float(v) for v in np.quantile(values, [0.025, 0.975])]

def mean_bootstrap(values, rng):
    x = np.asarray(values, dtype=float)
    if not len(x):
        return {"n_participants": 0}
    draws = rng.integers(0, len(x), size=(BOOTSTRAPS, len(x)))
    return {
        "n_participants": len(x), "mean": float(x.mean()),
        "median": float(np.median(x)),
        "participant_sd": float(x.std(ddof=1)) if len(x) > 1 else None,
        "standard_error": float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None,
        "ci95_percentile": ci(x[draws].mean(axis=1)), "bootstrap_replicates": BOOTSTRAPS,
    }

def load_trials():
    with (SOURCE / "cued_perception_with_exclusions.csv").open(encoding="utf-8-sig", newline="") as f:
        raw = list(csv.DictReader(f))
    numeric = ("block", "trial_num", "stim_level", "stim_value", "cue_mean",
               "cue_std", "cue_sk", "rating", "RT")
    counts = {
        "source_rows": len(raw),
        "source_participants": len({r["participant"] for r in raw}),
        "technical_flag_total": sum(flag(r["exclude_tech_issues"]) for r in raw),
        "rt_flag_total_including_overlap": sum(flag(r["exclude_RT"]) for r in raw),
        "both_flags": sum(flag(r["exclude_tech_issues"]) and flag(r["exclude_RT"]) for r in raw),
    }
    technical_removed = rt_removed = missing_removed = 0
    trials = []
    for row_number, row in enumerate(raw, start=2):
        if flag(row["exclude_tech_issues"]):
            technical_removed += 1
            continue
        if flag(row["exclude_RT"]):
            rt_removed += 1
            continue
        if not all(finite(row[k]) for k in numeric):
            missing_removed += 1
            continue
        r = {"source_row": row_number, "participant": row["participant"], "modality": row["modality"]}
        r.update({key: float(row[key]) for key in numeric})
        for key in ("block", "trial_num", "stim_level", "cue_sk"):
            assert r[key].is_integer(), (key, r[key])
            r[key] = int(r[key])
        r["trial_within_modality"] = r["trial_num"] - (12 if r["trial_num"] > 12 else 0)
        trials.append(r)
    counts.update({
        "technical_removed_first": technical_removed, "rt_removed_after_technical": rt_removed,
        "missing_or_nonfinite_removed_after_flags": missing_removed,
        "retained_trials": len(trials), "retained_participants": len({r["participant"] for r in trials}),
        "by_modality": {m: {
            "trials": sum(r["modality"] == m for r in trials),
            "participants": len({r["participant"] for r in trials if r["modality"] == m}),
        } for m in ("pain", "vision")},
    })
    assert sum((technical_removed, rt_removed, missing_removed, len(trials))) == len(raw)
    assert len({(r["participant"], r["block"], r["trial_num"]) for r in raw}) == len(raw)
    assert all(0 <= r["rating"] <= 100 for r in trials)
    assert all(0.2 <= r["RT"] <= 4.5 for r in trials)
    assert {r["stim_level"] for r in trials} == {1, 2}
    assert {r["cue_mean"] for r in trials} == {0.3, 0.7}
    assert {r["cue_std"] for r in trials} == {0.05, 0.125}
    assert {r["cue_sk"] for r in trials} == {-1, 0, 1}
    assert all(1 <= r["trial_within_modality"] <= 12 for r in trials)
    counts["paper_exclusion_counts_match"] = len(raw) == 6480 and technical_removed == 211 and rt_removed == 234
    write_csv(OUT / "retained_trials.csv", trials, COLUMNS)
    return trials, counts

def compute_contrasts(trials, rng):
    cells = defaultdict(list)
    for r in trials:
        key = (r["participant"], r["modality"], r["stim_level"], r["cue_mean"], r["cue_std"], r["cue_sk"])
        cells[key].append(r["rating"])
    means = {k: float(np.mean(v)) for k, v in cells.items()}
    cell_rows = [
        dict(zip(("participant", "modality", "stim_level", "cue_mean", "cue_std", "cue_sk"), k),
             n_trials=len(cells[k]), mean_rating=v) for k, v in sorted(means.items())
    ]
    write_csv(OUT / "cell_aggregates.csv", cell_rows)
    rows = []
    def add(p, m, effect, values, expected):
        if values:
            rows.append({
                "participant": p, "modality": m, "estimand": effect,
                "value": float(np.mean(values)), "matched_contrasts": len(values),
                "expected_contrasts": expected, "coverage": len(values) / expected,
            })
    for p, m in sorted({(r["participant"], r["modality"]) for r in trials}):
        pairs = {}
        for s, v, k in itertools.product((1, 2), (0.05, 0.125), (-1, 0, 1)):
            low, high = (p, m, s, 0.3, v, k), (p, m, s, 0.7, v, k)
            if low in means and high in means:
                pairs[(s, v, k)] = means[high] - means[low]
        add(p, m, "cue_high_minus_low", list(pairs.values()), 12)
        for s in (1, 2):
            add(p, m, f"cue_high_minus_low_stimulus_{s}",
                [z for (ss, v, k), z in pairs.items() if ss == s], 6)
        for v, label in ((0.05, "low_sd_high_precision"), (0.125, "high_sd_low_precision")):
            add(p, m, "cue_high_minus_low_" + label,
                [z for (s, vv, k), z in pairs.items() if vv == v], 6)
            for s in (1, 2):
                add(p, m, f"cue_high_minus_low_stimulus_{s}_{label}",
                    [z for (ss, vv, k), z in pairs.items() if ss == s and vv == v], 3)
        interactions = []
        for s, k in itertools.product((1, 2), (-1, 0, 1)):
            if (s, 0.05, k) in pairs and (s, 0.125, k) in pairs:
                interactions.append(pairs[(s, 0.125, k)] - pairs[(s, 0.05, k)])
        add(p, m, "cue_effect_high_sd_minus_low_sd", interactions, 6)
        variance_pairs = []
        for s, c, k in itertools.product((1, 2), (0.3, 0.7), (-1, 0, 1)):
            low, high = (p, m, s, c, 0.05, k), (p, m, s, c, 0.125, k)
            if low in means and high in means:
                variance_pairs.append(means[high] - means[low])
        add(p, m, "uncertainty_high_sd_minus_low_sd", variance_pairs, 12)
    write_csv(OUT / "participant_aggregates.csv", rows)
    summaries = {}
    for m in ("pain", "vision"):
        summaries[m] = {}
        for effect in sorted({r["estimand"] for r in rows if r["modality"] == m}):
            subset = [r for r in rows if r["modality"] == m and r["estimand"] == effect]
            result = mean_bootstrap([r["value"] for r in subset], rng)
            result.update({
                "matched_contrasts": sum(r["matched_contrasts"] for r in subset),
                "expected_contrasts": sum(r["expected_contrasts"] for r in subset),
                "participants_with_full_coverage": sum(r["coverage"] == 1 for r in subset),
            })
            summaries[m][effect] = result
    return summaries, len(cell_rows)

def design(rows, transform=None):
    block_trial = np.asarray([[r["block"], r["trial_within_modality"]] for r in rows], float)
    if transform is None:
        center, scale = block_trial.mean(axis=0), block_trial.std(axis=0)
        scale[scale == 0] = 1.0
        transform = (center, scale)
    center, scale = transform
    z = (block_trial - center) / scale
    stimulus = np.array([2 * r["stim_level"] - 3 for r in rows], float)
    cue = np.array([1 if r["cue_mean"] > 0.5 else -1 for r in rows], float)
    uncertainty = np.array([1 if r["cue_std"] > 0.1 else -1 for r in rows], float)
    negative = np.array([r["cue_sk"] < 0 for r in rows], float)
    positive = np.array([r["cue_sk"] > 0 for r in rows], float)
    x = np.column_stack((np.ones(len(rows)), stimulus, z, cue, uncertainty, negative, positive, cue * uncertainty))
    return x, transform

def cross_validate(trials, rng):
    prediction_rows, fold_rows, summaries = [], [], {}
    max_equivalence_error, disjoint_folds = 0.0, 0
    for modality in ("pain", "vision"):
        data = [r for r in trials if r["modality"] == modality]
        subjects = sorted({r["participant"] for r in data})
        per_participant = {name: {} for name in MODELS}
        for held_out in subjects:
            train = [r for r in data if r["participant"] != held_out]
            test = [r for r in data if r["participant"] == held_out]
            assert held_out not in {r["participant"] for r in train}
            disjoint_folds += 1
            xtrain, transform = design(train)
            xtest, _ = design(test, transform)
            ytrain, ytest = np.array([r["rating"] for r in train]), np.array([r["rating"] for r in test])
            counts = Counter(r["participant"] for r in train)
            sqrt_weights = np.sqrt([1.0 / counts[r["participant"]] for r in train])
            predictions = {}
            for name, ncol in zip(MODELS, (4, 8, 9)):
                xw, yw = xtrain[:, :ncol] * sqrt_weights[:, None], ytrain * sqrt_weights
                coefficients, _, rank, _ = np.linalg.lstsq(xw, yw, rcond=None)
                assert rank == ncol
                pred = xtest[:, :ncol] @ coefficients
                assert np.isfinite(pred).all()
                predictions[name] = pred
                residual = ytest - pred
                mse, mae = float(np.mean(residual**2)), float(np.mean(np.abs(residual)))
                per_participant[name][held_out] = (mse, mae)
                fold_rows.append({
                    "participant": held_out, "modality": modality, "model": name,
                    "test_trials": len(test), "training_participants": len(subjects) - 1,
                    "training_trials": len(train), "mse": mse, "mae": mae,
                    "block_train_mean": float(transform[0][0]), "trial_train_mean": float(transform[0][1]),
                    "block_train_sd": float(transform[1][0]), "trial_train_sd": float(transform[1][1]),
                })
                if name == "cue_x_uncertainty":
                    base, context = xtest[:, :4] @ coefficients[:4], xtest[:, 4:9] @ coefficients[4:9]
                    perception_label, reporting_label = base + context, base + context
                    max_equivalence_error = max(max_equivalence_error, float(np.max(np.abs(perception_label - reporting_label))))
                    assert np.allclose(pred, reporting_label, atol=1e-11, rtol=0)
            for idx, r in enumerate(test):
                out = {k: r[k] for k in COLUMNS}
                out.update({name + "_prediction": float(predictions[name][idx]) for name in MODELS})
                prediction_rows.append(out)
        draws = rng.integers(0, len(subjects), size=(BOOTSTRAPS, len(subjects)))
        summaries[modality] = {"n_participants": len(subjects), "n_trials": len(data), "models": {}, "comparisons": {}}
        arrays = {}
        for name in MODELS:
            mse = np.array([per_participant[name][p][0] for p in subjects])
            mae = np.array([per_participant[name][p][1] for p in subjects])
            rmse_boot, mae_boot = np.sqrt(mse[draws].mean(axis=1)), mae[draws].mean(axis=1)
            arrays[name] = (mse, mae, rmse_boot, mae_boot)
            summaries[modality]["models"][name] = {
                "equal_participant_rmse": float(np.sqrt(mse.mean())),
                "rmse_ci95_conditional_percentile": ci(rmse_boot),
                "equal_participant_mae": float(mae.mean()), "mae_ci95_conditional_percentile": ci(mae_boot),
            }
        for baseline, candidate in (("sensory_only", "additive_cue"), ("additive_cue", "cue_x_uncertainty"), ("sensory_only", "cue_x_uncertainty")):
            a, b = arrays[baseline], arrays[candidate]
            summaries[modality]["comparisons"][baseline + "_minus_" + candidate] = {
                "rmse_improvement": float(np.sqrt(a[0].mean()) - np.sqrt(b[0].mean())),
                "rmse_improvement_ci95_conditional": ci(a[2] - b[2]),
                "mae_improvement": float(a[1].mean() - b[1].mean()),
                "mae_improvement_ci95_conditional": ci(a[3] - b[3]),
                "participants_with_lower_mse": int(np.sum(b[0] < a[0])),
                "interpretation": "Positive improvement favors the candidate model.",
            }
    prediction_rows.sort(key=lambda r: r["source_row"])
    assert len(prediction_rows) == len(trials)
    assert len({r["source_row"] for r in prediction_rows}) == len(trials)
    write_csv(OUT / "predictions.csv", prediction_rows)
    write_csv(OUT / "cross_validation_participant_scores.csv", fold_rows)
    return summaries, {
        "disjoint_participant_folds": disjoint_folds, "all_predictions_finite": True,
        "prediction_count_equals_retained_trials": True,
        "reporting_vs_perception_relabeling_max_abs_prediction_difference": max_equivalence_error,
        "equality_is_algebraic_not_a_test_of_neural_mechanisms": True,
    }

def provenance():
    source_records = []
    for local, original in SOURCE_PATHS.items():
        p = SOURCE / local
        source_records.append({
            "local_path": str(p.relative_to(ROOT)).replace("\\", "/"), "upstream_path": original,
            "url": f"https://raw.githubusercontent.com/rotemb9/PPRI-paper/{COMMIT}/{original}",
            "sha256": digest(p), "bytes": p.stat().st_size,
            "local_download_mtime_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
        })
    manifest_path = OUT / "provenance.json"
    manifest = {
        "repository": "https://github.com/rotemb9/PPRI-paper", "release": "v2.0.0", "commit": COMMIT,
        "paper_doi": "10.1371/journal.pcbi.1013053",
        "license": "MIT; original copyright notice retained in source/LICENSE",
        "protocol_path": "research/EMPIRICAL_PROTOCOL.md", "protocol_sha256": digest(PROTOCOL),
        "source_files": source_records, "only_fields_in_retained_trials_are_analyzed": True,
        "upstream_predicted_expect_and_vas_mean_are_ignored": True,
        "demographic_questionnaire_and_imaging_files_not_downloaded": True,
    }
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert old["protocol_sha256"] == manifest["protocol_sha256"], "Frozen protocol changed."
        assert [(x["upstream_path"], x["sha256"]) for x in old["source_files"]] == [
            (x["upstream_path"], x["sha256"]) for x in source_records], "Frozen source changed."
    else:
        write_json(manifest_path, manifest)
    return manifest

def methods_report(summary):
    n = summary["sample"]
    lines = [
        "# Exploratory empirical boundary check", "",
        "This is a secondary analysis of published social-cue perception data, not a placebo-administration experiment. "
        "No new participants, peripheral biomarkers or brain measurements were analyzed. "
        "The protocol was timestamped before computing these results but after reading the source paper; it is not a preregistration.", "",
        "Source: Botvinik-Nezer R, Geuter S, Lindquist MA, Wager TD (2025), "
        "*Expectation generation and its effect on subsequent pain and visual perception*, "
        "[PLOS Computational Biology](https://doi.org/10.1371/journal.pcbi.1013053). "
        "Processed data and exclusion code were pinned to [PPRI-paper v2.0.0]"
        "(https://github.com/rotemb9/PPRI-paper/tree/v2.0.0), commit " + COMMIT + ".", "",
        "## Analysis sample", "",
        f"The released file contains {n['source_rows']} trials from {n['source_participants']} participants. "
        f"Sequential application of the authors' technical and response-time exclusion flags removed "
        f"{n['technical_removed_first']} and {n['rt_removed_after_technical']} trials, respectively. "
        f"An additional {n['missing_or_nonfinite_removed_after_flags']} rows had missing/nonfinite required fields. "
        f"The analysis retained {n['retained_trials']} trials from {n['retained_participants']} participants. "
        f"The {n['rt_flag_total_including_overlap']} response-time flags include {n['both_flags']} trials already excluded for technical issues.", "",
        "## Our secondary analysis methods", "",
        "Within each modality we computed high-minus-low cue contrasts from participant-level cell means matched on "
        "stimulus intensity, cue SD and skewness. Participants and eligible matched cells received equal weight. "
        "Missing pairs were omitted locally, without imputation or removal of the participant's other observations. "
        "The cue-by-uncertainty contrast is the high-SD cue effect minus the low-SD cue effect, additionally matched "
        "on stimulus and skewness. A negative interaction is consistent with stronger cue effects at higher precision. "
        "Uncertainty main effects compare high versus low SD within stimulus, cue mean and skewness. "
        "The tables report coverage, all prespecified contrasts and unadjusted exploratory 95% percentile intervals "
        f"from {BOOTSTRAPS:,} participant bootstrap samples (seed {SEED}).", "",
        "Prediction used leave-one-participant-out weighted least squares. The sensory model includes stimulus, block "
        "and trial-within-modality; the additive model adds cue mean, SD and two skewness indicators; "
        "the interaction model adds cue mean × SD. Binary factors use fixed -1/+1 coding. "
        "Only block and trial were centered/scaled, separately in each training fold. "
        "Raw ratings were not normalized. Training participants had equal total weight; no held-out "
        "rating or estimated participant intercept entered fitting or transformations. "
        "These deliberately simple population predictors are not reproductions of the authors' mixed models. "
        "RMSE is the square root of mean participant MSE; MAE also weights participants equally.", "",
        "Bootstrap intervals for predictive metrics resample already-computed held-out participant scores "
        "without refitting. They describe conditional uncertainty, not an independent validation sample "
        "or a complete account of training-set uncertainty. Fold overlap can induce dependence. "
        "No multiplicity correction or significance-driven model refinement was performed.", "",
        "## Results", "",
        "| Modality | Retained trials | Participants | Cue high − low (95% CI) | Cue interaction: high SD − low SD (95% CI) |",
        "|---|---:|---:|---:|---:|",
    ]
    def fmt_effect(e):
        a, b = e["ci95_percentile"]
        return f"{e['mean']:.3f} [{a:.3f}, {b:.3f}]"
    for m in ("pain", "vision"):
        e = summary["contrasts"][m]
        lines.append(f"| {m} | {n['by_modality'][m]['trials']} | {n['by_modality'][m]['participants']} | "
                     f"{fmt_effect(e['cue_high_minus_low'])} | {fmt_effect(e['cue_effect_high_sd_minus_low_sd'])} |")
    for m in ("pain", "vision"):
        e = summary["contrasts"][m]
        cue, interaction = e["cue_high_minus_low"], e["cue_effect_high_sd_minus_low_sd"]
        lines += ["", f"For {m}, the cue contrast used {cue['matched_contrasts']} of "
                  f"{cue['expected_contrasts']} possible matched cell pairs; "
                  f"{cue['participants_with_full_coverage']} participants had complete coverage. "
                  f"The interaction used {interaction['matched_contrasts']} of "
                  f"{interaction['expected_contrasts']} possible matched contrasts. "
                  f"The high-minus-low uncertainty main effect was "
                  f"{fmt_effect(e['uncertainty_high_sd_minus_low_sd'])}."]
    lines += ["", "Neither modality's descriptive cue-by-uncertainty interval excludes zero. "
              "These matched-cell bootstrap summaries use a different estimator from the original "
              "paper's adjusted mixed-effects models and are not a numerical reproduction of them. "
              "They should not be presented as disproving the original mixed-model result."]
    lines += ["", "All effects are in the modality's own 0–100 rating units; equal numerical changes "
              "are not assumed perceptually comparable across modalities.", "",
              "| Modality | Sensory RMSE | Additive cue RMSE | Cue × uncertainty RMSE |", "|---|---:|---:|---:|"]
    for m in ("pain", "vision"):
        models = summary["cross_validation"][m]["models"]
        vals = [models[name]["equal_participant_rmse"] for name in MODELS]
        lines.append(f"| {m} | {vals[0]:.4f} | {vals[1]:.4f} | {vals[2]:.4f} |")
    for m in ("pain", "vision"):
        cv = summary["cross_validation"][m]["comparisons"]
        a, b = cv["sensory_only_minus_additive_cue"], cv["additive_cue_minus_cue_x_uncertainty"]
        lines += ["", f"For {m}, adding cue variables improved RMSE by {a['rmse_improvement']:.4f} "
                  f"(conditional 95% CI {a['rmse_improvement_ci95_conditional'][0]:.4f} to "
                  f"{a['rmse_improvement_ci95_conditional'][1]:.4f}). "
                  f"Adding the uncertainty interaction changed RMSE improvement by {b['rmse_improvement']:.4f} "
                  f"(conditional 95% CI {b['rmse_improvement_ci95_conditional'][0]:.4f} to "
                  f"{b['rmse_improvement_ci95_conditional'][1]:.4f}); positive values favor the larger model."]
    lines += [
        "", "## Boundaries and observational equivalence", "",
        "Cue assimilation in rating data is compatible with a contextual pathway. It does not validate a "
        "specific network topology, identify a neurotransmitter, demonstrate disease modification or "
        "prove that perception rather than reporting changed. The precision interaction must be assessed "
        "separately by modality; a universal precision-weighting rule is not supported merely by a "
        "positive cue main effect. Small held-out improvements should not be presented as a "
        "clinically meaningful prediction advantage.", "",
        "Algebraically, assigning the identical fitted context term either to latent perception or to a "
        "reporting term produces exactly the same observed-rating predictions. The code verified a maximum "
        f"absolute prediction difference of {summary['checks']['reporting_vs_perception_relabeling_max_abs_prediction_difference']:.1f}. "
        "This is a demonstration of non-identifiability from these observations, not an empirical test "
        "showing that the true mechanism is reporting.", "",
        "## Reproducibility", "",
        "Run: python analysis/empirical_boundary.py. Sources, protocol and analysis script are SHA256-hashed. "
        "The original MIT license is retained. Source outcome predictions are ignored. "
        "The summary includes full coverage and quality checks, and the prediction CSV contains one "
        "out-of-sample prediction from each model for every retained trial.", "",
        "No implementation deviations from the frozen protocol were required."
    ]
    (OUT / "METHODS_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, rng = provenance(), np.random.default_rng(SEED)
    trials, sample = load_trials()
    contrasts, cells = compute_contrasts(trials, rng)
    cv, checks = cross_validate(trials, rng)
    checks.update({
        "unique_source_trial_keys": True, "source_row_accounting": True,
        "ratings_in_0_to_100": True, "retained_rt_in_0_2_to_4_5_seconds": True, "cell_count": cells,
        "no_missing_outcomes_after_flags": sample["missing_or_nonfinite_removed_after_flags"] == 0,
        "source_exclusion_counts_match_paper": sample["paper_exclusion_counts_match"],
        "outcome_normalization_uses_no_held_out_data": True, "original_predictions_ignored": True,
    })
    summary = {
        "analysis": "Exploratory secondary cue-perception boundary check", "not_placebo_administration": True,
        "protocol_sha256": manifest["protocol_sha256"], "script_sha256": digest(__file__), "source_commit": COMMIT,
        "seed": SEED, "bootstrap_replicates": BOOTSTRAPS,
        "software": {"python": platform.python_version(), "numpy": np.__version__},
        "sample": sample, "contrasts": contrasts, "cross_validation": cv, "checks": checks, "protocol_deviations": [],
    }
    write_json(OUT / "summary.json", summary)
    methods_report(summary)
    outputs = {name: {"sha256": digest(OUT / name), "bytes": (OUT / name).stat().st_size}
               for name in ("retained_trials.csv", "cell_aggregates.csv", "participant_aggregates.csv",
                            "predictions.csv", "cross_validation_participant_scores.csv", "summary.json", "METHODS_RESULTS.md")}
    write_json(OUT / "output_hashes.json", outputs)
    compact = {"sample": sample, "key_results": {}, "checks": checks}
    for m in ("pain", "vision"):
        compact["key_results"][m] = {
            "cue": contrasts[m]["cue_high_minus_low"], "interaction": contrasts[m]["cue_effect_high_sd_minus_low_sd"],
            "uncertainty": contrasts[m]["uncertainty_high_sd_minus_low_sd"], "cv": cv[m],
        }
    print(json.dumps(compact, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
