"""
Agent 1: Structural — Municipal-Level Analysis
Leverages incidencia_municipal (~2.5M rows, ~2,457 municipalities) to break
through the N=32 state-level barrier. Tests whether digital infrastructure
relationships hold at finer granularity.
"""
import numpy as np
import pandas as pd
from scipy import stats
from experiments.data_utils import load_all_data, AgentSession, ExperimentResult

AGENT_ID = 'structural'
OBJECTIVE = 'Break N=32 barrier using municipal-level data; test if IDDE→crime relationships hold at finer granularity'


def run():
    session = AgentSession(AGENT_ID, OBJECTIVE)
    D = load_all_data()
    cross = D['cross_cl']
    panel = D['panel']
    muni = D['muni_annual'].copy()
    muni_crime = D['muni_crime']
    INFRA_VARS = D['INFRA_VARS']
    SEC_COL_LABELS = D['SEC_COL_LABELS']

    # Pre-filter to 2022-2025 and valid populations
    muni = muni[(muni['ano'] >= 2022) & (muni['ano'] <= 2025)].copy()
    muni = muni[muni['pop'] > 0].copy()
    muni['log_pop'] = np.log1p(muni['pop'])

    # Assign state-level IDDE to each municipality
    idde_map = panel.groupby('estado')['idde_index'].mean().to_dict()
    muni['idde'] = muni['estado'].map(idde_map)

    # Classify urban vs rural (population threshold)
    pop_median = muni['pop'].median()
    muni['urban'] = (muni['pop'] >= pop_median).astype(int)

    # Current-year cross-sectional (most recent year)
    muni_latest = muni[muni['ano'] == muni['ano'].max()].copy()

    print(f"Agent {AGENT_ID}: {len(muni_latest)} municipalities in latest year, "
          f"{muni_latest['estado'].nunique()} states")

    # ── EXP 1.1: State-level IDDE vs municipal crime rates ────────────
    print("  [1.1] State IDDE → municipal crime...")
    sub = muni_latest.dropna(subset=['idde', 'rate_100k'])
    if len(sub) > 50:
        # Remove extreme outliers (3σ winsorize)
        q_low, q_hi = sub['rate_100k'].quantile([0.01, 0.99])
        sub_clean = sub[(sub['rate_100k'] >= q_low) & (sub['rate_100k'] <= q_hi)]
        r, p = stats.pearsonr(sub_clean['idde'], sub_clean['rate_100k'])

        # Compare to population-weighted correlation (see 1.6)
        r_w_val = r  # placeholder; weighted version in 1.6

        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.1',
            title='State IDDE → Municipal crime (N=2457)',
            description='State-level IDDE correlated with each municipality crime rate',
            finding=f'r={r:.4f}, p={p:.2e}, N={len(sub_clean)}. '
                    f'{"Significant" if p < 0.05 else "Not significant"} at municipal level.',
            stat_value=round(r, 4), stat_name='r', p_value=round(p, 6),
            confidence=7 if p < 0.05 else 3,
            novelty=6,
            narrative_value=7 if p < 0.05 else 3,
            recommendation='If significant, this massively strengthens the dashboard claim with N=2457.',
        ))

    # ── EXP 1.2: Within-state heterogeneity ───────────────────────────
    print("  [1.2] Within-state crime variance...")
    within_vars = []
    for estado, grp in muni_latest.groupby('estado'):
        if len(grp) >= 5:
            cv = grp['rate_100k'].std() / grp['rate_100k'].mean() if grp['rate_100k'].mean() > 0 else 0
            within_vars.append({'estado': estado, 'cv': cv, 'n_munis': len(grp),
                                'idde': grp['idde'].iloc[0]})
    wv = pd.DataFrame(within_vars)
    if len(wv) > 10:
        r_cv, p_cv = stats.pearsonr(wv['idde'], wv['cv'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.2',
            title='IDDE → Within-state crime heterogeneity',
            description='Does digital development reduce crime variance within states?',
            finding=f'r(IDDE, CV)={r_cv:.4f}, p={p_cv:.4f}. '
                    f'{"States with higher IDDE have more uniform crime rates" if r_cv < 0 and p_cv < 0.05 else "No clear pattern"}.',
            stat_value=round(r_cv, 4), stat_name='r', p_value=round(p_cv, 4),
            confidence=6 if p_cv < 0.05 else 3,
            novelty=7,
            narrative_value=6 if p_cv < 0.05 else 2,
        ))

    # ── EXP 1.3: Urban vs rural municipalities ────────────────────────
    print("  [1.3] Urban vs rural crime gap by IDDE...")
    for label, grp in muni_latest.groupby('urban'):
        if len(grp) > 50:
            r_u, p_u = stats.pearsonr(grp.dropna(subset=['idde', 'rate_100k'])['idde'],
                                       grp.dropna(subset=['idde', 'rate_100k'])['rate_100k'])
            tag = 'Urban' if label == 1 else 'Rural'
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id=f'1.3{"u" if label == 1 else "r"}',
                title=f'State IDDE → Crime in {tag} municipalities',
                description=f'Correlation of state IDDE with crime in {tag.lower()} municipalities',
                finding=f'{tag}: r={r_u:.4f}, p={p_u:.4f}, N={len(grp)}.',
                stat_value=round(r_u, 4), stat_name='r', p_value=round(p_u, 4),
                confidence=5 if p_u < 0.05 else 3,
                novelty=6,
                narrative_value=5,
            ))

    # ── EXP 1.4: Crime type decomposition at municipal level ──────────
    print("  [1.4] Crime type decomposition...")
    violent_types = ['Homicidio doloso', 'Secuestro', 'Extorsión',
                     'Violencia familiar', 'Abuso sexual', 'Feminicidio']
    property_types = ['Robo', 'Fraude', 'Daño a la propiedad']

    # Aggregate by crime category at state level from municipal data
    muni_cat = muni_crime[muni_crime['ano'] == muni_crime['ano'].max()].copy()
    muni_cat['idde'] = muni_cat['estado'].map(idde_map)

    for cat_name, cat_list in [('violent', violent_types), ('property', property_types)]:
        cat_data = muni_cat[muni_cat['subtipo'].isin(cat_list)]
        state_cat = cat_data.groupby('estado').agg({'total': 'sum', 'pop': 'first'}).reset_index()
        state_cat['rate'] = (state_cat['total'] / state_cat['pop'].replace(0, np.nan)) * 1e5
        state_cat['idde'] = state_cat['estado'].map(idde_map)
        sub = state_cat.dropna(subset=['idde', 'rate'])
        if len(sub) > 10:
            r_c, p_c = stats.pearsonr(sub['idde'], sub['rate'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id=f'1.4_{cat_name}',
                title=f'State IDDE → {cat_name.title()} crime (municipal aggregation)',
                description=f'Correlation of IDDE with {cat_name} crimes aggregated from municipal data',
                finding=f'{cat_name.title()} crime: r={r_c:.4f}, p={p_c:.4f}, N={len(sub)}.',
                stat_value=round(r_c, 4), stat_name='r', p_value=round(p_c, 4),
                confidence=6 if p_c < 0.05 else 3,
                novelty=7,
                narrative_value=7 if p_c < 0.05 else 3,
                recommendation=f'Violent vs property crime split could reveal which crime types are most affected by digitalization.',
            ))

    # ── EXP 1.5: Crime concentration (Gini) by state ──────────────────
    print("  [1.5] Crime concentration Gini...")
    ginis = []
    for estado, grp in muni_latest.groupby('estado'):
        if len(grp) >= 10:
            vals = np.sort(grp['total'].values)
            n = len(vals)
            cum = np.cumsum(vals)
            gini = 1 - 2 * np.sum(cum) / (n * cum[-1]) if cum[-1] > 0 else 0
            ginis.append({'estado': estado, 'gini': gini, 'idde': idde_map.get(estado)})
    gd = pd.DataFrame(ginis)
    if len(gd) > 10:
        r_g, p_g = stats.pearsonr(gd['idde'], gd['gini'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.5',
            title='IDDE → Crime concentration (Gini) by state',
            description='Does digital development concentrate or disperse crime across municipalities?',
            finding=f'r(IDDE, Gini)={r_g:.4f}, p={p_g:.4f}. '
                    f'{"Higher IDDE → more concentrated crime" if r_g < 0 and p_g < 0.05 else "No significant relationship"}.',
            stat_value=round(r_g, 4), stat_name='r', p_value=round(p_g, 4),
            confidence=5 if p_g < 0.05 else 3,
            novelty=8,
            narrative_value=6 if p_g < 0.05 else 2,
        ))

    # ── EXP 1.6: Population-weighted analysis ─────────────────────────
    print("  [1.6] Population-weighted correlations...")
    # Weighted correlation using population as weight
    sub = muni_latest.dropna(subset=['idde', 'rate_100k', 'pop']).copy()
    sub = sub[sub['pop'] > 0]
    if len(sub) > 50:
        w = sub['pop'].values
        x = sub['idde'].values
        y = sub['rate_100k'].values
        # Weighted correlation
        mx = np.average(x, weights=w)
        my = np.average(y, weights=w)
        cov_xy = np.average((x - mx) * (y - my), weights=w)
        cov_xx = np.average((x - mx)**2, weights=w)
        cov_yy = np.average((y - my)**2, weights=w)
        r_w = cov_xy / np.sqrt(cov_xx * cov_yy) if cov_xx > 0 and cov_yy > 0 else 0

        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.6',
            title='Population-weighted IDDE → municipal crime',
            description='Correlation weighted by municipality population (big cities count more)',
            finding=f'Weighted r={r_w:.4f} vs unweighted r from 1.1. '
                    f'{"Weighted correlation is stronger" if abs(r_w) > abs(r) else "Unweighted correlation is stronger"}.',
            stat_value=round(r_w, 4), stat_name='r_weighted',
            confidence=7,
            novelty=5,
            narrative_value=6,
        ))

    # ── EXP 1.7: Border municipalities ────────────────────────────────
    print("  [1.7] Border state municipalities...")
    border_states = ['Baja California', 'Sonora', 'Chihuahua', 'Coahuila',
                     'Nuevo León', 'Tamaulipas']
    muni_border = muni_latest[muni_latest['estado'].isin(border_states)]
    muni_interior = muni_latest[~muni_latest['estado'].isin(border_states)]
    for tag, grp in [('Border', muni_border), ('Interior', muni_interior)]:
        sub = grp.dropna(subset=['idde', 'rate_100k'])
        if len(sub) > 30:
            r_b, p_b = stats.pearsonr(sub['idde'], sub['rate_100k'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id=f'1.7_{tag.lower()}',
                title=f'State IDDE → Crime in {tag} municipalities',
                description=f'Border states have different crime dynamics (narco-trafficking)',
                finding=f'{tag}: r={r_b:.4f}, p={p_b:.4f}, N={len(sub)}.',
                stat_value=round(r_b, 4), stat_name='r', p_value=round(p_b, 4),
                confidence=5 if p_b < 0.05 else 3,
                novelty=7,
                narrative_value=5,
            ))

    # ── EXP 1.8: Large vs small municipalities ────────────────────────
    print("  [1.8] Large vs small municipalities...")
    pop_q75 = muni_latest['pop'].quantile(0.75)
    large = muni_latest[muni_latest['pop'] >= pop_q75]
    small = muni_latest[muni_latest['pop'] < pop_q75]
    for tag, grp in [('Large (>Q75)', large), ('Small (<Q75)', small)]:
        sub = grp.dropna(subset=['idde', 'rate_100k'])
        if len(sub) > 30:
            r_s, p_s = stats.pearsonr(sub['idde'], sub['rate_100k'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id=f'1.8_{"lg" if "Large" in tag else "sm"}',
                title=f'State IDDE → Crime in {tag} municipalities',
                description=f'Do large or small municipalities show stronger IDDE-crime correlation?',
                finding=f'{tag}: r={r_s:.4f}, p={p_s:.4f}, N={len(sub)}.',
                stat_value=round(r_s, 4), stat_name='r', p_value=round(p_s, 4),
                confidence=5 if p_s < 0.05 else 3,
                novelty=6,
                narrative_value=5,
            ))

    # ── EXP 1.9: Year-over-year change at municipal level ─────────────
    print("  [1.9] Municipal crime change 2022→2025...")
    m22 = muni[muni['ano'] == 2022].set_index(['clave_ent', 'cve_municipio'])['rate_100k']
    m25 = muni[muni['ano'] == muni['ano'].max()].set_index(['clave_ent', 'cve_municipio'])['rate_100k']
    dm = pd.DataFrame({'r22': m22, 'r25': m25}).dropna()
    dm['delta'] = dm['r25'] - dm['r22']
    dm = dm.reset_index().merge(
        muni_latest[['clave_ent', 'cve_municipio', 'idde', 'estado']].drop_duplicates(),
        on=['clave_ent', 'cve_municipio'], how='left'
    )
    sub = dm.dropna(subset=['idde', 'delta'])
    if len(sub) > 50:
        r_d, p_d = stats.pearsonr(sub['idde'], sub['delta'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.9',
            title='State IDDE → Municipal crime change (2022→latest)',
            description='Does IDDE predict crime reduction at the municipal level?',
            finding=f'r={r_d:.4f}, p={p_d:.4f}, N={len(sub)}. '
                    f'{"Higher IDDE → crime reduction" if r_d < 0 and p_d < 0.05 else "No significant relationship"}.',
            stat_value=round(r_d, 4), stat_name='r', p_value=round(p_d, 4),
            confidence=7 if p_d < 0.05 else 3,
            novelty=7,
            narrative_value=8 if p_d < 0.05 else 3,
            recommendation='This is the strongest possible evidence: same municipality, crime change predicted by state IDDE.',
        ))

    # ── EXP 1.10: Homicide-specific analysis at municipal level ───────
    print("  [1.10] Homicide at municipal level...")
    homicidio = muni_crime[
        (muni_crime['subtipo'] == 'Homicidio doloso') &
        (muni_crime['ano'] == muni_crime['ano'].max())
    ].copy()
    homicidio['idde'] = homicidio['estado'].map(idde_map)
    state_homicide = homicidio.groupby('estado').agg({'total': 'sum', 'pop': 'first'}).reset_index()
    state_homicide['homicide_rate'] = (state_homicide['total'] / state_homicide['pop'].replace(0, np.nan)) * 1e5
    state_homicide['idde'] = state_homicide['estado'].map(idde_map)
    sub = state_homicide.dropna(subset=['idde', 'homicide_rate'])
    if len(sub) > 10:
        r_h, p_h = stats.pearsonr(sub['idde'], sub['homicide_rate'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.10',
            title='State IDDE → Homicide rate (municipal aggregation)',
            description='Homicide doloso aggregated from municipality level using latest year data',
            finding=f'r={r_h:.4f}, p={p_h:.4f}, N={len(sub)}.',
            stat_value=round(r_h, 4), stat_name='r', p_value=round(p_h, 4),
            confidence=6 if p_h < 0.05 else 3,
            novelty=5,
            narrative_value=7 if p_h < 0.05 else 3,
        ))

    # ── EXP 1.11: Top/bottom IDDE states — crime distribution ─────────
    print("  [1.11] Top vs bottom IDDE states crime distribution...")
    median_idde = cross['indice_de_desarrollo_digital_estatal_2025'].median()
    high_idde_states = set(cross[cross['indice_de_desarrollo_digital_estatal_2025'] >= median_idde]['estado'])
    low_idde_states = set(cross[cross['indice_de_desarrollo_digital_estatal_2025'] < median_idde]['estado'])

    high_rates = muni_latest[muni_latest['estado'].isin(high_idde_states)]['rate_100k'].dropna()
    low_rates = muni_latest[muni_latest['estado'].isin(low_idde_states)]['rate_100k'].dropna()

    if len(high_rates) > 30 and len(low_rates) > 30:
        # Mann-Whitney U test (non-parametric)
        u_stat, p_mw = stats.mannwhitneyu(high_rates, low_rates, alternative='two-sided')
        d_cohen = (high_rates.mean() - low_rates.mean()) / np.sqrt(
            (high_rates.std()**2 + low_rates.std()**2) / 2)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.11',
            title='High vs low IDDE states: municipal crime distribution',
            description='Non-parametric test of whether municipal crime rates differ by state IDDE level',
            finding=f'Mann-Whitney U={u_stat:.0f}, p={p_mw:.4f}. Cohen d={d_cohen:.3f}. '
                    f'High IDDE mean={high_rates.mean():.1f}, Low IDDE mean={low_rates.mean():.1f}.',
            stat_value=round(p_mw, 4), stat_name='p_MW', p_value=round(p_mw, 4),
            confidence=6,
            novelty=5,
            narrative_value=6,
        ))

    # ── EXP 1.12: Variance decomposition (between vs within states) ───
    print("  [1.12] Variance decomposition...")
    total_var = muni_latest['rate_100k'].var()
    between_var = muni_latest.groupby('estado')['rate_100k'].mean().var()
    within_var = total_var - between_var
    icc = between_var / total_var if total_var > 0 else 0
    session.record(ExperimentResult(
        agent_id=AGENT_ID, exp_id='1.12',
        title='Crime variance decomposition: between vs within states',
        description='ICC (Intraclass Correlation): how much crime variance is between vs within states',
        finding=f'ICC={icc:.3f}. {icc*100:.1f}% of municipal crime variance is BETWEEN states. '
                f'{(1-icc)*100:.1f}% is WITHIN states. '
                f'{"State-level analysis captures most variance" if icc > 0.5 else "Municipal-level analysis is essential — most variance is within states"}.',
        stat_value=round(icc, 3), stat_name='ICC',
        confidence=8,
        novelty=7,
        narrative_value=8 if icc < 0.5 else 5,
        recommendation='If ICC < 0.5, the dashboard MUST justify using state-level analysis when most variance is municipal.',
    ))

    # ── EXP 1.13: Spearman rank correlation (robust to outliers) ──────
    print("  [1.13] Spearman at municipal level...")
    sub = muni_latest.dropna(subset=['idde', 'rate_100k'])
    if len(sub) > 50:
        rho, p_sp = stats.spearmanr(sub['idde'], sub['rate_100k'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.13',
            title='Spearman rank correlation: IDDE → municipal crime',
            description='Non-parametric rank correlation, robust to outliers and nonlinear monotonic relationships',
            finding=f'ρ={rho:.4f}, p={p_sp:.4f}, N={len(sub)}. '
                    f'Compare to Pearson r from 1.1 to assess outlier influence.',
            stat_value=round(rho, 4), stat_name='rho', p_value=round(p_sp, 4),
            confidence=7 if p_sp < 0.05 else 3,
            novelty=4,
            narrative_value=5,
        ))

    # ── EXP 1.14: Crime type × IDDE correlation matrix ────────────────
    print("  [1.14] Crime type correlation matrix...")
    muni_types = muni_crime[muni_crime['ano'] == muni_crime['ano'].max()].copy()
    muni_types['idde'] = muni_types['estado'].map(idde_map)
    state_types = muni_types.groupby(['estado', 'subtipo']).agg({'total': 'sum', 'pop': 'first'}).reset_index()
    state_types['rate'] = (state_types['total'] / state_types['pop'].replace(0, np.nan)) * 1e5
    state_types['idde'] = state_types['estado'].map(idde_map)

    type_corrs = []
    for st, grp in state_types.groupby('subtipo'):
        sub = grp.dropna(subset=['idde', 'rate'])
        if len(sub) >= 15:
            r_t, p_t = stats.pearsonr(sub['idde'], sub['rate'])
            type_corrs.append({'subtipo': st, 'r': r_t, 'p': p_t, 'n': len(sub)})

    tc = pd.DataFrame(type_corrs).sort_values('r')
    if len(tc) > 5:
        # Top negative (crime reduced by IDDE)
        top_neg = tc.head(3)
        top_pos = tc.tail(3)
        neg_text = '; '.join(f'{r.subtipo}: r={r.r:.3f}' for _, r in top_neg.iterrows())
        pos_text = '; '.join(f'{r.subtipo}: r={r.r:.3f}' for _, r in top_pos.iterrows())
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.14',
            title='Crime type × IDDE correlation breakdown',
            description='Which specific crime types correlate most/least with IDDE?',
            finding=f'Most negative (crime ↓ with IDDE): {neg_text}. '
                    f'Most positive (crime ↑ with IDDE): {pos_text}.',
            stat_value=round(tc['r'].median(), 4), stat_name='median_r',
            confidence=7,
            novelty=8,
            narrative_value=8,
            recommendation='Crime type heterogeneity reveals which crimes digitalization might address.',
        ))

    # ── EXP 1.15: Year-by-year municipal cross-sections ───────────────
    print("  [1.15] Year-by-year municipal correlations...")
    yearly = []
    for yr in sorted(muni['ano'].unique()):
        yr_data = muni[muni['ano'] == yr].dropna(subset=['idde', 'rate_100k'])
        if len(yr_data) > 50:
            r_y, p_y = stats.pearsonr(yr_data['idde'], yr_data['rate_100k'])
            yearly.append({'year': yr, 'r': r_y, 'p': p_y, 'n': len(yr_data)})

    yd = pd.DataFrame(yearly)
    if len(yd) >= 2:
        trend_text = '; '.join(f'{int(r.year)}: r={r.r:.3f} (p={r.p:.3f})' for _, r in yd.iterrows())
        # Test if correlation is strengthening over time
        if len(yd) >= 3:
            r_trend, p_trend = stats.pearsonr(yd['year'], yd['r'])
        else:
            r_trend, p_trend = 0, 1
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.15',
            title='Year-by-year municipal IDDE→crime correlation trend',
            description='Is the IDDE-crime relationship stable across years or strengthening/weakening?',
            finding=f'{trend_text}. Trend in r: r_trend={r_trend:.3f}, p={p_trend:.4f}.',
            stat_value=round(r_trend, 4) if len(yd) >= 3 else None,
            stat_name='r_trend', p_value=round(p_trend, 4) if len(yd) >= 3 else None,
            confidence=6,
            novelty=7,
            narrative_value=7,
        ))

    # ── EXP 1.16: Municipality-level permutation test ─────────────────
    print("  [1.16] Permutation test (municipal)...")
    sub = muni_latest.dropna(subset=['idde', 'rate_100k'])
    if len(sub) > 50:
        observed_r, _ = stats.pearsonr(sub['idde'], sub['rate_100k'])
        rng = np.random.default_rng(42)
        n_perm = 5000
        perm_rs = []
        for _ in range(n_perm):
            shuffled = sub['idde'].values.copy()
            rng.shuffle(shuffled)
            perm_r, _ = stats.pearsonr(shuffled, sub['rate_100k'])
            perm_rs.append(perm_r)
        perm_rs = np.array(perm_rs)
        p_perm = np.mean(np.abs(perm_rs) >= np.abs(observed_r))

        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.16',
            title='Permutation test: IDDE → municipal crime (N=5000)',
            description='Exact p-value from label-shuffling permutation test, no distributional assumptions',
            finding=f'Observed r={observed_r:.4f}. Permutation p={p_perm:.4f} (5000 permutations). '
                    f'{"Significant" if p_perm < 0.05 else "Not significant"} — '
                    f'this is the most honest p-value possible.',
            stat_value=round(observed_r, 4), stat_name='r',
            p_value=round(p_perm, 4),
            confidence=9 if p_perm < 0.05 else 4,
            novelty=6,
            narrative_value=8 if p_perm < 0.05 else 3,
            recommendation='Permutation test is the gold standard for non-parametric inference. Report this number.',
        ))

    # ── EXP 1.17: DENUE business density vs IDDE ─────────────────────
    print("  [1.17] DENUE business density...")
    denue = D['denue'].copy()
    # Aggregate by state: total companies and employees
    denue_state = denue.groupby('estado').agg({
        'companies': 'sum',
        'number_of_employees_midpoint': 'sum'
    }).reset_index()
    denue_state['idde'] = denue_state['estado'].map(idde_map)
    cross_denue = cross.merge(denue_state, on='estado', how='left', suffixes=('', '_denue'))
    sub = cross_denue.dropna(subset=['idde', 'companies'])
    if len(sub) > 10:
        r_bd, p_bd = stats.pearsonr(sub['idde'], sub['companies'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='1.17',
            title='IDDE → Business density (DENUE)',
            description='Completely new data source: does digital development correlate with business count?',
            finding=f'r(IDDE, companies)={r_bd:.4f}, p={p_bd:.4f}, N={len(sub)}.',
            stat_value=round(r_bd, 4), stat_name='r', p_value=round(p_bd, 4),
            confidence=6 if p_bd < 0.05 else 3,
            novelty=8,
            narrative_value=7 if p_bd < 0.05 else 3,
            recommendation='DENUE is an entirely unused dataset. If significant, this adds a new dimension to the dashboard.',
        ))

    # Save and report
    path = session.save()
    print(session.summary())
    return session


if __name__ == '__main__':
    run()
