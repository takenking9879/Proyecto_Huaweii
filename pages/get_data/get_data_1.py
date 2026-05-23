from pages.db import query

# CONAPO mid-year population estimates (persons) — key years interpolated linearly
POBLACION = {
    'Aguascalientes':               {2015: 1312544,  2020: 1434635,  2025: 1563053},
    'Baja California':              {2015: 3315766,  2020: 3769020,  2025: 4192534},
    'Baja California Sur':          {2015: 712029,   2020: 798447,   2025: 897487},
    'Campeche':                     {2015: 899931,   2020: 928363,   2025: 975528},
    'Chiapas':                      {2015: 5217908,  2020: 5543828,  2025: 5816003},
    'Chihuahua':                    {2015: 3556574,  2020: 3741869,  2025: 3907760},
    'Ciudad de México':             {2015: 8918653,  2020: 9209944,  2025: 9433137},
    'Coahuila de Zaragoza':         {2015: 2954915,  2020: 3146771,  2025: 3352283},
    'Colima':                       {2015: 711235,   2020: 731391,   2025: 754803},
    'Durango':                      {2015: 1754754,  2020: 1832650,  2025: 1906808},
    'Guanajuato':                   {2015: 5853677,  2020: 6166934,  2025: 6478042},
    'Guerrero':                     {2015: 3388768,  2020: 3540685,  2025: 3664869},
    'Hidalgo':                      {2015: 2858359,  2020: 3082841,  2025: 3302025},
    'Jalisco':                      {2015: 7844830,  2020: 8348151,  2025: 8848192},
    'México':                       {2015: 16187608, 2020: 16992418, 2025: 17694226},
    'Michoacán de Ocampo':          {2015: 4584471,  2020: 4748846,  2025: 4898892},
    'Morelos':                      {2015: 1903811,  2020: 1971520,  2025: 2041576},
    'Nayarit':                      {2015: 1181050,  2020: 1235456,  2025: 1291112},
    'Nuevo León':                   {2015: 5119504,  2020: 5784442,  2025: 6373232},
    'Oaxaca':                       {2015: 3967889,  2020: 4132148,  2025: 4291270},
    'Puebla':                       {2015: 6168883,  2020: 6583278,  2025: 7011748},
    'Querétaro':                    {2015: 2038372,  2020: 2368467,  2025: 2689988},
    'Quintana Roo':                 {2015: 1501562,  2020: 1857985,  2025: 2184143},
    'San Luis Potosí':              {2015: 2717820,  2020: 2822255,  2025: 2936889},
    'Sinaloa':                      {2015: 2966321,  2020: 3026981,  2025: 3083898},
    'Sonora':                       {2015: 2850330,  2020: 2944840,  2025: 3046739},
    'Tabasco':                      {2015: 2395272,  2020: 2402598,  2025: 2433765},
    'Tamaulipas':                   {2015: 3441698,  2020: 3527735,  2025: 3615694},
    'Tlaxcala':                     {2015: 1272847,  2020: 1342977,  2025: 1407844},
    'Veracruz de Ignacio de la Llave': {2015: 8112505, 2020: 8062579, 2025: 8028879},
    'Yucatán':                      {2015: 2097175,  2020: 2320898,  2025: 2511049},
    'Zacatecas':                    {2015: 1579209,  2020: 1622138,  2025: 1663029},
}


def get_pob(estado, anio):
    data = POBLACION.get(estado)
    if not data:
        return None
    years = sorted(data.keys())
    if anio <= years[0]:
        return data[years[0]]
    if anio >= years[-1]:
        return data[years[-1]]
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i + 1]
        if y0 <= anio <= y1:
            t = (anio - y0) / (y1 - y0)
            return data[y0] + t * (data[y1] - data[y0])
    return None


_df = None


def _load():
    global _df
    if _df is not None:
        return _df
    _df = query("""
        SELECT f.anio, f.mes_num, f.incidencia_delictiva, e.estado
        FROM incidencia_estatal f
        JOIN dim_estado e ON f.clave_ent = e.clave_ent
    """)
    return _df


def get_entidades():
    return ['Nacional'] + sorted(_load()['estado'].unique().tolist())


def get_anios():
    return sorted(_load()['anio'].unique().tolist())


def _filtrar(estado=None, anio_inicio=None, anio_fin=None):
    df = _load()
    if estado and estado != 'Nacional':
        df = df[df['estado'] == estado]
    if anio_inicio:
        df = df[df['anio'] >= anio_inicio]
    if anio_fin:
        df = df[df['anio'] <= anio_fin]
    return df


def get_tendencia_anual(estado=None, anio_inicio=None, anio_fin=None):
    return (_filtrar(estado, anio_inicio, anio_fin)
            .groupby('anio')['incidencia_delictiva'].sum().reset_index())


def get_estacionalidad(estado=None, anio_inicio=None, anio_fin=None):
    MESES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
             7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    df = _filtrar(estado, anio_inicio, anio_fin)
    res = df.groupby('mes_num')['incidencia_delictiva'].mean().reset_index()
    res['mes'] = res['mes_num'].map(MESES)
    return res.sort_values('mes_num')


def get_kpis(estado=None, anio_inicio=None, anio_fin=None):
    por_anio = (_filtrar(estado, anio_inicio, anio_fin)
                .groupby('anio')['incidencia_delictiva'].sum())
    if por_anio.empty:
        return {'total': 0, 'anio_pico': 0, 'variacion': 0}
    total    = int(por_anio.sum())
    pico     = int(por_anio.idxmax())
    anios    = sorted(por_anio.index)
    variacion = 0
    if len(anios) >= 2:
        u, p = por_anio[anios[-1]], por_anio[anios[-2]]
        variacion = round((u - p) / p * 100, 1) if p > 0 else 0
    return {'total': total, 'anio_pico': pico, 'variacion': variacion}


def get_top_estados_lineas(n=5):
    df = _load()
    top = df.groupby('estado')['incidencia_delictiva'].sum().nlargest(n).index.tolist()
    res = (df[df['estado'].isin(top)]
           .groupby(['anio', 'estado'])['incidencia_delictiva'].sum().reset_index())
    return res, top


def get_top_estados_percapita(n=5):
    df = _load()
    anual = df.groupby(['anio', 'estado'])['incidencia_delictiva'].sum().reset_index()
    anual['poblacion'] = anual.apply(lambda r: get_pob(r['estado'], r['anio']), axis=1)
    anual = anual.dropna(subset=['poblacion'])
    anual['tasa'] = anual['incidencia_delictiva'] / anual['poblacion'] * 100_000
    top = anual.groupby('estado')['tasa'].mean().nlargest(n).index.tolist()
    return anual[anual['estado'].isin(top)], top
