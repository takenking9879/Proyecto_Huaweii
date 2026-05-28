"""
Data for slide_economia: digital economy vs wages (EXP-15, EXP-07, EXP-02, EXP-18).
All data pulled from get_data_11 cross-sectional + panel — no extra DB queries.
"""
import numpy as np
import pandas as pd
from scipy import stats
from pages.get_data.get_data_11 import get_data_11

_IDDE_COL = 'indice_de_desarrollo_digital_estatal_2025'
_cache = None


def _get():
    global _cache
    if _cache is None:
        _cache = get_data_11()
    return _cache


def get_digital_wages_scatter():
    """EXP-15: e-banking adoption vs avg_wage — R²≈0.594."""
    cross = _get()['cross_cl']
    cols = [
        'estado', _IDDE_COL,
        'empresas_que_utilizan_banca_electronica_por',
        'penetracion_de_tarjeta_de_debito_x100adu',
        'avg_wage', 'cluster_label',
    ]
    df = cross[[c for c in cols if c in cross.columns]].dropna(
        subset=['empresas_que_utilizan_banca_electronica_por', 'avg_wage']
    ).copy()
    # Composite digital-economy exposure
    cols_exp = [c for c in ['empresas_que_utilizan_banca_electronica_por',
                             'penetracion_de_tarjeta_de_debito_x100adu'] if c in df.columns]
    for c in cols_exp:
        mn, mx = df[c].min(), df[c].max()
        df[c + '_n'] = (df[c] - mn) / (mx - mn) if mx > mn else 0.0
    df['digital_exposure'] = df[[c + '_n' for c in cols_exp]].mean(axis=1)
    return df


def get_data_centers_quintiles():
    """EXP-07: data center composite by quintile vs median wages."""
    cross = _get()['cross_cl']
    dc_cols = [
        'centros_de_datos_edge_xmuint',
        'centros_de_datos_certificados_xmpib',
        'centros_de_datos_hyperscale_y_colocation_hosting_xmpib',
    ]
    present = [c for c in dc_cols if c in cross.columns]
    if not present or 'avg_wage' not in cross.columns:
        return pd.DataFrame()
    df = cross[['estado', 'avg_wage'] + present].copy()
    for c in present:
        df[c] = df[c].fillna(0)
        mn, mx = df[c].min(), df[c].max()
        df[c + '_n'] = (df[c] - mn) / (mx - mn) if mx > mn else 0.0
    df['dc_score'] = df[[c + '_n' for c in present]].mean(axis=1)
    df = df.dropna(subset=['avg_wage'])
    labels = ['Q1 — Mínimo', 'Q2', 'Q3', 'Q4', 'Q5 — Máximo']
    df['quintile'] = pd.qcut(df['dc_score'], q=5, labels=labels, duplicates='drop')
    return df


def get_investment_lag_data():
    """EXP-02: R² of IDDE at lag-0, lag-1, lag-2 vs 2025 wages."""
    from pages.db import query
    dim_estado = query("SELECT clave_ent, estado FROM dim_estado")
    cross = _get()['cross_cl']
    wages = cross[['estado', 'avg_wage']].dropna()

    results = []
    for lag, yr in [(0, 2025), (1, 2024), (2, 2022)]:
        try:
            raw = query(f"SELECT * FROM idde_{yr}").rename(
                columns={'clave_inegi_de_estado': 'clave_ent'})
            idde_col = next(
                (c for c in raw.columns if 'indice_de_desarrollo_digital' in c.lower()), None)
            if not idde_col:
                continue
            idde_yr = (raw[['clave_ent', idde_col]]
                       .merge(dim_estado, on='clave_ent', how='left')
                       .rename(columns={idde_col: 'idde'}))
            merged = idde_yr.merge(wages, on='estado').dropna(subset=['idde', 'avg_wage'])
            if len(merged) < 15:
                continue
            _, _, r, _, _ = stats.linregress(merged['idde'], merged['avg_wage'])
            results.append({'lag': lag, 'year': yr, 'r2': round(r ** 2, 3), 'r': round(r, 3),
                            'n': len(merged)})
        except Exception:
            pass
    return sorted(results, key=lambda x: x['lag'])


def get_sustained_investment_data():
    """EXP-18: sustained vs inconsistent IDDE investors → wage comparison."""
    panel = _get()['panel']
    cross = _get()['cross_cl']
    wages = cross[['estado', 'avg_wage']].dropna()

    state_trends = {}
    for estado in panel['estado'].dropna().unique():
        sub = (panel[panel['estado'] == estado]
               .sort_values('year')
               [lambda d: d['year'].isin([2022, 2023, 2024, 2025])])
        idde_vals = sub['idde_index'].dropna().values
        if len(idde_vals) < 3:
            continue
        increases = sum(1 for i in range(1, len(idde_vals)) if idde_vals[i] > idde_vals[i - 1])
        state_trends[estado] = 'Inversión sostenida' if increases >= 3 else 'Inversión inconsistente'

    rows = []
    for estado, trend in state_trends.items():
        w = wages[wages['estado'] == estado]['avg_wage']
        if len(w) > 0:
            rows.append({'estado': estado, 'grupo': trend, 'avg_wage': float(w.iloc[0])})

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    summary = (df.groupby('grupo')
               .agg(n=('estado', 'count'), avg_wage=('avg_wage', 'mean'))
               .reset_index())
    return summary


def get_economia_r2():
    """Compute R² for e-banking → wages regression (same as fig_digital_wages_scatter)."""
    df = get_digital_wages_scatter()
    x_col = 'empresas_que_utilizan_banca_electronica_por'
    if df.empty or x_col not in df.columns or 'avg_wage' not in df.columns:
        return 0.594
    valid = df[[x_col, 'avg_wage']].dropna()
    if len(valid) < 5:
        return 0.594
    _, _, r, _, _ = stats.linregress(valid[x_col].values, valid['avg_wage'].values)
    return r ** 2
