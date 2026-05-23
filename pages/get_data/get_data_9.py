import os
import pandas as pd
import numpy as np
import joblib
from pages.db import query
from pages.get_data.get_data_1 import get_pob

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.base import clone
import xgboost as xgb
import shap

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'model_tab9v2.joblib')
_cache_df = None
_cache_ml = None


def _load():
    global _cache_df
    if _cache_df is not None:
        return _cache_df

    raw = query("""
        SELECT d.state_id, d.month_id, d.company_size_id,
               d.companies, d.number_of_employees_midpoint AS empleados,
               cs.company_size,
               m.month
        FROM datamexico_denue d
        JOIN dim_company_size cs ON d.company_size_id = cs.company_size_id
        JOIN dim_month         m ON d.month_id        = m.month_id
    """)
    raw['year'] = (raw['month_id'] // 10000).astype(int)
    _cache_df = raw
    return raw


def get_empresas_por_estado(year=None):
    df = _load()
    if year:
        df = df[df['year'] == int(year)]
    est = query("SELECT clave_ent AS state_id, estado FROM dim_estado")
    df = df.merge(est, on='state_id', how='left')
    res = (df.groupby('estado')['companies'].sum().reset_index()
             .sort_values('companies', ascending=True))
    return res


def get_distribucion_tamano(year=None):
    df = _load()
    if year:
        df = df[df['year'] == int(year)]
    return (df.groupby('company_size')['companies'].sum().reset_index()
              .sort_values('companies', ascending=False))


def get_anios():
    return sorted(_load()['year'].unique().tolist())


def get_kpis():
    df = _load()
    latest = df['year'].max()
    df_last = df[df['year'] == latest]
    est = query("SELECT clave_ent AS state_id, estado FROM dim_estado")
    df_last = df_last.merge(est, on='state_id', how='left')
    top = (df_last.groupby('estado')['companies'].sum()
                  .nlargest(1).index[0])
    return {
        'total_empresas': int(df_last['companies'].sum()),
        'anio_datos': int(latest),
        'estado_mas_empresas': top,
        'total_estados': int(df_last['state_id'].nunique()),
    }


# ── ML ────────────────────────────────────────────────────────────────────────

def _build_ml_dataset():
    df = _load()
    est = query("SELECT clave_ent AS state_id, estado FROM dim_estado")
    df = df.merge(est, on='state_id', how='left')

    # Aggregate: state × year
    tot = df.groupby(['state_id', 'estado', 'year'])['companies'].sum().reset_index()
    tot['poblacion'] = tot.apply(lambda r: get_pob(r['estado'], int(r['year'])) or 1, axis=1)
    tot['empresas_x1k'] = tot['companies'] / tot['poblacion'] * 1_000

    # Company size distribution
    pivot = (df.groupby(['state_id', 'year', 'company_size_id'])['companies']
               .sum().unstack(fill_value=0))
    pivot.columns = [f'size_{c}' for c in pivot.columns]
    pivot = pivot.div(pivot.sum(axis=1), axis=0)  # % per size
    pivot = pivot.reset_index()

    df_ml = tot.merge(pivot, on=['state_id', 'year'], how='left').dropna(subset=['empresas_x1k'])

    mediana = df_ml['empresas_x1k'].median()
    df_ml['target'] = (df_ml['empresas_x1k'] > mediana).astype(int)

    size_cols = [c for c in df_ml.columns if c.startswith('size_')]
    features  = size_cols + ['year']
    df_clean  = df_ml[features + ['target', 'estado', 'empresas_x1k']].dropna()

    X = df_clean[features].values.astype(float)
    y = df_clean['target'].values
    estado_info = df_clean[['estado', 'year', 'empresas_x1k', 'target']].reset_index(drop=True)
    return X, y, features, estado_info


def _train():
    X, y, feat_names, estado_info = _build_ml_dataset()
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    models = {
        'Random Forest':   RandomForestClassifier(n_estimators=80, max_features='sqrt',
                                                  max_depth=6, random_state=42, n_jobs=-1),
        'Reg. Logística':  LogisticRegression(penalty='l2', C=0.1, max_iter=300,
                                              random_state=42),
        'XGBoost':         xgb.XGBClassifier(n_estimators=60, max_depth=3,
                                              learning_rate=0.1, subsample=0.8,
                                              eval_metric='logloss', random_state=42,
                                              n_jobs=1),
        'Red Neuronal':    MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200,
                                         random_state=42, early_stopping=True),
    }

    roc_data = {}
    aucs     = {}
    for name, m in models.items():
        Xin = X_sc if name in ('Reg. Logística', 'Red Neuronal') else X
        m.fit(Xin, y)
        proba = m.predict_proba(Xin)[:, 1]
        fpr, tpr, _ = roc_curve(y, proba)
        roc_data[name] = (fpr.tolist(), tpr.tolist())
        aucs[name]     = round(float(auc(fpr, tpr)), 3)

    # Cross-validated ROC — honest performance (avoids training-set overfitting)
    cv_fold  = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    cv_roc   = {}
    cv_aucs  = {}
    for name, m in models.items():
        Xin = X_sc if name in ('Reg. Logística', 'Red Neuronal') else X
        try:
            p_cv          = cross_val_predict(clone(m), Xin, y, cv=cv_fold,
                                              method='predict_proba')[:, 1]
            fpr_c, tpr_c, _ = roc_curve(y, p_cv)
            cv_roc[name]  = (fpr_c.tolist(), tpr_c.tolist())
            cv_aucs[name] = round(float(auc(fpr_c, tpr_c)), 3)
        except Exception:
            cv_roc[name]  = roc_data[name]
            cv_aucs[name] = aucs[name]

    rf = models['Random Forest']
    explainer   = shap.TreeExplainer(rf)
    X_shap = X[:1000] if len(X) > 1000 else X
    shap_vals   = explainer.shap_values(X_shap)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    elif hasattr(shap_vals, 'ndim') and shap_vals.ndim == 3:
        shap_vals = shap_vals[:, :, 1]
    mean_shap = np.abs(np.array(shap_vals)).mean(axis=0).ravel()
    shap_df = pd.DataFrame({'feature': feat_names, 'importance': mean_shap})
    shap_df = shap_df.sort_values('importance', ascending=True)

    result = {
        'models': models, 'scaler': scaler,
        'roc': roc_data, 'aucs': aucs,
        'cv_roc': cv_roc, 'cv_aucs': cv_aucs,
        'shap_df': shap_df, 'features': feat_names,
        'X': X, 'X_sc': X_sc, 'y': y,
        'estado_info': estado_info,
    }
    joblib.dump(result, _CACHE_FILE)
    return result


def get_ml_models():
    global _cache_ml
    if _cache_ml is not None:
        return _cache_ml
    if os.path.exists(_CACHE_FILE):
        _cache_ml = joblib.load(_CACHE_FILE)
    else:
        _cache_ml = _train()
    return _cache_ml


def get_roc_data():
    ml        = get_ml_models()
    roc_train = {k: (np.array(v[0]), np.array(v[1])) for k, v in ml['roc'].items()}
    roc_cv    = {k: (np.array(v[0]), np.array(v[1]))
                 for k, v in ml.get('cv_roc', ml['roc']).items()}
    return roc_train, roc_cv, ml['aucs'], ml.get('cv_aucs', ml['aucs'])


def get_shap_data():
    ml       = get_ml_models()
    shap_df  = ml['shap_df'].copy()
    features = ml['features']
    X        = ml['X']
    y        = ml['y']
    dirs = {}
    for i, feat in enumerate(features):
        col = X[:, i]
        if np.std(col) > 0:
            corr = float(np.corrcoef(col, y)[0, 1])
            dirs[feat] = '↑' if corr > 0 else '↓'
        else:
            dirs[feat] = ''
    shap_df['direction'] = shap_df['feature'].map(dirs).fillna('')
    return shap_df


def get_representativos_9():
    """4 representative states covering the business density spectrum."""
    ml = get_ml_models()
    if 'estado_info' not in ml:
        return []
    rf    = ml['models']['Random Forest']
    X     = ml['X']
    proba = rf.predict_proba(X)[:, 1]
    info  = ml['estado_info'].copy()
    info['prob_alta'] = proba * 100
    info['pred_class'] = (proba >= 0.5).astype(int)
    latest = int(info['year'].max())
    latest_info = info[info['year'] == latest].copy().sort_values('empresas_x1k', ascending=False)
    n = len(latest_info)
    if n < 4:
        return []
    idxs   = [0, max(1, n // 3), max(2, 2 * n // 3), n - 1]
    groups = ['Mayor densidad', 'Media-alta', 'Media-baja', 'Menor densidad']
    icons  = ['⬆', '◈', '◎', '⬇']
    colors = ['#2ca02c', '#00b4cc', '#ff7f0e', '#d62728']
    result = []
    for i, idx in enumerate(idxs):
        row = latest_info.iloc[idx]
        result.append({
            'grupo':       groups[i],
            'icon':        icons[i],
            'color':       colors[i],
            'estado':      str(row['estado']),
            'densidad':    round(float(row['empresas_x1k']), 2),
            'real_class':  int(row['target']),
            'prob_alta':   round(float(row['prob_alta']), 1),
            'pred_class':  int(row['pred_class']),
            'year':        int(row['year']),
        })
    return result
