"""Replay the preserved figure-only generator in a separate empty directory.

No model fitting or bootstrap is performed. All source values and plotting
definitions are hash-checked; the seven PDF-rendered previews are compared.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, shutil, subprocess, sys

HERE = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=HERE/'replay')
    output = parser.parse_args().output_dir.resolve()
    if output == HERE or output in HERE.parents:
        raise ValueError('Choose a separate empty replay directory.')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Replay directory must be empty.')
    provenance = json.loads((HERE/'03_figures/source_provenance.json').read_text(encoding='utf-8'))
    sources = ['03_figures/generate_final_figures.py']
    for item in provenance['inputs']:
        rel = item['preserved_copy']
        assert sha(HERE/rel) == item['sha256'], rel
        sources.append(rel)
    expected = json.loads((HERE/'public_figure_manifest.json').read_text(encoding='utf-8'))
    for entry in expected['files']:
        assert sha(HERE/entry['path']) == entry['sha256'], entry['path']
    output.mkdir(parents=True, exist_ok=True)
    for rel in sources:
        target = output/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE/rel, target)
    run = subprocess.run([sys.executable, str(output/'03_figures/generate_final_figures.py')], capture_output=True, text=True, encoding='utf-8')
    (output/'figure_replay.log').write_text(run.stdout+'\n'+run.stderr, encoding='utf-8')
    if run.returncode:
        raise RuntimeError('Figure generation failed; see figure_replay.log')
    from PIL import Image, ImageChops
    previews = []
    for reference in sorted((HERE/'previews').glob('*_pdf_render.png')):
        actual = output/'03_figures/visual_qa'/reference.name
        with Image.open(reference) as a, Image.open(actual) as b:
            a, b = a.convert('RGB'), b.convert('RGB')
            same = a.size == b.size and ImageChops.difference(a,b).getbbox() is None
            previews.append({'name':reference.name, 'pixel_identical':same, 'pixels':list(a.size)})
            assert same, 'Rendered pixels differ: '+reference.name
    assert len(previews) == 7
    data_checks=[]
    for rel in ['03_figures/Figure1_data.csv','03_figures/Figure2_data.csv','03_figures/Figure3_data.csv','03_figures/graphical_abstract/data.csv']:
        assert sha(HERE/rel)==sha(output/rel), rel
        data_checks.append({'path':rel,'sha256_match':True})
    validation = json.loads((output/'03_figures/export_validation.json').read_text(encoding='utf-8'))
    assert validation['preserved_inputs_unchanged'] and len(validation['figures']) == 7
    report={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'all_seven_pdf_render_pixels_match':True,
            'preview_checks':previews,'plotted_data_checks':data_checks,'source_hashes_verified':True,
            'statistical_models_or_bootstraps_rerun':False,'generator_unchanged':True,
            'note':'Exact rendered-pixel equality was checked in the preparation environment. Font/library differences can change rendering on other systems; original vectors and plotted values are preserved.'}
    (output/'figure_replay_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'replay_passed':True,'figures':7,'plotted_data_files_verified':len(data_checks)}))

if __name__=='__main__':main()
