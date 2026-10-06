"""Export existing validated figures in Pain Medicine submission formats.

Run from any directory after installing the repository requirements. This script
uses make_figures.py without changing it, its inputs, or the statistical analysis.
It performs no model fitting and recalculates no statistical uncertainty.

Outputs are separate from the general figures: journal_formats/pain_medicine/.
The graphical abstract is reserve material, not an upload for the main paper.
"""

from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

from PIL import Image


PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE / "05_reproducibility/make_figures.py"
OUTPUT = PACKAGE / "journal_formats/pain_medicine"
OUTPUT.mkdir(parents=True, exist_ok=True)

INPUTS = [SOURCE]
INPUTS += list((PACKAGE / "05_reproducibility/analysis_run").rglob("*"))
INPUTS += list((PACKAGE / "03_supplementary").glob("*.csv"))
INPUTS = sorted(p for p in INPUTS if p.is_file())


def hash_inputs():
    return {
        p.relative_to(PACKAGE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in INPUTS
    }


before = hash_inputs()
code = SOURCE.read_text(encoding="utf-8")
old_paths = (
    "BASE=Path(__file__).resolve().parent;PKG=BASE.parent\n"
    "DATA=BASE/'analysis_run/data/empirical';FIG=PKG/'02_figures'"
)
new_paths = (
    "BASE=SOURCE_PACKAGE/'05_reproducibility';PKG=SOURCE_PACKAGE\n"
    "DATA=BASE/'analysis_run/data/empirical';FIG=TARGET_OUTPUT"
)
if code.count(old_paths) != 1:
    raise RuntimeError("The figure source layout changed; review this export adapter.")
code = code.replace(old_paths, new_paths)
start, end = code.index("def save("), code.index("def box(")

# Only the output/save function is adapted. All data handling and plotting
# coordinates come from the existing figure source.
save_function = '''def save(fig,stem,caption):
    import re
    reserve = stem == 'graphical_abstract'
    destination = FIG/'reserve_graphical_abstract' if reserve else FIG
    destination.mkdir(parents=True, exist_ok=True)
    removed = []
    if not reserve:
        for axis in fig.axes:
            for location in ('left', 'center', 'right'):
                title = axis.get_title(loc=location)
                if title:
                    match = re.match(r'^([A-Z])(?:\\s+|$)', title)
                    replacement = match.group(1) if match else ''
                    removed.append({'before':title,'after':replacement})
                    axis.set_title(replacement, loc=location)
    for extension in ('pdf','svg'):
        fig.savefig(destination/(stem+'.'+extension),bbox_inches='tight',pad_inches=.12)
    fig.savefig(destination/(stem+'.png'),dpi=600,bbox_inches='tight',pad_inches=.12)
    fig.savefig(destination/(stem+'_600dpi.tiff'),dpi=600,bbox_inches='tight',pad_inches=.12,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(destination/(stem+'_preview.png'),dpi=140,bbox_inches='tight',pad_inches=.12)
    role = ('reserve_only_not_for_upload' if reserve else
            'supplementary_figure_asset_include_with_legend' if stem.startswith('figure_S') else
            'main_figure')
    manifest.append({'stem':stem,'caption':caption,'directory':destination.relative_to(FIG).as_posix(),
                     'submission_role':role,
                     'formats':['PNG 600 dpi','PDF vector','SVG vector','TIFF 600 dpi LZW'],
                     'panel_title_changes':removed})
    plt.close(fig)
'''
code = code[:start] + save_function + code[end:]
namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE),
    "SOURCE_PACKAGE": PACKAGE,
    "TARGET_OUTPUT": OUTPUT,
}
exec(compile(code, str(SOURCE), "exec"), namespace)

after = hash_inputs()
if before != after:
    raise RuntimeError("An analysis input changed during figure export.")

expected = {
    "figure_1_analysis_workflow",
    "figure_2_matched_contrasts",
    "figure_3_predictive_performance",
    "figure_4_coverage_sensitivity",
    "figure_S1_data_coverage",
    "graphical_abstract",
}
if {record["stem"] for record in namespace["manifest"]} != expected:
    raise RuntimeError("The figure set differs from the expected six outputs.")

validation = []
for record in namespace["manifest"]:
    directory = OUTPUT / record["directory"]
    stem = record["stem"]
    pdf_path = directory / (stem + ".pdf")
    svg_path = directory / (stem + ".svg")
    if not pdf_path.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError(f"Invalid PDF header: {stem}")
    svg = ET.parse(svg_path)
    svg_text = " ".join(svg.getroot().itertext())
    for change in record["panel_title_changes"]:
        if change["before"] in svg_text:
            raise RuntimeError(f"Descriptive panel title remains: {stem}")
    with Image.open(directory / (stem + "_600dpi.tiff")) as raster:
        dimensions = list(raster.size)
        dpi = [float(value) for value in raster.info["dpi"]]
        if not all(abs(value - 600) < 0.01 for value in dpi):
            raise RuntimeError(f"Unexpected TIFF resolution: {stem}")
    validation.append({
        "stem": stem,
        "pdf_header_valid": True,
        "svg_xml_valid": True,
        "tiff_dimensions_px": dimensions,
        "tiff_dpi": dpi,
        "submission_role": record["submission_role"],
    })

(OUTPUT / "export_validation.json").write_text(json.dumps({
    "purpose": "Journal-format exports only; no statistical analysis rerun",
    "source_inputs_unchanged": before == after,
    "input_sha256": before,
    "panel_identifiers_preserved": True,
    "numerical_content_changed": False,
    "graphical_abstract": "reserve_only_not_for_upload",
    "figure_S1": "Include with its legend in the separate supplementary document",
    "figures": validation,
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "output": str(OUTPUT),
    "figures": len(validation),
    "inputs_unchanged": True,
}, ensure_ascii=True))
