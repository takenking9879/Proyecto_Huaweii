import duckdb
import os
import threading

_DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'db').replace('\\', '/')

_TABLES = [
    'incidencia_estatal', 'incidencia_municipal', 'victimas_fuero_comun',
    'dim_estado', 'dim_municipio', 'dim_subtipo_delito', 'dim_sexo',
    'dim_rango_edad', 'dim_bien_juridico_afectado', 'dim_modalidad',
    'dim_month', 'dim_quarter', 'dim_company_size', 'dim_job_situation',
    'dim_occupation', 'dim_instruction_level', 'dim_schooling_years',
    'dim_percepcion_seguridad', 'dim_nivel_confianza', 'dim_nivel_confianza_personal',
    'dim_gastos_proteccion', 'dim_rango_porcentaje', 'dim_economically_active_population',
    'dim_estrato_sociodemografico', 'dim_grupo_digitalizacion',
    'idde_2022', 'idde_2023', 'idde_2024', 'idde_2025',
    'pib_estatal', 'bien_map', 'poblacion_ancla',
    'datamexico_denue', 'datamexico_enoe', 'datamexico_envipe',
    'datamexico_population',
]

# Thread-local storage — each thread gets its own DuckDB connection
_tls = threading.local()


def get_con():
    if not hasattr(_tls, 'con'):
        con = duckdb.connect()
        for t in _TABLES:
            path = f'{_DB_DIR}/{t}.parquet'
            if os.path.exists(path):
                con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{path}')")
        _tls.con = con
    return _tls.con


def query(sql: str):
    return get_con().execute(sql).df()
