"""Replay the archived exploratory revision without overwriting its results.

This adapter was written after the original run. It changes paths only, then
compares every exported CSV and model summary with the archived outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

REVISION = Path(__file__).resolve().parent
REPOSITORY = REVISION.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_frozen_path(label):
    """Map preserved original relative provenance labels to repository paths."""
    prefix = 'submission_package_2026-10-06/'
    if label.startswith(prefix):
        return REPOSITORY / label[len(prefix):]
    if label == 'perception_submission_2026-10-16/02_analysis/REVISION_ANALYSIS_PLAN.md':
        return REVISION / 'REVISION_ANALYSIS_PLAN.md'
    raise ValueError('Unknown frozen input label: ' + label)


def verify_frozen_inputs(freeze):
    for entry in freeze['files']:
        path = resolve_frozen_path(entry['path'])
        if digest(path) != entry['sha256']:
            raise AssertionError('Frozen input differs: ' + entry['path'])


def compare_csv(reference, replay):
    def read(path):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            return reader.fieldnames, list(reader)
    fields_a, rows_a = read(reference)
    fields_b, rows_b = read(replay)
    assert fields_a == fields_b and len(rows_a) == len(rows_b), reference.name
    largest = 0.0
    for row_a, row_b in zip(rows_a, rows_b):
        for key in fields_a:
            a, b = row_a[key], row_b[key]
            if a == b:
                continue
            try:
                x, y = float(a), float(b)
            except ValueError:
                raise AssertionError((reference.name, key, a, b)) from None
            assert math.isclose(x, y, rel_tol=1e-11, abs_tol=1e-9), (reference.name, key, x, y)
            largest = max(largest, abs(x-y))
    return {'rows': len(rows_a), 'max_absolute_numeric_difference': largest}


def compare_nested(reference, replay):
    if isinstance(reference, dict):
        assert reference.keys() == replay.keys()
        return max((compare_nested(reference[k], replay[k]) for k in reference), default=0.0)
    if isinstance(reference, (list, tuple)):
        assert len(reference) == len(replay)
        return max((compare_nested(a, b) for a, b in zip(reference, replay)), default=0.0)
    if isinstance(reference, (int, float)) and not isinstance(reference, bool):
        assert math.isclose(reference, replay, rel_tol=1e-11, abs_tol=1e-9)
        return abs(reference-replay)
    assert reference == replay
    return 0.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=REVISION / 'replay')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == REVISION or output in REVISION.parents or output == REPOSITORY:
        raise ValueError('Use a separate empty replay directory.')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Replay directory is not empty; choose a new --output-dir.')
    provenance = json.loads((REVISION / 'portability_provenance.json').read_text(encoding='utf-8'))
    archived_script = REVISION / 'run_mean_only_ablation_original.py'
    assert digest(archived_script) == provenance['original_script_sha256']
    freeze = json.loads((REVISION / 'plan_freeze.json').read_text(encoding='utf-8'))
    verify_frozen_inputs(freeze)
    output.mkdir(parents=True, exist_ok=True)
    for name in ('REVISION_ANALYSIS_PLAN.md', 'plan_freeze.json'):
        shutil.copyfile(REVISION / name, output / name)

    spec = importlib.util.spec_from_file_location('archived_mean_only_analysis', archived_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = output
    module.ROOT = REPOSITORY
    module.SOURCE = REPOSITORY / '05_reproducibility/analysis_run'
    module.DATA = module.SOURCE / 'data/empirical'
    module.OUT = output / 'results'
    module.FIG = output / 'figures'
    module.frozen_inputs_ok = verify_frozen_inputs
    module.main()

    comparisons = {}
    for reference in sorted((REVISION / 'results').glob('*.csv')):
        comparisons['results/' + reference.name] = compare_csv(reference, output / 'results' / reference.name)
    for reference in sorted((REVISION / 'figures').glob('*.csv')):
        comparisons['figures/' + reference.name] = compare_csv(reference, output / 'figures' / reference.name)
    reference_summary = json.loads((REVISION / 'results/summary.json').read_text(encoding='utf-8'))
    replay_summary = json.loads((output / 'results/summary.json').read_text(encoding='utf-8'))
    max_summary_diff = compare_nested(reference_summary['modalities'], replay_summary['modalities'])
    report = {
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'all_numeric_comparisons_passed': True,
        'absolute_tolerance': 1e-9,
        'relative_tolerance': 1e-11,
        'csv_comparisons': comparisons,
        'max_summary_numeric_difference': max_summary_diff,
        'original_scientific_script_unchanged': True,
        'archived_results_not_overwritten': True,
        'scope': 'Computational replay; not independent human scientific validation. Figure byte hashes may change with metadata or platform.'
    }
    (output / 'portable_replay_validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'portable_replay_passed': True, 'csv_files_compared': len(comparisons), 'max_summary_numeric_difference': max_summary_diff}))


if __name__ == '__main__':
    main()
