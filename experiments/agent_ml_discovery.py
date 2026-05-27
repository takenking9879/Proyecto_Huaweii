"""
Agent 3: ML Discovery — Nonlinear patterns, feature importance, interactions.
Uses ML models to discover relationships that linear correlation misses.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, ElasticNet, LassoCV, RidgeCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.feature_selection import mutual_info_regression, RFE
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from experiments.data_utils import load_all_data, AgentSession, ExperimentResult

AGENT_ID = 'ml_discovery'
OBJECTIVE = 'Discover nonlinear patterns, feature interactions, and optimal predictors using ML'


def _get_feature_target_pairs(cross):
    """Define which features and targets to analyze."""
    infra_features = [
        'cobertura_de_banda_ancha_fija_por',
        'penetracion_de_banda_ancha_fija_x100hab',
        'cobertura_de_redes_moviles_por',
        'empresas_que_utilizan_banca_electronica_por',
        'graduados_en_programas_stem_xmhab',
        'velocidad_de_descarga_de_banda_ancha_movil_mbps',
        'indice_de_desarrollo_digital_estatal_2025',
    ]
    targets = [
        ('avg_wage', 'Average wage'),
        ('crime_rate_100k', 'Crime rate'),
        ('homicidio_rate_100k', 'Homicide rate'),
        ('fraude_rate_100k', 'Fraud rate'),
        ('conf_familia', 'Family trust'),
        ('conf_amigos', 'Friend trust'),
    ]
    avail_features = [f for f in infra_features if f in cross.columns]
    avail_targets = [(t, n) for t, n in targets if t in cross.columns]
    return avail_features, avail_targets


def run():
    session = AgentSession(AGENT_ID, OBJECTIVE)
    D = load_all_data()
    cross = D['cross_cl']
    INFRA_VARS = D['INFRA_VARS']
    features, targets = _get_feature_target_pairs(cross)

    print(f"Agent {AGENT_ID}: {len(features)} features × {len(targets)} targets")

    # ── EXP 3.1: RF permutation importance ────────────────────────────
    print("  [3.1] Random Forest permutation importance...")
    for target_col, target_name in targets:
        df = cross[['estado'] + features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        rf = RandomForestRegressor(n_estimators=200, max_depth=3, random_state=42, n_jobs=1)
        rf.fit(X, y)
        perm = permutation_importance(rf, X, y, n_repeats=100, random_state=42)
        importances = sorted(zip(features, perm.importances_mean, perm.importances_std),
                             key=lambda x: x[1], reverse=True)
        top3 = importances[:3]
        top3_str = ', '.join(f'{f[0][:30]}={f[1]:.4f}±{f[2]:.4f}' for f in top3)
        r2_train = rf.score(X, y)
        loo = LeaveOneOut()
        loo_scores = cross_val_score(rf, X, y, cv=loo)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.1',
            title=f'RF permutation importance → {target_name}',
            description=f'Random Forest with N={len(df)}, 200 trees, max_depth=3',
            finding=f'R²_train={r2_train:.3f}, R²_LOOCV={loo_scores.mean():.3f}. Top 3: {top3_str}',
            stat_value=round(loo_scores.mean(), 3), stat_name='R2_LOOCV',
            confidence=7,
            novelty=6,
            narrative_value=7 if loo_scores.mean() > 0.2 else 3,
            recommendation='If LOOCV R² > 0.2, there are genuine nonlinear patterns. Report feature importances.',
        ))

    # ── EXP 3.2: Mutual information vs Pearson ────────────────────────
    print("  [3.2] Mutual information vs Pearson...")
    for target_col, target_name in targets:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        mi = mutual_info_regression(X, y, random_state=42, n_neighbors=5)
        mi_ranked = sorted(zip(features, mi), key=lambda x: x[1], reverse=True)
        # Compare to Pearson
        pearson_r2 = []
        for f in features:
            sub = cross[[f, target_col]].dropna()
            if len(sub) > 10:
                r, _ = stats.pearsonr(sub[f], sub[target_col])
                pearson_r2.append((f, r**2))
        pearson_ranked = sorted(pearson_r2, key=lambda x: x[1], reverse=True)

        # Check if rankings differ
        mi_top3 = set(f for f, _ in mi_ranked[:3])
        pearson_top3 = set(f for f, _ in pearson_ranked[:3])
        overlap = mi_top3 & pearson_top3
        divergence = len(mi_top3 - pearson_top3)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.2',
            title=f'MI vs Pearson: {target_name}',
            description='Mutual information (nonlinear) vs Pearson (linear) feature ranking',
            finding=f'MI top 3: {", ".join(f[:25] for f, _ in mi_ranked[:3])}. '
                    f'Pearson top 3: {", ".join(f[:25] for f, _ in pearson_ranked[:3])}. '
                    f'Overlap={len(overlap)}/3. {divergence} features are nonlinear-only.',
            stat_value=len(overlap), stat_name='top3_overlap',
            confidence=7,
            novelty=7 if divergence > 0 else 3,
            narrative_value=7 if divergence > 0 else 2,
            recommendation='Features that rank high in MI but not in Pearson have nonlinear relationships.',
        ))

    # ── EXP 3.3: Linear vs RF R² comparison ───────────────────────────
    print("  [3.3] Linear vs RF R² comparison...")
    for target_col, target_name in targets:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        # Linear
        lr = LinearRegression()
        lr_r2 = cross_val_score(lr, X, y, cv=5, scoring='r2').mean()
        # RF
        rf = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=1)
        rf_r2 = cross_val_score(rf, X, y, cv=5, scoring='r2').mean()
        delta = rf_r2 - lr_r2
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.3',
            title=f'Linear vs RF R²: {target_name}',
            description='Does RF capture patterns that linear regression misses?',
            finding=f'Linear R²={lr_r2:.3f}, RF R²={rf_r2:.3f}, Δ={delta:+.3f}. '
                    f'{"Nonlinear patterns present" if delta > 0.10 else "Linear captures most variance"}.',
            stat_value=round(delta, 3), stat_name='delta_R2',
            confidence=7,
            novelty=6 if delta > 0.10 else 3,
            narrative_value=6 if delta > 0.10 else 2,
        ))

    # ── EXP 3.4: Interaction effects ──────────────────────────────────
    print("  [3.4] Feature interaction effects...")
    # Test if top 2 features interact
    if len(features) >= 2:
        for target_col, target_name in targets[:3]:
            df = cross[features[:4] + [target_col]].dropna()
            if len(df) < 15:
                continue
            X_base = df[features[:4]].values
            y = df[target_col].values
            # Add interactions
            poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
            X_poly = poly.fit_transform(X_base)
            feature_names = poly.get_feature_names_out(features[:4])
            lr_base = LinearRegression()
            lr_poly = LinearRegression()
            r2_base = cross_val_score(lr_base, X_base, y, cv=5, scoring='r2').mean()
            r2_poly = cross_val_score(lr_poly, X_poly, y, cv=5, scoring='r2').mean()
            delta = r2_poly - r2_base
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='3.4',
                title=f'Interaction effects → {target_name}',
                description=f'Polynomial (degree=2, interaction_only) vs linear with {len(features[:4])} features',
                finding=f'Linear R²={r2_base:.3f}, With interactions R²={r2_poly:.3f}, Δ={delta:+.3f}. '
                        f'N_interactions={X_poly.shape[1]-X_base.shape[1]}.',
                stat_value=round(delta, 3), stat_name='delta_R2_interactions',
                confidence=6,
                novelty=7 if delta > 0.05 else 3,
                narrative_value=6 if delta > 0.05 else 2,
            ))

    # ── EXP 3.5: Elastic Net feature selection ────────────────────────
    print("  [3.5] Elastic Net regularization path...")
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = StandardScaler().fit_transform(df[features].values)
        y = df[target_col].values
        en = ElasticNet(l1_ratio=0.5, random_state=42, max_iter=10000)
        from sklearn.linear_model import enet_path
        alphas, coefs, _ = enet_path(X, y, l1_ratio=0.5, n_alphas=50)
        # Find where each feature becomes zero
        nonzero_at = {}
        for i, f in enumerate(features):
            for j, alpha in enumerate(alphas):
                if abs(coefs[i, j]) < 1e-6:
                    nonzero_at[f] = float(alpha)
                    break
            else:
                nonzero_at[f] = 0.0  # never zero
        # Features that survive longest (most important)
        ranked = sorted(nonzero_at.items(), key=lambda x: x[1], reverse=True)
        top3 = ranked[:3]
        top3_str = ', '.join(f'{f[:25]}(α={a:.4f})' for f, a in top3)
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.5',
            title=f'Elastic Net features → {target_name}',
            description='Which features survive regularization longest?',
            finding=f'Top 3 (last to be zeroed): {top3_str}',
            confidence=6,
            novelty=5,
            narrative_value=5,
        ))

    # ── EXP 3.6: Gradient Boosting vs RF ──────────────────────────────
    print("  [3.6] Gradient Boosting comparison...")
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        gb = GradientBoostingRegressor(n_estimators=100, max_depth=2, random_state=42)
        rf = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=1)
        gb_r2 = cross_val_score(gb, X, y, cv=5, scoring='r2').mean()
        rf_r2 = cross_val_score(rf, X, y, cv=5, scoring='r2').mean()
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.6',
            title=f'GB vs RF: {target_name}',
            description='Gradient Boosting (sequential) vs Random Forest (bagging)',
            finding=f'GB R²={gb_r2:.3f}, RF R²={rf_r2:.3f}. '
                    f'{"GB is better" if gb_r2 > rf_r2 + 0.05 else "Comparable performance"}.',
            stat_value=round(gb_r2, 3), stat_name='R2_GB',
            confidence=6,
            novelty=4,
            narrative_value=4,
        ))

    # ── EXP 3.7: Nonlinear threshold effects ──────────────────────────
    print("  [3.7] Threshold effects (piecewise linear)...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    for target_col, target_name in [('crime_rate_100k', 'Crime'), ('avg_wage', 'Wage')]:
        if idde_col not in cross.columns or target_col not in cross.columns:
            continue
        df = cross[['estado', idde_col, target_col]].dropna()
        if len(df) < 15:
            continue
        # Try all possible thresholds
        best_r2 = -np.inf
        best_thresh = None
        for thresh in np.percentile(df[idde_col], np.arange(10, 91, 5)):
            df['above'] = (df[idde_col] >= thresh).astype(int)
            df['idde_above'] = df[idde_col] * df['above']
            df['idde_below'] = df[idde_col] * (1 - df['above'])
            X = df[['idde_above', 'idde_below', 'above']].values
            y = df[target_col].values
            lr = LinearRegression()
            r2 = cross_val_score(lr, X, y, cv=5, scoring='r2').mean()
            if r2 > best_r2:
                best_r2 = r2
                best_thresh = thresh
        # Compare to simple linear
        lr_simple = LinearRegression()
        r2_simple = cross_val_score(lr_simple, df[[idde_col]].values,
                                     df[target_col].values, cv=5, scoring='r2').mean()
        delta = best_r2 - r2_simple
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.7',
            title=f'Threshold effect: IDDE → {target_name}',
            description='Piecewise linear regression with optimal breakpoint in IDDE',
            finding=f'Best threshold={best_thresh:.1f}, R²_piecewise={best_r2:.3f}, '
                    f'R²_linear={r2_simple:.3f}, Δ={delta:+.3f}. '
                    f'{"Threshold effect detected" if delta > 0.05 else "No threshold"}.',
            stat_value=round(delta, 3), stat_name='delta_R2_threshold',
            confidence=6,
            novelty=8 if delta > 0.05 else 3,
            narrative_value=7 if delta > 0.05 else 2,
            recommendation='If threshold found, the dashboard can say "above IDDE=X, the relationship changes."',
        ))

    # ── EXP 3.8: Recursive Feature Elimination ────────────────────────
    print("  [3.8] Recursive Feature Elimination...")
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        rf = RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42, n_jobs=1)
        rfe = RFE(rf, n_features_to_select=3, step=1)
        rfe.fit(X, y)
        selected = [f for f, s in zip(features, rfe.support_) if s]
        r2_rfe = cross_val_score(rf, X[:, rfe.support_], y, cv=5, scoring='r2').mean()
        r2_all = cross_val_score(rf, X, y, cv=5, scoring='r2').mean()
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.8',
            title=f'RFE top 3 features → {target_name}',
            description='Recursive Feature Elimination: which 3 features matter most?',
            finding=f'Selected: {", ".join(s[:25] for s in selected)}. '
                    f'R²(3 features)={r2_rfe:.3f}, R²(all)={r2_all:.3f}.',
            stat_value=round(r2_rfe, 3), stat_name='R2_RFE_top3',
            confidence=6,
            novelty=6,
            narrative_value=6,
        ))

    # ── EXP 3.9: PCA-based regression ─────────────────────────────────
    print("  [3.9] PCA regression...")
    from sklearn.decomposition import PCA
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = StandardScaler().fit_transform(df[features].values)
        y = df[target_col].values
        pca = PCA()
        X_pca = pca.fit_transform(X)
        # Test 1 to k components
        best_k, best_r2 = 1, -np.inf
        for k in range(1, min(len(features), len(df) // 3)):
            lr = LinearRegression()
            r2 = cross_val_score(lr, X_pca[:, :k], y, cv=5, scoring='r2').mean()
            if r2 > best_r2:
                best_r2 = r2
                best_k = k
        var_explained = pca.explained_variance_ratio_[:best_k].sum()
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.9',
            title=f'PCA regression → {target_name}',
            description=f'Optimal number of principal components for prediction',
            finding=f'Best k={best_k}, R²={best_r2:.3f}, variance explained={var_explained:.1%}. '
                    f'Linear R²(all features) from 3.3 for comparison.',
            stat_value=round(best_r2, 3), stat_name='R2_PCA',
            confidence=6,
            novelty=5,
            narrative_value=4,
        ))

    # ── EXP 3.10: Nonlinear dose-response curves ──────────────────────
    print("  [3.10] Dose-response (LOWESS-style)...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    for target_col, target_name in [('avg_wage', 'Wage'), ('crime_rate_100k', 'Crime')]:
        if idde_col not in cross.columns or target_col not in cross.columns:
            continue
        df = cross[['estado', idde_col, target_col]].dropna().sort_values(idde_col)
        if len(df) < 15:
            continue
        # Bin analysis: divide IDDE into quartiles
        df['idde_q'] = pd.qcut(df[idde_col], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        means = df.groupby('idde_q')[target_col].mean()
        stds = df.groupby('idde_q')[target_col].std()
        # Test linearity: is Q4-Q3 > Q2-Q1?
        jump_high = means.iloc[-1] - means.iloc[-2] if len(means) >= 4 else 0
        jump_low = means.iloc[1] - means.iloc[0] if len(means) >= 2 else 0
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.10',
            title=f'Dose-response quartiles: IDDE → {target_name}',
            description='Mean of target by IDDE quartile to detect nonlinearity',
            finding=f'Q1={means.iloc[0]:.1f}, Q2={means.iloc[1]:.1f}, Q3={means.iloc[2]:.1f}, Q4={means.iloc[3]:.1f}. '
                    f'Jump Q1→Q2={jump_low:.1f}, Q3→Q4={jump_high:.1f}. '
                    f'{"Accelerating" if abs(jump_high) > abs(jump_low) * 1.5 else "Approximately linear"}.',
            stat_value=round(jump_high - jump_low, 1), stat_name='acceleration',
            confidence=6,
            novelty=7 if abs(jump_high) > abs(jump_low) * 1.5 else 3,
            narrative_value=6 if abs(jump_high) > abs(jump_low) * 1.5 else 2,
        ))

    # ── EXP 3.11: Crime type × feature importance ranking ─────────────
    print("  [3.11] Feature importance by crime type...")
    crime_targets = [
        ('homicidio_rate_100k', 'Homicide'),
        ('robo_rate_100k', 'Robbery'),
        ('fraude_rate_100k', 'Fraud'),
        ('violencia_familiar_rate_100k', 'Domestic violence'),
        ('narcomenudeo_rate_100k', 'Drug trafficking'),
    ]
    for target_col, target_name in crime_targets:
        if target_col not in cross.columns:
            continue
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        rf = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42, n_jobs=1)
        rf.fit(X, y)
        imp = sorted(zip(features, rf.feature_importances_), key=lambda x: x[1], reverse=True)
        top1 = imp[0]
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.11',
            title=f'Top predictor → {target_name}',
            description='Which digital feature best predicts each crime type?',
            finding=f'{target_name}: #1 predictor = {top1[0][:30]} (importance={top1[1]:.3f}). '
                    f'Top 3: {", ".join(f[0][:25] for f in imp[:3])}',
            stat_value=round(top1[1], 3), stat_name='top_importance',
            confidence=6,
            novelty=8,
            narrative_value=8,
            recommendation='Different crime types have different predictors. This is a powerful narrative for the dashboard.',
        ))

    # ── EXP 3.12: Ridge regression with polynomial features ───────────
    print("  [3.12] Ridge + polynomial features...")
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = StandardScaler().fit_transform(df[features].values)
        y = df[target_col].values
        # Degree 2 polynomial
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)
        ridge = RidgeCV(alphas=np.logspace(-3, 3, 20), scoring='r2')
        ridge_r2 = cross_val_score(ridge, X_poly, y, cv=5, scoring='r2').mean()
        lr_r2 = cross_val_score(LinearRegression(), X, y, cv=5, scoring='r2').mean()
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.12',
            title=f'Ridge+Poly → {target_name}',
            description='Ridge regression with degree-2 polynomial features',
            finding=f'Linear R²={lr_r2:.3f}, Ridge+Poly R²={ridge_r2:.3f}, Δ={ridge_r2-lr_r2:+.3f}.',
            stat_value=round(ridge_r2, 3), stat_name='R2_Ridge_Poly',
            confidence=6,
            novelty=5,
            narrative_value=5,
        ))

    # ── EXP 3.13: Cluster-specific models ─────────────────────────────
    print("  [3.13] Per-cluster RF models...")
    for target_col, target_name in [('avg_wage', 'Wage'), ('crime_rate_100k', 'Crime')]:
        if target_col not in cross.columns or 'cluster' not in cross.columns:
            continue
        cluster_r2s = []
        for cl, cl_grp in cross.groupby('cluster'):
            df = cl_grp[features + [target_col]].dropna()
            if len(df) < 5:
                continue
            X = df[features].values
            y = df[target_col].values
            rf = RandomForestRegressor(n_estimators=50, max_depth=2, random_state=42, n_jobs=1)
            # LOO within cluster
            loo = LeaveOneOut()
            try:
                loo_r2 = cross_val_score(rf, X, y, cv=loo, scoring='r2').mean()
            except:
                loo_r2 = np.nan
            cluster_r2s.append({'cluster': cl, 'n': len(df), 'r2_loocv': loo_r2})
        if cluster_r2s:
            text = ', '.join(f'C{c["cluster"]}: R²={c["r2_loocv"]:.3f} (n={c["n"]})'
                            for c in cluster_r2s if not np.isnan(c['r2_loocv']))
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='3.13',
                title=f'Per-cluster LOOCV → {target_name}',
                description='Does the model predict differently within each digitalization cluster?',
                finding=f'{text}',
                confidence=6,
                novelty=7,
                narrative_value=6,
            ))

    # ── EXP 3.14: Stacking (LR + RF + GB) ────────────────────────────
    print("  [3.14] Model stacking...")
    for target_col, target_name in targets[:3]:
        df = cross[features + [target_col]].dropna()
        if len(df) < 15:
            continue
        X = df[features].values
        y = df[target_col].values
        # Base predictions (LOO)
        lr_preds = np.zeros(len(df))
        rf_preds = np.zeros(len(df))
        gb_preds = np.zeros(len(df))
        loo = LeaveOneOut()
        for train_idx, test_idx in loo.split(X):
            lr = LinearRegression().fit(X[train_idx], y[train_idx])
            rf = RandomForestRegressor(n_estimators=50, max_depth=2, random_state=42, n_jobs=1).fit(X[train_idx], y[train_idx])
            gb = GradientBoostingRegressor(n_estimators=50, max_depth=2, random_state=42).fit(X[train_idx], y[train_idx])
            lr_preds[test_idx] = lr.predict(X[test_idx])
            rf_preds[test_idx] = rf.predict(X[test_idx])
            gb_preds[test_idx] = gb.predict(X[test_idx])
        # Stack: meta-learner on base predictions
        X_stack = np.column_stack([lr_preds, rf_preds, gb_preds])
        meta = LinearRegression().fit(X_stack, y)
        r2_stack = meta.score(X_stack, y)
        r2_best_base = max(
            r2_score(y, lr_preds),
            r2_score(y, rf_preds),
            r2_score(y, gb_preds),
        )
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.14',
            title=f'Stacking → {target_name}',
            description='Stacked ensemble: Linear + RF + GB → meta-learner (LOO)',
            finding=f'Stacking R²={r2_stack:.3f}, best base R²={r2_best_base:.3f}, '
                    f'Δ={r2_stack-r2_best_base:+.3f}. Weights: LR={meta.coef_[0]:.2f}, RF={meta.coef_[1]:.2f}, GB={meta.coef_[2]:.2f}',
            stat_value=round(r2_stack, 3), stat_name='R2_stacking',
            confidence=7,
            novelty=6,
            narrative_value=5,
        ))

    # ── EXP 3.15: Violent crime nonlinear patterns ────────────────────
    print("  [3.15] Violent crime nonlinear structure...")
    # Use binary: above/below median crime
    if 'homicidio_rate_100k' in cross.columns:
        df = cross[features + ['homicidio_rate_100k']].dropna()
        if len(df) >= 15:
            median_crime = df['homicidio_rate_100k'].median()
            df['high_crime'] = (df['homicidio_rate_100k'] > median_crime).astype(int)
            X = df[features].values
            y = df['high_crime'].values
            # Classification via RF
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score, roc_auc_score
            clf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42, n_jobs=1)
            from sklearn.model_selection import cross_val_predict
            y_pred = cross_val_predict(clf, X, y, cv=5)
            y_prob = cross_val_predict(clf, X, y, cv=5, method='predict_proba')[:, 1]
            acc = accuracy_score(y, y_pred)
            try:
                auc = roc_auc_score(y, y_prob)
            except:
                auc = 0.5
            clf.fit(X, y)
            imp = sorted(zip(features, clf.feature_importances_), key=lambda x: x[1], reverse=True)
            session.record(ExperimentResult(
                agent_id=AGENT_ID, exp_id='3.15',
                title='High vs low crime state classification',
                description=f'Can digital features classify states as high/low crime? (median split)',
                finding=f'Accuracy={acc:.3f}, AUC={auc:.3f}. Top predictor: {imp[0][0][:30]} ({imp[0][1]:.3f}). '
                        f'{"Good separation" if auc > 0.75 else "Weak separation"}.',
                stat_value=round(auc, 3), stat_name='AUC',
                confidence=6,
                novelty=6,
                narrative_value=6 if auc > 0.7 else 3,
            ))

    # ── EXP 3.16: SHAP-style feature effect direction ─────────────────
    print("  [3.16] Feature effect direction (marginal effects)...")
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    for target_col, target_name in [('avg_wage', 'Wage'), ('crime_rate_100k', 'Crime')]:
        if idde_col not in cross.columns or target_col not in cross.columns:
            continue
        df = cross[['estado', idde_col, target_col]].dropna()
        if len(df) < 15:
            continue
        # Fit RF and get partial dependence manually
        rf = RandomForestRegressor(n_estimators=200, max_depth=3, random_state=42, n_jobs=1)
        rf.fit(df[[idde_col]].values, df[target_col].values)
        # Grid of IDDE values
        grid = np.linspace(df[idde_col].min(), df[idde_col].max(), 20)
        pdp = []
        for g in grid:
            X_copy = df[[idde_col]].values.copy()
            X_copy[:, 0] = g
            pdp.append(rf.predict(X_copy).mean())
        # Check monotonicity
        diffs = np.diff(pdp)
        n_positive = (diffs > 0).sum()
        n_negative = (diffs < 0).sum()
        monotonic = n_positive == 0 or n_negative == 0
        session.record(ExperimentResult(
            agent_id=AGENT_ID, exp_id='3.16',
            title=f'PDP monotonicity: IDDE → {target_name}',
            description='Is the partial dependence curve monotonic or does it have reversals?',
            finding=f'PDP range: [{min(pdp):.1f}, {max(pdp):.1f}]. '
                    f'Monotonic={monotonic}. '
                    f'{n_positive} increasing steps, {n_negative} decreasing steps.',
            stat_value=1 if monotonic else 0, stat_name='monotonic',
            confidence=7,
            novelty=6,
            narrative_value=6,
            recommendation='Non-monotonic PDP means "more IDDE is not always better" — powerful nuance.',
        ))

    path = session.save()
    print(session.summary())
    return session


if __name__ == '__main__':
    run()
