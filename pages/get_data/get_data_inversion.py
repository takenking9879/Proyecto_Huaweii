"""
Investment opportunity data layer — reuses get_data_11 analysis.
Provides cluster profiles, ROI projections, and per-state executive summaries.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from pages.get_data.get_data_11 import get_data_11

_IDDE_COL = 'indice_de_desarrollo_digital_estatal_2025'

_CLUSTER_INVESTMENT = {
    'C0': {
        'priority': 'Infraestructura básica',
        'description': 'Mayor brecha digital del país. Mayor ROI por peso invertido en conectividad básica.',
        'roi_label': 'ROI máximo',
        'tier_color': '#d15b4a',
    },
    'C1': {
        'priority': 'Gobernanza digital y confianza',
        'description': 'Alta conectividad pero peor percepción ciudadana. El retorno está en recuperar confianza institucional.',
        'roi_label': 'ROI social',
        'tier_color': '#3891c7',
    },
    'C2': {
        'priority': 'Infraestructura avanzada y nube',
        'description': 'Modelo aspiracional: IDDE alto + mejor percepción. Inversión en calidad y sofisticación.',
        'roi_label': 'ROI productividad',
        'tier_color': '#2bb573',
    },
    'C3': {
        'priority': 'Tecnología especializada',
        'description': 'Buena conectividad pero crisis de violencia. El retorno requiere soluciones institucionales + datos.',
        'roi_label': 'ROI seguridad',
        'tier_color': '#e4982e',
    },
}

_cache_inv = None


def _get_cached():
    global _cache_inv
    if _cache_inv is None:
        _cache_inv = get_data_11()
    return _cache_inv


def _fit_slope(x, y):
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 5:
        return 0.0
    lr = LinearRegression()
    lr.fit(x[mask].reshape(-1, 1), y[mask])
    return float(lr.coef_[0])


def get_cluster_profiles():
    """Returns list of cluster dicts enriched with investment framing."""
    d = _get_cached()
    cluster_stats = d['cluster_stats']
    label_map     = d['label_map']
    cross_cl      = d['cross_cl']

    profiles = []
    for c_id, stats in cluster_stats.items():
        code, name, color, _ = label_map[c_id]
        inv = _CLUSTER_INVESTMENT.get(code, {})

        sub = cross_cl[cross_cl['cluster'] == c_id]
        avg_wage = float(sub['avg_wage'].mean()) if 'avg_wage' in sub.columns else 0.0
        avg_trust = 0.0
        trust_cols = ['conf_familia', 'conf_amigos', 'conf_vecinos']
        available = [c for c in trust_cols if c in sub.columns]
        if available:
            avg_trust = float(sub[available].mean(axis=1).mean())

        profiles.append({
            'cluster_id':   c_id,
            'code':         code,
            'name':         name,
            'color':        color,
            'n':            stats['n'],
            'estados':      stats['estados'],
            'avg_idde':     round(stats['idde'], 2),
            'avg_crime':    round(stats['crime'], 1),
            'avg_homicidio':round(stats['homicidio'], 1),
            'avg_percepcion': round(stats['percepcion'], 2),
            'avg_wage':     round(avg_wage, 0),
            'avg_trust':    round(avg_trust, 2),
            'priority':     inv.get('priority', ''),
            'description':  inv.get('description', ''),
            'roi_label':    inv.get('roi_label', ''),
        })

    profiles.sort(key=lambda p: p['code'])
    return profiles


def get_roi_projections(delta_idde=10.0):
    """
    Returns projected changes per cluster for +delta_idde points of IDDE.
    Uses OLS slopes fit on cross-sectional data.
    """
    d  = _get_cached()
    df = d['cross_cl'].copy()

    idde_vals = df[_IDDE_COL].values.astype(float)

    slope_wage  = _fit_slope(idde_vals, df['avg_wage'].values.astype(float)
                             if 'avg_wage' in df.columns else np.zeros(len(df)))
    slope_trust = _fit_slope(idde_vals,
                             df[['conf_familia', 'conf_amigos', 'conf_vecinos']]
                             .mean(axis=1).values.astype(float)
                             if all(c in df.columns for c in ['conf_familia', 'conf_amigos', 'conf_vecinos'])
                             else np.zeros(len(df)))
    slope_perc  = _fit_slope(idde_vals, df['percepcion_segura'].values.astype(float)
                             if 'percepcion_segura' in df.columns else np.zeros(len(df)))

    result = {}
    for p in get_cluster_profiles():
        code = p['code']
        base_wage  = p['avg_wage']  or 1.0
        base_trust = p['avg_trust'] or 1.0
        base_perc  = p['avg_percepcion'] or 0.01

        d_wage  = slope_wage  * delta_idde
        d_trust = slope_trust * delta_idde
        d_perc  = slope_perc  * delta_idde

        result[code] = {
            'delta_wage_pct':  round((d_wage  / base_wage)  * 100, 1) if base_wage  > 0 else 0,
            'delta_trust_pct': round((d_trust / base_trust) * 100, 1) if base_trust > 0 else 0,
            'delta_perc_pct':  round((d_perc  / base_perc)  * 100, 1) if base_perc  > 0 else 0,
            'delta_wage_abs':  round(d_wage, 0),
            'delta_trust_abs': round(d_trust, 3),
            'delta_perc_abs':  round(d_perc, 3),
            'slope_wage':      round(slope_wage, 2),
            'slope_trust':     round(slope_trust, 4),
            'slope_perc':      round(slope_perc, 4),
        }

    return result


def get_state_investment_table():
    """Returns DataFrame: 32 states × cluster, IDDE, gap to C2 avg, projected wage gain."""
    d        = _get_cached()
    cross_cl = d['cross_cl'].copy()
    roi      = get_roi_projections()

    # C2 mean IDDE as the "developed" target
    c2_rows = cross_cl[cross_cl['cluster_code'] == 'C2']
    c2_idde_mean = float(c2_rows[_IDDE_COL].mean()) if len(c2_rows) > 0 else 60.0

    rows = []
    for _, row in cross_cl.iterrows():
        idde_val = float(row[_IDDE_COL]) if _IDDE_COL in cross_cl.columns else 0.0
        code = row.get('cluster_code', 'C0')
        gap = 0.0 if code == 'C2' else max(0.0, c2_idde_mean - idde_val)
        slope_wage = roi.get(code, {}).get('slope_wage', 0)
        projected_wage_gain = round(gap * slope_wage, 0)

        rows.append({
            'estado':         row['estado'],
            'cluster_code':   code,
            'cluster_name':   row.get('cluster_name', ''),
            'cluster_color':  row.get('cluster_color', '#888'),
            'idde':           round(idde_val, 2),
            'gap_to_c2':      round(gap, 2),
            'avg_wage':       round(row['avg_wage'], 0) if 'avg_wage' in row.index else 0,
            'projected_wage_gain': projected_wage_gain,
        })

    return pd.DataFrame(rows).sort_values('idde')


def get_state_profile(estado):
    """Returns a single state's full investment profile."""
    d        = _get_cached()
    cross_cl = d['cross_cl'].copy()
    cluster_stats = d['cluster_stats']
    label_map     = d['label_map']

    row = cross_cl[cross_cl['estado'] == estado]
    if len(row) == 0:
        return None
    row = row.iloc[0]

    code  = row.get('cluster_code', 'C0')
    c_id  = row.get('cluster', 0)

    # National mean IDDE
    nat_mean = float(cross_cl[_IDDE_COL].mean()) if _IDDE_COL in cross_cl.columns else 50.0
    nat_rank = int(cross_cl[_IDDE_COL].rank(ascending=False).loc[row.name]) if _IDDE_COL in cross_cl.columns else 16
    idde_val = float(row[_IDDE_COL]) if _IDDE_COL in cross_cl.columns else 0.0

    # C2 target gap — C2 states already at target level
    c2_rows = cross_cl[cross_cl['cluster_code'] == 'C2']
    c2_idde = float(c2_rows[_IDDE_COL].mean()) if len(c2_rows) > 0 else 60.0
    gap = 0.0 if code == 'C2' else max(0.0, c2_idde - idde_val)

    roi = get_roi_projections()
    slope_wage = roi.get(code, {}).get('slope_wage', 0)
    projected_wage = round(gap * slope_wage, 0)

    inv = _CLUSTER_INVESTMENT.get(code, {})
    _, name, color, _ = label_map.get(int(c_id), ('?', '?', '#888', ''))

    return {
        'estado':           estado,
        'cluster_code':     code,
        'cluster_name':     name,
        'cluster_color':    color,
        'idde':             round(idde_val, 2),
        'idde_national_mean': round(nat_mean, 2),
        'national_rank':    nat_rank,
        'gap_to_c2':        round(gap, 2),
        'projected_wage_gain': projected_wage,
        'avg_wage':         round(float(row['avg_wage']), 0) if 'avg_wage' in row.index else 0,
        'percepcion_segura':round(float(row['percepcion_segura']), 2) if 'percepcion_segura' in row.index else 0,
        'priority':         inv.get('priority', ''),
        'description':      inv.get('description', ''),
        'roi_label':        inv.get('roi_label', ''),
    }


def get_radar_data(estado):
    """
    Returns radar chart data: state values vs cluster centroid vs national mean.
    6 dimensions: IDDE, velocidad móvil, usuarios internet, salario, percepción, confianza social.
    All normalized 0–1 within national range.
    """
    d        = _get_cached()
    cross_cl = d['cross_cl'].copy()

    radar_cols = [
        _IDDE_COL,
        'velocidad_de_descarga_de_banda_ancha_movil_mbps',
        'usuarios_de_internet_por',
        'avg_wage',
        'percepcion_segura',
        'conf_familia',
    ]
    labels = ['IDDE', 'Vel. móvil', 'Internet %', 'Salario', 'Percepción', 'Conf. social']

    available = [c for c in radar_cols if c in cross_cl.columns]
    labels_av = [labels[radar_cols.index(c)] for c in available]

    row  = cross_cl[cross_cl['estado'] == estado]
    if len(row) == 0:
        return None
    row = row.iloc[0]
    code = row.get('cluster_code', 'C0')

    cluster_rows = cross_cl[cross_cl['cluster_code'] == code]

    state_vals   = []
    cluster_vals = []
    national_vals = []

    for col in available:
        col_data  = cross_cl[col].dropna()
        col_min   = col_data.min()
        col_range = col_data.max() - col_min or 1.0

        state_v   = (float(row[col])                          - col_min) / col_range
        cluster_v = (float(cluster_rows[col].mean())          - col_min) / col_range
        national_v = (float(col_data.mean())                  - col_min) / col_range

        state_vals.append(round(min(1.0, max(0.0, state_v)), 3))
        cluster_vals.append(round(min(1.0, max(0.0, cluster_v)), 3))
        national_vals.append(round(min(1.0, max(0.0, national_v)), 3))

    color = cross_cl.loc[cross_cl['estado'] == estado, 'cluster_color'].iloc[0]

    return {
        'labels':         labels_av,
        'state':          state_vals,
        'cluster':        cluster_vals,
        'national':       national_vals,
        'cluster_code':   code,
        'cluster_color':  color,
    }


def get_estados_list():
    d = _get_cached()
    return sorted(d['cross_cl']['estado'].dropna().unique().tolist())
