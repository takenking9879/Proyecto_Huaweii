from pages.db import query

_df_estados = None


def _load_estados():
    global _df_estados
    if _df_estados is not None:
        return _df_estados
    _df_estados = query("""
        SELECT f.anio, e.estado, e.abrev,
               SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_estado e ON f.clave_ent = e.clave_ent
        GROUP BY f.anio, e.estado, e.abrev
    """)
    return _df_estados


def get_anios():
    return sorted(_load_estados()['anio'].unique().tolist())


def get_ranking_estados(anio=None):
    df = _load_estados()
    if anio:
        df = df[df['anio'] == anio]
    return (df.groupby(['estado', 'abrev'])['total'].sum()
              .reset_index()
              .sort_values('total', ascending=True))


def get_evolucion_estados(n=5):
    df = _load_estados()
    top = df.groupby('estado')['total'].sum().nlargest(n).index.tolist()
    return df[df['estado'].isin(top)].sort_values('anio'), top


def get_top_municipios(anio=None, n=15):
    where = f"WHERE f.ano = {anio}" if anio else ""
    return query(f"""
        SELECT e.estado, m.municipio,
               SUM(f.enero + f.febrero + f.marzo + f.abril + f.mayo + f.junio +
                   f.julio + f.agosto + f.septiembre + f.octubre +
                   f.noviembre + f.diciembre) AS total
        FROM incidencia_municipal f
        JOIN dim_estado    e ON f.clave_ent    = e.clave_ent
        JOIN dim_municipio m ON f.clave_ent    = m.clave_ent
                           AND f.cve_municipio = m.cve_municipio
        {where}
        GROUP BY e.estado, m.municipio
        ORDER BY total DESC
        LIMIT {n}
    """)
