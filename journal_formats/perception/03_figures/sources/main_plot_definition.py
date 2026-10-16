def make_figures(models, comparisons, gains):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'pdf.fonttype': 42, 'ps.fonttype': 42, 'axes.labelcolor': '#20262E', 'xtick.color': '#20262E', 'ytick.color': '#20262E'})
    colors = {'pain': '#176C9C', 'vision': '#A85B22'}
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, mod, letter in zip(axs, ('pain', 'vision'), ('A', 'B')):
        rs = [r for r in models if r['modality'] == mod]
        for j, r in enumerate(rs):
            ax.plot([r['rmse_conditional_low'], r['rmse_conditional_high']], [j, j], color=colors[mod], lw=1.4)
            ax.scatter(r['rmse'], j, color=colors[mod], marker='o' if j != 1 else 'D', s=42, zorder=3)
            ax.annotate(f"{r['rmse']:.4f}", (r['rmse'], j), xytext=(0, 8), textcoords='offset points', ha='center', fontsize=9)
        ax.set_yticks(range(4), LABELS)
        ax.set_ylim(3.5, -0.7)
        ax.set_xlim(0, 30)
        ax.set_xlabel('Participant-weighted RMSE (rating points)')
        ax.set_title(letter + '  ' + mod.capitalize(), loc='left', fontweight='bold')
        ax.grid(axis='x', alpha=0.18)
    fig.tight_layout()
    save(fig, 'figure_R1_all_model_rmse')
    pairlabels = [f'M{MODELS.index(a)} to M{MODELS.index(b)}' for a, b in PAIRS]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6), sharex=True, sharey=True)
    for ax, mod, letter in zip(axs, ('pain', 'vision'), ('A', 'B')):
        rs = [r for r in comparisons if r['modality'] == mod]
        for j, r in enumerate(rs):
            focal = (r['baseline'], r['candidate']) in [(MODELS[0], MODELS[1]), (MODELS[1], MODELS[2])]
            color = colors[mod] if focal else '#687581'
            ax.plot([r['rmse_conditional_low'], r['rmse_conditional_high']], [j, j], color=color, lw=1.5)
            ax.scatter(r['rmse_improvement'], j, color=color, s=40, marker='D' if focal else 'o', zorder=3)
        ax.axvline(0, color='#333333', lw=0.9, ls='--')
        ax.set_yticks(range(6), pairlabels)
        ax.set_ylim(5.5, -0.6)
        ax.set_xlabel('RMSE improvement (rating points)')
        ax.set_title(letter + '  ' + mod.capitalize(), loc='left', fontweight='bold')
        ax.grid(axis='x', alpha=0.18)
    fig.tight_layout()
    save(fig, 'figure_R2_all_paired_rmse_differences')
    consecutive = list(zip(MODELS[:-1], MODELS[1:]))
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
    for ax, mod, letter in zip(axs, ('pain', 'vision'), ('A', 'B')):
        for j, (a, b) in enumerate(consecutive):
            vals = sorted((r['individual_rmse_improvement'] for r in gains if r['modality'] == mod and r['baseline'] == a and (r['candidate'] == b)))
            offsets = np.linspace(-0.22, 0.22, len(vals))
            ax.scatter(j + offsets, vals, s=18, facecolors='none', edgecolors=colors[mod], linewidths=0.8)
            ax.plot([j - 0.28, j + 0.28], [np.median(vals)] * 2, color='#20262E', lw=2)
        ax.axhline(0, color='#333333', lw=0.9, ls='--')
        ax.set_xticks(range(3), ('M0 to M1', 'M1 to M2', 'M2 to M3'))
        ax.set_title(letter + '  ' + mod.capitalize(), loc='left', fontweight='bold')
        ax.grid(axis='y', alpha=0.18)
        ax.set_xlabel('Consecutive nested-model comparison')
    axs[0].set_ylabel('Individual RMSE improvement (rating points)')
    fig.tight_layout()
    save(fig, 'figure_R3_participant_gain_distribution')
    write_csv(FIG / 'figure_R1_data.csv', models)
    write_csv(FIG / 'figure_R2_data.csv', comparisons)
    write_csv(FIG / 'figure_R3_data.csv', [r for r in gains if (r['baseline'], r['candidate']) in consecutive])
    (FIG / 'captions.md').write_text('# Revision figure captions\n\nFigure R1. All four fixed models, evaluated with 45 leave-one-participant-out folds per modality (pain: 3,005 trials; vision: 3,030 trials). Points show equal-participant RMSE, with numerical values labelled; lines show descriptive 95% percentile intervals conditional on the fitted predictions. M0 includes stimulus and temporal variables; M1 adds cue mean; M2 adds cue SD and skewness indicators; M3 adds the cue-mean-by-SD interaction. The mean-only M1 model is the new exploratory revision. Lower RMSE is better. A: pain; B: vision. Both panels use the same 0-30 axis.\n\nFigure R2. All six paired model differences. Positive values favor the second model. Lines are paired descriptive 95% percentile intervals from 10,000 resamples of the 45 fixed participant error scores; no models were refitted. Diamonds distinguish the two focal new comparisons, M0 to M1 and M1 to M2, from contextual comparisons; no comparison is omitted. These conditional intervals do not fully represent model-fitting uncertainty or training-fold dependence and are not independent-population confidence intervals. A: pain; B: vision; a shared difference axis is used.\n\nFigure R3. Individual participant RMSE differences for the three consecutive model increments. Every circle is one of 45 held-out participants; horizontal offsets are a deterministic display arrangement only. Short black lines indicate medians, not uncertainty intervals. Positive values indicate lower RMSE for the larger model. Individual RMSE differences are distinct from the aggregate participant-weighted RMSE difference in Figure R2. Both modalities use the same vertical scale. A: pain; B: vision. All six comparison distributions are available in participant_gains.csv.\n', encoding='utf-8')
