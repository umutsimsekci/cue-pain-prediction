# Frozen revision analysis plan: cue-mean-only ablation

Status: exploratory revision analysis, specified after the original study and the original secondary-analysis results were known, but before calculating the new cue-mean-only model. This is not a preregistration or a confirmatory analysis. The local freeze record records the plan hash, UTC timestamp, and hashes of all analysis inputs. No future public deposit or timestamp is implied.

## Question and scope

Does the displayed cue distribution's standard deviation and skewness add participant-held-out predictive information beyond cue mean, stimulus intensity, and temporal variables? The original comparison added cue mean, standard deviation, and skewness jointly. This revision adds exactly one model, separating that joint comparison into two increments. It does not search alternative predictors, transformations, exclusions, random seeds, outcomes, or favorable subgroups.

Use the unchanged processed retained-trial dataset from the original secondary analysis: 45 participants, 3,005 pain trials and 3,030 visual trials (6,035 total). The upstream data are PPRI-paper v2.0.0, commit 84dc29cdaefcf78de489e990419a8a398419cb6d, accompanying Botvinik-Nezer et al. (2025), doi:10.1371/journal.pcbi.1013053. The original technical and response-time exclusions remain unchanged. No new data, participant selection, imputation, outcome normalization, or clipping will be introduced. Analyze modalities separately.

## Four fixed models

- M0, `sensory_only`: intercept, stimulus intensity, block, within-modality trial (4 coefficients).
- M1, `cue_mean_only`: M0 plus cue mean (5 coefficients; the only new model).
- M2, `additive_cue`: M1 plus cue standard deviation, negative-skew indicator, positive-skew indicator (8 coefficients; original model).
- M3, `cue_x_uncertainty`: M2 plus cue-mean-by-standard-deviation product (9 coefficients; original model retained).

Use the original coding: stimulus, mean, and standard deviation have minus-one/plus-one coding; symmetric skewness is the indicator reference. Block and within-modality trial are centered and scaled using training rows only, with population standard deviation (ddof=0). Models use weighted least squares with each training trial assigned the inverse of its participant's retained modality-specific trial count, so each training participant has total weight one.

## Validation target and outcomes

Use exactly 45 leave-one-participant-out folds per modality. Every observation of the test participant is excluded from training and preprocessing. No subject-specific test intercept, test outcome, hyperparameter tuning, or model selection is permitted. The target is raw 0-100 ratings of a held-out participant from the same experimental cohort, not clinical benefit or independent-cohort validation.

For participant i, MSE_i is the mean squared prediction error across that person's test trials, and MAE_i is the mean absolute error. Overall RMSE is sqrt(mean_i MSE_i); overall MAE is mean_i MAE_i. Each participant has equal influence. RMSE is not the mean of individual RMSE values, and trial pooling is not used. For a comparison A to B, RMSE improvement is RMSE_A minus RMSE_B and MAE improvement is MAE_A minus MAE_B; positive values favor B.

Report every model and all six pairwise comparisons in both modalities. The focal new comparisons are M0 versus M1 and M1 versus M2; original comparisons are retained as context. Report absolute RMSE and MAE, their improvements, and counts of participants with lower/equal/higher MSE. For the participant gain distribution, report MSE and MAE differences and individual RMSE differences with median, quartiles, minimum and maximum. Individual RMSE differences must not be confused with the aggregate RMSE improvement.

## Descriptive uncertainty

Use 10,000 paired bootstrap resamples of the 45 fixed participant-level scores. Set NumPy RNG seed 20261016 once; process pain then vision and use the same draws for all models within a modality. Report 2.5th and 97.5th percentile intervals, explicitly labelled descriptive and conditional on the fitted LOPO predictions. Do not refit models within this bootstrap, calculate p-values, infer equivalence, or label these intervals independent-population confidence intervals. Training-fold overlap and fitting uncertainty are not fully represented. New intervals use a new frozen seed and need not match the original script's intervals. The original interval files remain unchanged.

## Verification before reporting

Verify the plan and source hashes at run start and finish. Require all 6,035 unique source rows, 45 participants per modality, disjoint train/test participant sets, full-rank model matrices, finite predictions, and participant weights summing to one. Reproduce all three original model prediction arrays against the archived predictions (target absolute tolerance 1e-9, with actual maximum difference reported); reproduce their original aggregate RMSE and MAE. Independently reconstruct the design matrix using the source function and compare it to the revision design. Independently solve each fit using QR decomposition and compare predictions to the least-squares solution. Check nested-model training weighted SSE does not increase beyond numerical tolerance. Independently recalculate metrics from written trial predictions using Python's standard-library math/csv, not only from in-memory summary arrays.

If verification fails, investigate an implementation discrepancy without changing the frozen question, sample, models, or outcomes. Report any necessary code correction in the run record. Preserve all original files. New code and outputs remain under `perception_submission_2026-10-16/02_analysis`.

## Deliverables and interpretation

Produce reproducible code, source/plan provenance, all trial predictions, fold metrics and coefficients, model summaries, pairwise comparisons, participant gains, descriptive bootstrap intervals, validation records, and concise English comparison prose. Provide figures showing all models, incremental paired RMSE differences with conditional intervals, and participant gain distributions; export the underlying plotted CSV data. Use neutral labels and disclose descriptive conditional uncertainty in the captions. Preserve unfavorable, near-zero, or inconsistent results. No neural, causal, clinical, equivalence, or novel-method claim follows from this ablation.
