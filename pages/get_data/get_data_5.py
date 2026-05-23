import pandas as pd
import numpy as np
from pages.db import query
from pages.get_data.get_data_1 import get_pob

_cache = None


def _load():
    global _cache
    if _cache is not None:
        return _cache
    crime = query("""
        SELECT e.estado, e.abrev, f.anio,
               SUM(f.incidencia_delictiva) AS total_delitos
        FROM incidencia_estatal f
        JOIN dim_estado e ON f.clave_ent = e.clave_ent
        GROUP BY e.estado, e.abrev, f.anio
    """)
    crime['poblacion'] = crime.apply(lambda r: get_pob(r['estado'], int(r['anio'])), axis=1)
    crime['tasa_x100k'] = crime['total_delitos'] / crime['poblacion'] * 100_000

    pib = query("SELECT estado, anio, variacion_pib FROM pib_estatal")
    df = crime.merge(pib, on=['estado', 'anio'], how='inner')
    _cache = df.dropna(subset=['tasa_x100k', 'variacion_pib'])
    return _cache


def get_anios():
    return sorted(_load()['anio'].unique().tolist())


def get_estados():
    return sorted(_load()['estado'].unique().tolist())


def get_scatter_pib(anio=None):
    df = _load()
    if anio:
        df = df[df['anio'] == int(anio)]
    return df


def get_tendencia_nacional():
    df = _load()
    return df.groupby('anio').agg(
        tasa_crimen=('tasa_x100k', 'mean'),
        pib_crecimiento=('variacion_pib', 'mean'),
    ).reset_index()


def get_ranking_doble(anio=None):
    df = get_scatter_pib(anio)
    df = df.groupby(['estado', 'abrev']).agg(
        tasa_crimen=('tasa_x100k', 'mean'),
        pib_crecimiento=('variacion_pib', 'mean'),
    ).reset_index().sort_values('tasa_crimen', ascending=False)
    return df


def get_kpis():
    df = _load()
    corr = df[['tasa_x100k', 'variacion_pib']].corr().iloc[0, 1]
    anio_max_crime = int(df.groupby('anio')['tasa_x100k'].mean().idxmax())
    pib_2022 = df[df['anio'] == 2022]['variacion_pib'].mean()
    return {
        'correlacion': round(float(corr), 3),
        'anio_pico_crimen': anio_max_crime,
        'avg_pib_2022': round(float(pib_2022), 2),
        'n_estados': int(df['estado'].nunique()),
    }
