"""
Agent 2: Robustness — Stress-test existing dashboard claims.
Identifies which findings are driven by outliers, which hold under
different specifications, and which are fragile.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from experiments.data_utils import load_all_data, AgentSession, ExperimentResult

AGENT_ID = 'robustness'
OBJECTIVE = 'Stress-test every key dashboard claim: leave-one-out, winsorize, permutation, alternative specs'


def run():
    session = AgentSession(AGENT_ID, OBJECTIVE)
    D = load_all_data()
    cross = D['cross_cl']
    panel = D['panel']
    INFRA_VARS = D['INFRA_VARS']
    SEC_COL_LABELS = D['SEC_COL_LABELS']

    # Key correlations to test (from dashboard)
    key_pairs = [
        ('cobertura_de_banda_ancha_fija_por', 'conf_amigos', 'BB coverage → Friend trust (r=0.78)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'conf_familia', 'IDDE → Family trust (r=0.65)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'fraude_rate_100k', 'IDDE → Fraud (r=0.63)'),
        ('empresas_que_utilizan_banca_electronica_por', 'avg_wage', 'E-banking → Wage (R²=0.43)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'percepcion_segura', 'IDDE → Safety perception (R²=0.45)'),
        ('cobertura_de_banda_ancha_fija_por', 'avg_wage', 'BB coverage → Wage (r=0.67)'),
    ]

    print(f"Agent {AGENT_ID}: Testing {len(key_pairs)} key correlations × multiple robustness checks")

    # ── EXP 2.1: Leave-one-out influence ──────────────────────────────
    print("  [2.1] Leave-one-out influence analysis...")
    loo_results = {}
    for x_col, y_col, label in key_pairs:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[['estado', x_col, y_col]].dropna()
        full_r, _ = stats.pearsonr(df[x_col], df[y_col])
        max_delta = 0
        max_state = ''
        for i in range(len(df)):
            loo = df.drop(df.index[i])
            loo_r, _ = stats.pearsonr(loo[x_col], loo[y_col])
            delta = abs(loo_r - full_r)
            if delta > max_delta:
                max_delta = delta
                max_state = df.iloc[i]['estado']
        loo_results[label] = {'full_r': round(full_r, 4),
                               'max_delta': round(max_delta, 4),
                               'max_state': max_state}
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id=f'2.1',
            title=f'LOO influence: {label}',
            description='How much does removing one state change the correlation?',
            finding=f'Full r={full_r:.4f}. Max Δr={max_delta:.4f} (removing {max_state}). '
                    f'{"Robust" if max_delta < 0.10 else "Sensitive to " + max_state}.',
            stat_value=round(max_delta, 4), stat_name='max_delta_r',
            confidence=8,
            novelty=5,
            narrative_value=7 if max_delta > 0.10 else 4,
            recommendation=f'If max_delta > 0.10, the correlation is driven by {max_state}. Must disclose.',
        ))

    # ── EXP 2.2: Cook's distance ─────────────────────────────────────
    print("  [2.2] Cook's distance analysis...")
    for x_col, y_col, label in key_pairs[:3]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[['estado', x_col, y_col]].dropna()
        X = df[[x_col]].values
        y = df[y_col].values
        lr = LinearRegression().fit(X, y)
        y_pred = lr.predict(X)
        residuals = y - y_pred
        mse = np.mean(residuals**2)
        h = np.diag(X @ np.linalg.pinv(X.T @ X) @ X.T)  # leverage
        cooks = residuals**2 / (mse * 2) * h / (1 - h)**2
        df = df.copy()
        df['cooks_d'] = cooks
        threshold = 4 / len(df)
        influential = df[df['cooks_d'] > threshold]
        if len(influential) > 0:
            states_str = ', '.join(influential['estado'].tolist())
            max_cooks = influential['cooks_d'].max()
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='2.2',
                title=f"Cook's distance: {label}",
                description=f'States with Cook\'s D > {threshold:.3f} (4/n threshold)',
                finding=f'{len(influential)} influential states: {states_str}. Max Cook\'s D={max_cooks:.3f}.',
                stat_value=round(max_cooks, 3), stat_name='max_cooks_d',
                confidence=7,
                novelty=5,
                narrative_value=6,
            ))

    # ── EXP 2.3: Winsorized correlations ──────────────────────────────
    print("  [2.3] Winsorized (5%) correlations...")
    for x_col, y_col, label in key_pairs:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[['estado', x_col, y_col]].dropna().copy()
        for col in [x_col, y_col]:
            lo, hi = df[col].quantile(0.025), df[col].quantile(0.975)
            df[col] = df[col].clip(lo, hi)
        r_win, p_win = stats.pearsonr(df[x_col], df[y_col])
        full_r, _ = stats.pearsonr(cross[[x_col, y_col]].dropna()[x_col],
                                    cross[[x_col, y_col]].dropna()[y_col])
        delta = abs(r_win - full_r)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.3',
            title=f'Winsorized (5%): {label}',
            description='Correlation after clipping extreme values at 2.5%/97.5%',
            finding=f'Winsorized r={r_win:.4f} vs original r={full_r:.4f}. Δ={delta:.4f}. '
                    f'{"Robust to outliers" if delta < 0.05 else "Sensitive to outliers"}.',
            stat_value=round(r_win, 4), stat_name='r_winsorized',
            confidence=7,
            novelty=4,
            narrative_value=5,
        ))

    # ── EXP 2.4: Permutation test for key correlations ────────────────
    print("  [2.4] Permutation tests (1000×)...")
    rng = np.random.default_rng(42)
    for x_col, y_col, label in key_pairs[:3]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        observed_r, _ = stats.pearsonr(df[x_col], df[y_col])
        perm_rs = []
        for _ in range(1000):
            shuffled = df[x_col].values.copy()
            rng.shuffle(shuffled)
            pr, _ = stats.pearsonr(shuffled, df[y_col])
            perm_rs.append(pr)
        p_perm = np.mean(np.abs(perm_rs) >= np.abs(observed_r))
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.4',
            title=f'Permutation test: {label}',
            description='Exact p-value from 1000 label-shuffling permutations',
            finding=f'r={observed_r:.4f}, permutation p={p_perm:.4f} (1000 perms). '
                    f'{"Confirmed significant" if p_perm < 0.05 else "NOT confirmed"}.',
            stat_value=round(observed_r, 4), stat_name='r',
            p_value=round(p_perm, 4),
            confidence=9 if p_perm < 0.05 else 5,
            novelty=5,
            narrative_value=7 if p_perm < 0.05 else 4,
        ))

    # ── EXP 2.5: Subsample bootstrap (80% × 500) ─────────────────────
    print("  [2.5] Subsample bootstrap stability...")
    for x_col, y_col, label in key_pairs[:3]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        n = len(df)
        n_sub = int(n * 0.8)
        boot_rs = []
        for _ in range(500):
            idx = rng.choice(n, size=n_sub, replace=False)
            sub = df.iloc[idx]
            br, _ = stats.pearsonr(sub[x_col], sub[y_col])
            boot_rs.append(br)
        ci_lo, ci_hi = np.percentile(boot_rs, [2.5, 97.5])
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.5',
            title=f'Bootstrap 80% stability: {label}',
            description='Correlation stability when using 80% subsamples (500 iterations)',
            finding=f'Bootstrap r: median={np.median(boot_rs):.4f}, '
                    f'95% CI=[{ci_lo:.4f}, {ci_hi:.4f}]. '
                    f'Range width={ci_hi-ci_lo:.4f}.',
            stat_value=round(np.median(boot_rs), 4), stat_name='median_r',
            confidence=8,
            novelty=4,
            narrative_value=5,
        ))

    # ── EXP 2.6: Leave-region-out ─────────────────────────────────────
    print("  [2.6] Leave-region-out...")
    # Rough geographic groupings
    north = ['Baja California', 'Baja California Sur', 'Sonora', 'Chihuahua',
             'Coahuila', 'Nuevo León', 'Tamaulipas', 'Sinaloa', 'Durango']
    central = ['Aguascalientes', 'Guanajuato', 'Jalisco', 'Querétaro',
               'San Luis Potosí', 'Zacatecas', 'Nayarit', 'Colima']
    south = ['Campeche', 'Chiapas', 'Guerrero', 'Oaxaca', 'Quintana Roo',
             'Tabasco', 'Veracruz', 'Yucatán']
    regions = {'North': north, 'Central': central, 'South': south}

    for x_col, y_col, label in key_pairs[:2]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[['estado', x_col, y_col]].dropna()
        full_r, _ = stats.pearsonr(df[x_col], df[y_col])
        for region_name, region_states in regions.items():
            loo = df[~df['estado'].isin(region_states)]
            if len(loo) > 10:
                loo_r, _ = stats.pearsonr(loo[x_col], loo[y_col])
                delta = loo_r - full_r
                session.record(ExperimentResult(
                    agent_id=AGENT_ID, exp_id='2.6',
                    title=f'Leave {region_name} out: {label}',
                    description=f'Correlation after removing all {region_name} states',
                    finding=f'Full r={full_r:.4f}, without {region_name} r={loo_r:.4f}, Δ={delta:+.4f}.',
                    stat_value=round(loo_r, 4), stat_name=f'r_no_{region_name.lower()}',
                    confidence=6,
                    novelty=6,
                    narrative_value=6 if abs(delta) > 0.05 else 3,
                ))

    # ── EXP 2.7: IDDE pillar decomposition ────────────────────────────
    print("  [2.7] IDDE pillar decomposition...")
    pillar_cols = [
        ('pilar_de_gobierno_digital', 'Gov digital pillar'),
        ('pilar_de_economia_digital', 'Economy digital pillar'),
        ('pilar_de_infraestructura_digital', 'Infra digital pillar'),
        ('subpilar_de_innovacion', 'Innovation subpillar'),
    ]
    target = 'crime_rate_100k'
    for pcol, pname in pillar_cols:
        if pcol in cross.columns and target in cross.columns:
            sub = cross[[pcol, target]].dropna()
            if len(sub) > 10:
                r_p, p_p = stats.pearsonr(sub[pcol], sub[target])
                session.record(ExperimentResult(
                    agent_id=AGENT_ID, exp_id='2.7',
                    title=f'{pname} → Crime rate',
                    description=f'Which IDDE pillar drives the crime correlation?',
                    finding=f'{pname}: r={r_p:.4f}, p={p_p:.4f}.',
                    stat_value=round(r_p, 4), stat_name='r_pillar',
                    p_value=round(p_p, 4),
                    confidence=6 if p_p < 0.05 else 3,
                    novelty=7,
                    narrative_value=7 if p_p < 0.05 else 3,
                    recommendation='If one pillar dominates, the dashboard should highlight that specific pillar.',
                ))

    # ── EXP 2.8: Spearman vs Pearson ──────────────────────────────────
    print("  [2.8] Spearman vs Pearson comparison...")
    for x_col, y_col, label in key_pairs:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        r_p, p_p = stats.pearsonr(df[x_col], df[y_col])
        r_s, p_s = stats.spearmanr(df[x_col], df[y_col])
        delta = r_s - r_p
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.8',
            title=f'Spearman vs Pearson: {label}',
            description='Does rank correlation differ from Pearson? Tests for nonlinearity/outliers.',
            finding=f'Pearson r={r_p:.4f}, Spearman ρ={r_s:.4f}, Δ={delta:+.4f}. '
                    f'{"Nonlinearity detected" if abs(delta) > 0.10 else "Consistent"}.',
            stat_value=round(r_s, 4), stat_name='rho',
            confidence=7,
            novelty=5,
            narrative_value=6 if abs(delta) > 0.10 else 3,
        ))

    # ── EXP 2.9: Year-by-year cross-sections ─────────────────────────
    print("  [2.9] Year-by-year panel cross-sections...")
    for target in ['avg_wage', 'crime_rate_100k']:
        idde_col = 'indice_de_desarrollo_digital_estatal_2025'
        yearly = []
        for yr in sorted(panel['year'].unique()):
            yr_panel = panel[panel['year'] == yr].merge(
                cross[['estado', target]], on='estado', how='left')
            sub = yr_panel[['idde_index', target]].dropna()
            if len(sub) > 10:
                r_y, p_y = stats.pearsonr(sub['idde_index'], sub[target])
                yearly.append({'year': int(yr), 'r': round(r_y, 4), 'p': round(p_y, 4), 'n': len(sub)})
        if len(yearly) >= 2:
            trend = '; '.join(f"{y['year']}: r={y['r']}" for y in yearly)
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='2.9',
                title=f'Panel year-by-year: IDDE → {target}',
                description='Does the cross-sectional relationship hold in each year separately?',
                finding=f'{trend}. '
                        f'{"Consistent across years" if all(y["r"] < 0 for y in yearly) or all(y["r"] > 0 for y in yearly) else "Direction varies by year"}.',
                stat_value=yearly[-1]['r'] if yearly else None, stat_name=f'r_{yearly[-1]["year"]}' if yearly else None,
                confidence=7,
                novelty=5,
                narrative_value=6,
            ))

    # ── EXP 2.10: Trimmed means comparison ────────────────────────────
    print("  [2.10] Trimmed means (20%) for $790 claim...")
    # Sustained vs inconsistent investment with 20% trimmed means
    panel['idde_pct_change'] = panel.groupby('estado')['idde_index'].pct_change()
    pct_changes = panel.groupby('estado')['idde_pct_change'].apply(
        lambda x: (x > 0).sum()
    ).reset_index(name='n_increases')
    sustained = pct_changes[pct_changes['n_increases'] >= 3]['estado']
    inconsistent = pct_changes[pct_changes['n_increases'] < 3]['estado']

    if 'avg_wage' in cross.columns:
        s_wages = cross[cross['estado'].isin(sustained)]['avg_wage'].dropna()
        i_wages = cross[cross['estado'].isin(inconsistent)]['avg_wage'].dropna()
        if len(s_wages) >= 3 and len(i_wages) >= 10:
            # Trimmed means (20%)
            from scipy.stats import trim_mean
            s_trim = trim_mean(s_wages, 0.2) if len(s_wages) >= 5 else s_wages.mean()
            i_trim = trim_mean(i_wages, 0.2)
            diff_trim = s_trim - i_trim
            diff_raw = s_wages.mean() - i_wages.mean()
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='2.10',
                title='Trimmed means (20%): wage gap',
                description='Wage gap after trimming 20% from each tail to remove outlier influence',
                finding=f'Trimmed gap=${diff_trim:.0f} vs raw gap=${diff_raw:.0f}. '
                        f'N(sustained)={len(s_wages)}, N(inconsistent)={len(i_wages)}.',
                stat_value=round(diff_trim, 0), stat_name='trimmed_gap',
                confidence=5,
                novelty=4,
                narrative_value=5,
            ))

    # ── EXP 2.11: Alternative IDDE specifications ─────────────────────
    print("  [2.11] Alternative IDDE: subpillars vs outcomes...")
    subpilars = [c for c in cross.columns if 'subpilar' in c.lower()]
    for sp in subpilars[:4]:
        for target, tname in [('avg_wage', 'Wage'), ('crime_rate_100k', 'Crime')]:
            if target in cross.columns:
                sub = cross[[sp, target]].dropna()
                if len(sub) > 10:
                    r_sp, p_sp = stats.pearsonr(sub[sp], sub[target])
                    session.record(ExperimentResult(
                        agent_id=AGENT_ID, exp_id='2.11',
                        title=f'{sp[:30]}... → {tname}',
                        description='Alternative IDDE specification using subpillars instead of aggregate',
                        finding=f'r={r_sp:.4f}, p={p_sp:.4f}.',
                        stat_value=round(r_sp, 4), stat_name='r_subpillar',
                        p_value=round(p_sp, 4),
                        confidence=5 if p_sp < 0.05 else 3,
                        novelty=5,
                        narrative_value=5 if p_sp < 0.05 else 2,
                    ))

    # ── EXP 2.12: Quadratic vs linear fit ─────────────────────────────
    print("  [2.12] Quadratic vs linear fit comparison...")
    for x_col, y_col, label in key_pairs[:3]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        X = df[x_col].values
        y = df[y_col].values
        # Linear
        lr1 = LinearRegression().fit(X.reshape(-1, 1), y)
        r2_lin = lr1.score(X.reshape(-1, 1), y)
        # Quadratic
        X2 = np.column_stack([X, X**2])
        lr2 = LinearRegression().fit(X2, y)
        r2_quad = lr2.score(X2, y)
        delta_r2 = r2_quad - r2_lin
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.12',
            title=f'Linear vs quadratic: {label}',
            description='Does a quadratic term improve the fit?',
            finding=f'Linear R²={r2_lin:.4f}, Quadratic R²={r2_quad:.4f}, ΔR²={delta_r2:+.4f}. '
                    f'{"Nonlinear effect detected" if delta_r2 > 0.05 else "Linear is sufficient"}.',
            stat_value=round(delta_r2, 4), stat_name='delta_R2',
            confidence=6,
            novelty=6 if delta_r2 > 0.05 else 3,
            narrative_value=6 if delta_r2 > 0.05 else 2,
        ))

    # ── EXP 2.13: Control for population ──────────────────────────────
    print("  [2.13] Partial correlation controlling for population...")
    if 'poblacion_total_2020' in cross.columns:
        for x_col, y_col, label in key_pairs[:2]:
            if x_col not in cross.columns or y_col not in cross.columns:
                continue
            df = cross[['estado', x_col, y_col, 'poblacion_total_2020']].dropna()
            # Partial correlation: residualize x and y against population
            z = df['poblacion_total_2020'].values
            x_res = LinearRegression().fit(z.reshape(-1, 1), df[x_col].values).predict(z.reshape(-1, 1))
            y_res = LinearRegression().fit(z.reshape(-1, 1), df[y_col].values).predict(z.reshape(-1, 1))
            x_partial = df[x_col].values - x_res
            y_partial = df[y_col].values - y_res
            r_partial, p_partial = stats.pearsonr(x_partial, y_partial)
            r_unadjusted, _ = stats.pearsonr(df[x_col], df[y_col])
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='2.13',
                title=f'Partial r (controlling pop): {label}',
                description='Correlation after removing the effect of state population',
                finding=f'Unadjusted r={r_unadjusted:.4f}, partial r={r_partial:.4f}, '
                        f'Δ={r_partial-r_unadjusted:+.4f}. p={p_partial:.4f}.',
                stat_value=round(r_partial, 4), stat_name='partial_r',
                p_value=round(p_partial, 4),
                confidence=7,
                novelty=6,
                narrative_value=7,
                recommendation='If partial r is much smaller, population is a confounder.',
            ))

    # ── EXP 2.14: Weighted regression (by population) ─────────────────
    print("  [2.14] Population-weighted regressions...")
    if 'poblacion_total_2020' in cross.columns:
        for x_col, y_col, label in key_pairs[:3]:
            if x_col not in cross.columns or y_col not in cross.columns:
                continue
            df = cross[[x_col, y_col, 'poblacion_total_2020']].dropna()
            w = df['poblacion_total_2020'].values
            w = w / w.sum() * len(w)  # normalize weights
            x = df[x_col].values
            y = df[y_col].values
            # Weighted correlation
            mx = np.average(x, weights=w)
            my = np.average(y, weights=w)
            cov_xy = np.average((x - mx) * (y - my), weights=w)
            cov_xx = np.average((x - mx)**2, weights=w)
            cov_yy = np.average((y - my)**2, weights=w)
            r_w = cov_xy / np.sqrt(cov_xx * cov_yy) if cov_xx > 0 and cov_yy > 0 else 0
            r_unweighted, _ = stats.pearsonr(x, y)
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='2.14',
                title=f'Pop-weighted r: {label}',
                description='Population-weighted correlation (big states count more)',
                finding=f'Unweighted r={r_unweighted:.4f}, weighted r={r_w:.4f}, '
                        f'Δ={r_w-r_unweighted:+.4f}.',
                stat_value=round(r_w, 4), stat_name='r_weighted',
                confidence=7,
                novelty=4,
                narrative_value=5,
            ))

    # ── EXP 2.15: Stability of R² under random subsets ────────────────
    print("  [2.15] R² stability under random subsets (500×)...")
    for x_col, y_col, label in key_pairs[:3]:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        n = len(df)
        r2s = []
        for _ in range(500):
            size = max(10, int(n * 0.7))
            idx = rng.choice(n, size=size, replace=False)
            sub = df.iloc[idx]
            r_sub, _ = stats.pearsonr(sub[x_col], sub[y_col])
            r2s.append(r_sub**2)
        r2_median = np.median(r2s)
        r2_iqr = np.percentile(r2s, 75) - np.percentile(r2s, 25)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='2.15',
            title=f'R² stability (70% subsamples): {label}',
            description='Distribution of R² across 500 random 70% subsets',
            finding=f'R² median={r2_median:.4f}, IQR={r2_iqr:.4f}. '
                    f'{"Stable" if r2_iqr < 0.10 else "Unstable — sensitive to sample composition"}.',
            stat_value=round(r2_median, 4), stat_name='R2_median',
            confidence=8,
            novelty=4,
            narrative_value=6 if r2_iqr > 0.10 else 3,
        ))

    # ── EXP 2.16: Multiple comparison sensitivity ─────────────────────
    print("  [2.16] How many correlations survive sequential Bonferroni...")
    all_pairs = []
    infra_cols = [c for c in INFRA_VARS.keys() if c in cross.columns]
    sec_cols = [c for c in SEC_COL_LABELS.keys() if c in cross.columns]
    for ic in infra_cols:
        for sc in sec_cols:
            sub = cross[[ic, sc]].dropna()
            if len(sub) >= 10:
                r, p = stats.pearsonr(sub[ic], sub[sc])
                all_pairs.append({'x': ic, 'y': sc, 'r': r, 'p': p})

    pdf = pd.DataFrame(all_pairs).sort_values('p')
    m = len(pdf)
    # Sequential Bonferroni (Holm)
    pdf['rank'] = range(1, m + 1)
    pdf['holm_thresh'] = 0.05 / (m + 1 - pdf['rank'])
    pdf['holm_sig'] = pdf['p'] <= pdf['holm_thresh']
    n_holm = int(pdf['holm_sig'].sum())
    n_nominal = int((pdf['p'] < 0.05).sum())

    session.record(ExperimentResult(
        agent_id=AGENT_ID, exp_id='2.16',
        title='Holm correction: how many correlations survive?',
        description='Sequential Bonferroni (Holm) is stricter than BH. Compares to BH result (105/532).',
        finding=f'Nominal p<0.05: {n_nominal}/{m}. After Holm correction: {n_holm}/{m}. '
                f'After BH (from EXP-26): 105/{m}.',
        stat_value=n_holm, stat_name='n_holm',
        confidence=8,
        novelty=5,
        narrative_value=7,
        recommendation=f'If Holm is much stricter than BH, the dashboard should note which specific correlations are most robust.',
    ))

    path = session.save()
    print(session.summary())
    return session


if __name__ == '__main__':
    run()
