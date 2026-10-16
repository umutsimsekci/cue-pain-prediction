"""Reproduce final Perception figures from preserved numerical outputs only.

No statistical model, bootstrap, or data exclusion is rerun. Copy this folder and
../04_supplement/figures/source_data together to reproduce the figure package.
Requires NumPy, Matplotlib, Pillow, pypdf and pypdfium2. An existing extra library
directory may be supplied through ECNP_EXTRA_PYTHONPATH.
"""
from pathlib import Path
import csv, hashlib, itertools, json, os, re, sys
if os.environ.get('ECNP_EXTRA_PYTHONPATH'):sys.path.append(os.environ['ECNP_EXTRA_PYTHONPATH'])
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from pypdf import PdfReader
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
SUP=HERE.parent/'04_supplement/figures'
SUPDATA=SUP/'source_data'
GA=HERE/'graphical_abstract'
QA=HERE/'visual_qa'
for p in (SUP,GA,QA):p.mkdir(parents=True,exist_ok=True)
MODELS=('sensory_only','cue_mean_only','additive_cue','cue_x_uncertainty')
LABELS=('M0: Stimulus + time','M1: + Cue mean','M2: + SD + skewness','M3: + Mean x SD')
PAIRS=list(itertools.combinations(MODELS,2))
mapping={'figure_R1_all_model_rmse':'Figure1_all_model_RMSE',
         'figure_R2_all_paired_rmse_differences':'Figure2_paired_RMSE_differences',
         'figure_R3_participant_gain_distribution':'Figure3_participant_gain_distribution'}
supmap={'figure_2_matched_contrasts':'FigureS1_matched_contrasts',
        'figure_4_coverage_sensitivity':'FigureS2_coverage_sensitivity',
        'figure_S1_data_coverage':'FigureS3_data_coverage'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def typed(p):
    rows=readcsv(p)
    for r in rows:
        for k,v in r.items():
            if k not in ('modality','model','baseline','candidate','participant'):r[k]=float(v)
    return rows
def writecsv(p,rows):
    p=Path(p);p=p.with_name(p.name.replace('figure_R1','Figure1').replace('figure_R2','Figure2').replace('figure_R3','Figure3'))
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
inputs=[*sorted((HERE/'data').glob('*')),*sorted((HERE/'sources').glob('*')),*sorted(SUPDATA.glob('*'))]
before={str(p):sha(p) for p in inputs if p.is_file()}
records=[];supp_captions=[]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':12,
                     'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
                     'svg.fonttype':'none','savefig.facecolor':'white'})

def save_final(fig,stem,location,main=False,graphical=False):
    # Resolve light grid opacity to a solid light grey, also supported by EPS.
    if main:
        for ax in fig.axes:
            for line in [*ax.get_xgridlines(),*ax.get_ygridlines()]:
                if line.get_visible():line.set_color('#EEEEEE');line.set_alpha(1.)
    opts={} if graphical else {'bbox_inches':'tight','pad_inches':.12}
    formats=['pdf','svg']+(['eps'] if main or graphical else [])
    for ext in formats:fig.savefig(location/(stem+'.'+ext),**opts)
    fig.savefig(location/(stem+'.png'),dpi=240 if graphical else 300,**opts)
    if main or graphical:
        fig.savefig(location/(stem+'_800dpi.tiff'),dpi=800,pil_kwargs={'compression':'tiff_lzw'},**opts)
    record={'stem':stem,'directory':str(location.relative_to(HERE.parent)),
            'role':'graphical_abstract' if graphical else 'main_figure' if main else 'supplementary_figure',
            'formats':formats+['png']+(['800dpi LZW TIFF'] if main or graphical else [])}
    records.append(record)
    plt.close(fig)

def save_main(fig,stem):save_final(fig,mapping[stem],HERE,main=True)
env={'np':np,'plt':plt,'MODELS':MODELS,'LABELS':LABELS,'PAIRS':PAIRS,'FIG':HERE,'save':save_main,'write_csv':writecsv}
exec(compile((HERE/'sources/main_plot_definition.py').read_text(encoding='utf-8'),'preserved main figure function','exec'),env)
env['make_figures'](typed(HERE/'data/model_metrics.csv'),typed(HERE/'data/pairwise_comparisons.csv'),typed(HERE/'data/participant_gains.csv'))
original=(HERE/'sources/revision_captions_original.md').read_text(encoding='utf-8')
captions=re.sub(r'Figure R([123])',r'Figure \1',original)
captions=captions.replace('# Revision figure captions','# Main figure captions')
(HERE/'maincaptions.txt').write_text(captions,encoding='utf-8')
# The preserved drawing function also emits its original captions; make the local
# final copy consistent with the journal numbering without editing the source.
(HERE/'captions.md').write_text(captions,encoding='utf-8')

def save_supp(fig,stem,caption):
    for ax in fig.axes:
        for loc in ('left','center','right'):
            title=ax.get_title(loc=loc)
            if title:
                match=re.match(r'^([A-Z])(?:\s+|$)',title)
                ax.set_title(match.group(1) if match else '',loc=loc)
    name=supmap[stem]
    save_final(fig,name,SUP)
    supp_captions.append(name.split('_')[0].replace('Figure','Figure ')+'. '+caption)
oldenv={'np':np,'plt':plt,'readcsv':readcsv,'SUPDATA':SUPDATA,
        'S':json.loads((SUPDATA/'summary.json').read_text()),
        'C':json.loads((SUPDATA/'coverage_sensitivity.json').read_text()),
        'AG':readcsv(SUPDATA/'participant_aggregates.csv'),
        'COL':{'pain':'#0072B2','vision':'#D55E00'},'LABEL':{'pain':'Pain','vision':'Vision'},'save':save_supp}
exec(compile((HERE/'sources/supplement_plot_definitions.py').read_text(encoding='utf-8'),'preserved supplement plot definitions','exec'),oldenv)
(SUP/'supplement_captions.txt').write_text('\n\n'.join(supp_captions)+'\n',encoding='utf-8')

# An original, entirely programmatic 16:9 summary of the validated comparison.
summary=json.loads((HERE/'data/revision_summary.json').read_text())['modalities']
fig=plt.figure(figsize=(13.333333333333334,7.5),facecolor='white')
ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ink='#20262E';muted='#50616F';blue='#176C9C';orange='#A85B22'
ax.text(.045,.95,'Social cue means and distribution shape in\nprediction of pain and visual ratings',fontsize=22,weight='bold',color=ink,va='top',linespacing=1.16)
ax.text(.045,.825,'Exploratory secondary analysis of public behavioural data',fontsize=13,color=muted,va='top')
ax.plot([.045,.955],[.785,.785],color='#D5DEE4',lw=1)
ax.text(.05,.728,'DATA AND VALIDATION',fontsize=11.5,weight='bold',color=blue)
ax.text(.05,.662,'45 participants',fontsize=22,weight='bold',color=ink)
ax.text(.05,.610,'6,035 retained trials',fontsize=18,color=ink)
ax.text(.05,.540,'Thermal pain + visual contrast',fontsize=13,color=muted)
ax.text(.05,.453,'Train on 44 people; test on 1',fontsize=14,weight='bold',color=ink)
ax.text(.05,.407,'45 leave-one-participant-out folds\nper modality',fontsize=13,color=muted,linespacing=1.4,va='top')
ax.plot([.385,.385],[.365,.738],color='#D5DEE4',lw=1)
ax.text(.425,.728,'PARTICIPANT-WEIGHTED RMSE',fontsize=11.5,weight='bold',color=blue)
ax.text(.425,.688,'Lower is better; rating-point units',fontsize=11.5,color=muted)
xs=[.495,.675,.865]
for x,head in zip(xs,['M0\nStimulus + time','M1\n+ Cue mean','M2\n+ SD + skewness']):
    ax.text(x,.626,head,ha='center',va='top',fontsize=12,weight='bold',color=ink,linespacing=1.35)
for y,mod,color in [(.505,'pain',blue),(.437,'vision',orange)]:
    ax.text(.444,y,mod.capitalize(),ha='right',va='center',fontsize=13,color=color,weight='bold')
    for x,model in zip(xs,MODELS[:3]):
        ax.text(x,y,f"{summary[mod]['models'][model]['rmse']:.3f}",ha='center',va='center',fontsize=19,color=color)
ax.plot([.445,.945],[.548,.548],color='#D5DEE4',lw=1)
ax.text(.425,.370,'Adding SD and skewness changed RMSE by\nless than 0.01 points in either modality.',fontsize=12,color=muted,linespacing=1.4,va='top')
ax.add_patch(Rectangle((.045,.165),.91,.13,facecolor='#EAF3F8',edgecolor='none'))
ax.text(.5,.247,'The model including cue mean recovered nearly all the modest gain',ha='center',va='center',fontsize=16,weight='bold',color=ink)
ax.text(.5,.198,'Additional distribution features offered little gain in these fixed linear models.',ha='center',va='center',fontsize=12.5,color=muted)
ax.text(.5,.112,'One experiment  |  Exploratory comparison  |  No external validation or mechanistic inference',ha='center',fontsize=11,color=muted)
ax.text(.045,.045,'Umut Şimşekçi  |  October 2026',fontsize=11,color=ink)
ax.text(.955,.045,'Data: Botvinik-Nezer et al. (2025)  |  PPRI-paper v2.0.0',ha='right',fontsize=9.5,color=muted)
save_final(fig,'Graphical_abstract',GA,graphical=True)
(GA/'caption.txt').write_text('Graphical abstract. Exploratory participant-held-out prediction in one public cohort. M0 includes stimulus intensity and temporal variables; M1 adds cue mean; M2 adds cue SD and skewness indicators. Values are equal-participant RMSE. All coefficients are refitted per model and fold. The mean-only model recovered nearly all the observed additive-model gain. SD/skewness comparisons changed RMSE by less than 0.01 points in either modality; this is not evidence of equivalence, causal attribution, absence of uncertainty effects, external validity, or clinical benefit. Descriptive conditional intervals and the interaction model are reported in the article and supplementary outputs. Author: Umut Şimşekçi; October 2026. Generated only with Python plotting libraries; no generative images.\n',encoding='utf-8')
writecsv(GA/'data.csv',[{'modality':mod,'model':m,'rmse':summary[mod]['models'][m]['rmse']} for mod in ('pain','vision') for m in MODELS[:3]])

validation=[]
for rec in records:
    directory=HERE.parent/rec['directory'];pdf=directory/(rec['stem']+'.pdf')
    reader=PdfReader(pdf);assert len(reader.pages)==1
    text=reader.pages[0].extract_text() or '';assert len(text)>40
    record=dict(rec,pdf_pages=1,pdf_text_characters=len(text))
    if rec['role'] in ('main_figure','graphical_abstract'):
        tif=directory/(rec['stem']+'_800dpi.tiff')
        with Image.open(tif) as im:
            dpi=[float(x) for x in im.info['dpi']];size=list(im.size);compression=int(im.tag_v2[259])
        assert all(abs(d-800)<.01 for d in dpi) and compression==5
        record.update(tiff_pixels=size,tiff_dpi=dpi,tiff_compression='LZW',tiff_bytes=tif.stat().st_size,tiff_under_10MB=tif.stat().st_size<10_000_000)
        assert record['tiff_under_10MB'], 'TIFF exceeds 10 MB; report and revise export dimensions without upsampling.'
        if rec['role']=='graphical_abstract':
            assert abs(size[0]/size[1]-16/9)<.001
            record['canvas_inches']=[13.333333333333334,7.5]
    doc=pdfium.PdfDocument(pdf);page=doc[0];png=QA/(rec['stem']+'_pdf_render.png')
    page.render(scale=1.6).to_pil().save(png);page.close();doc.close()
    record['pdf_render']=png.relative_to(HERE.parent).as_posix();validation.append(record)
assert before=={str(p):sha(p) for p in inputs if p.is_file()}
(HERE/'export_validation.json').write_text(json.dumps({'purpose':'Final journal exports only; no new analysis','preserved_inputs_unchanged':True,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'figures':validation},indent=2)+'\n',encoding='utf-8')
manifest=[]
for location in (HERE,SUP):
    for p in sorted(location.rglob('*')):
        if p.is_file() and p.name not in ('figure_file_manifest.json',):
            manifest.append({'path':p.relative_to(HERE.parent).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
(HERE/'figure_file_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'figures':len(records),'files':len(manifest),'validation':validation},indent=2))
