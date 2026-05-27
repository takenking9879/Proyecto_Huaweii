"""
Agent 4: Unorthodox — Novel, creative, and non-standard approaches.
Tests unconventional hypotheses, uses unused data sources, and applies
advanced methods that go beyond standard correlation analysis.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, QuantileRegressor, RANSACRegressor
from sklearn.ensemble import RandomForestRegressor
from experiments.data_utils import load_all_data, AgentSession, ExperimentResult

AGENT_ID = 'unorthodox'
OBJECTIVE = 'Test unconventional hypotheses: cifra negra, crime heterogeneity, quantile effects, stationarity, novel combos'


def run():
    session = AgentSession(AGENT_ID, OBJECTIVE)
    D = load_all_data()
    cross = D['cross_cl']
    panel = D['panel']
    muni_crime = D['muni_crime']
    muni_annual = D['muni_annual']
    victims = D['victims']
    denue = D['denue']
    INFRA_VARS = D['INFRA_VARS']
    SEC_COL_LABELS = D['SEC_COL_LABELS']

    print(f"Agent {AGENT_ID}: Exploring unorthodox hypotheses")

    # ── EXP 4.1: Cifra negra adjustment ───────────────────────────────
    print("  [4.1] Cifra negra (underreporting) adjustment...")
    # States with higher digital development likely report more crime
    # Adjust: reported_crime / reporting_rate = estimated_actual_crime
    # Use ENVIPE perception as proxy: states where people say "unsafe" likely report more
    if 'percepcion_segura' in cross.columns and 'crime_rate_100k' in cross.columns:
        idde_col = 'indice_de_desarrollo_digital_estatal_2025'
        sub = cross[['estado', idde_col, 'crime_rate_100k', 'percepcion_segura']].dropna()
        if len(sub) > 10:
            # Simple model: reporting rate ~ perception of insecurity
            # Higher insecurity → more reporting → reported rate is closer to actual
            sub['reporting_proxy'] = sub['percepcion_segura']  # % that say safe → could report
            sub['adjusted_crime'] = sub['crime_rate_100k'] / sub['reporting_proxy'].clip(0.1)
            r_raw, p_raw = stats.pearsonr(sub[idde_col], sub['crime_rate_100k'])
            r_adj, p_adj = stats.pearsonr(sub[idde_col], sub['adjusted_crime'])
            delta = r_adj - r_raw
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.1',
                title='Cifra negra: adjusted vs raw IDDE→crime',
                description='Adjusting crime rates for underreporting using perception as proxy',
                finding=f'Raw r={r_raw:.4f} (p={p_raw:.4f}). Adjusted r={r_adj:.4f} (p={p_adj:.4f}). '
                        f'Δ={delta:+.4f}. '
                        f'{"Underreporting inflates the IDDE-crime correlation" if delta < -0.05 else "Minimal impact of underreporting adjustment"}.',
                stat_value=round(r_adj, 4), stat_name='r_adjusted',
                p_value=round(p_adj, 4),
                confidence=5,  # proxy is crude
                novelty=9,
                narrative_value=8,
                recommendation='If delta is large, the dashboard MUST acknowledge cifra negra as a confounder.',
            ))

    # ── EXP 4.2: Crime type heterogeneity ─────────────────────────────
    print("  [4.2] Violent vs property vs fraud crime × IDDE...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    crime_groups = {
        'Violent': ['homicidio_rate_100k', 'robo_con_violencia_rate_100k'],
        'Property': ['robo_sin_violencia_rate_100k', 'robo_de_vehiculo_rate_100k'],
        'Cyber': ['fraude_rate_100k'],
        'Domestic': ['violencia_familiar_rate_100k'],
        'Drug': ['narcomenudeo_rate_100k'],
    }
    for group_name, cols in crime_groups.items():
        avail = [c for c in cols if c in cross.columns]
        if not avail:
            continue
        # Average rate across available crime types
        cross[f'_crime_{group_name}'] = cross[avail].mean(axis=1)
        sub = cross[[idde_col, f'_crime_{group_name}']].dropna()
        if len(sub) > 10:
            r_g, p_g = stats.pearsonr(sub[idde_col], sub[f'_crime_{group_name}'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.2',
                title=f'IDDE → {group_name} crime group',
                description=f'Composite rate of {group_name.lower()} crimes vs IDDE',
                finding=f'{group_name}: r={r_g:.4f}, p={p_g:.4f}. '
                        f'{"Negative (crime ↓ with IDDE)" if r_g < 0 else "Positive (crime ↑ with IDDE)"}.',
                stat_value=round(r_g, 4), stat_name='r',
                p_value=round(p_g, 4),
                confidence=6 if p_g < 0.05 else 3,
                novelty=7,
                narrative_value=8 if p_g < 0.05 else 3,
                recommendation=f'If {group_name} crime shows different direction than total crime, this is a key finding.',
            ))
        # Cleanup temp column
        cross.drop(columns=[f'_crime_{group_name}'], inplace=True, errors='ignore')

    # ── EXP 4.3: Quantile regression (median vs tails) ────────────────
    print("  [4.3] Quantile regression...")
    if idde_col in cross.columns and 'avg_wage' in cross.columns:
        sub = cross[[idde_col, 'avg_wage']].dropna()
        if len(sub) >= 15:
            X = sub[[idde_col]].values
            y = sub['avg_wage'].values
            quantiles = [0.25, 0.50, 0.75]
            quant_results = []
            for q in quantiles:
                try:
                    qr = QuantileRegressor(quantile=q, alpha=0, solver='highs')
                    qr.fit(X, y)
                    quant_results.append({'q': q, 'coef': qr.coef_[0], 'intercept': qr.intercept_})
                except Exception:
                    quant_results.append({'q': q, 'coef': np.nan, 'intercept': np.nan})
            valid = [r for r in quant_results if not np.isnan(r['coef'])]
            if len(valid) >= 2:
                spread = valid[-1]['coef'] - valid[0]['coef']
                session.record(ExperimentResult(
                    agent_id=AGENT_ID, exp_id='4.3',
                    title='Quantile regression: IDDE → Wage',
                    description='Does the IDDE-wage relationship differ at the 25th vs 75th percentile?',
                    finding='; '.join(f'Q{int(r["q"]*100)}: β={r["coef"]:.1f}' for r in valid) +
                            f'. Spread={spread:.1f}. '
                            f'{"Effect is heterogeneous across wage distribution" if abs(spread) > 200 else "Effect is similar across quantiles"}.',
                    stat_value=round(spread, 1), stat_name='quantile_spread',
                    confidence=6,
                    novelty=8,
                    narrative_value=7 if abs(spread) > 200 else 3,
                    recommendation='If spread is large, IDDE benefits high-wage states more (or less).',
                ))

    # ── EXP 4.4: RANSAC robust regression ─────────────────────────────
    print("  [4.4] RANSAC robust regression...")
    for x_col, y_col, label in [
        (idde_col, 'avg_wage', 'IDDE → Wage'),
        (idde_col, 'crime_rate_100k', 'IDDE → Crime'),
    ]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        sub = cross[[x_col, y_col]].dropna()
        if len(sub) < 15:
            continue
        X = sub[[x_col]].values
        y = sub[y_col].values
        # Standard OLS
        lr = LinearRegression().fit(X, y)
        r2_ols = lr.score(X, y)
        coef_ols = lr.coef_[0]
        # RANSAC
        ransac = RANSACRegressor(LinearRegression(), random_state=42)
        ransac.fit(X, y)
        r2_ransac = ransac.score(X, y)
        coef_ransac = ransac.estimator_.coef_[0]
        n_inliers = ransac.inlier_mask_.sum()
        n_outliers = (~ransac.inlier_mask_).sum()
        outlier_states = sub[~ransac.inlier_mask_]['estado'].tolist() if 'estado' in sub.columns else []
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.4',
            title=f'RANSAC robust: {label}',
            description='RANSAC identifies outliers automatically and fits to inliers only',
            finding=f'OLS β={coef_ols:.1f}, R²={r2_ols:.3f}. '
                    f'RANSAC β={coef_ransac:.1f}, R²={r2_ransac:.3f}. '
                    f'Inliers={n_inliers}, Outliers={n_outliers}: {", ".join(str(s)[:10] for s in outlier_states[:5])}.',
            stat_value=round(coef_ransac, 1), stat_name='ransac_coef',
            confidence=7,
            novelty=7,
            narrative_value=6,
        ))

    # ── EXP 4.5: Crime victim demographics ────────────────────────────
    print("  [4.5] Victim demographics × IDDE...")
    # Victims by sex
    vic_sex = victims.groupby(['estado', 'sexo_id']).agg({'total': 'sum'}).reset_index()
    vic_pivot = vic_sex.pivot_table(index='estado', columns='sexo_id', values='total', aggfunc='sum').fillna(0)
    if vic_pivot.shape[1] >= 2:
        vic_pivot['male_share'] = vic_pivot.iloc[:, 0] / vic_pivot.sum(axis=1)
        vic_pivot = vic_pivot.reset_index()
        vic_pivot['idde'] = vic_pivot['estado'].map(
            dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
        sub = vic_pivot.dropna(subset=['idde', 'male_share'])
        if len(sub) > 10:
            r_sex, p_sex = stats.pearsonr(sub['idde'], sub['male_share'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.5',
                title='IDDE → Male victim share',
                description='Does digitalization correlate with the gender distribution of crime victims?',
                finding=f'r(IDDE, male_share)={r_sex:.4f}, p={p_sex:.4f}.',
                stat_value=round(r_sex, 4), stat_name='r',
                p_value=round(p_sex, 4),
                confidence=5,
                novelty=8,
                narrative_value=6,
            ))

    # ── EXP 4.6: DENUE company size distribution × IDDE ───────────────
    print("  [4.6] Company size distribution × IDDE...")
    denue_agg = denue.groupby(['estado', 'company_size']).agg({
        'companies': 'sum', 'number_of_employees_midpoint': 'sum'
    }).reset_index()
    # Get share of large companies (251+)
    large = denue_agg[denue_agg['company_size'] == '251+'].set_index('estado')['companies']
    total = denue_agg.groupby('estado')['companies'].sum()
    large_share = (large / total).reset_index()
    large_share.columns = ['estado', 'large_share']
    large_share['idde'] = large_share['estado'].map(
        dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
    sub = large_share.dropna(subset=['idde', 'large_share'])
    if len(sub) > 10:
        r_ls, p_ls = stats.pearsonr(sub['idde'], sub['large_share'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.6',
            title='IDDE → Large company share (DENUE)',
            description='Does digital development correlate with having more large companies?',
            finding=f'r(IDDE, large_share)={r_ls:.4f}, p={p_ls:.4f}.',
            stat_value=round(r_ls, 4), stat_name='r',
            p_value=round(p_ls, 4),
            confidence=6 if p_ls < 0.05 else 3,
            novelty=8,
            narrative_value=7 if p_ls < 0.05 else 3,
            recommendation='DENUE is completely unused in the dashboard. If significant, adds economic depth.',
        ))

    # ── EXP 4.7: Total employment × IDDE ─────────────────────────────
    print("  [4.7] Total employment × IDDE (DENUE)...")
    emp_by_state = denue.groupby('estado').agg({
        'number_of_employees_midpoint': 'sum',
        'companies': 'sum'
    }).reset_index()
    emp_by_state['emp_per_company'] = (emp_by_state['number_of_employees_midpoint'] /
                                         emp_by_state['companies'].replace(0, np.nan))
    emp_by_state['idde'] = emp_by_state['estado'].map(
        dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
    sub = emp_by_state.dropna(subset=['idde', 'number_of_employees_midpoint'])
    if len(sub) > 10:
        r_emp, p_emp = stats.pearsonr(sub['idde'], sub['number_of_employees_midpoint'])
        r_epc, p_epc = stats.pearsonr(
            sub.dropna(subset=['idde', 'emp_per_company'])['idde'],
            sub.dropna(subset=['idde', 'emp_per_company'])['emp_per_company'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.7',
            title='IDDE → Employment (DENUE)',
            description='Total employment and employees-per-company vs IDDE',
            finding=f'Total employment: r={r_emp:.4f} (p={p_emp:.4f}). '
                    f'Employees/company: r={r_epc:.4f} (p={p_epc:.4f}).',
            stat_value=round(r_emp, 4), stat_name='r_total_emp',
            p_value=round(p_emp, 4),
            confidence=6 if p_emp < 0.05 else 3,
            novelty=8,
            narrative_value=7 if p_emp < 0.05 else 3,
        ))

    # ── EXP 4.8: Temporal stationarity test (panel) ───────────────────
    print("  [4.8] Stationarity test on IDDE panel...")
    # With only 4 years, formal ADF is unreliable, but we can check trend
    idde_series = panel.groupby('year')['idde_index'].mean()
    if len(idde_series) >= 4:
        # Simple trend test
        years = np.array(idde_series.index)
        values = idde_series.values
        slope, intercept, r, p, se = stats.linregress(years, values)
        # Unit root proxy: compare variance of first differences to levels
        diffs = np.diff(values)
        var_levels = np.var(values, ddof=1)
        var_diffs = np.var(diffs, ddof=1)
        ratio = var_diffs / var_levels if var_levels > 0 else 0
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.8',
            title='IDDE panel stationarity check',
            description='Is IDDE trending? If non-stationary, panel regression results may be spurious.',
            finding=f'Trend slope={slope:.3f}/year, R²={r**2:.3f}, p={p:.4f}. '
                    f'Var(diff)/Var(level)={ratio:.3f}. '
                    f'{"Trending upward" if slope > 0 and p < 0.10 else "No clear trend"}. '
                    f'With only 4 years, formal ADF is unreliable.',
            stat_value=round(ratio, 3), stat_name='var_ratio',
            confidence=4,  # very limited with 4 years
            novelty=7,
            narrative_value=5,
            recommendation='If IDDE is trending, panel FE might capture spurious trends. Acknowledge in defense doc.',
        ))

    # ── EXP 4.9: Lagged difference model ──────────────────────────────
    print("  [4.9] Lagged difference: Δcrime ~ ΔIDDE(t-1)...")
    # Arellano-Bond approximation with N=32, T=4
    panel_sorted = panel.sort_values(['estado', 'year'])
    lag_results = []
    for estado, grp in panel_sorted.groupby('estado'):
        if len(grp) < 3:
            continue
        grp = grp.sort_values('year')
        for i in range(1, len(grp)):
            lag_results.append({
                'estado': estado,
                'year': grp.iloc[i]['year'],
                'd_idde_t': grp.iloc[i]['idde_index'] - grp.iloc[i-1]['idde_index'],
                'd_crime_t': grp.iloc[i]['crime_rate'] - grp.iloc[i-1]['crime_rate'],
                'd_idde_t1': grp.iloc[i-1]['idde_index'] - (grp.iloc[i-2]['idde_index'] if i >= 2 else np.nan),
                'crime_level_t1': grp.iloc[i-1]['crime_rate'],
            })
    lag_df = pd.DataFrame(lag_results).dropna()
    if len(lag_df) > 30:
        # Δcrime(t) ~ ΔIDDE(t-1) + crime_level(t-1)
        sub = lag_df.dropna(subset=['d_idde_t1', 'd_crime_t', 'crime_level_t1'])
        X = sub[['d_idde_t1', 'crime_level_t1']].values
        y = sub['d_crime_t'].values
        lr = LinearRegression().fit(X, y)
        r2 = lr.score(X, y)
        coef_idde = lr.coef_[0]
        t_stat = coef_idde / (np.std(y - lr.predict(X)) / np.sqrt(len(y))) if np.std(y - lr.predict(X)) > 0 else 0
        # Simple correlation for comparison
        r_simple, p_simple = stats.pearsonr(sub['d_idde_t1'], sub['d_crime_t'])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.9',
            title='Lagged difference: Δcrime(t) ~ ΔIDDE(t-1)',
            description='Dynamic panel approximation: does last year IDDE change predict this year crime change?',
            finding=f'β(ΔIDDE t-1)={coef_idde:.4f}, R²={r2:.4f}, N={len(sub)} (state×year obs). '
                    f'Simple r(ΔIDDE_t-1, Δcrime_t)={r_simple:.4f}, p={p_simple:.4f}. '
                    f'{"Temporal precedence confirmed" if p_simple < 0.05 else "No significant lagged effect"}.',
            stat_value=round(coef_idde, 4), stat_name='beta_lagged',
            p_value=round(p_simple, 4),
            confidence=6 if p_simple < 0.05 else 3,
            novelty=7,
            narrative_value=8 if p_simple < 0.05 else 3,
            recommendation='This is the closest we can get to Granger causality with 4 years.',
        ))

    # ── EXP 4.10: Rank-rank regression ────────────────────────────────
    print("  [4.10] Rank-rank regression...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    for target_col, target_name in [('avg_wage', 'Wage'), ('crime_rate_100k', 'Crime')]:
        if idde_col not in cross.columns or target_col not in cross.columns:
            continue
        sub = cross[['estado', idde_col, target_col]].dropna()
        if len(sub) < 15:
            continue
        sub['rank_idde'] = sub[idde_col].rank()
        sub['rank_target'] = sub[target_col].rank()
        r_rank, p_rank = stats.pearsonr(sub['rank_idde'], sub['rank_target'])
        r_raw, p_raw = stats.pearsonr(sub[idde_col], sub[target_col])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.10',
            title=f'Rank-rank: IDDE → {target_name}',
            description='Rank correlation removes scale effects; tests pure ordinal relationship',
            finding=f'Rank-rank r={r_rank:.4f} (p={p_rank:.4f}), Raw r={r_raw:.4f} (p={p_raw:.4f}). '
                    f'Δ={r_rank-r_raw:+.4f}.',
            stat_value=round(r_rank, 4), stat_name='r_rank',
            p_value=round(p_rank, 4),
            confidence=6,
            novelty=5,
            narrative_value=5,
        ))

    # ── EXP 4.11: Crime seasonality × IDDE ────────────────────────────
    print("  [4.11] Crime seasonality × IDDE...")
    months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    muni_crime_latest = muni_crime[muni_crime['ano'] == muni_crime['ano'].max()].copy()
    muni_crime_latest['idde'] = muni_crime_latest['estado'].map(
        dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
    # Get monthly variance by state (measure of seasonality)
    # First need monthly data — the muni_crime table has annual totals already aggregated
    # Let's use a different approach: crime type concentration as proxy
    if 'subtipo' in muni_crime_latest.columns:
        state_type = muni_crime_latest.groupby(['estado', 'subtipo']).agg({'total': 'sum'}).reset_index()
        state_total = state_type.groupby('estado')['total'].sum()
        # HHI (Herfindahl) for crime type concentration
        state_type['share'] = state_type.apply(
            lambda r: (r['total'] / state_total[r['estado']])**2 if state_total[r['estado']] > 0 else 0, axis=1)
        hhi = state_type.groupby('estado')['share'].sum().reset_index()
        hhi.columns = ['estado', 'crime_hhi']
        hhi['idde'] = hhi['estado'].map(
            dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
        sub = hhi.dropna(subset=['idde', 'crime_hhi'])
        if len(sub) > 10:
            r_hhi, p_hhi = stats.pearsonr(sub['idde'], sub['crime_hhi'])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.11',
                title='IDDE → Crime type concentration (HHI)',
                description='Herfindahl index of crime types: higher = more concentrated in few types',
                finding=f'r(IDDE, HHI)={r_hhi:.4f}, p={p_hhi:.4f}. '
                        f'{"Higher IDDE → more diverse crime" if r_hhi < 0 and p_hhi < 0.05 else "No significant relationship"}.',
                stat_value=round(r_hhi, 4), stat_name='r',
                p_value=round(p_hhi, 4),
                confidence=5 if p_hhi < 0.05 else 3,
                novelty=8,
                narrative_value=6 if p_hhi < 0.05 else 2,
            ))

    # ── EXP 4.12: Digital inequality (Gini of IDDE sub-pillars) ───────
    print("  [4.12] Digital inequality within IDDE...")
    subpillar_cols = [c for c in cross.columns if 'subpilar' in c.lower() or 'pilar_de' in c.lower()]
    if len(subpillar_cols) >= 3:
        # For each state, compute the coefficient of variation across IDDE sub-pillars
        digital_ineq = []
        for _, row in cross.iterrows():
            vals = [row[c] for c in subpillar_cols if pd.notna(row[c])]
            if len(vals) >= 3 and np.mean(vals) > 0:
                cv = np.std(vals) / np.mean(vals)
                digital_ineq.append({'estado': row['estado'], 'digital_cv': cv})
        di = pd.DataFrame(digital_ineq)
        di['idde'] = di['estado'].map(
            dict(zip(cross['estado'], cross['indice_de_desarrollo_digital_estatal_2025'])))
        # Does digital inequality predict crime?
        if 'crime_rate_100k' in cross.columns:
            di = di.merge(cross[['estado', 'crime_rate_100k']], on='estado', how='left')
            sub = di.dropna(subset=['digital_cv', 'crime_rate_100k'])
            if len(sub) > 10:
                r_di, p_di = stats.pearsonr(sub['digital_cv'], sub['crime_rate_100k'])
                session.record(ExperimentResult(
                    agent_id=AGENT_ID, exp_id='4.12',
                    title='Digital inequality (CV) → Crime',
                    description='States with unbalanced digital development (high in some areas, low in others)',
                    finding=f'r(digital_CV, crime)={r_di:.4f}, p={p_di:.4f}. '
                            f'{"Unbalanced digitalization → more crime" if r_di > 0 and p_di < 0.05 else "No significant relationship"}.',
                    stat_value=round(r_di, 4), stat_name='r',
                    p_value=round(p_di, 4),
                    confidence=5 if p_di < 0.05 else 3,
                    novelty=9,
                    narrative_value=8 if p_di < 0.05 else 3,
                    recommendation='If significant, the dashboard should warn that UNBALANCED digitalization is harmful.',
                ))

    # ── EXP 4.13: Natural experiment: states with biggest IDDE jumps ──
    print("  [4.13] Natural experiment: largest IDDE jumps...")
    if len(panel) > 0:
        idde_changes = panel.sort_values(['estado', 'year']).groupby('estado').apply(
            lambda g: g['idde_index'].iloc[-1] - g['idde_index'].iloc[0] if len(g) >= 2 else 0,
            include_groups=False
        ).reset_index(name='idde_change')
        idde_changes = idde_changes.sort_values('idde_change', ascending=False)
        top5_states = idde_changes.head(5)['estado'].tolist()
        bottom5_states = idde_changes.tail(5)['estado'].tolist()
        # Compare crime change in top vs bottom
        if 'crime_rate' in panel.columns:
            crime_changes = panel.sort_values(['estado', 'year']).groupby('estado').apply(
                lambda g: g['crime_rate'].iloc[-1] - g['crime_rate'].iloc[0] if len(g) >= 2 else 0,
                include_groups=False
            ).reset_index(name='crime_change')
            top5_crime = crime_changes[crime_changes['estado'].isin(top5_states)]['crime_change'].mean()
            bot5_crime = crime_changes[crime_changes['estado'].isin(bottom5_states)]['crime_change'].mean()
            diff = top5_crime - bot5_crime
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.13',
                title='Natural experiment: top vs bottom IDDE changers',
                description=f'Top 5 IDDE changers ({", ".join(s[:8] for s in top5_states)}) vs bottom 5',
                finding=f'Top 5 crime Δ: {top5_crime:.1f}. Bottom 5 crime Δ: {bot5_crime:.1f}. '
                        f'Diff: {diff:.1f}. '
                        f'{"Top IDDE changers reduced crime more" if diff < 0 else "Top IDDE changers did NOT reduce crime more"}.',
                stat_value=round(diff, 1), stat_name='crime_diff',
                confidence=4,  # very small N
                novelty=7,
                narrative_value=6,
            ))

    # ── EXP 4.14: Entropy-based dependency ────────────────────────────
    print("  [4.14] Entropy-based dependency...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    for target_col, target_name in [('crime_rate_100k', 'Crime'), ('avg_wage', 'Wage')]:
        if idde_col not in cross.columns or target_col not in cross.columns:
            continue
        sub = cross[[idde_col, target_col]].dropna()
        if len(sub) < 15:
            continue
        # Discretize into 4 bins
        x_bins = pd.qcut(sub[idde_col], q=4, labels=False, duplicates='drop')
        y_bins = pd.qcut(sub[target_col], q=4, labels=False, duplicates='drop')
        # Joint entropy
        joint = pd.crosstab(x_bins, y_bins, normalize=True)
        h_xy = -np.sum(joint.values * np.log2(joint.values + 1e-10))
        h_x = -np.sum(joint.sum(axis=1).values * np.log2(joint.sum(axis=1).values + 1e-10))
        h_y = -np.sum(joint.sum(axis=0).values * np.log2(joint.sum(axis=0).values + 1e-10))
        mi = h_x + h_y - h_xy  # mutual information
        nmi = mi / np.sqrt(h_x * h_y) if h_x > 0 and h_y > 0 else 0  # normalized
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='4.14',
            title=f'Entropy-based: IDDE ↔ {target_name}',
            description='Normalized mutual information from discretized variables (captures nonlinear deps)',
            finding=f'MI={mi:.3f}, NMI={nmi:.3f} (normalized to [0,1]). '
                    f'Compare to Pearson r² from linear correlation.',
            stat_value=round(nmi, 3), stat_name='NMI',
            confidence=5,
            novelty=7,
            narrative_value=5,
        ))

    # ── EXP 4.15: Crime reduction leaders analysis ────────────────────
    print("  [4.15] Crime reduction leaders...")
    if 'crime_rate' in panel.columns:
        crime_chg = panel.sort_values(['estado', 'year']).groupby('estado').apply(
            lambda g: g['crime_rate'].iloc[-1] - g['crime_rate'].iloc[0] if len(g) >= 2 else 0,
            include_groups=False
        ).reset_index(name='crime_change')
        crime_chg = crime_chg.merge(
            cross[['estado', 'indice_de_desarrollo_digital_estatal_2025']],
            on='estado', how='left')
        crime_chg = crime_chg.merge(
            cross[['estado', 'cluster']],
            on='estado', how='left', suffixes=('', '_cl'))
        sub = crime_chg.dropna(subset=['indice_de_desarrollo_digital_estatal_2025', 'crime_change'])
        if len(sub) > 10:
            r_cr, p_cr = stats.pearsonr(sub['indice_de_desarrollo_digital_estatal_2025'], sub['crime_change'])
            # Who are the crime reduction leaders?
            leaders = sub[sub['crime_change'] < 0].sort_values('crime_change')
            leader_text = ', '.join(f"{r['estado'][:8]}({r['crime_change']:.0f})" for _, r in leaders.head(5).iterrows())
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='4.15',
                title='Crime reduction leaders × IDDE',
                description='Which states reduced crime the most? Do they have high IDDE?',
                finding=f'r(IDDE, Δcrime)={r_cr:.4f}, p={p_cr:.4f}. '
                        f'Crime reducers: {leader_text}. '
                        f'{"Higher IDDE → more crime reduction" if r_cr < 0 and p_cr < 0.05 else "IDDE does not predict crime reduction direction"}.',
                stat_value=round(r_cr, 4), stat_name='r',
                p_value=round(p_cr, 4),
                confidence=6 if p_cr < 0.05 else 3,
                novelty=6,
                narrative_value=7 if p_cr < 0.05 else 3,
            ))

    # ── EXP 4.16: Cross-table composite evidence score ────────────────
    print("  [4.16] Cross-table composite evidence score...")
    # Build a composite "digital advantage" score from multiple data sources
    # and test if it predicts outcomes better than IDDE alone
    composite_parts = []
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    if idde_col in cross.columns:
        composite_parts.append(('idde', cross[idde_col]))
    if 'avg_wage' in cross.columns:
        composite_parts.append(('wage', cross['avg_wage']))
    # Add DENUE employment
    emp_map = dict(zip(denue.groupby('estado')['number_of_employees_midpoint'].sum().index,
                       denue.groupby('estado')['number_of_employees_midpoint'].sum().values))
    cross['_denue_emp'] = cross['estado'].map(emp_map)
    if cross['_denue_emp'].notna().sum() > 10:
        composite_parts.append(('denue_emp', cross['_denue_emp']))

    if len(composite_parts) >= 2:
        # Standardize and average
        from sklearn.preprocessing import StandardScaler
        parts = [StandardScaler().fit_transform(v.values.reshape(-1, 1)).flatten()
                 for _, v in composite_parts]
        composite = np.nanmean(parts, axis=0)
        cross['_composite'] = composite
        for target_col, target_name in [('crime_rate_100k', 'Crime'), ('conf_familia', 'Family trust')]:
            if target_col not in cross.columns:
                continue
            sub = cross[['_composite', target_col]].dropna()
            if len(sub) > 10:
                r_c, p_c = stats.pearsonr(sub['_composite'], sub[target_col])
                r_idde, p_idde = stats.pearsonr(
                    cross[[idde_col, target_col]].dropna()[idde_col],
                    cross[[idde_col, target_col]].dropna()[target_col])
                session.record(ExperimentResult(
                    agent_id=AGENT_ID, exp_id='4.16',
                    title=f'Composite score → {target_name}',
                    description=f'Average of {len(composite_parts)} standardized variables (IDDE + employment + wages)',
                    finding=f'Composite r={r_c:.4f} (p={p_c:.4f}) vs IDDE r={r_idde:.4f} (p={p_idde:.4f}). '
                            f'Δ={abs(r_c)-abs(r_idde):+.4f}.',
                    stat_value=round(r_c, 4), stat_name='r_composite',
                    p_value=round(p_c, 4),
                    confidence=6,
                    novelty=7,
                    narrative_value=6,
                ))
        cross.drop(columns=['_composite', '_denue_emp'], inplace=True, errors='ignore')

    path = session.save()
    print(session.summary())
    return session


if __name__ == '__main__':
    run()
