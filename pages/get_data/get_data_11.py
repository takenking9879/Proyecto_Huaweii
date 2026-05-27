"""
personal_analysis.ipynb → Dash data layer.
Infraestructura Digital × Seguridad en México (corte transversal 2025 + panel 2022-2025).
"""
import os
import numpy as np
import pandas as pd
import joblib
from pages.db import query
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'model_tab11.joblib')
_cache = None

# ── Variable dictionaries ────────────────────────────────────────────────────

INFRA_VARS = {
    'penetracion_de_banda_ancha_fija_x100hab':              'Pen. BB fija',
    'penetracion_de_banda_ancha_movil_x100hab':             'Pen. BB móvil',
    'conexiones_de_banda_ancha_fija_con_fibra_optica_por':  'Fibra óptica %',
    'cobertura_de_banda_ancha_fija_por':                    'Cobertura BB fija',
    'cobertura_de_redes_moviles_por':                       'Cobertura móvil',
    'cobertura_5g_por':                                     'Cobertura 5G',
    'velocidad_de_descarga_de_banda_ancha_fija_mbps':       'Vel. DL fija',
    'velocidad_de_descarga_de_banda_ancha_movil_mbps':      'Vel. DL móvil',
    'centros_de_datos_edge_xmuint':                         'DC Edge',
    'centros_de_datos_certificados_xmpib':                  'DC Cert.',
    'centros_de_datos_hyperscale_y_colocation_hosting_xmpib': 'DC Hyper.',
    'acciones_de_ciberseguridad_en_las_empresas_por':       'Ciberseg. emp.',
    'empresas_que_utilizan_banca_electronica_por':          'Banca elect.',
    'penetracion_de_tarjeta_de_debito_x100adu':             'Tarjeta débito',
    'penetracion_de_banda_ancha_fija_no_residencial_x100ue':'BB no resid.',
    'usuarios_de_internet_por':                             'Usuarios internet',
    'usuarios_de_telefonos_inteligentes_por':               'Usuarios smartphone',
    'graduados_en_programas_stem_xmhab':                    'Graduados STEM',
    'policia_cibernetica_xmhab':                            'Policía cibernét.',
    'indice_de_desarrollo_digital_estatal_2025':            'IDDE 2025',
    'pilar_infraestructura':                                'Pilar Infra.',
    'subpilar_de_ciberseguridad':                           'Sub. Ciberseg.',
    'subpilar_de_economia_digital':                         'Sub. Econ. digital',
    'subpilar_de_innovacion':                               'Sub. Innovación',
    'subpilar_de_gobierno_digital_y_entorno_regulatorio':   'Sub. Gob. digital',
    'subpilar_de_comercio_electronico':                     'Sub. Com. elect.',
    'subpilar_de_cobertura_acceso_y_calidad':               'Sub. Cobertura',
    'subpilar_de_infraestructura_de_datos':                 'Sub. Datos',
}

INFRA_GROUPS = {
    'Pen. BB fija':       'Conectividad',
    'Pen. BB móvil':      'Conectividad',
    'Fibra óptica %':     'Conectividad',
    'Cobertura BB fija':  'Conectividad',
    'Cobertura móvil':    'Conectividad',
    'Cobertura 5G':       'Conectividad',
    'Vel. DL fija':       'Velocidad/Calidad',
    'Vel. DL móvil':      'Velocidad/Calidad',
    'DC Edge':            'Datos/Nube',
    'DC Cert.':           'Datos/Nube',
    'DC Hyper.':          'Datos/Nube',
    'Ciberseg. emp.':     'Economía digital',
    'Banca elect.':       'Economía digital',
    'Tarjeta débito':     'Economía digital',
    'BB no resid.':       'Economía digital',
    'Usuarios internet':  'Cap. humano/Digital',
    'Usuarios smartphone':'Cap. humano/Digital',
    'Graduados STEM':     'Cap. humano/Digital',
    'Policía cibernét.':  'Cap. humano/Digital',
    'IDDE 2025':          'IDDE/Pilares',
    'Pilar Infra.':       'IDDE/Pilares',
    'Sub. Ciberseg.':     'IDDE/Pilares',
    'Sub. Econ. digital': 'IDDE/Pilares',
    'Sub. Innovación':    'IDDE/Pilares',
    'Sub. Gob. digital':  'IDDE/Pilares',
    'Sub. Com. elect.':   'IDDE/Pilares',
    'Sub. Cobertura':     'IDDE/Pilares',
    'Sub. Datos':         'IDDE/Pilares',
}

SEC_COL_LABELS = {
    'crime_rate_100k':          'Crimen total',
    'homicidio_rate_100k':      'Homicidios',
    'robo_rate_100k':           'Robos',
    'fraude_rate_100k':         'Fraudes',
    'narcomenudeo_rate_100k':   'Narcomenudeo',
    'violencia_familiar_rate_100k': 'Violencia familiar',
    'percepcion_segura':        'Perc. seguro',
    'conf_ejercito':            'Conf. Ejército',
    'conf_policia_estatal':     'Conf. Policía Est.',
    'conf_policia_federal':     'Conf. Policía Fed.',
    'conf_jueces':              'Conf. Jueces',
    'conf_fiscalia':            'Conf. Fiscalía',
    'conf_mp':                  'Conf. Min. Público',
    'conf_familia':             'Conf. Familia',
    'conf_amigos':              'Conf. Amigos',
    'conf_vecinos':             'Conf. Vecinos',
    'conf_trabajo':             'Conf. Trabajo',
    'gastos_proteccion':        'Gasto protección',
    'avg_wage':                 'Salario promedio',
}

SEC_GROUPS = {
    'Crimen total':       'Crimen (tasas)',
    'Homicidios':         'Crimen (tasas)',
    'Robos':              'Crimen (tasas)',
    'Fraudes':            'Crimen (tasas)',
    'Narcomenudeo':       'Crimen (tasas)',
    'Violencia familiar': 'Crimen (tasas)',
    'Perc. seguro':       'Percepción',
    'Conf. Ejército':     'Conf. institucional',
    'Conf. Policía Est.': 'Conf. institucional',
    'Conf. Policía Fed.': 'Conf. institucional',
    'Conf. Jueces':       'Conf. institucional',
    'Conf. Fiscalía':     'Conf. institucional',
    'Conf. Min. Público': 'Conf. institucional',
    'Conf. Familia':      'Conf. social',
    'Conf. Amigos':       'Conf. social',
    'Conf. Vecinos':      'Conf. social',
    'Conf. Trabajo':      'Conf. social',
    'Gasto protección':   'Económico',
    'Salario promedio':   'Económico',
}

_IDDE_COL = 'indice_de_desarrollo_digital_estatal_2025'

_CRIME_TYPES = {
    'homicidio':          'Homicidio',
    'robo':               'Robo',
    'fraude':             'Fraude',
    'narcomenudeo':       'Narcomenudeo',
    'violencia_familiar': 'Violencia familiar',
    'lesiones':           'Lesiones',
    'extorsion':          'Extorsión',
    'secuestro':          'Secuestro',
}

# Cluster colour scheme — color-blind safe with distinct lightness steps
# C0 (warm coral L≈22%), C1 (steel blue L≈25%), C2 (emerald L≈35%), C3 (amber L≈39%)
CLUSTER_COLORS = ['#d15b4a', '#3891c7', '#2bb573', '#e4982e']


# ── Build dataset ─────────────────────────────────────────────────────────────

def _build():
    dim_estado = query("SELECT clave_ent, estado FROM dim_estado")

    # Population 2020 (closest census year in table)
    pop_raw = query("SELECT state_id AS clave_ent, population, year_id FROM datamexico_population")
    pop2020 = (pop_raw[pop_raw['year_id'] == 2020][['clave_ent', 'population']]
               .merge(dim_estado, on='clave_ent', how='left'))

    # IDDE 2025
    idde25_raw = query("SELECT * FROM idde_2025").rename(
        columns={'clave_inegi_de_estado': 'clave_ent'})
    idde25 = idde25_raw.merge(dim_estado, on='clave_ent', how='left')

    # Crime 2025 (total + by type)
    crime_raw = query("""
        SELECT e.estado, s.subtipo, SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_estado e ON f.clave_ent = e.clave_ent
        JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
        WHERE f.anio = 2025
        GROUP BY e.estado, s.subtipo
    """)
    crime_total = crime_raw.groupby('estado')['total'].sum().reset_index(name='total_crimes')
    for cat, pat in _CRIME_TYPES.items():
        sub = crime_raw[crime_raw['subtipo'].str.contains(pat, case=False, na=False)]
        agg = sub.groupby('estado')['total'].sum().reset_index(name=f'crimes_{cat}')
        crime_total = crime_total.merge(agg, on='estado', how='left')
    crime_total = crime_total.fillna(0)

    # ENVIPE — encode dimension IDs to numeric scores
    conf_auth_map = query("SELECT nivel_confianza_id AS id, nivel_confianza AS lbl FROM dim_nivel_confianza")
    conf_auth_num = {
        'Mucha Confianza': 4, 'Algo de Confianza': 3,
        'Algo de Desconfianza': 2, 'Mucha Desconfianza': 1,
    }
    conf_auth_dict = {r['id']: conf_auth_num.get(r['lbl']) for _, r in conf_auth_map.iterrows()}

    conf_pers_map = query("SELECT nivel_confianza_personal_id AS id, nivel_confianza_personal AS lbl FROM dim_nivel_confianza_personal")
    conf_pers_num = {'Mucha': 4, 'Alguna': 3, 'Poca': 2, 'Nada': 1}
    conf_pers_dict = {r['id']: conf_pers_num.get(r['lbl']) for _, r in conf_pers_map.iterrows()}

    percep_map = query("SELECT percepcion_id AS id, percepcion AS lbl FROM dim_percepcion_seguridad")
    percep_dict = {r['id']: (1 if r['lbl'] == 'Seguro' else (0 if r['lbl'] == 'Inseguro' else np.nan))
                   for _, r in percep_map.iterrows()}

    envipe_raw = query("SELECT * FROM datamexico_envipe").merge(
        dim_estado, left_on='state_id', right_on='clave_ent', how='left')

    envipe_raw['conf_ejercito']       = envipe_raw['confidence_in_army_id'].map(conf_auth_dict)
    envipe_raw['conf_policia_federal']= envipe_raw['confidence_in_federal_police_id'].map(conf_auth_dict)
    envipe_raw['conf_mp']             = envipe_raw['confidence_in_public_ministry_and_state_prosecutors_id'].map(conf_auth_dict)
    envipe_raw['conf_policia_estatal']= envipe_raw['confidence_in_state_police_id'].map(conf_auth_dict)
    envipe_raw['conf_jueces']         = envipe_raw['confidence_in_judges_id'].map(conf_auth_dict)
    envipe_raw['conf_fiscalia']       = envipe_raw['confidence_in_state_prosecutor_of_the_republic_id'].map(conf_auth_dict)
    envipe_raw['percepcion_segura']   = envipe_raw['security_perception_in_their_state_id'].map(percep_dict)
    envipe_raw['conf_familia']        = envipe_raw['trust_in_family_id'].map(conf_pers_dict)
    envipe_raw['conf_amigos']         = envipe_raw['trust_in_friends_id'].map(conf_pers_dict)
    envipe_raw['conf_vecinos']        = envipe_raw['trust_in_neighborhood_id'].map(conf_pers_dict)
    envipe_raw['conf_trabajo']        = envipe_raw['trust_in_coworkers_id'].map(conf_pers_dict)
    # gastos_proteccion: ID midpoint in $k
    def _gastos(x):
        if pd.isna(x) or x == 99:  return np.nan
        if x == 1:  return 0.5
        if x == 41: return 40.0
        return float(x) - 0.5
    envipe_raw['gastos_proteccion'] = envipe_raw['expenses_in_protection_against_crime_id'].apply(_gastos)

    num_cols = ['conf_ejercito', 'conf_policia_federal', 'conf_mp', 'conf_policia_estatal',
                'conf_jueces', 'conf_fiscalia', 'percepcion_segura',
                'conf_familia', 'conf_amigos', 'conf_vecinos', 'conf_trabajo',
                'gastos_proteccion', 'homes', 'people']
    envipe_state = envipe_raw.groupby('estado')[num_cols].mean().reset_index()

    # ENOE 2025 wages
    enoe_raw = query("""
        SELECT e.state_id, e.monthly_wage, e.workforce
        FROM datamexico_enoe e
        WHERE e.quarter_id >= 20251 AND e.monthly_wage > 0
    """).merge(dim_estado, left_on='state_id', right_on='clave_ent', how='left')
    enoe_state = enoe_raw.groupby('estado').agg(avg_wage=('monthly_wage', 'mean')).reset_index()

    # Unified cross-sectional dataset
    infra_cols = [c for c in INFRA_VARS if c in idde25.columns]
    cross = (idde25[['estado'] + infra_cols].copy()
             .merge(pop2020[['estado', 'population']], on='estado', how='left')
             .merge(crime_total, on='estado', how='left')
             .merge(envipe_state, on='estado', how='left')
             .merge(enoe_state, on='estado', how='left'))

    # Crime rates
    cross['crime_rate_100k'] = (cross['total_crimes'] / cross['population']) * 100_000
    for cat in _CRIME_TYPES:
        col = f'crimes_{cat}'
        if col in cross.columns:
            cross[f'{cat}_rate_100k'] = (cross[col] / cross['population']) * 100_000

    # ── Correlations IDDE vs crime type ──────────────────────────────────────
    crime_type_corrs = {}
    for cat, display in [
        ('homicidio', 'Homicidio'), ('robo', 'Robo'), ('fraude', 'Fraude'),
        ('narcomenudeo', 'Narcomenudeo'), ('violencia_familiar', 'Violencia familiar'),
        ('lesiones', 'Lesiones'), ('extorsion', 'Extorsión'), ('secuestro', 'Secuestro'),
    ]:
        col = f'{cat}_rate_100k'
        if col not in cross.columns: continue
        d = cross[[_IDDE_COL, col]].dropna()
        if len(d) < 10: continue
        crime_type_corrs[display] = {
            'r': float(d[_IDDE_COL].corr(d[col])),
            'mean_rate': float(d[col].mean()),
        }

    # ── Full correlation matrix (infra × security), sorted by group ──────────
    hv = [c for c in INFRA_VARS if c in cross.columns]
    sv = [c for c in SEC_COL_LABELS if c in cross.columns]

    # Sort rows and columns by their group so related vars are adjacent
    def _sort_by_group(keys, group_dict, label_dict):
        labelled = [(k, label_dict[k]) for k in keys]
        return sorted(labelled, key=lambda x: (group_dict.get(x[1], 'ZZ'), x[1]))

    hv_sorted = [k for k, _ in _sort_by_group(hv, INFRA_GROUPS, INFRA_VARS)]
    sv_sorted = [k for k, _ in _sort_by_group(sv, SEC_GROUPS, SEC_COL_LABELS)]

    corr_raw = cross[hv_sorted + sv_sorted].corr().loc[hv_sorted, sv_sorted]
    corr_matrix = corr_raw.copy()
    corr_matrix.index   = [INFRA_VARS[c] for c in corr_raw.index]
    corr_matrix.columns = [SEC_COL_LABELS[c] for c in corr_raw.columns]

    # Group boundary annotations
    infra_group_sizes = {}
    for c in hv_sorted:
        g = INFRA_GROUPS.get(INFRA_VARS[c], 'Otro')
        infra_group_sizes[g] = infra_group_sizes.get(g, 0) + 1
    sec_group_sizes = {}
    for c in sv_sorted:
        g = SEC_GROUPS.get(SEC_COL_LABELS[c], 'Otro')
        sec_group_sizes[g] = sec_group_sizes.get(g, 0) + 1

    # ── Panel analysis 2022-2025 ──────────────────────────────────────────────
    panel_rows = []
    for yr, tbl in [(2022, 'idde_2022'), (2023, 'idde_2023'), (2024, 'idde_2024'), (2025, 'idde_2025')]:
        raw = query(f"SELECT * FROM {tbl}").rename(columns={'clave_inegi_de_estado': 'clave_ent'})
        idde_yr_col = next((c for c in raw.columns if 'indice_de_desarrollo_digital' in c.lower()), None)
        if not idde_yr_col: continue
        idde_yr = (raw[['clave_ent', idde_yr_col]].copy()
                   .merge(dim_estado, on='clave_ent', how='left'))
        idde_yr.columns = ['clave_ent', 'idde_index', 'estado']
        idde_yr['year'] = yr
        crime_yr = query(f"""
            SELECT e.estado, SUM(f.incidencia_delictiva) AS total_crimes
            FROM incidencia_estatal f JOIN dim_estado e ON f.clave_ent = e.clave_ent
            WHERE f.anio = {yr} GROUP BY e.estado
        """)
        idde_yr = (idde_yr
                   .merge(crime_yr, on='estado', how='left')
                   .merge(pop2020[['estado', 'population']], on='estado', how='left'))
        idde_yr['crime_rate'] = (idde_yr['total_crimes'] / idde_yr['population']) * 100_000
        panel_rows.append(idde_yr)

    panel = pd.concat(panel_rows, ignore_index=True).sort_values(['estado', 'year'])
    panel['didde']       = panel.groupby('estado')['idde_index'].diff()
    panel['dcrime_rate'] = panel.groupby('estado')['crime_rate'].diff()

    # Changes 2022 → 2025
    changes_rows = []
    for estado in cross['estado'].dropna().unique():
        sub = panel[panel['estado'] == estado]
        p22 = sub[sub['year'] == 2022]
        p25 = sub[sub['year'] == 2025]
        if p22.empty or p25.empty: continue
        changes_rows.append({
            'estado': estado,
            'didde':  float(p25['idde_index'].values[0]) - float(p22['idde_index'].values[0]),
            'dcrime': float(p25['crime_rate'].values[0]) - float(p22['crime_rate'].values[0]),
        })
    changes_df = pd.DataFrame(changes_rows).dropna()
    panel_r_overall = float(changes_df['didde'].corr(changes_df['dcrime'])) if len(changes_df) > 3 else 0.0

    # Per-crime-type panel correlations
    panel_type_corrs = {}
    deltas = panel.dropna(subset=['didde', 'dcrime_rate'])
    panel_type_corrs['Crimen total'] = float(deltas['didde'].corr(deltas['dcrime_rate']))

    # ── Velocity vs Coverage R² ───────────────────────────────────────────────
    cv_col  = 'cobertura_de_banda_ancha_fija_por'
    spd_col = 'velocidad_de_descarga_de_banda_ancha_movil_mbps'
    r2_rows = []
    for tgt, tgt_name in [
        ('avg_wage', 'Salario promedio'), ('crime_rate_100k', 'Crimen total'), ('homicidio_rate_100k', 'Homicidios')
    ]:
        if tgt not in cross.columns: continue
        d = cross[[cv_col, spd_col, tgt]].dropna()
        if len(d) < 15: continue
        r2_c = float(LinearRegression().fit(d[[cv_col]], d[tgt]).score(d[[cv_col]], d[tgt]))
        r2_s = float(LinearRegression().fit(d[[spd_col]], d[tgt]).score(d[[spd_col]], d[tgt]))
        r2_b = float(LinearRegression().fit(d[[cv_col, spd_col]], d[tgt]).score(d[[cv_col, spd_col]], d[tgt]))
        r2_rows.append({'target': tgt_name, 'r2_cob': r2_c, 'r2_vel': r2_s, 'r2_amb': r2_b,
                        'winner': 'Velocidad' if r2_s > r2_c else 'Cobertura'})
    r2_df = pd.DataFrame(r2_rows)

    # ── K-Means k=4 ──────────────────────────────────────────────────────────
    cluster_feats = [c for c in [
        _IDDE_COL, 'crime_rate_100k', 'homicidio_rate_100k',
        'percepcion_segura', 'conf_familia', 'conf_policia_estatal',
    ] if c in cross.columns]
    X_cl = cross[cluster_feats].dropna()
    scaler = StandardScaler()
    X_scl  = scaler.fit_transform(X_cl)
    km     = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = km.fit_predict(X_scl)
    cross_cl = cross.loc[X_cl.index].copy()
    cross_cl['cluster'] = labels

    # Auto-label clusters from their profile
    cluster_stats = {}
    for c_id in sorted(cross_cl['cluster'].unique()):
        sub = cross_cl[cross_cl['cluster'] == c_id]
        cluster_stats[int(c_id)] = {
            'idde':       float(sub[_IDDE_COL].mean()),
            'crime':      float(sub['crime_rate_100k'].mean()),
            'homicidio':  float(sub['homicidio_rate_100k'].mean()) if 'homicidio_rate_100k' in sub else 0,
            'percepcion': float(sub['percepcion_segura'].mean()) if 'percepcion_segura' in sub else 0.3,
            'estados':    sorted(sub['estado'].dropna().tolist()),
            'n':          int(len(sub)),
        }

    def _auto_label(c_id, stats):
        s   = stats[c_id]
        hom = s['homicidio']
        prc = s['percepcion']
        idd = s['idde']
        all_idd  = sorted([v['idde']       for v in stats.values()])
        all_hom  = sorted([v['homicidio']  for v in stats.values()])
        if idd <= all_idd[0] * 1.05:        # lowest IDDE
            return ('C0', 'Tradicionales',       '#d15b4a',
                'Menor IDDE del país. Crimen reportado bajo por subregistro. Baja cobertura y conectividad. '
                'Potencial para infraestructura básica de Huawei.')
        elif hom >= all_hom[-1] * 0.85:    # highest homicidios
            return ('C3', 'Violentos-conectados', '#e4982e',
                'Buena infraestructura digital pero crisis de homicidios (4× el promedio nacional). '
                'La tecnología sin institucionalidad no resuelve la violencia. Necesitan seguridad inteligente, no más fibra.')
        elif prc >= max(v['percepcion'] for v in stats.values()) * 0.85:  # highest perception
            return ('C2', 'Desarrollados-seguros', '#2bb573',
                'Mejor IDDE + alta percepción de seguridad + bajos homicidios. '
                'El modelo aspiracional: digitalización y seguridad coexisten. Referencia para política pública.')
        else:                               # residual = CDMX/EdoMex/Jalisco
            return ('C1', 'Inseguros-urbanos',    '#3891c7',
                'CDMX, EdoMex, Jalisco. Tienen acceso digital pero la PEOR percepción de seguridad (solo ~16% se siente seguro). '
                'El alto crimen reportado refleja MEJOR sistema de denuncias, no necesariamente más crimen real. '
                'La digitalización financiera aquí correlaciona negativamente con la confianza institucional.')

    label_map = {c_id: _auto_label(c_id, cluster_stats) for c_id in cluster_stats}
    cross_cl['cluster_code']  = cross_cl['cluster'].map(lambda x: label_map[x][0])
    cross_cl['cluster_name']  = cross_cl['cluster'].map(lambda x: label_map[x][1])
    cross_cl['cluster_color'] = cross_cl['cluster'].map(lambda x: label_map[x][2])

    return {
        'cross':              cross,
        'cross_cl':           cross_cl,
        'crime_type_corrs':   crime_type_corrs,
        'corr_matrix':        corr_matrix,
        'infra_group_sizes':  infra_group_sizes,
        'sec_group_sizes':    sec_group_sizes,
        'panel':              panel,
        'panel_r_overall':    panel_r_overall,
        'panel_type_corrs':   panel_type_corrs,
        'changes_df':         changes_df,
        'r2_df':              r2_df,
        'cluster_stats':      cluster_stats,
        'label_map':          label_map,
    }


def get_data_11():
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(_CACHE_FILE):
        _cache = joblib.load(_CACHE_FILE)
        return _cache
    result = _build()
    joblib.dump(result, _CACHE_FILE)
    _cache = result
    return result
