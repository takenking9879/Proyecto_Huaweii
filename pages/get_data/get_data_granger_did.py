"""
Data layer for Granger causality, Difference-in-Differences, Panel Fixed Effects,
and diagnostic tests (VIF, Breusch-Pagan, Bootstrap CI, LOOCV, Benjamini-Hochberg).

Used by get_figures_granger_did.py and run_experiments.py.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
from pages.db import query
from pages.get_data.get_data_11 import get_data_11

_IDDE_COL = 'indice_de_desarrollo_digital_estatal_2025'

_cache = {}


def _g():
    if 'd11' not in _cache:
        _cache['d11'] = get_data_11()
    return _cache['d11']


def _get_enoe_panel():
    """ENOE wage panel 2022–2025 by state."""
    dim_estado = query("SELECT clave_ent, estado FROM dim_estado")
    rows = []
    for yr in [2022, 2023, 2024, 2025]:
        w = query(f"""
            SELECT e.state_id, AVG(e.monthly_wage) as avg_wage
            FROM datamexico_enoe e
            WHERE e.quarter_id >= {yr*10+1} AND e.quarter_id <= {yr*10+4}
              AND e.monthly_wage > 0
            GROUP BY e.state_id
        """)
        w = w.merge(dim_estado, left_on='state_id', right_on='clave_ent', how='left')
        w['year'] = yr
        rows.append(w[['estado', 'year', 'avg_wage']])
    return pd.concat(rows, ignore_index=True)


# ═══════════════════════════════════════════════════════════════════════
# Granger Causality
# ═══════════════════════════════════════════════════════════════════════

def get_granger_results():
    """
    EXP-05 expanded: Pooled panel Granger causality IDDE <-> crime.
    Returns lag-1 and lag-2 results for both directions.
    """
    d = _g()
    panel = d['panel'].sort_values(['estado', 'year']).copy()
    panel = panel.dropna(subset=['idde_index', 'crime_rate'])

    panel['d_idde']  = panel.groupby('estado')['idde_index'].diff()
    panel['d_crime'] = panel.groupby('estado')['crime_rate'].diff()
    panel['lag_d_crime'] = panel.groupby('estado')['d_crime'].shift(1)
    panel['lag_d_idde']  = panel.groupby('estado')['d_idde'].shift(1)

    def _granger_f(y, x_restricted_cols, x_unrestricted_cols, data):
        sub = data[[y] + x_restricted_cols + x_unrestricted_cols].dropna()
        if len(sub) < 10:
            return {'f': np.nan, 'p': np.nan, 'n': len(sub)}
        X_r = sub[x_restricted_cols].values
        X_u = sub[x_unrestricted_cols].values
        yv  = sub[y].values
        # restricted model
        lr_r = LinearRegression().fit(X_r, yv)
        rss_r = np.sum((yv - lr_r.predict(X_r))**2)
        # unrestricted model
        X_all = np.column_stack([X_r, X_u]) if X_r.shape[1] > 0 else X_u
        lr_u = LinearRegression().fit(X_all, yv)
        rss_u = np.sum((yv - lr_u.predict(X_all))**2)
        df1 = X_u.shape[1]
        df2 = len(yv) - X_all.shape[1] - 1
        if rss_u == 0 or df2 <= 0:
            return {'f': np.nan, 'p': np.nan, 'n': len(sub)}
        f = ((rss_r - rss_u) / df1) / (rss_u / df2)
        p = 1 - stats.f.cdf(f, df1, df2)
        return {'f': round(f, 3), 'p': round(float(p), 4), 'n': len(sub)}

    results = []

    # IDDE -> Crime (lag 1)
    r = _granger_f('d_crime', ['lag_d_crime'], ['lag_d_idde'], panel)
    results.append({'direction': 'IDDE → Crimen', 'lag': 1, **r})

    # Crime -> IDDE (lag 1)
    r = _granger_f('d_idde', ['lag_d_idde'], ['lag_d_crime'], panel)
    results.append({'direction': 'Crimen → IDDE', 'lag': 1, **r})

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════
# Difference-in-Differences
# ═══════════════════════════════════════════════════════════════════════

def get_did_results():
    """
    EXP-11: DiD — states with large IDDE increase (top tercile 2022→2024)
    vs control states, comparing wage trajectories 2022 vs 2025.
    """
    d = _g()
    panel = d['panel'].copy()
    enoe  = _get_enoe_panel()

    # IDDE change 2022→2024
    idde_pivot = panel.pivot_table(index='estado', columns='year',
                                    values='idde_index').reset_index()
    yr_list = sorted([int(c) for c in idde_pivot.columns if c != 'estado' and not isinstance(c, str)])
    col_map = {y: f'idde_{y}' for y in yr_list}
    idde_pivot.rename(columns=col_map, inplace=True)

    if 'idde_2022' in idde_pivot.columns and 'idde_2024' in idde_pivot.columns:
        idde_pivot['d_idde_22_24'] = idde_pivot['idde_2024'] - idde_pivot['idde_2022']
    else:
        idde_pivot['d_idde_22_24'] = 0

    threshold = np.percentile(idde_pivot['d_idde_22_24'].dropna(), 67)
    idde_pivot['treated'] = idde_pivot['d_idde_22_24'] >= threshold

    # Wage pivot
    wage_pivot = enoe.pivot_table(index='estado', columns='year',
                                   values='avg_wage').reset_index()
    wage_yr_list = sorted([int(c) for c in wage_pivot.columns if c != 'estado' and not isinstance(c, str)])
    wage_map = {y: f'wage_{y}' for y in wage_yr_list}
    wage_pivot.rename(columns=wage_map, inplace=True)

    merged = idde_pivot.merge(wage_pivot, on='estado', how='left')

    # Compute wage delta (prefer 2025→2022, fallback to 2024→2022)
    d_wage_start = 'wage_2022'
    if 'wage_2025' in merged.columns:
        merged['d_wage'] = merged['wage_2025'] - merged[d_wage_start]
    elif 'wage_2024' in merged.columns:
        merged['d_wage'] = merged['wage_2024'] - merged[d_wage_start]

    did = merged.dropna(subset=['d_wage', 'treated'])
    treated = did[did['treated']]
    control = did[~did['treated']]

    # Build trajectories for plotting
    traj_years = [y for y in [2022, 2023, 2024, 2025] if f'wage_{y}' in merged.columns]
    trajectories = []
    for _, row in did.iterrows():
        for y in traj_years:
            col = f'wage_{y}'
            if not pd.isna(row.get(col)):
                trajectories.append({
                    'estado': row['estado'],
                    'year': y,
                    'wage': row[col],
                    'treated': bool(row['treated']),
                })

    return {
        'n_treated': int(did['treated'].sum()),
        'n_control': int((~did['treated']).sum()),
        'threshold': round(float(threshold), 2),
        'treated_mean_d': round(float(treated['d_wage'].mean()), 2) if len(treated) else 0,
        'control_mean_d': round(float(control['d_wage'].mean()), 2) if len(control) else 0,
        'diff_in_diff': round(float(treated['d_wage'].mean() - control['d_wage'].mean()), 2)
                        if len(treated) and len(control) else 0,
        'trajectories': pd.DataFrame(trajectories),
        'treated_states': treated['estado'].tolist(),
        'control_states': control['estado'].tolist(),
    }


# ═══════════════════════════════════════════════════════════════════════
# Panel Fixed Effects
# ═══════════════════════════════════════════════════════════════════════

def get_panel_fe_results():
    """
    EXP-21: Panel Fixed Effects — wage_it = α_i + δ_t + β·IDDE_it + ε_it.
    Returns coefficients, SEs, R², and within-R².
    """
    d = _g()
    panel = d['panel'].copy()
    enoe  = _get_enoe_panel()

    merged = panel.merge(enoe, on=['estado', 'year'], how='left')
    merged = merged.dropna(subset=['idde_index', 'avg_wage'])

    states = merged['estado'].unique()
    years  = sorted(merged['year'].unique())

    # Create dummies for FE estimation via LSDV
    X_cols = ['idde_index']
    for s in states[1:]:
        merged[f'fe_{s}'] = (merged['estado'] == s).astype(float)
        X_cols.append(f'fe_{s}')
    for y in years[1:]:
        merged[f'yr_{y}'] = (merged['year'] == y).astype(float)
        X_cols.append(f'yr_{y}')

    sub = merged.dropna(subset=X_cols + ['avg_wage'])
    X = sub[X_cols].values
    y = sub['avg_wage'].values

    lr = LinearRegression().fit(X, y)
    r2 = lr.score(X, y)
    y_pred = lr.predict(X)
    residuals = y - y_pred
    n, k = X.shape
    se_ols = np.sqrt(np.sum(residuals**2) / (n - k) * np.linalg.inv(X.T @ X).diagonal())

    # Cluster-robust SE at state level
    try:
        import statsmodels.api as sm
        from statsmodels.iolib.summary2 import summary_col
        ols = sm.OLS(y, X).fit()
        robust_se = ols.get_robustcov_results(cov_type='cluster', groups=sub['estado'].values).bse
        idde_se_clustered = robust_se[0]
    except Exception:
        idde_se_clustered = se_ols[0]

    idde_coef = lr.coef_[0]
    idde_se   = se_ols[0]
    t_stat    = idde_coef / idde_se if idde_se > 0 else 0
    p_val     = 2 * (1 - stats.t.cdf(abs(t_stat), n - k))

    # Within R²: demeaning approach
    merged['wage_dm'] = merged.groupby('estado')['avg_wage'].transform(lambda x: x - x.mean())
    merged['idde_dm'] = merged.groupby('estado')['idde_index'].transform(lambda x: x - x.mean())
    sub_w = merged.dropna(subset=['wage_dm', 'idde_dm'])
    lr_w = LinearRegression().fit(sub_w[['idde_dm']], sub_w['wage_dm'])
    within_r2 = lr_w.score(sub_w[['idde_dm']], sub_w['wage_dm'])

    return {
        'n_obs': n,
        'n_states': len(states),
        'n_years': len(years),
        'idde_coef': round(float(idde_coef), 2),
        'idde_se': round(float(idde_se), 2),
        'idde_se_clustered': round(float(idde_se_clustered), 2),
        't_stat': round(float(t_stat), 2),
        'p_val': round(float(p_val), 4),
        'r2_total': round(float(r2), 4),
        'within_r2': round(float(within_r2), 4),
        'significant_05': p_val < 0.05,
    }


# ═══════════════════════════════════════════════════════════════════════
# VIF — Multicollinearity
# ═══════════════════════════════════════════════════════════════════════

def get_vif_results():
    """
    EXP-22: VIF for the main regression predictors (cross-section 2025).
    """
    d = _g()
    cross = d['cross_cl'].copy()
    predictors = [
        'empresas_que_utilizan_banca_electronica_por',
        'penetracion_de_banda_ancha_fija_x100hab',
        'cobertura_de_redes_moviles_por',
        'graduados_en_programas_stem_xmhab',
    ]
    available = [c for c in predictors if c in cross.columns]
    if 'avg_wage' not in cross.columns:
        return []

    df = cross[['estado'] + available + ['avg_wage']].dropna()
    out = []
    for i, col in enumerate(available):
        others = [c for j, c in enumerate(available) if j != i]
        X = df[others].values
        y = df[col].values
        lr = LinearRegression().fit(X, y)
        r2 = lr.score(X, y)
        vif = 1 / (1 - r2) if r2 < 1 else float('inf')
        out.append({'variable': col, 'r2_aux': round(float(r2), 4),
                    'vif': round(float(vif), 2)})
    return out


# ═══════════════════════════════════════════════════════════════════════
# Breusch-Pagan
# ═══════════════════════════════════════════════════════════════════════

def get_bp_test():
    """
    EXP-23: Breusch-Pagan test for heteroskedasticity.
    H0: homoskedastic errors.
    """
    d = _g()
    cross = d['cross_cl'].copy()

    x_col = 'empresas_que_utilizan_banca_electronica_por'
    if x_col not in cross.columns or 'avg_wage' not in cross.columns:
        return {'lm': np.nan, 'p': np.nan, 'n': 0}

    df = cross[[x_col, 'avg_wage']].dropna()
    X = df[[x_col]].values
    y = df['avg_wage'].values

    lr = LinearRegression().fit(X, y)
    residuals = y - lr.predict(X)
    residuals_sq = residuals ** 2

    # Regress squared residuals on X
    X_aux = np.column_stack([np.ones(len(df)), X])
    lr_bp = LinearRegression().fit(X_aux, residuals_sq)
    predicted = lr_bp.predict(X_aux)
    r2_bp = np.corrcoef(residuals_sq, predicted)[0, 1] ** 2

    n = len(df)
    lm = n * r2_bp
    p = 1 - stats.chi2.cdf(lm, df=X.shape[1])

    return {'lm': round(float(lm), 3), 'p': round(float(p), 4), 'n': n}


# ═══════════════════════════════════════════════════════════════════════
# Bootstrap Confidence Intervals
# ═══════════════════════════════════════════════════════════════════════

def get_bootstrap_cis(n_bootstrap=10000):
    """
    EXP-24: Bootstrap 95% CIs for key correlations and R².
    """
    d = _g()
    cross = d['cross_cl'].copy()

    pairs = [
        ('empresas_que_utilizan_banca_electronica_por', 'avg_wage', 'Banca electrónica → Salario (R²)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'percepcion_segura', 'IDDE → Percepción segura (R²)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'conf_familia', 'IDDE → Confianza familiar (r)'),
        ('indice_de_desarrollo_digital_estatal_2025', 'fraude_rate_100k', 'IDDE → Fraude (r)'),
    ]

    results = []
    for x_col, y_col, label in pairs:
        if x_col not in cross.columns or y_col not in cross.columns:
            continue
        df = cross[[x_col, y_col]].dropna()
        n = len(df)

        # OLS point estimate from full sample
        slope_full, intercept_full, r_full, _, _ = stats.linregress(df[x_col], df[y_col])
        is_r2 = 'R²' in label
        full_est = r_full ** 2 if is_r2 else r_full

        boot_vals = []
        rng = np.random.default_rng(42)
        for _ in range(n_bootstrap):
            idx = rng.integers(0, n, size=n)
            xb = df.iloc[idx][x_col].values
            yb = df.iloc[idx][y_col].values
            slope, intercept, r, _, _ = stats.linregress(xb, yb)
            boot_vals.append(r**2 if is_r2 else r)

        ci_lower = np.percentile(boot_vals, 2.5)
        ci_upper = np.percentile(boot_vals, 97.5)

        results.append({
            'label': label,
            'point': round(float(full_est), 4),
            'ci_lower': round(float(ci_lower), 4),
            'ci_upper': round(float(ci_upper), 4),
            'n': n,
            'metric': 'R²' if is_r2 else 'r',
        })

    return results


# ═══════════════════════════════════════════════════════════════════════
# Leave-One-Out CV for Slide 10 (Crimen → Innovación)
# ═══════════════════════════════════════════════════════════════════════

def get_loocv_results():
    """
    EXP-25: Leave-one-out cross-validation for the RF model in slide 10.
    Trains model on 31 states, predicts the held-out state.
    """
    d = _g()
    cross = d['cross_cl'].copy()

    # Target: pilar de innovación
    target = 'subpilar_de_innovacion'
    feature_cols = [
        'tasa_Sociedad', 'tasa_Patrimonio', 'tasa_Vida',
        'tasa_Familia', 'tasa_Sexual', 'tasa_Estado',
        'crime_rate_100k', 'homicidio_rate_100k',
    ]
    available = [c for c in feature_cols if c in cross.columns]
    if target not in cross.columns:
        return {'r2_loocv': 0, 'r2_train_mean': 0, 'predictions': [], 'n': 0}

    df = cross[['estado'] + available + [target]].dropna()
    X = df[available].values
    y = df[target].values

    loo = LeaveOneOut()
    predictions = []
    train_r2s = []

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        rf = RandomForestRegressor(n_estimators=100, max_depth=4,
                                    random_state=42, n_jobs=1)
        rf.fit(X_train, y_train)

        # In-sample R² for this fold
        train_pred = rf.predict(X_train)
        ss_res = np.sum((y_train - train_pred)**2)
        ss_tot = np.sum((y_train - y_train.mean())**2)
        train_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        train_r2s.append(train_r2)

        # Out-of-sample prediction
        pred = rf.predict(X_test)[0]
        predictions.append({
            'estado': df.iloc[test_idx[0]]['estado'],
            'real': float(y_test[0]),
            'pred': float(pred),
        })

    pred_df = pd.DataFrame(predictions)
    ss_res_loo = np.sum((pred_df['real'] - pred_df['pred'])**2)
    ss_tot_loo = np.sum((pred_df['real'] - pred_df['real'].mean())**2)
    r2_loocv = 1 - ss_res_loo / ss_tot_loo if ss_tot_loo > 0 else 0

    return {
        'r2_loocv': round(float(r2_loocv), 4),
        'r2_train_mean': round(float(np.mean(train_r2s)), 4),
        'predictions': pred_df,
        'n': len(df),
    }


# ═══════════════════════════════════════════════════════════════════════
# Benjamini-Hochberg Correction
# ═══════════════════════════════════════════════════════════════════════

def get_bh_correction_results():
    """
    EXP-26: Benjamini-Hochberg FDR correction for the 532+ correlations
    in slide 11 (28 infra × 19 security variables).
    """
    from pages.get_data.get_data_11 import get_data_11, INFRA_VARS, SEC_COL_LABELS
    d = get_data_11()
    cross = d['cross_cl'].copy()

    infra_cols = [c for c in INFRA_VARS.keys() if c in cross.columns]
    sec_cols   = [c for c in SEC_COL_LABELS.keys() if c in cross.columns]

    if not infra_cols or not sec_cols:
        return {'n_total': 0, 'n_nominal': 0, 'n_bh': 0,
                'top_survivors': [], 'all_results': []}

    # Compute all pairwise correlations
    all_pairs = []
    for ic in infra_cols:
        for sc in sec_cols:
            sub = cross[[ic, sc]].dropna()
            if len(sub) < 10:
                continue
            r, p = stats.pearsonr(sub[ic], sub[sc])
            all_pairs.append({
                'infra': ic,
                'sec': sc,
                'r': round(float(r), 4),
                'p': round(float(p), 6),
                'n': len(sub),
            })

    df_pairs = pd.DataFrame(all_pairs).sort_values('p')
    df_pairs['rank'] = range(1, len(df_pairs) + 1)
    m = len(df_pairs)
    df_pairs['bh_threshold'] = df_pairs['rank'] / m * 0.05  # FDR = 0.05
    df_pairs['bh_significant'] = df_pairs['p'] <= df_pairs['bh_threshold']

    n_nominal = int((df_pairs['p'] < 0.05).sum())
    n_bh      = int(df_pairs['bh_significant'].sum())

    # Top 10 survivors
    top = (df_pairs[df_pairs['bh_significant']]
           .sort_values('p')
           .head(10)
           [['infra', 'sec', 'r', 'p']]
           .to_dict('records'))

    return {
        'n_total': len(df_pairs),
        'n_nominal': n_nominal,
        'n_bh': n_bh,
        'top_survivors': top,
    }


# ═══════════════════════════════════════════════════════════════════════
# Wage Gap: Sustained vs Inconsistent (robust version)
# ═══════════════════════════════════════════════════════════════════════

def get_robust_wage_gap():
    """
    EXP-18 enhanced: sustained vs inconsistent investors, with bootstrap CI.
    """
    d = _g()
    panel = d['panel'].copy()
    cross = d['cross_cl'].copy()

    wages = cross[['estado', 'avg_wage']].dropna()

    state_trends = {}
    for estado in panel['estado'].dropna().unique():
        sub = panel[panel['estado'] == estado].sort_values('year')
        idde_vals = sub['idde_index'].dropna().values
        if len(idde_vals) < 3:
            continue
        increases = sum(1 for i in range(1, len(idde_vals))
                       if idde_vals[i] > idde_vals[i - 1])
        state_trends[estado] = 'Sostenida' if increases >= 3 else 'Inconsistente'

    rows = []
    for estado, trend in state_trends.items():
        w = wages[wages['estado'] == estado]['avg_wage']
        if len(w) > 0:
            rows.append({'estado': estado, 'grupo': trend, 'avg_wage': float(w.iloc[0])})

    df = pd.DataFrame(rows)
    if df.empty:
        return {'gap': 0, 'ci_lower': 0, 'ci_upper': 0, 'n_sustained': 0, 'n_inconsistent': 0}

    sustained   = df[df['grupo'] == 'Sostenida']['avg_wage']
    inconsistent = df[df['grupo'] == 'Inconsistente']['avg_wage']

    gap = sustained.mean() - inconsistent.mean()

    # Bootstrap CI for the gap
    rng = np.random.default_rng(42)
    boot_gaps = []
    n_boot = 10000
    for _ in range(n_boot):
        s_sample = sustained.sample(n=len(sustained), replace=True, random_state=rng.integers(0, 2**31))
        i_sample = inconsistent.sample(n=len(inconsistent), replace=True, random_state=rng.integers(0, 2**31))
        boot_gaps.append(s_sample.mean() - i_sample.mean())

    ci_lower = np.percentile(boot_gaps, 2.5)
    ci_upper = np.percentile(boot_gaps, 97.5)

    return {
        'gap': round(float(gap), 0),
        'ci_lower': round(float(ci_lower), 0),
        'ci_upper': round(float(ci_upper), 0),
        'n_sustained': int(len(sustained)),
        'n_inconsistent': int(len(inconsistent)),
        'mean_sustained': round(float(sustained.mean()), 0),
        'mean_inconsistent': round(float(inconsistent.mean()), 0),
    }
