# Exploratory empirical boundary-check protocol

Frozen before outcome calculations: 2026-09-03 22:02:48 UTC.
Status: exploratory secondary analysis; not a preregistration. The source article's published findings and methods were already known when this protocol was written. The source CSV had been downloaded and its header inspected; no outcome summaries or model fits had been computed.

## Scope and source

Use only the cued-perception ratings from Botvinik-Nezer, Geuter, Lindquist and Wager (2025), *Expectation generation and its effect on subsequent pain and visual perception*, DOI 10.1371/journal.pcbi.1013053. The study manipulated social distribution cues before thermal pain and visual-contrast stimuli. It did not administer placebo treatment. This analysis cannot validate placebo efficacy, a brain-body network or any peripheral pathway.

Frozen source: https://github.com/rotemb9/PPRI-paper/tree/v2.0.0
Commit: 84dc29cdaefcf78de489e990419a8a398419cb6d.
Use `data_for_analysis/processed_data/task-expectpercept_all_subjs_with_pred_and_exclusions.csv` and original `analysis/behavioral_analysis.R`. Retain the upstream MIT licence. Do not download demographics, questionnaires, fMRI or stimulus-response/expectation-task data. Ignore the source's fitted prediction columns. Record SHA256 hashes and retrieval time.

## Exclusions and coding

Follow original R code lines 216–249: first remove `exclude_tech_issues`, then `exclude_RT`. Keep all participants remaining in this file; no outcome-dependent participant exclusion, outlier trimming or winsorization. Check finite raw ratings and required covariates, count any remaining missing rows explicitly. The paper reports 6480 trials, 211 technical exclusions and 234 additional response-time exclusions; verify against the released file without forcing counts to match.

Analyze pain and vision separately in raw 0–100 rating units. Reproduce stimulus level and cue mean/variance coding (-1 low, +1 high), cue skewness (negative/none/positive; none reference), block number and within-modality trial number (subtract 12 when source `trial_num>12`). Cue mean threshold .5 and cue SD threshold .1 follow original code. Cue standard deviation is the manipulation of uncertainty; high precision corresponds to low SD. No direct comparison of magnitude between pain and vision is interpreted as a difference on a common perceptual scale.

## Descriptive estimands and uncertainty

Within each participant and modality, compute mean ratings in every stimulus × cue mean × cue SD × skewness cell. Estimate the high-minus-low cue-mean contrast using matched cells, averaging equally across stimulus, SD and skewness. Also output contrasts separately by stimulus and SD. For the precision interaction estimate, within each stimulus × skewness pair compute cue contrast at high SD minus cue contrast at low SD, then average; negative values mean stronger assimilation under more precise cues. For the uncertainty main effect match high versus low SD within stimulus × cue mean × skewness.

If a required cell is absent, omit that specific matched contrast, count it and report coverage; do not impute. Participants without any eligible contrasts for an estimand remain in other analyses. Compute group means with equal participant weight. Use participant resampling (10,000 replicates, NumPy random seed 20260904), percentile 95% bootstrap confidence intervals. These are exploratory descriptive intervals, without multiplicity correction. No significance-driven follow-up or alternative bootstrap choices. Include standard errors and medians as descriptive checks.

## Prespecified predictive comparison

For each modality perform leave-one-participant-out cross-validation with all trials from the held-out participant excluded from training. Fit three fixed linear models by weighted least squares:

- Sensory-only: intercept + stimulus + block + within-modality trial.
- Additive cue: sensory-only + cue mean + cue SD + negative-skew indicator + positive-skew indicator.
- Cue × uncertainty: additive cue + cue mean × cue SD.

Within each training fold, center and scale block and trial using training rows only. Binary/categorical coding is fixed by the design. Do not standardize outcomes or use any held-out rating for normalization, model fitting, hyperparameter choice or participant intercept estimation. Weight each training participant equally (each trial weight 1 divided by that participant's available trial count). No hyperparameter tuning, neural-network fitting or selection of additional interactions.

Output every held-out prediction with anonymized public participant code, modality, block, trial, design factors and observed rating. Evaluate equal-participant RMSE (square root of average participant MSE) and equal-participant MAE. Bootstrap participant MSE/MAE summaries for paired model-performance differences with 10,000 replicates. These conditional intervals do not refit all cross-validation models and are descriptive; overlapping training sets limit a naive inferential interpretation. Report all three models regardless of which wins.

## Observational equivalence and interpretation

For ratings alone, `rating = sensory contribution + context contribution + error` gives identical predictions whether the context contribution is assigned to latent perception or reporting. Demonstrate exact numerical prediction equality under this relabeling; do not claim the analysis identifies either mechanism. Favor neither narrative on rating fit alone.

This is a bounded boundary check of cue-based behavior, not independent confirmatory validation of the proposed network. In particular, report any cue-by-uncertainty interaction inconsistent with universal precision weighting and any lack of predictive improvement. No treatment recommendation, drug substitution claim or causal brain/body inference follows from these data.

## Deliverables and checks

Write `analysis/empirical_boundary.py`, frozen provenance, compact retained-variable trial CSV, cell/participant aggregates, cross-validated predictions, numeric summary JSON and generated Methods/Results markdown inside `data/empirical/`. Include Python/NumPy versions, exact seed and protocol/script hashes. Check source row accounting, unique trial keys, exclusions, design-level values, rating range, contrast coverage, finite predictions, train-test participant disjointness, and prediction count. A deterministic rerun must reproduce numeric outputs. Do not silently edit this protocol after results; document any necessary implementation deviation in the generated summary.

