# Data dictionary

The analysis uses the cued-perception task only. Ratings and source data are attributable to the original investigators. All participant labels below are anonymised public dataset codes.

## Retained-trial CSV

`analysis_run/data/empirical/retained_trials.csv` contains 6,035 retained observations, one row per trial. No outcome was imputed.

| Field | Meaning and units |
|---|---|
| `source_row` | Source CSV row number including the header as row 1; first data row is 2 |
| `participant` | Public participant code such as sub-01; 45 distinct participants |
| `modality` | pain or vision |
| `block` | Original task block; training-only centring/scaling in the predictive models |
| `trial_num` | Source trial number within block |
| `trial_within_modality` | Within-modality trial position, 1–12; subtract 12 from source trial numbers above 12 |
| `stim_level` | Two-level stimulus code, 1 or 2; fixed −1/+1 coding in model matrices |
| `stim_value` | Physical source stimulus value; pain 47/48 °C, vision 50/60 percent luminance contrast |
| `cue_mean` | Source fractional cue mean, 0.3/0.7; displayed rating means 30/70 |
| `cue_std` | Source fractional cue SD, 0.05/0.125; displayed rating SD 5/12.5 |
| `cue_sk` | Cue skewness −1, 0 or +1; symmetric reference and two indicator variables in prediction |
| `rating` | Observed pain or visual rating on the source 0–100 scale; outcome |
| `RT` | Rating response time in seconds; retained for audit, not used as a model predictor |

Source technical flags remove 211 trials, followed by 234 additional response-time exclusions. The 337 response-time flags include 103 overlapping technical exclusions. The retained CSV does not include excluded observations; they remain available in the preserved source file. Source-supplied `predicted_expect` and `vas_mean` are not model predictors.

## Derived outputs

| File | Contents |
|---|---|
| `cell_aggregates.csv` | Participant × modality × stimulus × cue mean × cue SD × skewness cell summaries |
| `participant_aggregates.csv` | Participant-level matched contrasts, available-pair counts and coverage |
| `predictions.csv` | Observed rating and all three held-out predictions for every retained source row |
| `cross_validation_participant_scores.csv` | Per-person error scores used in equal-participant summaries and paired conditional bootstraps |
| `summary.json` | Full primary descriptive, matched-contrast and prediction results |
| `coverage_sensitivity.json` | Main and interaction contrasts for 43 complete-coverage participants per modality |

Models are named `sensory_only`, `additive_cue` and `cue_x_uncertainty`. The first includes stimulus and temporal variables; the second adds cue mean, cue SD and skewness indicators; the third adds cue mean × SD. The label sensory_only does not mean that temporal variables are absent.

In supplementary tables, positive `rmse_improvement` means lower prediction error for the larger model. RMSE is the square root of mean participant MSE, not mean participant RMSE. Coverage sensitivity subsets differ by modality and share 42 people. Matched-contrast intervals are exploratory percentile intervals; predictive-performance intervals are conditional on fixed held-out scores. No multiplicity adjustment was applied.
