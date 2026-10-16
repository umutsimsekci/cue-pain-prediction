# Perception figure package, 16 October 2026

This folder contains the final scientific figure layouts and a portable figure-only generator. It accompanies the exploratory secondary analysis at [analysis commit 2c404a5](https://github.com/umutsimsekci/cue-pain-prediction/tree/2c404a5d5a95e0cc5befe2d93d10fa4fc3838d67). These files do not indicate journal submission or acceptance. The manuscript and private submission documents are not included.

## Included files

- `03_figures/`: three main figures, their captions, plotted values, frozen source values and plotting definitions.
- `03_figures/graphical_abstract/`: the programmatically drawn graphical abstract, its caption and values.
- `04_supplement/figures/`: three supplementary figures, captions and original numerical inputs.
- `previews/`: small renders of all seven PDFs, copied from the inspected final figure package.

Each figure is provided as vector PDF and SVG. Large raster TIFF files and duplicate full-resolution PNG/EPS exports are omitted from GitHub; the unmodified generator recreates the full export set, including true 800 dpi LZW TIFF for the main figures and graphical abstract. `03_figures/export_validation.json` preserves the checks on that complete original export set. It is not an inventory of this smaller public subset; use `public_figure_manifest.json` for the public files and hashes.

## Reproduce in a separate directory

From the repository root, in an isolated environment:

```sh
python -m pip install -r journal_formats/perception/requirements.txt
python journal_formats/perception/reproduce_figures.py
```

Python 3.12.14 was used for preparation. The replay adapter copies only the preserved figure inputs, plotting definitions and generator into an empty `journal_formats/perception/replay/` directory. Choose a different empty location with `--output-dir PATH` for another run. The adapter verifies source hashes, runs the original generator without editing it, checks the plotted CSVs and compares all seven PDF-rendered previews pixel by pixel. It never fits a statistical model or reruns a bootstrap. Generated PDF/SVG metadata can differ across runs; font/library differences can change rendering on another system, so exact plotted values and source hashes remain the primary provenance.

The generator uses the relative `03_figures` and `04_supplement/figures/source_data` layout. Old relative source labels in `source_provenance.json` document where values originally came from; they are not filesystem dependencies. No original project directory or personal path is required.

## Interpretation and attribution

The figures show fixed-model participant-held-out prediction in one existing experimental cohort. Predictive intervals are descriptive and conditional on fixed fitted LOPO scores, without model refitting; overlapping training folds and model-fitting uncertainty are not fully represented. Individual RMSE differences are distinct from the aggregate RMSE difference. The matched-contrast and coverage figures retain their original participant-bootstrap interpretation. Neither the graphical abstract nor the other figures establish causal attribution, equivalence, absence of uncertainty effects, external validity or clinical benefit.

Original experiment/data: Botvinik-Nezer et al. (2025), doi:10.1371/journal.pcbi.1013053; PPRI-paper v2.0.0, source commit `84dc29cdaefcf78de489e990419a8a398419cb6d`. Secondary analysis: Umut Şimşekçi. Figures were rendered with Python plotting libraries, not generative images. See the root AI disclosure for code and drafting assistance. Existing licence terms remain unchanged; public accessibility is not a newly assigned reuse licence.
