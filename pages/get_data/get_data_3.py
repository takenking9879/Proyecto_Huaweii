from pages.db import query

# Subtipo -> bien juridico mapping (methodological — differs from DB taxonomy)
BIEN_JURIDICO_MAP = {
    'Feminicidio':           'Vida e Integridad Corporal',
    'Homicidio doloso':      'Vida e Integridad Corporal',
    'Homicidio culposo':     'Vida e Integridad Corporal',
    'Lesiones dolosas':      'Vida e Integridad Corporal',
    'Lesiones culposas':     'Vida e Integridad Corporal',
    'Aborto':                'Vida e Integridad Corporal',
    'Secuestro':             'Libertad Personal',
    'Trata de personas':     'Libertad Personal',
    'Rapto':                 'Libertad Personal',
    'Otros delitos que atentan contra la libertad personal': 'Libertad Personal',
    'Violación simple':      'Libertad y Seguridad Sexual',
    'Violación equiparada':  'Libertad y Seguridad Sexual',
    'Abuso sexual':          'Libertad y Seguridad Sexual',
    'Acoso sexual':          'Libertad y Seguridad Sexual',
    'Hostigamiento sexual':  'Libertad y Seguridad Sexual',
    'Otros delitos que atentan contra la libertad y la seguridad sexual': 'Libertad y Seguridad Sexual',
    'Robo de vehículo automotor':                 'El Patrimonio',
    'Robo a casa habitación':                     'El Patrimonio',
    'Robo a negocio':                             'El Patrimonio',
    'Robo a transeúnte en vía pública con violencia': 'El Patrimonio',
    'Robo a transeúnte en vía pública sin violencia': 'El Patrimonio',
    'Robo en transporte público colectivo':       'El Patrimonio',
    'Robo a bordo de metro':                      'El Patrimonio',
    'Robo a institución bancaria':                'El Patrimonio',
    'Robo de autopartes':                         'El Patrimonio',
    'Robo de maquinaria':                         'El Patrimonio',
    'Robo de ganado':                             'El Patrimonio',
    'Robo de madera':                             'El Patrimonio',
    'Robo en carretera':                          'El Patrimonio',
    'Robo a transportista':                       'El Patrimonio',
    'Robo a repartidor':                          'El Patrimonio',
    'Robo a bordo de microbús':                   'El Patrimonio',
    'Robo a bordo de taxi':                       'El Patrimonio',
    'Robo a bordo de tren':                       'El Patrimonio',
    'Otros robos':                                'El Patrimonio',
    'Fraude':                                     'El Patrimonio',
    'Extorsión':                                  'El Patrimonio',
    'Abigeato':                                   'El Patrimonio',
    'Despojo':                                    'El Patrimonio',
    'Daño a la propiedad':                        'El Patrimonio',
    'Violencia familiar':                         'La Familia',
    'Violencia de género en todas sus modalidades distinta a la violencia familiar': 'La Familia',
    'Incesto':                                    'La Familia',
    'Otros delitos contra la familia':            'La Familia',
    'Narcomenudeo':                               'La Sociedad',
    'Corrupción de menores':                      'La Sociedad',
    'Tráfico de menores':                         'La Sociedad',
    'Lenocinio':                                  'La Sociedad',
    'Otros delitos contra la sociedad':           'La Sociedad',
    'Delitos ambientales':                        'Estado y Seguridad Pública',
}

_df = None


def _load():
    global _df
    if _df is not None:
        return _df
    raw = query("""
        SELECT f.anio, s.subtipo, e.estado,
               SUM(f.incidencia_delictiva) AS total
        FROM incidencia_estatal f
        JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
        JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
        GROUP BY f.anio, s.subtipo, e.estado
    """)
    raw['bien_juridico'] = (raw['subtipo']
                            .map(BIEN_JURIDICO_MAP)
                            .fillna('Otros bienes jurídicos'))
    _df = raw
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


def get_distribucion_bienes(estado=None, anio_inicio=None, anio_fin=None):
    return (_filtrar(estado, anio_inicio, anio_fin)
            .groupby('bien_juridico')['total'].sum().reset_index()
            .sort_values('total', ascending=False))


def get_subtipos_detalle(estado=None, anio_inicio=None, anio_fin=None):
    return (_filtrar(estado, anio_inicio, anio_fin)
            .groupby(['bien_juridico', 'subtipo'])['total'].sum().reset_index())


def get_tendencia_bienes(estado=None):
    df = _load()
    if estado and estado != 'Nacional':
        df = df[df['estado'] == estado]
    return df.groupby(['anio', 'bien_juridico'])['total'].sum().reset_index()
