import os
import pandas as pd
import numpy as np
import joblib
from pages.db import query

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, auc
import xgboost as xgb
import shap

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'model_tab8v2.joblib')
_cache_df   = None
_cache_ml   = None

_GRUPO_NIVEL = {'Básico': 1, 'Emprendedor': 2, 'Avanzado': 3, 'Líder': 4}


def _get_grupo_map():
    """Returns {state_id: grupo_nivel 1-4} using IDDE 2022 classifications."""
    try:
        rows = query("""
            SELECT i.clave_inegi_de_estado AS state_id, g.grupo
            FROM idde_2022 i
            JOIN dim_grupo_digitalizacion g ON i.grupo_de_digitalizacion_id = g.grupo_id
        """)
        return {int(r['state_id']): _GRUPO_NIVEL.get(r['grupo'], 2)
                for _, r in rows.iterrows()}
    except Exception:
        return {}


def _load():
    global _cache_df
    if _cache_df is not None:
        return _cache_df

    raw = query("""
        SELECT e.state_id, e.quarter_id,
               e.instruction_level_id, e.job_situation_id,
               e.monthly_wage,
               e.schooling_years_id,
               il.instruction_level,
               sy.schooling_years
        FROM datamexico_enoe e
        JOIN dim_instruction_level il ON e.instruction_level_id = il.instruction_level_id
        JOIN dim_schooling_years   sy ON e.schooling_years_id   = sy.schooling_years_id
        WHERE e.monthly_wage > 0
    """)

    raw['year'] = (raw['quarter_id'] // 10).astype(int)
    raw['monthly_wage'] = raw['monthly_wage'].astype(float)
    grupo_map = _get_grupo_map()
    raw['grupo_nivel'] = raw['state_id'].map(grupo_map).fillna(2).astype(int)
    _cache_df = raw.dropna(subset=['monthly_wage'])
    return _cache_df


def get_salario_por_educacion():
    df = _load()
    return (df.groupby(['instruction_level', 'instruction_level_id'])
              .agg(salario_promedio=('monthly_wage', 'mean'))
              .reset_index()
              .sort_values('instruction_level_id'))


def get_salario_por_estado():
    df = _load()
    est = query("SELECT clave_ent AS state_id, estado FROM dim_estado")
    res = df.merge(est, on='state_id', how='left')
    return (res.groupby('estado')
               .agg(salario_promedio=('monthly_wage', 'mean'))
               .reset_index()
               .sort_values('salario_promedio', ascending=True))


def get_kpis():
    df = _load()
    return {
        'mediana_salario':  round(float(df['monthly_wage'].median()), 0),
        'promedio_salario': round(float(df['monthly_wage'].mean()), 0),
        'n_registros':      int(len(df)),
        'max_educacion':    df.groupby('instruction_level')['monthly_wage'].mean().idxmax(),
    }


# ── ML ────────────────────────────────────────────────────────────────────────

def _train():
    df = _load().copy()
    mediana = df['monthly_wage'].median()
    df['target'] = (df['monthly_wage'] > mediana).astype(int)

    features = ['schooling_years', 'instruction_level_id',
                'job_situation_id', 'grupo_nivel', 'year']
    df_ml = df[features + ['target']].dropna()

    # Sample for speed
    if len(df_ml) > 8_000:
        df_ml = df_ml.sample(n=8_000, random_state=42)

    X = df_ml[features].values.astype(float)
    y = df_ml['target'].values

    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    models = {
        'Random Forest':   RandomForestClassifier(n_estimators=80, max_features='sqrt',
                                                  max_depth=8, random_state=42, n_jobs=-1),
        'Reg. Logística':  LogisticRegression(penalty='l2', C=0.1, max_iter=300,
                                              random_state=42),
        'XGBoost':         xgb.XGBClassifier(n_estimators=60, max_depth=4,
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

    rf = models['Random Forest']
    explainer   = shap.TreeExplainer(rf)
    X_shap = X[:1000] if len(X) > 1000 else X
    shap_values = explainer.shap_values(X_shap)
    if isinstance(shap_values, list):
        sv = shap_values[1]
    elif hasattr(shap_values, 'ndim') and shap_values.ndim == 3:
        sv = shap_values[:, :, 1]
    else:
        sv = shap_values
    mean_shap = np.abs(np.array(sv)).mean(axis=0).ravel()
    shap_df = pd.DataFrame({'feature': features, 'importance': mean_shap})
    shap_df = shap_df.sort_values('importance', ascending=True)

    result = {
        'models': models, 'scaler': scaler,
        'roc': roc_data, 'aucs': aucs,
        'shap_df': shap_df, 'features': features,
        'X': X, 'X_sc': X_sc, 'y': y,
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
    ml = get_ml_models()
    # roc values stored as lists for joblib serialisation
    roc = {k: (np.array(v[0]), np.array(v[1])) for k, v in ml['roc'].items()}
    return roc, ml['aucs']


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


def get_representativos_8():
    """4 representative worker profiles spanning the education spectrum."""
    # (group, icon, educacion, estado, school, instr, job, grupo_nivel, year)
    profiles = [
        ('Líder',      '⭐', 'Posgrado',     'CDMX',       16, 7, 1, 4, 2023),
        ('Avanzado',   '◈',  'Licenciatura', 'Nuevo León', 16, 6, 1, 3, 2023),
        ('Transición', '◎',  'Preparatoria', 'Jalisco',    12, 4, 1, 2, 2023),
        ('Básico',     '⌬',  'Primaria',     'Oaxaca',      6, 2, 1, 1, 2023),
    ]
    results = []
    for group, icon, educacion, estado, school, instr, job, state, year in profiles:
        try:
            prob = predict_salario(school, instr, job, state, year)
        except Exception:
            prob = 50.0
        results.append({
            'group': group, 'icon': icon,
            'educacion': educacion, 'estado': estado,
            'school': school, 'year': year,
            'prob': prob,
        })
    return results


def predict_salario(schooling_years, instruction_level_id, job_situation_id,
                    grupo_nivel, year):
    ml  = get_ml_models()
    row = np.array([[schooling_years, instruction_level_id,
                     job_situation_id, grupo_nivel, year]], dtype=float)
    prob = ml['models']['Random Forest'].predict_proba(row)[0][1]
    return round(float(prob) * 100, 1)
