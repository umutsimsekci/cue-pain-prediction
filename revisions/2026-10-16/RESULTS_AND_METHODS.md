# Cue-mean-only ablation: exploratory revision results

This analysis was planned after the original results were known and before the new mean-only model was run. It is not preregistered. Original observations, exclusions, outcome definitions, and original model specifications were preserved. Exactly one model was added.

## Methods for manuscript adaptation

A post-original-results exploratory ablation inserted a cue-mean-only model between the stimulus/time baseline and the full additive cue model. The new model comprised an intercept, stimulus intensity, training-standardised block and trial, and cue mean (five coefficients). It used the same participant-weighted least-squares fitting and 45 leave-one-participant-out folds as the original models. All four models and all six pairwise comparisons were reported separately for pain and vision. Positive improvement denotes lower error for the larger model. Descriptive percentile intervals used 10,000 paired resamples of fixed participant error scores (seed 20261016), without refitting.

## All model results

| Modality | Model | RMSE | MAE |
|---|---|---:|---:|
| pain | sensory_only | 22.466920 | 18.336591 |
| pain | cue_mean_only | 21.660252 | 17.257857 |
| pain | additive_cue | 21.669488 | 17.254026 |
| pain | cue_x_uncertainty | 21.672379 | 17.257453 |
| vision | sensory_only | 16.352446 | 13.361684 |
| vision | cue_mean_only | 15.622626 | 12.484998 |
| vision | additive_cue | 15.613534 | 12.481901 |
| vision | cue_x_uncertainty | 15.613002 | 12.474862 |

## Focal new comparisons

For pain, sensory_only to cue_mean_only: RMSE improvement 0.806669 rating points (descriptive conditional 95% interval 0.408064 to 1.237722); MAE improvement 1.078734 (0.703247 to 1.468713). MSE was lower for 31 of 45 participants, equal for 0, and higher for 14.

For pain, cue_mean_only to additive_cue: RMSE improvement -0.009237 rating points (descriptive conditional 95% interval -0.050629 to 0.029131); MAE improvement 0.003831 (-0.031766 to 0.036034). MSE was lower for 24 of 45 participants, equal for 0, and higher for 21.

For vision, sensory_only to cue_mean_only: RMSE improvement 0.729820 rating points (descriptive conditional 95% interval 0.375811 to 1.098254); MAE improvement 0.876686 (0.541648 to 1.202553). MSE was lower for 31 of 45 participants, equal for 0, and higher for 14.

For vision, cue_mean_only to additive_cue: RMSE improvement 0.009091 rating points (descriptive conditional 95% interval -0.011731 to 0.029096); MAE improvement 0.003097 (-0.021155 to 0.026389). MSE was lower for 29 of 45 participants, equal for 0, and higher for 16.

## Interpretation boundaries

The mean-only comparison separates the joint contribution of mean, SD, and skewness into two prespecified revision increments; it is not a new independent sample. Adding SD and skewness jointly does not identify either variable's individual contribution. Absence of a meaningful gain for these fixed additive features does not establish equivalence or absence of uncertainty effects under other models, tasks, or mechanisms. An interval spanning zero is not an equivalence test. Conversely, an interval excluding zero is not independent-cohort evidence. Participant gain distributions and all pairwise comparisons must accompany aggregate results.

The fixed-score bootstrap conditions on previously fitted LOPO predictions. Training sets overlap across folds, and the procedure does not propagate the full learning process. Intervals are descriptive and conditional, without p-values or multiplicity-adjusted inference. They must not be presented as proof of clinical usefulness, external validity, or mechanism. The original interval files remain unchanged; the revision uses a new frozen seed and therefore may differ slightly in conditional bounds.

Computational checks establish numerical agreement of implementations, not independent human scientific validation. The source investigators retain attribution for the experiment and established cue effects.
