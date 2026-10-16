"""One frozen exploratory mean-only ablation; preserve all original data and outputs.

Run with the bundled Python; ECNP_EXTRA_PYTHONPATH may point to the existing
work/manuscript_python_deps directory. All generated files stay beside this script.
"""
from __future__ import annotations
import ast, csv, hashlib, itertools, json, math, os, platform, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

if os.environ.get('ECNP_EXTRA_PYTHONPATH'):
    sys.path.append(os.environ['ECNP_EXTRA_PYTHONPATH'])
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'submission_package_2026-10-06/05_reproducibility/analysis_run'
DATA = SOURCE / 'data/empirical'
OUT = HERE / 'results'
FIG = HERE / 'figures'
MODELS = ('sensory_only', 'cue_mean_only', 'additive_cue', 'cue_x_uncertainty')
NCOL = (4, 5, 8, 9)
LABELS = ('M0: Stimulus + time', 'M1: + Cue mean', 'M2: + SD + skewness', 'M3: + Mean x SD')
PAIRS = list(itertools.combinations(MODELS, 2))
SEED, NBOOT = 20261016, 10000

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p, obj): p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8')
def read_csv(p):
    with p.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def write_csv(p, rows):
    with p.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def ci(a): return [float(v) for v in np.quantile(a, [0.025, .975])]
def frozen_inputs_ok(freeze):
    for entry in freeze['files']:
        assert sha(ROOT / entry['path']) == entry['sha256'], 'Frozen input changed: ' + entry['path']

def design(rows, transform=None):
    bt = np.asarray([[r['block'], r['trial_within_modality']] for r in rows], float)
    if transform is None:
        center, scale = bt.mean(axis=0), bt.std(axis=0)
        scale[scale == 0] = 1.
        transform = center, scale
    center, scale = transform
    z = (bt - center) / scale
    stimulus = np.array([2 * r['stim_level'] - 3 for r in rows], float)
    cue = np.array([1 if r['cue_mean'] > .5 else -1 for r in rows], float)
    sd = np.array([1 if r['cue_std'] > .1 else -1 for r in rows], float)
    neg = np.array([r['cue_sk'] < 0 for r in rows], float)
    pos = np.array([r['cue_sk'] > 0 for r in rows], float)
    return np.column_stack((np.ones(len(rows)), stimulus, z, cue, sd, neg, pos, cue * sd)), transform

def main():
    started = datetime.now(timezone.utc).isoformat()
    freeze = json.loads((HERE / 'plan_freeze.json').read_text())
    frozen_inputs_ok(freeze)
    assert freeze['frozen_at_utc'] < started
    assert not (OUT / 'summary.json').exists(), 'Existing completed run preserved; use a separately documented run directory.'
    OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    # Compile only the frozen original design function, without executing its driver.
    tree = ast.parse((SOURCE / 'analysis/empirical_boundary.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'design')
    env = {'np': np}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<frozen original design>', 'exec'), env)
    source_design = env['design']
    raw = read_csv(DATA / 'retained_trials.csv')
    intcols = {'source_row', 'block', 'trial_num', 'trial_within_modality', 'stim_level', 'cue_sk'}
    trials = [{k: (v if k in ('participant', 'modality') else int(v) if k in intcols else float(v)) for k,v in r.items()} for r in raw]
    assert len(trials) == 6035 and len({r['source_row'] for r in trials}) == 6035
    archived = {int(r['source_row']): r for r in read_csv(DATA / 'predictions.csv')}
    old_summary = json.loads((DATA / 'summary.json').read_text())['cross_validation']
    fold_rows, pred_rows, coef_rows, gain_rows = [], [], [], []
    model_rows, comp_rows, distribution_rows = [], [], []
    validation = {'all_frozen_inputs_unchanged_before_run': True, 'unique_source_rows': 6035,
                  'disjoint_participant_folds': 0, 'fit_count': 0, 'max_original_prediction_difference': 0.,
                  'max_qr_vs_lstsq_prediction_difference': 0., 'max_weight_total_deviation': 0.,
                  'max_original_rmse_mae_difference': 0., 'full_rank_all_models': True,
                  'nested_training_weighted_sse_nonincreasing': True, 'source_design_exact_match': True}
    summary = {'analysis': 'Post-original-results exploratory cue-mean-only ablation',
               'started_at_utc': started, 'plan_frozen_at_utc': freeze['frozen_at_utc'],
               'plan_sha256': sha(HERE / 'REVISION_ANALYSIS_PLAN.md'), 'script_sha256': sha(Path(__file__)),
               'seed': SEED, 'bootstrap_replicates': NBOOT,
               'interval_interpretation': 'Descriptive 95% percentile intervals conditional on fixed fitted LOPO scores; no refitting; training-fold dependence and model-fitting uncertainty not fully represented; not independent-population confidence intervals.',
               'software': {'python': platform.python_version(), 'numpy': np.__version__, 'matplotlib': matplotlib.__version__},
               'source_commit': '84dc29cdaefcf78de489e990419a8a398419cb6d', 'modalities': {}}
    rng = np.random.default_rng(SEED)
    for modality, expected_n in (('pain', 3005), ('vision', 3030)):
        data = [r for r in trials if r['modality'] == modality]
        participants = sorted({r['participant'] for r in data})
        assert len(data) == expected_n and len(participants) == 45
        scores = {m: {} for m in MODELS}
        for person in participants:
            train = [r for r in data if r['participant'] != person]
            test = [r for r in data if r['participant'] == person]
            assert person not in {r['participant'] for r in train}
            validation['disjoint_participant_folds'] += 1
            xtrain, trans = design(train); xtest, _ = design(test, trans)
            original_x, original_trans = source_design(train)
            original_test, _ = source_design(test, original_trans)
            assert np.array_equal(xtrain, original_x) and np.array_equal(xtest, original_test)
            yt, yv = np.array([r['rating'] for r in train]), np.array([r['rating'] for r in test])
            counts = Counter(r['participant'] for r in train)
            weights = np.array([1. / counts[r['participant']] for r in train]); sw = np.sqrt(weights)
            for p in counts:
                dev = abs(float(sum(weights[j] for j,r in enumerate(train) if r['participant'] == p)) - 1.)
                validation['max_weight_total_deviation'] = max(validation['max_weight_total_deviation'], dev)
                assert dev < 1e-12
            preds, previous_sse = {}, None
            for model, ncol in zip(MODELS, NCOL):
                a, b = xtrain[:, :ncol] * sw[:, None], yt * sw
                beta, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
                assert rank == ncol
                pred = xtest[:, :ncol] @ beta
                q, rr = np.linalg.qr(a, mode='reduced')
                beta_qr = np.linalg.solve(rr, q.T @ b)
                qr_diff = float(np.max(np.abs(pred - xtest[:, :ncol] @ beta_qr)))
                validation['max_qr_vs_lstsq_prediction_difference'] = max(validation['max_qr_vs_lstsq_prediction_difference'], qr_diff)
                assert qr_diff < 1e-9
                sse = float(np.sum((a @ beta - b)**2))
                assert previous_sse is None or sse <= previous_sse + 1e-7
                previous_sse = sse
                assert np.isfinite(pred).all()
                mse, mae = float(np.mean((yv-pred)**2)), float(np.mean(abs(yv-pred)))
                scores[model][person] = (mse, mae); preds[model] = pred
                row = {'participant':person, 'modality':modality, 'model':model, 'test_trials':len(test),
                       'training_participants':44, 'training_trials':len(train), 'mse':mse, 'mae':mae,
                       'individual_rmse':math.sqrt(mse), 'block_train_mean':float(trans[0][0]),
                       'trial_train_mean':float(trans[0][1]), 'block_train_sd':float(trans[1][0]),
                       'trial_train_sd':float(trans[1][1]), 'weighted_training_sse':sse}
                fold_rows.append(row)
                for j, val in enumerate(beta):
                    coef_rows.append({'participant_held_out':person, 'modality':modality, 'model':model,
                                      'coefficient_index':j, 'coefficient':float(val)})
                validation['fit_count'] += 1
                if model != 'cue_mean_only':
                    old = np.array([float(archived[r['source_row']][model+'_prediction']) for r in test])
                    diff = float(np.max(abs(pred-old)))
                    validation['max_original_prediction_difference'] = max(validation['max_original_prediction_difference'], diff)
                    assert diff < 1e-9
            for j, r in enumerate(test):
                pred_rows.append(dict(r, **{m+'_prediction':float(preds[m][j]) for m in MODELS}))
        draws = rng.integers(0, 45, size=(NBOOT,45))
        arrays = {}; mod_summary = {'n_participants':45, 'n_trials':len(data), 'models':{}, 'comparisons':{}}
        for m in MODELS:
            mse = np.array([scores[m][p][0] for p in participants]); mae = np.array([scores[m][p][1] for p in participants])
            rb = np.sqrt(mse[draws].mean(axis=1)); ab = mae[draws].mean(axis=1)
            arrays[m] = mse, mae, rb, ab
            entry = {'rmse':float(np.sqrt(mse.mean())), 'mae':float(mae.mean()),
                     'rmse_conditional_low':ci(rb)[0], 'rmse_conditional_high':ci(rb)[1],
                     'mae_conditional_low':ci(ab)[0], 'mae_conditional_high':ci(ab)[1]}
            mod_summary['models'][m] = entry
            model_rows.append({'modality':modality,'model':m,'coefficients':NCOL[MODELS.index(m)], **entry})
            if m != 'cue_mean_only':
                for key, old_key in (('rmse','equal_participant_rmse'),('mae','equal_participant_mae')):
                    diff = abs(entry[key]-old_summary[modality]['models'][m][old_key])
                    validation['max_original_rmse_mae_difference'] = max(validation['max_original_rmse_mae_difference'], diff)
                    assert diff < 1e-10
        for base, cand in PAIRS:
            a,b = arrays[base],arrays[cand]
            ri, ai = ci(a[2]-b[2]),ci(a[3]-b[3])
            name = base+'_minus_'+cand
            entry = {'rmse_improvement':float(np.sqrt(a[0].mean())-np.sqrt(b[0].mean())),
                     'rmse_conditional_low':ri[0], 'rmse_conditional_high':ri[1],
                     'mae_improvement':float(a[1].mean()-b[1].mean()),
                     'mae_conditional_low':ai[0], 'mae_conditional_high':ai[1],
                     'participants_lower_mse':int(np.sum(b[0]<a[0])),
                     'participants_equal_mse':int(np.sum(b[0]==a[0])), 'participants_higher_mse':int(np.sum(b[0]>a[0]))}
            mod_summary['comparisons'][name] = entry
            comp_rows.append({'modality':modality,'baseline':base,'candidate':cand,**entry})
            individual_rmse = np.sqrt(a[0])-np.sqrt(b[0])
            for idx,p in enumerate(participants):
                gain_rows.append({'modality':modality,'participant':p,'baseline':base,'candidate':cand,
                                  'mse_improvement':float(a[0][idx]-b[0][idx]), 'mae_improvement':float(a[1][idx]-b[1][idx]),
                                  'individual_rmse_improvement':float(individual_rmse[idx])})
            for metric, values in (('mse_improvement',a[0]-b[0]),('mae_improvement',a[1]-b[1]),('individual_rmse_improvement',individual_rmse)):
                distribution_rows.append({'modality':modality,'baseline':base,'candidate':cand,'metric':metric,
                                          'minimum':float(values.min()),'q25':float(np.quantile(values,.25)),
                                          'median':float(np.median(values)),'q75':float(np.quantile(values,.75)),
                                          'maximum':float(values.max()),'n_participants':45})
        summary['modalities'][modality] = mod_summary
    pred_rows.sort(key=lambda r:r['source_row'])
    for name, rows in (('predictions',pred_rows),('fold_metrics',fold_rows),('fold_coefficients',coef_rows),
                       ('model_metrics',model_rows),('pairwise_comparisons',comp_rows),
                       ('participant_gains',gain_rows),('participant_gain_distribution_summary',distribution_rows)):
        write_csv(OUT/(name+'.csv'), rows)
    # Independent metric reconstruction from the written output, using math.fsum.
    reloaded = read_csv(OUT/'predictions.csv'); grouped = defaultdict(list)
    for r in reloaded: grouped[(r['modality'],r['participant'])].append(r)
    max_metric_diff = 0.
    for modality in ('pain','vision'):
        for model in MODELS:
            ms,ma = [],[]
            for (mod,p), rows in sorted(grouped.items()):
                if mod != modality: continue
                errors = [float(r['rating'])-float(r[model+'_prediction']) for r in rows]
                ms.append(math.fsum(e*e for e in errors)/len(errors)); ma.append(math.fsum(abs(e) for e in errors)/len(errors))
            target = summary['modalities'][modality]['models'][model]
            d = max(abs(math.sqrt(math.fsum(ms)/len(ms))-target['rmse']),abs(math.fsum(ma)/len(ma)-target['mae']))
            max_metric_diff = max(max_metric_diff,d); assert d < 1e-10
    validation['max_standard_library_metric_difference'] = max_metric_diff
    validation['output_rows'] = {p.stem:len(read_csv(p)) for p in OUT.glob('*.csv')}
    frozen_inputs_ok(freeze); validation['all_frozen_inputs_unchanged_after_run'] = True
    validation['plan_preceded_new_run'] = True
    validation['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    write_json(OUT/'summary.json',summary); write_json(OUT/'validation.json',validation)
    make_figures(model_rows,comp_rows,gain_rows)
    report(summary)
    manifest = [{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='analysis_file_manifest.json']
    write_json(HERE/'analysis_file_manifest.json',manifest)
    print(json.dumps({'summary':summary['modalities'],'validation':validation},indent=2))

def save(fig, name):
    fig.savefig(FIG/(name+'.pdf'), bbox_inches='tight')
    fig.savefig(FIG/(name+'.svg'), bbox_inches='tight')
    fig.savefig(FIG/(name+'.png'), dpi=300, bbox_inches='tight')
    fig.savefig(FIG/(name+'.tiff'), dpi=600, bbox_inches='tight',pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)

def make_figures(models, comparisons, gains):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
                         'axes.labelcolor':'#20262E','xtick.color':'#20262E','ytick.color':'#20262E'})
    colors = {'pain':'#176C9C','vision':'#A85B22'}
    fig,axs=plt.subplots(1,2,figsize=(10,3.8),sharey=True)
    for ax,mod,letter in zip(axs,('pain','vision'),('A','B')):
        rs=[r for r in models if r['modality']==mod]
        for j,r in enumerate(rs):
            ax.plot([r['rmse_conditional_low'],r['rmse_conditional_high']],[j,j],color=colors[mod],lw=1.4)
            ax.scatter(r['rmse'],j,color=colors[mod],marker='o' if j!=1 else 'D',s=42,zorder=3)
            ax.annotate(f"{r['rmse']:.4f}",(r['rmse'],j),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
        ax.set_yticks(range(4),LABELS);ax.set_ylim(3.5,-.7);ax.set_xlim(0,30)
        ax.set_xlabel('Participant-weighted RMSE (rating points)')
        ax.set_title(letter+'  '+mod.capitalize(),loc='left',fontweight='bold')
        ax.grid(axis='x',alpha=.18)
    fig.tight_layout();save(fig,'figure_R1_all_model_rmse')
    pairlabels=[f'M{MODELS.index(a)} to M{MODELS.index(b)}' for a,b in PAIRS]
    fig,axs=plt.subplots(1,2,figsize=(10,4.6),sharex=True,sharey=True)
    for ax,mod,letter in zip(axs,('pain','vision'),('A','B')):
        rs=[r for r in comparisons if r['modality']==mod]
        for j,r in enumerate(rs):
            focal=(r['baseline'],r['candidate']) in [(MODELS[0],MODELS[1]),(MODELS[1],MODELS[2])]
            color=colors[mod] if focal else '#687581'
            ax.plot([r['rmse_conditional_low'],r['rmse_conditional_high']],[j,j],color=color,lw=1.5)
            ax.scatter(r['rmse_improvement'],j,color=color,s=40,marker='D' if focal else 'o',zorder=3)
        ax.axvline(0,color='#333333',lw=.9,ls='--');ax.set_yticks(range(6),pairlabels);ax.set_ylim(5.5,-.6)
        ax.set_xlabel('RMSE improvement (rating points)');ax.set_title(letter+'  '+mod.capitalize(),loc='left',fontweight='bold')
        ax.grid(axis='x',alpha=.18)
    fig.tight_layout();save(fig,'figure_R2_all_paired_rmse_differences')
    consecutive=list(zip(MODELS[:-1],MODELS[1:]))
    fig,axs=plt.subplots(1,2,figsize=(10,4.8),sharey=True)
    for ax,mod,letter in zip(axs,('pain','vision'),('A','B')):
        for j,(a,b) in enumerate(consecutive):
            vals=sorted(r['individual_rmse_improvement'] for r in gains if r['modality']==mod and r['baseline']==a and r['candidate']==b)
            offsets=np.linspace(-.22,.22,len(vals))
            ax.scatter(j+offsets,vals,s=18,facecolors='none',edgecolors=colors[mod],linewidths=.8)
            ax.plot([j-.28,j+.28],[np.median(vals)]*2,color='#20262E',lw=2)
        ax.axhline(0,color='#333333',lw=.9,ls='--');ax.set_xticks(range(3),('M0 to M1','M1 to M2','M2 to M3'))
        ax.set_title(letter+'  '+mod.capitalize(),loc='left',fontweight='bold');ax.grid(axis='y',alpha=.18)
        ax.set_xlabel('Consecutive nested-model comparison')
    axs[0].set_ylabel('Individual RMSE improvement (rating points)')
    fig.tight_layout();save(fig,'figure_R3_participant_gain_distribution')
    write_csv(FIG/'figure_R1_data.csv',models);write_csv(FIG/'figure_R2_data.csv',comparisons)
    write_csv(FIG/'figure_R3_data.csv',[r for r in gains if (r['baseline'],r['candidate']) in consecutive])
    (FIG/'captions.md').write_text('''# Revision figure captions

Figure R1. All four fixed models, evaluated with 45 leave-one-participant-out folds per modality (pain: 3,005 trials; vision: 3,030 trials). Points show equal-participant RMSE, with numerical values labelled; lines show descriptive 95% percentile intervals conditional on the fitted predictions. M0 includes stimulus and temporal variables; M1 adds cue mean; M2 adds cue SD and skewness indicators; M3 adds the cue-mean-by-SD interaction. The mean-only M1 model is the new exploratory revision. Lower RMSE is better. A: pain; B: vision. Both panels use the same 0-30 axis.

Figure R2. All six paired model differences. Positive values favor the second model. Lines are paired descriptive 95% percentile intervals from 10,000 resamples of the 45 fixed participant error scores; no models were refitted. Diamonds distinguish the two focal new comparisons, M0 to M1 and M1 to M2, from contextual comparisons; no comparison is omitted. These conditional intervals do not fully represent model-fitting uncertainty or training-fold dependence and are not independent-population confidence intervals. A: pain; B: vision; a shared difference axis is used.

Figure R3. Individual participant RMSE differences for the three consecutive model increments. Every circle is one of 45 held-out participants; horizontal offsets are a deterministic display arrangement only. Short black lines indicate medians, not uncertainty intervals. Positive values indicate lower RMSE for the larger model. Individual RMSE differences are distinct from the aggregate participant-weighted RMSE difference in Figure R2. Both modalities use the same vertical scale. A: pain; B: vision. All six comparison distributions are available in participant_gains.csv.
''',encoding='utf-8')

def report(s):
    lines=['# Cue-mean-only ablation: exploratory revision results','',
           'This analysis was planned after the original results were known and before the new mean-only model was run. It is not preregistered. Original observations, exclusions, outcome definitions, and original model specifications were preserved. Exactly one model was added.','',
           '## Methods for manuscript adaptation','',
           'A post-original-results exploratory ablation inserted a cue-mean-only model between the stimulus/time baseline and the full additive cue model. The new model comprised an intercept, stimulus intensity, training-standardised block and trial, and cue mean (five coefficients). It used the same participant-weighted least-squares fitting and 45 leave-one-participant-out folds as the original models. All four models and all six pairwise comparisons were reported separately for pain and vision. Positive improvement denotes lower error for the larger model. Descriptive percentile intervals used 10,000 paired resamples of fixed participant error scores (seed 20261016), without refitting.','',
           '## All model results','',
           '| Modality | Model | RMSE | MAE |','|---|---|---:|---:|']
    for mod in ('pain','vision'):
        for m in MODELS:
            r=s['modalities'][mod]['models'][m]
            lines.append(f"| {mod} | {m} | {r['rmse']:.6f} | {r['mae']:.6f} |")
    lines += ['','## Focal new comparisons','']
    for mod in ('pain','vision'):
        for a,b in ((MODELS[0],MODELS[1]),(MODELS[1],MODELS[2])):
            r=s['modalities'][mod]['comparisons'][a+'_minus_'+b]
            lines.append(f"For {mod}, {a} to {b}: RMSE improvement {r['rmse_improvement']:.6f} rating points (descriptive conditional 95% interval {r['rmse_conditional_low']:.6f} to {r['rmse_conditional_high']:.6f}); MAE improvement {r['mae_improvement']:.6f} ({r['mae_conditional_low']:.6f} to {r['mae_conditional_high']:.6f}). MSE was lower for {r['participants_lower_mse']} of 45 participants, equal for {r['participants_equal_mse']}, and higher for {r['participants_higher_mse']}.")
            lines.append('')
    lines += ['## Interpretation boundaries','',
              'The mean-only comparison separates the joint contribution of mean, SD, and skewness into two prespecified revision increments; it is not a new independent sample. Adding SD and skewness jointly does not identify either variable\'s individual contribution. Absence of a meaningful gain for these fixed additive features does not establish equivalence or absence of uncertainty effects under other models, tasks, or mechanisms. An interval spanning zero is not an equivalence test. Conversely, an interval excluding zero is not independent-cohort evidence. Participant gain distributions and all pairwise comparisons must accompany aggregate results.','',
              'The fixed-score bootstrap conditions on previously fitted LOPO predictions. Training sets overlap across folds, and the procedure does not propagate the full learning process. Intervals are descriptive and conditional, without p-values or multiplicity-adjusted inference. They must not be presented as proof of clinical usefulness, external validity, or mechanism. The original interval files remain unchanged; the revision uses a new frozen seed and therefore may differ slightly in conditional bounds.','',
              'Computational checks establish numerical agreement of implementations, not independent human scientific validation. The source investigators retain attribution for the experiment and established cue effects.']
    (HERE/'RESULTS_AND_METHODS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__ == '__main__': main()
