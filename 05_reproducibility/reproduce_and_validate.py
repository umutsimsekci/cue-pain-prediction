"""Replay the frozen primary analysis and the documented coverage sensitivity.

Run from any working directory. Writes only within this submission package.
No new inferential analysis or model selection is introduced.
"""
from pathlib import Path
import csv, hashlib, json, math, subprocess, sys
import numpy as np

BASE=Path(__file__).resolve().parent
PKG=BASE.parent
RUN=BASE/'analysis_run'
OUT=RUN/'data/empirical'
VALID=PKG/'07_validation'
TABLES=PKG/'03_supplementary'

def readcsv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def savecsv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compare(a,b,path=''):
    if isinstance(a,dict):
        for k in a.keys() & b.keys():compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-10),(path,a,b)

def main():
    archived=json.loads((VALID/'prior_analysis_archive/summary.json').read_text())
    proc=subprocess.run([sys.executable,str(RUN/'analysis/empirical_boundary.py')],capture_output=True,text=True,encoding='utf-8')
    (VALID/'primary_replay.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    assert proc.returncode==0,proc.stderr
    summary=json.loads((OUT/'summary.json').read_text())
    compare(archived,summary)
    archived_hashes=json.loads((VALID/'prior_analysis_archive/output_hashes.json').read_text())
    hash_checks={name:sha(OUT/name)==info['sha256'] for name,info in archived_hashes.items()}
    # Software/provenance metadata may change on another machine. Numerical checks remain binding.
    trials=readcsv(OUT/'retained_trials.csv');pred=readcsv(OUT/'predictions.csv')
    assert len(trials)==len(pred)==6035
    assert len({r['source_row'] for r in pred})==6035
    assert {r['source_row'] for r in trials}=={r['source_row'] for r in pred}
    metrics=[]
    for modality in ('pain','vision'):
        people=sorted({r['participant'] for r in pred if r['modality']==modality})
        assert len(people)==45
        for model in ('sensory_only','additive_cue','cue_x_uncertainty'):
            mse=[];mae=[]
            for p in people:
                rows=[r for r in pred if r['modality']==modality and r['participant']==p]
                e=np.array([float(r['rating'])-float(r[model+'_prediction']) for r in rows])
                mse.append(float(np.mean(e**2)));mae.append(float(np.mean(np.abs(e))))
            rmse=float(np.sqrt(np.mean(mse)));mean_mae=float(np.mean(mae))
            expected=summary['cross_validation'][modality]['models'][model]
            assert math.isclose(rmse,expected['equal_participant_rmse'],abs_tol=1e-10)
            assert math.isclose(mean_mae,expected['equal_participant_mae'],abs_tol=1e-10)
            metrics.append({'modality':modality,'model':model,'participants':45,'rmse':rmse,'mae':mean_mae,
                            'rmse_conditional_ci_low':expected['rmse_ci95_conditional_percentile'][0],
                            'rmse_conditional_ci_high':expected['rmse_ci95_conditional_percentile'][1]})
    savecsv(TABLES/'table_S2_model_performance.csv',metrics)
    ag=readcsv(OUT/'participant_aggregates.csv');rng=np.random.default_rng(20261005)
    sensitivity=[];coverage=[]
    for modality in ('pain','vision'):
        people={r['participant'] for r in ag if r['modality']==modality and r['estimand']=='cue_high_minus_low'}
        complete={r['participant'] for r in ag if r['modality']==modality and r['estimand']=='cue_high_minus_low' and float(r['coverage'])==1}
        assert len(complete)==43
        for p in sorted(people):
            rr=[r for r in ag if r['modality']==modality and r['participant']==p and r['estimand']=='cue_high_minus_low'][0]
            coverage.append({'modality':modality,'participant':p,'retained_trials':sum(t['modality']==modality and t['participant']==p for t in trials),
                             'matched_pairs':int(rr['matched_contrasts']),'expected_pairs':12,'complete_coverage':p in complete})
        for effect in ('cue_high_minus_low','cue_effect_high_sd_minus_low_sd'):
            rows=[r for r in ag if r['modality']==modality and r['estimand']==effect and r['participant'] in complete]
            values=np.array([float(r['value']) for r in rows])
            boot=values[rng.integers(0,len(values),size=(10000,len(values)))].mean(axis=1)
            sensitivity.append({'modality':modality,'estimand':effect,'participants':43,
                                'all_45_mean':summary['contrasts'][modality][effect]['mean'],
                                'full_coverage_mean':float(values.mean()),
                                'full_coverage_exploratory_ci95':np.quantile(boot,[.025,.975]).tolist()})
    original_sensitivity=json.loads((VALID/'prior_analysis_archive/validation_and_sensitivity.json').read_text())['coverage_sensitivity']
    compare(original_sensitivity,sensitivity)
    (OUT/'coverage_sensitivity.json').write_text(json.dumps(sensitivity,indent=2)+'\n')
    savecsv(TABLES/'table_S3_participant_coverage.csv',coverage)
    contrast_rows=[]
    for m in ('pain','vision'):
        for effect,r in summary['contrasts'][m].items():
            contrast_rows.append({'modality':m,'estimand':effect,'participants':r['n_participants'],'mean':r['mean'],'median':r['median'],
                                  'ci_low':r['ci95_percentile'][0],'ci_high':r['ci95_percentile'][1],'matched_contrasts':r['matched_contrasts'],
                                  'expected_contrasts':r['expected_contrasts'],'complete_participants':r['participants_with_full_coverage']})
    savecsv(TABLES/'table_S1_all_matched_contrasts.csv',contrast_rows)
    savecsv(TABLES/'table_S4_coverage_sensitivity.csv',[{k:v for k,v in r.items() if k!='full_coverage_exploratory_ci95'} | {'ci_low':r['full_coverage_exploratory_ci95'][0],'ci_high':r['full_coverage_exploratory_ci95'][1]} for r in sensitivity])
    comparison_rows=[]
    for m in ('pain','vision'):
        for name,r in summary['cross_validation'][m]['comparisons'].items():
            comparison_rows.append({'modality':m,'comparison':name,'rmse_improvement':r['rmse_improvement'],
                                   'conditional_ci_low':r['rmse_improvement_ci95_conditional'][0],'conditional_ci_high':r['rmse_improvement_ci95_conditional'][1],
                                   'mae_improvement':r['mae_improvement'],'mae_conditional_ci_low':r['mae_improvement_ci95_conditional'][0],
                                   'mae_conditional_ci_high':r['mae_improvement_ci95_conditional'][1],
                                   'participants_with_lower_mse':r['participants_with_lower_mse']})
    savecsv(TABLES/'table_S5_paired_model_comparisons.csv',comparison_rows)
    result={'checked_on':'2026-10-06','primary_numeric_reproduction':True,'coverage_sensitivity_reproduction':True,
            'archived_output_hash_matches':hash_checks,'independent_rmse_mae_checks':True,'retained_unique_rows':6035,
            'complete_coverage_pain':[r['participant'] for r in coverage if r['modality']=='pain' and r['complete_coverage']],
            'complete_coverage_vision':[r['participant'] for r in coverage if r['modality']=='vision' and r['complete_coverage']],
            'new_hypothesis_tests_added':False,'intervals':'Exploratory percentile; predictive intervals conditional on fixed held-out scores; no multiplicity adjustment'}
    (VALID/'reproduction_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('complete_coverage')},indent=2))
if __name__=='__main__':main()
