import os
import pandas as pd
import numpy as np
import joblib
from pages.db import query
from pages.get_data.get_data_1 import get_pob
from pages.get_data.get_data_6 import BIEN_MAP, GRUPO_COLORS, GRUPO_ORDER

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import shap

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'model_tab10v2.joblib')
_cache_df   = None
_cache_ml   = None


def _load():
    global _cache_df
    if _cache_df is not None:
        return _cache_df

    _IDDE_META = {
        2022: ('indice_de_desarrollo_digital_estatal_2022', 'grupo_de_digitalizacion_id'),
        2023: ('indice_de_desarrollo_digital_estatal_2023', 'grupo_de_digitalizacion_2023_id'),
        2024: ('indice_de_desarrollo_digital_estatal_2024', 'grupo_de_digitalizacion_2024_id'),
    }

    idde_frames = []
    for yr, (idde_col, grupo_col) in _IDDE_META.items():
        d = query(f"""
            SELECT clave_inegi_de_estado AS clave_ent,
                   {idde_col} AS idde_score,
                   pilar_infraestructura,
                   pilar_digitalizacion_de_las_personas_y_la_sociedad AS pilar_sociedad,
                   pilar_innovacion_y_adopcion_tecnologica_de_las_empresas AS pilar_innovacion,
                   usuarios_de_internet_por, habilidades_de_programacion_por,
                   solicitudes_de_patentes_xmhab, graduados_en_programas_stem_xmhab,
                   policia_cibernetica_xmhab, {grupo_col} AS grupo_id
            FROM idde_{yr}
        """)
        d['anio'] = yr
        idde_frames.append(d)

    idde_all = pd.concat(idde_frames, ignore_index=True)
    grupos = query("SELECT grupo_id, grupo FROM dim_grupo_digitalizacion")
    idde_all = idde_all.merge(grupos, on='grupo_id', how='left')
    idde_all.rename(columns={'grupo': 'grupo_label'}, inplace=True)

    crime = query("""
        SELECT f.anio, e.clave_ent, e.estado, s.subtipo,
               SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
        JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
        WHERE f.anio IN (2022, 2023, 2024)
        GROUP BY f.anio, e.clave_ent, e.estado, s.subtipo
    """)
    crime['categoria'] = crime['subtipo'].map(BIEN_MAP).fillna('Otros')
    cat = (crime.groupby(['anio', 'clave_ent', 'categoria'])['total'].sum()
               .unstack(fill_value=0).add_prefix('crime_').reset_index())
    tot = crime.groupby(['anio', 'clave_ent', 'estado'])['total'].sum().reset_index(name='total_delitos')

    df = tot.merge(cat, on=['anio', 'clave_ent']).merge(idde_all, on=['anio', 'clave_ent'])
    df['anio'] = df['anio'].astype(int)
    df['anio_2023'] = (df['anio'] == 2023).astype(int)
    df['anio_2024'] = (df['anio'] == 2024).astype(int)
    df['poblacion'] = df.apply(lambda r: get_pob(r['estado'], int(r['anio'])), axis=1)
    df['tasa_x100k'] = df['total_delitos'] / df['poblacion'] * 100_000
    for cat_col in [c for c in df.columns if c.startswith('crime_')]:
        df[cat_col.replace('crime_', 'tasa_')] = df[cat_col] / df['poblacion'] * 100_000
        df[cat_col.replace('crime_', 'share_')] = df[cat_col] / df['total_delitos'].replace(0, np.nan)

    _cache_df = df.reset_index(drop=True)
    return _cache_df


def get_df():
    return _load()


def _train():
    df = _load().copy()

    tasa_cols  = [c for c in df.columns if c.startswith('tasa_') and c != 'tasa_x100k']
    share_cols = [c for c in df.columns if c.startswith('share_')]
    features   = tasa_cols + share_cols + [
        'policia_cibernetica_xmhab', 'graduados_en_programas_stem_xmhab',
        'habilidades_de_programacion_por', 'anio_2023', 'anio_2024',
    ]
    target = 'pilar_innovacion'

    df_main = df[['estado', 'anio', 'grupo_label'] + features + [target]].dropna().reset_index(drop=True)
    feat_names = [c for c in features if c in df_main.columns]
    X_all = df_main[feat_names].values.astype(float)
    y     = df_main[target].values.astype(float)

    # PCA-based feature selection (replicates analisis_ml.ipynb)
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X_all)
    pca    = PCA().fit(X_sc)
    n_pc   = int((pca.explained_variance_ratio_.cumsum() <= 0.80).sum()) + 1

    # Save first 6 PCs for visualization
    n_vis       = min(6, pca.n_components_)
    pc_scores   = pca.transform(X_sc)[:, :n_vis]
    pc_loadings = pca.components_[:n_vis, :]
    pc_var      = pca.explained_variance_ratio_[:n_vis]

    S = np.cov(X_sc, rowvar=False)
    evals, Gamma = np.linalg.eig(S)
    evals = evals.real
    Gamma = Gamma.real
    cov_XY  = Gamma @ np.diag(evals)
    Dx_nsq  = np.diag(np.diag(S) ** (-0.5))
    Dy_nsq  = np.diag(np.where(evals > 1e-10, evals ** (-0.5), 0))
    corr_XY = Dx_nsq @ cov_XY @ Dy_nsq

    pares = [(0, k) for k in range(1, n_pc)]
    norms_rows = []
    for i, j in pares:
        row = {}
        for k, name in enumerate(feat_names):
            x_, y_ = corr_XY[k, i], corr_XY[k, j]
            row[name] = float(np.sqrt(x_**2 + y_**2))
        norms_rows.append(row)
    df_norms   = pd.DataFrame(norms_rows)
    cols_model = [c for c in df_norms.columns if (df_norms[c] >= 0.7).sum() > 0]
    if not cols_model:
        cols_model = feat_names[:12]

    X_model = df_main[cols_model].values.astype(float)

    rf  = RandomForestRegressor(n_estimators=100, max_features=0.5,
                                min_samples_leaf=2, max_depth=8,
                                random_state=42, n_jobs=-1)
    gbm = GradientBoostingRegressor(n_estimators=80, max_depth=3,
                                    learning_rate=0.1, subsample=0.8, random_state=42)
    rid = Ridge(alpha=5.0)
    xgbm = xgb.XGBRegressor(n_estimators=80, max_depth=3, learning_rate=0.1,
                              subsample=0.8, random_state=42, n_jobs=1)

    models_reg = {'Random Forest': rf, 'Grad. Boosting': gbm,
                  'Ridge': rid, 'XGBoost': xgbm}
    cv_scores  = {}
    for name, m in models_reg.items():
        cv_scores[name] = float(np.mean(
            cross_val_score(m, X_model, y, cv=3, scoring='r2', n_jobs=1)
        ))
        m.fit(X_model, y)

    # SHAP
    explainer   = shap.TreeExplainer(rf)
    X_shap = X_model[:1000] if len(X_model) > 1000 else X_model
    shap_values = explainer.shap_values(X_shap)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    mean_shap   = np.abs(np.array(shap_values)).mean(axis=0).ravel()
    shap_df = pd.DataFrame({'feature': cols_model, 'importance': mean_shap})
    shap_df = shap_df.sort_values('importance', ascending=True)

    # Clustering (k=4, state-level 2022 snapshot)
    df22 = df_main[df_main['anio'] == 2022].copy()
    if len(df22) > 4:
        X22 = scaler.transform(df22[feat_names].values.astype(float))
        km  = KMeans(n_clusters=2, random_state=42, n_init=20)
        df22['cluster'] = km.fit_predict(X22)
    else:
        df22['cluster'] = 0

    result = {
        'df_main': df_main, 'df22': df22,
        'cols_model': cols_model, 'feat_names': feat_names,
        'X_model': X_model, 'y': y,
        'models': models_reg, 'cv_scores': cv_scores,
        'rf': rf, 'shap_df': shap_df,
        'scaler': scaler, 'X_sc': X_sc,
        'pc_scores': pc_scores, 'pc_loadings': pc_loadings, 'pc_var': pc_var,
    }
    joblib.dump(result, _CACHE_FILE)
    return result


def get_ml():
    global _cache_ml
    if _cache_ml is not None:
        return _cache_ml
    if os.path.exists(_CACHE_FILE):
        _cache_ml = joblib.load(_CACHE_FILE)
    else:
        _cache_ml = _train()
    return _cache_ml


def get_kpis():
    ml = get_ml()
    best_name = max(ml['cv_scores'], key=lambda k: ml['cv_scores'][k])
    return {
        'rf_r2':        round(ml['cv_scores']['Random Forest'], 3),
        'best_model':   best_name,
        'best_r2':      round(ml['cv_scores'][best_name], 3),
        'n_features':   len(ml['cols_model']),
    }


def get_representatives_10():
    """One representative state per IDDE group with real vs RF-predicted innovation + PC z-scores."""
    ml      = get_ml()
    df      = ml['df_main'].copy()
    rf      = ml['models']['Random Forest']
    X       = ml['X_model']
    y_pred  = rf.predict(X)
    df['y_pred'] = y_pred

    pc_scores = ml.get('pc_scores', None)
    pc_mean   = pc_scores.mean(axis=0) if pc_scores is not None else None
    pc_std    = pc_scores.std(axis=0)  if pc_scores is not None else None

    latest_yr = int(df['anio'].max())
    df_latest = df[df['anio'] == latest_yr]

    _icons  = {'Líder': '⭐', 'Avanzado': '◈', 'Emprendedor': '◎', 'Básico': '⌬'}
    result  = []
    for grupo in GRUPO_ORDER:
        sub = df_latest[df_latest['grupo_label'] == grupo]
        if sub.empty:
            sub = df[df['grupo_label'] == grupo]
        if sub.empty:
            continue
        mean_pi = float(sub['pilar_innovacion'].mean())
        idx     = (sub['pilar_innovacion'] - mean_pi).abs().idxmin()
        row     = sub.loc[idx]

        pc_zscore = []
        if pc_scores is not None and idx < len(pc_scores):
            n_pc = min(3, pc_scores.shape[1])
            for j in range(n_pc):
                v  = float(pc_scores[idx, j])
                s  = float(pc_std[j]) if pc_std[j] > 1e-6 else 1.0
                pc_zscore.append(round((v - float(pc_mean[j])) / s, 2))

        result.append({
            'grupo':    grupo,
            'icon':     _icons.get(grupo, '◎'),
            'color':    GRUPO_COLORS.get(grupo, '#888888'),
            'estado':   str(row['estado']),
            'real':     round(float(row['pilar_innovacion']), 1),
            'pred':     round(float(row['y_pred']), 1),
            'anio':     int(row['anio']),
            'pc_zscore': pc_zscore,
        })
    return result


def predict_pilar(crime_values: dict) -> float:
    ml = get_ml()
    cols = ml['cols_model']
    row = np.array([[crime_values.get(c, 0.0) for c in cols]], dtype=float)
    pred = ml['models']['Random Forest'].predict(row)[0]
    return round(float(pred), 2)
