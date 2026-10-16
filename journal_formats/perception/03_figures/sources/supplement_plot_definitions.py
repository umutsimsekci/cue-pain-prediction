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
coverage=readcsv(SUPDATA/'table_S3_participant_coverage.csv')
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

