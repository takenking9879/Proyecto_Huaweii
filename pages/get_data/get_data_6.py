import pandas as pd
import numpy as np
from pages.db import query
from pages.get_data.get_data_1 import get_pob

BIEN_MAP = {
    'Feminicidio': 'Vida', 'Homicidio doloso': 'Vida', 'Homicidio culposo': 'Vida',
    'Lesiones dolosas': 'Vida', 'Lesiones culposas': 'Vida', 'Aborto': 'Vida',
    'Secuestro': 'Libertad', 'Trata de personas': 'Libertad', 'Rapto': 'Libertad',
    'Otros delitos que atentan contra la libertad personal': 'Libertad',
    'Violación simple': 'Sexual', 'Violación equiparada': 'Sexual',
    'Abuso sexual': 'Sexual', 'Acoso sexual': 'Sexual', 'Hostigamiento sexual': 'Sexual',
    'Otros delitos que atentan contra la libertad y la seguridad sexual': 'Sexual',
    'Violencia familiar': 'Familia',
    'Violencia de género en todas sus modalidades distinta a la violencia familiar': 'Familia',
    'Incesto': 'Familia', 'Otros delitos contra la familia': 'Familia',
    'Narcomenudeo': 'Sociedad', 'Corrupción de menores': 'Sociedad',
    'Tráfico de menores': 'Sociedad', 'Lenocinio': 'Sociedad',
    'Otros delitos contra la sociedad': 'Sociedad',
    'Delitos ambientales': 'Estado',
    'Robo de vehículo automotor': 'Patrimonio', 'Robo a casa habitación': 'Patrimonio',
    'Robo a negocio': 'Patrimonio', 'Robo a transeúnte en vía pública con violencia': 'Patrimonio',
    'Robo a transeúnte en vía pública sin violencia': 'Patrimonio',
    'Robo en transporte público colectivo': 'Patrimonio', 'Robo a bordo de metro': 'Patrimonio',
    'Robo a institución bancaria': 'Patrimonio', 'Robo de autopartes': 'Patrimonio',
    'Robo de maquinaria': 'Patrimonio', 'Robo de ganado': 'Patrimonio',
    'Robo de madera': 'Patrimonio', 'Robo en carretera': 'Patrimonio',
    'Robo a transportista': 'Patrimonio', 'Robo a repartidor': 'Patrimonio',
    'Robo a bordo de microbús': 'Patrimonio', 'Robo a bordo de taxi': 'Patrimonio',
    'Robo a bordo de tren': 'Patrimonio', 'Otros robos': 'Patrimonio',
    'Fraude': 'Patrimonio', 'Extorsión': 'Patrimonio', 'Abigeato': 'Patrimonio',
    'Despojo': 'Patrimonio', 'Daño a la propiedad': 'Patrimonio',
}

GRUPO_COLORS = {
    'Básico':      '#d62728',
    'Emprendedor': '#ff7f0e',
    'Avanzado':    '#1f77b4',
    'Líder':       '#2ca02c',
}
GRUPO_ORDER = ['Básico', 'Emprendedor', 'Avanzado', 'Líder']

_IDDE_META = {
    2022: ('indice_de_desarrollo_digital_estatal_2022', 'grupo_de_digitalizacion_id'),
    2023: ('indice_de_desarrollo_digital_estatal_2023', 'grupo_de_digitalizacion_2023_id'),
    2024: ('indice_de_desarrollo_digital_estatal_2024', 'grupo_de_digitalizacion_2024_id'),
}

_cache = {}


def _load_year(anio: int) -> pd.DataFrame:
    if anio in _cache:
        return _cache[anio]

    idde_col, grupo_col = _IDDE_META[anio]
    idde = query(f"""
        SELECT clave_inegi_de_estado AS clave_ent,
               {idde_col} AS idde_score,
               pilar_infraestructura,
               pilar_digitalizacion_de_las_personas_y_la_sociedad AS pilar_sociedad,
               pilar_innovacion_y_adopcion_tecnologica_de_las_empresas AS pilar_innovacion,
               {grupo_col} AS grupo_id
        FROM idde_{anio}
    """)
    grupos = query("SELECT grupo_id, grupo FROM dim_grupo_digitalizacion")
    idde = idde.merge(grupos, on='grupo_id', how='left')
    idde.rename(columns={'grupo': 'grupo_label'}, inplace=True)

    crime = query(f"""
        SELECT e.clave_ent, e.estado, s.subtipo,
               SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
        JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
        WHERE f.anio = {anio}
        GROUP BY e.clave_ent, e.estado, s.subtipo
    """)
    crime['categoria'] = crime['subtipo'].map(BIEN_MAP).fillna('Otros')
    cat = (crime.groupby(['clave_ent', 'categoria'])['total'].sum()
               .unstack(fill_value=0).add_prefix('crime_').reset_index())
    tot = crime.groupby(['clave_ent', 'estado'])['total'].sum().reset_index(name='total_delitos')

    df = tot.merge(cat, on='clave_ent').merge(idde, on='clave_ent')
    df['anio'] = anio
    df['poblacion'] = df['estado'].apply(lambda e: get_pob(e, anio))
    df['tasa_x100k'] = df['total_delitos'] / df['poblacion'] * 100_000
    for cat_col in [c for c in df.columns if c.startswith('crime_')]:
        df[cat_col.replace('crime_', 'tasa_')] = df[cat_col] / df['poblacion'] * 100_000

    _cache[anio] = df
    return df


def get_df(anio=2022):
    return _load_year(int(anio))


def get_df_all():
    frames = [_load_year(yr) for yr in [2022, 2023, 2024]]
    return pd.concat(frames, ignore_index=True)


def get_kpis(anio=2022):
    df = get_df(anio)
    tasa_col = 'tasa_Sociedad' if 'tasa_Sociedad' in df.columns else 'tasa_x100k'
    corr = df[['idde_score', tasa_col]].corr().iloc[0, 1]
    return {
        'correlacion': round(float(corr), 3),
        'mejor_estado': df.loc[df['idde_score'].idxmax(), 'estado'],
        'peor_estado':  df.loc[df['idde_score'].idxmin(), 'estado'],
        'n_lideres': int((df['grupo_label'] == 'Líder').sum()),
    }


def get_pilares_por_grupo(anio=2022):
    df = get_df(anio)
    return df.groupby('grupo_label')[
        ['pilar_infraestructura', 'pilar_sociedad', 'pilar_innovacion']
    ].mean().reset_index()


def get_crimen_por_grupo(anio=2022):
    df = get_df(anio)
    tasa_cols = [c for c in df.columns if c.startswith('tasa_') and c != 'tasa_x100k']
    return df.groupby('grupo_label')[tasa_cols + ['tasa_x100k']].mean().reset_index()
