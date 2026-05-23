from pages.db import query
from pages.get_data.get_data_3 import BIEN_JURIDICO_MAP

MESES_NOMBRES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                 7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

_df_heat = None
_df_vic  = None


def _load_heat():
    global _df_heat
    if _df_heat is not None:
        return _df_heat
    _df_heat = query("""
        SELECT f.anio, f.mes_num, e.estado,
               SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_estado e ON f.clave_ent = e.clave_ent
        GROUP BY f.anio, f.mes_num, e.estado
    """)
    return _df_heat


def _load_vic():
    global _df_vic
    if _df_vic is not None:
        return _df_vic
    _df_vic = query("""
        SELECT f.ano, x.sexo, r.rango_edad, e.estado,
               SUM(f.enero + f.febrero + f.marzo + f.abril + f.mayo + f.junio +
                   f.julio + f.agosto + f.septiembre + f.octubre +
                   f.noviembre + f.diciembre) AS total
        FROM victimas_fuero_comun f
        JOIN dim_estado     e ON f.clave_ent     = e.clave_ent
        JOIN dim_sexo       x ON f.sexo_id       = x.sexo_id
        JOIN dim_rango_edad r ON f.rango_edad_id = r.rango_edad_id
        GROUP BY f.ano, x.sexo, r.rango_edad, e.estado
    """)
    return _df_vic


def get_entidades():
    return ['Nacional'] + sorted(_load_heat()['estado'].unique().tolist())


def get_anios():
    return sorted(_load_heat()['anio'].unique().tolist())


def get_heatmap_data(estado=None):
    df = _load_heat()
    if estado and estado != 'Nacional':
        df = df[df['estado'] == estado]
    pivot = df.groupby(['anio', 'mes_num'])['total'].sum().reset_index()
    mat = pivot.pivot(index='mes_num', columns='anio', values='total').fillna(0)
    return mat


def get_victimas_sexo(estado=None):
    df = _load_vic()
    if estado and estado != 'Nacional':
        df = df[df['estado'] == estado]
    df = df[~df['sexo'].str.lower().str.contains('no identificado', na=False)]
    return df.groupby(['ano', 'sexo'])['total'].sum().reset_index()


def get_victimas_edad(estado=None):
    df = _load_vic()
    if estado and estado != 'Nacional':
        df = df[df['estado'] == estado]
    return df.groupby(['ano', 'rango_edad'])['total'].sum().reset_index()


def get_comparativa_anios(anio1, anio2, estado=None):
    where_estado = f'AND e.estado = \'{estado}\'' if estado and estado != 'Nacional' else ''
    df = query(f"""
        SELECT f.anio, s.subtipo, SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
        JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
        WHERE f.anio IN ({anio1}, {anio2}) {where_estado}
        GROUP BY f.anio, s.subtipo
    """)
    df['bien_juridico'] = df['subtipo'].map(BIEN_JURIDICO_MAP).fillna('Otros bienes jurídicos')
    piv = (df.pivot_table(index='bien_juridico', columns='anio', values='total', aggfunc='sum')
             .fillna(0))
    piv.columns = [str(c) for c in piv.columns]
    a1, a2 = str(anio1), str(anio2)
    if a1 in piv.columns and a2 in piv.columns:
        piv['delta']     = piv[a2] - piv[a1]
        piv['delta_pct'] = (piv['delta'] / piv[a1].replace(0, 1) * 100).round(1)
    return piv.reset_index().sort_values('delta', ascending=True)
