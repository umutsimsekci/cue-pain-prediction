# Exploratory cue-mean-only ablation, 16 October 2026

This revision separates cue mean from the joint addition of cue standard deviation and skewness. It adds one fixed model to the original analysis of 6,035 trials from 45 participants. All four models and all six pairwise comparisons are reported for pain and vision. This was planned after the original results were known, not preregistered.

## Reproduce without overwriting archived results

From the repository root, in an isolated Python environment:

```sh
python -m pip install -r revisions/2026-10-16/requirements.txt
python revisions/2026-10-16/reproduce_revision.py
```

The default output is `revisions/2026-10-16/replay/`, which must be empty. For a later run, add `--output-dir /path/to/a/new/empty/directory`. The adapter checks every frozen input, reruns the original scientific implementation, and compares all seven result CSVs, three plotted-data CSVs and the complete model/comparison summaries with the archived revision outputs. A failed comparison raises an error. The code writes figures in PDF, SVG, PNG and TIFF formats; GitHub contains the smaller vector versions.

`run_mean_only_ablation_original.py`, the plan and the original freeze record are preserved byte-for-byte. The adapter was written after the analysis and changes only filesystem paths/output destinations. The old relative workspace labels in the freeze record are mapped to existing public-repository files; this is documented in `portability_provenance.json`. No absolute personal path is needed. The locally frozen timestamp is not a public registration timestamp. The Python version used for the original run is recorded in `results/summary.json`.

## Contents and interpretation

- `results/` contains all trial predictions, fold coefficients and error scores, model metrics, every pairwise comparison, participant gain distributions, summary and numerical checks.
- `figures/` contains all three revision figures, their source tables and captions. These are research/repository figures; final journal layouts can be provided separately.
- `RESULTS_AND_METHODS.md` records all results and their interpretation limits.
- `plan_freeze.json` and `REVISION_ANALYSIS_PLAN.md` preserve the actual local analysis plan and input hashes.

Cue mean improved aggregate RMSE by about 0.807 points for pain and 0.730 for vision. Adding SD and skewness jointly changed RMSE by about -0.009 and +0.009 points, respectively (positive means improvement). This does not establish equivalence, prove an absence of uncertainty effects, isolate the separate effects of SD and skewness, or demonstrate clinical usefulness. All intervals are descriptive, conditional on the fixed fitted participant-held-out scores; models are not refitted within the bootstrap and training folds overlap. Computational replay is not independent human scientific validation.

The original experiment and observations remain credited to Botvinik-Nezer et al. (2025), doi:10.1371/journal.pcbi.1013053. The public source files and upstream MIT notice remain under `05_reproducibility/analysis_run/data/empirical/source/`. Existing licensing terms are unchanged: the author's secondary-analysis code is publicly accessible, but no additional reuse licence is assigned. See the root `AI_USE.md` for the actual scope of assistance.
