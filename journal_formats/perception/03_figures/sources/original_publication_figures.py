"""Publication figures made directly from validated numerical outputs."""
from pathlib import Path
import os,sys,json,csv,textwrap
if os.getenv('ECNP_EXTRA_PYTHONPATH'):sys.path.append(os.environ['ECNP_EXTRA_PYTHONPATH'])
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from PIL import Image

BASE=Path(__file__).resolve().parent;PKG=BASE.parent
DATA=BASE/'analysis_run/data/empirical';FIG=PKG/'02_figures'
S=json.loads((DATA/'summary.json').read_text());C=json.loads((DATA/'coverage_sensitivity.json').read_text())
def readcsv(p):
    with p.open(encoding='utf-8') as f:return list(csv.DictReader(f))
AG=readcsv(DATA/'participant_aggregates.csv');CV=readcsv(DATA/'cross_validation_participant_scores.csv')
COL={'pain':'#0072B2','vision':'#D55E00'};LABEL={'pain':'Pain','vision':'Vision'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':12,
                     'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
                     'svg.fonttype':'none','axes.grid':False,'savefig.facecolor':'white'})
manifest=[]
def save(fig,stem,caption):
    fig.savefig(FIG/(stem+'.png'),dpi=600,bbox_inches='tight',pad_inches=.12)
    for ext in ('pdf','svg'):fig.savefig(FIG/(stem+'.'+ext),bbox_inches='tight',pad_inches=.12)
    fig.savefig(FIG/(stem+'_300dpi.tiff'),dpi=300,bbox_inches='tight',pad_inches=.12,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(FIG/(stem+'_preview.png'),dpi=140,bbox_inches='tight',pad_inches=.12)
    manifest.append({'stem':stem,'caption':caption,'formats':['PNG 600 dpi','PDF vector','SVG vector','TIFF 300 dpi LZW']})
    plt.close(fig)
def box(ax,x,y,w,h,text,face='#F2F5F7',size=11):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01,rounding_size=0.012',lw=.8,edgecolor='#B7C1C9',facecolor=face))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size,linespacing=1.45)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,lw=1.2,color='#4B5560'))

# Figure 1: data and statistical workflow, an original schematic.
fig,ax=plt.subplots(figsize=(9.2,5.8));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
box(ax,.03,.72,.29,.19,'Public behavioural data\n45 participants\n6,480 trials',size=10.5)
box(ax,.375,.72,.25,.19,'Source exclusions\n211 technical trials\n234 additional trials\n(response-time flags)',size=9.5)
box(ax,.69,.72,.28,.19,'Retained observations\n3,005 pain + 3,030 vision\n45 people per modality',size=10)
arrow(ax,(.325,.815),(.37,.815));arrow(ax,(.63,.815),(.685,.815))
box(ax,.04,.33,.42,.26,'Within-participant contrasts\nHigh minus low cue mean\nMatched on stimulus, cue SD and skew\nEqual weight across pairs and people',size=11)
box(ax,.54,.33,.42,.26,'Prediction across participants\nTrain on 44 people; test on the 45th\nRepeat for every participant\nCompare three fixed linear models',size=11)
arrow(ax,(.83,.71),(.25,.605));arrow(ax,(.83,.71),(.75,.605))
box(ax,.04,.025,.42,.18,'Coverage sensitivity\n43 people per modality with all 12 pairs\n42 people common to both subsets',face='#EAF1F5',size=10.5)
box(ax,.54,.025,.42,.18,'Participant-weighted error\nRMSE and MAE on held-out ratings\nBootstrap intervals conditional on scores',face='#EAF1F5',size=10.5)
arrow(ax,(.25,.315),(.25,.215));arrow(ax,(.75,.315),(.75,.215))
save(fig,'figure_1_analysis_workflow','Analysis workflow. Source exclusions are sequential; 103 response-time flags overlap the technical exclusions and are not counted twice. Complete-coverage subsets differ by modality. All primary predictive fits use 45 held-out folds per modality. The source experiment and observations were produced by Botvinik-Nezer et al. (2025); this schematic depicts the secondary analysis.')

# Figure 2: all participants shown, intervals summarise participant-resampled contrasts.
fig,axes=plt.subplots(1,2,figsize=(9.3,4.5));rng=np.random.default_rng(107)
for ax,effect,title,xlab in zip(axes,['cue_high_minus_low','cue_effect_high_sd_minus_low_sd'],
                               ['A  Cue mean contrast','B  Cue by uncertainty contrast'],
                               ['High minus low cue rating (points)','High-SD minus low-SD cue effect (points)']):
    for i,m in enumerate(('pain','vision')):
        vals=np.array([float(r['value']) for r in AG if r['modality']==m and r['estimand']==effect])
        ax.scatter(vals,i+rng.uniform(-.13,.13,len(vals)),s=16,c=COL[m],alpha=.35,edgecolors='none',zorder=1)
        rr=S['contrasts'][m][effect];mu=rr['mean'];lo,hi=rr['ci95_percentile']
        ax.errorbar(mu,i-.24,xerr=[[mu-lo],[hi-mu]],fmt='o',color=COL[m],ms=7,capsize=4,lw=2,zorder=3)
        ax.text(.02,.95-i*.10,f"{LABEL[m]}: {mu:.2f} [{lo:.2f}, {hi:.2f}]",transform=ax.transAxes,fontsize=9,va='top')
    ax.axvline(0,color='#8B949B',lw=.8,ls='--');ax.set_ylim(-.6,1.65)
    ax.set_yticks([0,1],['Pain','Vision']);ax.set_title(title,loc='left',pad=12);ax.set_xlabel(xlab,labelpad=9)
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#E8EBED',lw=.6,zorder=0)
fig.tight_layout(w_pad=2)
save(fig,'figure_2_matched_contrasts','Participant-level matched contrasts in 45 participants per modality. Faint points show individual contrasts with display-only vertical jitter. Solid points and horizontal bars show the equally weighted mean and exploratory 95% percentile interval from 10,000 participant bootstrap samples. Panel A contrasts high versus low cue means. Panel B subtracts the low-SD cue effect from the high-SD cue effect, matching stimulus and skewness. The scales are modality-specific 0-100 rating points and are not perceptually interchangeable.')

# Figure 3: predictive performance and paired incremental utility.
fig,axes=plt.subplots(1,2,figsize=(9.3,4.8));names=['sensory_only','additive_cue','cue_x_uncertainty'];x=np.arange(3)
for m,offset,marker in [('pain',-.05,'o'),('vision',.05,'s')]:
    vals=[S['cross_validation'][m]['models'][n]['equal_participant_rmse'] for n in names]
    axes[0].plot(x+offset,vals,marker=marker,color=COL[m],lw=1.5,label=LABEL[m])
    for xx,v in zip(x+offset,vals):axes[0].annotate(f'{v:.2f}',(xx,v),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
axes[0].set_xticks(x,['Sensory +\ntime','Additive\ncue variables','Plus cue mean\nby SD'])
axes[0].set_ylabel('Participant-weighted RMSE (rating points)');axes[0].set_ylim(0,26);axes[0].legend(frameon=False,loc='lower left');axes[0].set_title('A  Error for held-out participants',loc='left',pad=12)
axes[0].grid(axis='y',color='#E8EBED',lw=.6)
for i,m in enumerate(('pain','vision')):
    for j,comp in enumerate(('sensory_only_minus_additive_cue','additive_cue_minus_cue_x_uncertainty')):
        r=S['cross_validation'][m]['comparisons'][comp];mu=r['rmse_improvement'];lo,hi=r['rmse_improvement_ci95_conditional'];y=i*2+j
        axes[1].errorbar(mu,y,xerr=[[mu-lo],[hi-mu]],fmt='o' if m=='pain' else 's',color=COL[m],capsize=4,ms=7,lw=1.7)
        axes[1].annotate(f'{mu:+.4f}',(mu,y),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
axes[1].set_yticks(range(4),['Pain: add cues','Pain: add interaction','Vision: add cues','Vision: add interaction'])
axes[1].set_ylim(3.5,-.65);axes[1].axvline(0,color='#8B949B',ls='--',lw=.8)
axes[1].set_xlabel('RMSE improvement (points)\nPositive favours the larger model',labelpad=9)
axes[1].set_title('B  Paired changes in error',loc='left',pad=12);axes[1].grid(axis='x',color='#E8EBED',lw=.6)
fig.tight_layout(w_pad=2.8)
save(fig,'figure_3_predictive_performance','Prediction with 45 leave-one-participant-out folds per modality. Panel A shows root mean squared error (RMSE), calculated as the square root of average participant MSE. Panel B shows paired RMSE improvements and conditional 95% percentile intervals from resampling fixed participant scores 10,000 times. The additive model includes cue mean, SD and two skewness indicators jointly; the interaction model adds cue mean by SD. Intervals do not include refitting uncertainty or fully represent dependence between overlapping training folds. Pain and vision use separate rating scales.')

# Figure 4: coverage sensitivity with its own recorded seed and participant sets.
fig,axes=plt.subplots(1,2,figsize=(9.3,4.1))
for ax,effect,title in zip(axes,['cue_high_minus_low','cue_effect_high_sd_minus_low_sd'],['A  Main cue contrast','B  Cue by uncertainty contrast']):
    labels=[]
    for i,m in enumerate(('pain','vision')):
        primary=S['contrasts'][m][effect];ss=next(r for r in C if r['modality']==m and r['estimand']==effect)
        for j,(mu,ci,n,marker) in enumerate([(primary['mean'],primary['ci95_percentile'],45,'o'),(ss['full_coverage_mean'],ss['full_coverage_exploratory_ci95'],43,'s')]):
            y=i*2+j;lo,hi=ci
            ax.errorbar(mu,y,xerr=[[mu-lo],[hi-mu]],fmt=marker,color=COL[m],mfc=COL[m] if n==45 else 'white',capsize=4,lw=1.5,ms=7)
            labels.append(f'{LABEL[m]}  n = {n}')
            ax.annotate(f'{mu:.2f}',(mu,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
    ax.set_yticks(range(4),labels);ax.set_ylim(3.5,-.6);ax.axvline(0,color='#8B949B',ls='--',lw=.8)
    ax.set_title(title,loc='left',pad=12);ax.set_xlabel('Matched contrast (rating points)',labelpad=10);ax.grid(axis='x',color='#E8EBED',lw=.6)
fig.tight_layout(w_pad=2.8)
save(fig,'figure_4_coverage_sensitivity','Primary 45-participant contrasts and post-protocol exploratory complete-coverage sensitivity. Filled circles show the primary analysis; open squares show the 43 participants per modality with all 12 matched cue pairs. Forty-two participants are common to the two complete-coverage subsets. Horizontal bars show separate participant-bootstrap 95% percentile intervals. Primary cue contrasts are stable, whereas the smaller pain interaction changes sign; all interaction intervals include zero. This is a comparison of matched contrasts, not a refit of the predictive models or a formal test of differences between nested samples.')

# Supplement: retained trial count and matched-pair availability.
coverage=readcsv(PKG/'03_supplementary/table_S3_participant_coverage.csv')
people=sorted({r['participant'] for r in coverage})
fig,axes=plt.subplots(2,1,figsize=(10,5.7),sharex=True)
for m,off in [('pain',-.18),('vision',.18)]:
    rows={r['participant']:r for r in coverage if r['modality']==m}
    axes[0].bar(np.arange(45)+off,[int(rows[p]['retained_trials']) for p in people],width=.34,color=COL[m],label=LABEL[m])
    axes[1].plot(np.arange(45),[int(rows[p]['matched_pairs']) for p in people],marker='o' if m=='pain' else 's',ms=4,lw=.9,color=COL[m],label=LABEL[m])
axes[0].axhline(72,color='#808890',ls='--',lw=.8);axes[0].set_ylabel('Retained trials');axes[0].set_ylim(0,92);axes[0].legend(frameon=False,ncol=2,loc='upper right')
axes[0].set_title('A  Trials available per participant and modality',loc='left')
axes[1].axhline(12,color='#808890',ls='--',lw=.8);axes[1].set_ylim(3,13);axes[1].set_ylabel('Matched cue pairs');axes[1].set_title('B  Complete coverage requires all 12 pairs',loc='left')
axes[1].set_xticks(np.arange(45),[p.replace('sub-','') for p in people],rotation=90,fontsize=7);axes[1].set_xlabel('Public anonymised participant code')
fig.tight_layout(h_pad=2)
save(fig,'figure_S1_data_coverage','Data availability after the source exclusion flags. Panel A shows retained trials out of 72 per modality. Panel B shows available matched high-minus-low cue pairs out of 12. The 43-person sensitivity excludes sub-02 and sub-06 for pain, and sub-03 and sub-06 for vision; these are anonymised public source codes. Primary models weight participants equally despite differing trial counts.')

# Graphical abstract: original analysis summary with outcome labels and no biological inference.
fig,ax=plt.subplots(figsize=(11.5,4.8));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ax.text(.03,.95,'Contextual cues and prediction of pain and visual ratings',fontsize=17,weight='bold',va='top')
ax.text(.03,.865,'Exploratory secondary analysis of public behavioural data',fontsize=11,color='#4C5963')
box(ax,.025,.24,.27,.53,'DATA\n\n45 participants\n6,035 retained trials\n\nThermal pain + visual contrast\nSocial cue mean, SD and skew',size=11)
box(ax,.365,.24,.27,.53,'WITHIN-PERSON CONTRAST\n\nHigh minus low cue mean\n\nPain: 12.08 points\nVision: 9.93 points\n\nStable with complete coverage',size=11)
box(ax,.705,.24,.27,.53,'HELD-OUT PREDICTION\n\nAdding cue variables\nreduces RMSE by\n\nPain: 0.797 points\nVision: 0.739 points\n\nInteraction adds almost nothing',size=11)
arrow(ax,(.302,.505),(.352,.505));arrow(ax,(.642,.505),(.692,.505))
ax.text(.5,.15,'Condition differences and predictive gains answer different questions',ha='center',fontsize=13,weight='bold')
ax.text(.5,.07,'One cohort  |  Modality-specific rating scales  |  Conditional predictive uncertainty',ha='center',fontsize=10,color='#4C5963')
save(fig,'graphical_abstract','Graphical abstract. The secondary analysis compares matched within-person cue contrasts with participant-held-out predictive utility. Complete-coverage sensitivity retains 43 participants per modality. Cue-variable prediction gains concern mean, SD and skewness together. The results concern rating data from one cohort; they do not demonstrate clinical utility or identify a neural, pharmacological or perceptual mechanism.')

(FIG/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(FIG/'figure_legends.md').write_text('\n\n'.join('## '+m['stem']+'\n\n'+m['caption'] for m in manifest)+'\n',encoding='utf-8')
print(json.dumps({'figures':len(manifest),'matplotlib':matplotlib.__version__,'numpy':np.__version__,'output':str(FIG)},ensure_ascii=True))
