import traceback
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from pages.components import sidebar
from pages.get_figures.get_figures_11 import (
    fig_crime_type_corrs, fig_corr_heatmap, fig_6_scatters,
    fig_clustering_scatter, fig_cluster_profiles,
)
from pages.get_figures.get_figures_6 import fig_scatter_idde
from pages.get_data.get_data_11 import get_data_11

dash.register_page(__name__, path='/slide_11')

_CHART_H = '340px'

_IDDE_ANIOS = [2022, 2023, 2024]
_IDDE_TASAS = [
    ('tasa_Sociedad',   'Tasa Sociedad'),
    ('tasa_Patrimonio', 'Tasa Patrimonio'),
    ('tasa_Vida',       'Tasa Vida'),
    ('tasa_Familia',    'Tasa Familia'),
    ('tasa_Sexual',     'Tasa Sexual'),
    ('tasa_x100k',      'Tasa Total'),
]

_INSIGHTS = [
    {
        'icon': '◈', 'color': 'card-success',
        'title': 'Fraude lidera — r = +0.63',
        'desc': 'Es el delito más correlacionado con digitalización. No porque la tecnología cause fraude, '
                'sino porque más IDDE = más transacciones digitales + mejores canales de denuncia. '
                'En el extremo opuesto, homicidios no correlacionan (r = +0.03): '
                'la violencia letal depende del crimen organizado, no del WiFi.',
    },
    {
        'icon': '◎', 'color': 'card-cyan',
        'title': 'Confianza social — r = +0.78 (la más fuerte)',
        'desc': 'La variable de seguridad que más responde a infraestructura digital no es ninguna tasa de crimen: '
                'es la confianza entre amigos y familia. Pero el efecto se invierte en instituciones: '
                'mayor bancarización digital → menor confianza en jueces y Ministerio Público (r hasta −0.50). '
                'El acceso digital expone las fallas del Estado más de lo que las resuelve.',
    },
    {
        'icon': '⌬', 'color': 'card-gold',
        'title': '4 perfiles — cada uno pide solución distinta',
        'desc': 'K-Means (k=4) sobre 6 dimensiones simultáneas (IDDE, crimen, homicidios, percepción, '
                'confianza familiar y policial) revela cuatro narrativas estratégicas: '
                'desde estados que necesitan cobertura básica (C0) hasta estados con buena infraestructura '
                'pero crisis de homicidios (C3). Una propuesta única no sirve para todos.',
    },
]


_CLUSTER_CALLOUTS = {
    'C0': (
        '¿Por qué C0 no es tan seguro como parece?',
        'Los estados Tradicionales registran el crimen más bajo (~984/100k), pero solo el 29% '
        'de su población se siente segura — apenas 13 puntos por encima del peor cluster. '
        'La paradoja se explica por subregistro: baja digitalización = menos canales de denuncia '
        '= menos crimen anotado en los registros, no menos crimen real. '
        'Guerrero y Chiapas concentran presencia fuerte del crimen organizado que no llega a las estadísticas oficiales. '
        'Mayor oportunidad de infraestructura básica (conectividad, fibra, cobertura móvil): '
        'la banda ancha aquí no solo conecta — también hace visible lo que antes era invisible '
        'y habilita servicios públicos digitales que hoy no existen.',
    ),
    'C1': (
        '¿Por qué C1 es el caso más complejo?',
        'CDMX, EdoMex y Jalisco tienen acceso digital comparable al C2 (Desarrollados), '
        'pero la peor percepción de seguridad del país (~16% se siente seguro). '
        'La explicación no es más crimen real, sino un mejor sistema de denuncias: '
        'más digitalización → más capacidad de reportar → más crimen registrado. '
        'Adicionalmente, la digitalización financiera (tarjetas, banca) correlaciona '
        'negativamente con la confianza institucional en estas entidades, '
        'lo que sugiere que el acceso digital expone más las fallas del Estado que las resuelve.',
    ),
}


def _insight_card(icon, color, title, desc, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Span(icon, className='insight-icon'),
            html.P(title, className='insight-title'),
            html.P(desc, className='insight-desc'),
        ], style={'padding': '16px 18px'}),
    ], className=f'animate-in h-100 {color} {delay}')


def _cluster_card(code, name, color, desc, estados, n, callout=None):
    border_style = f'2px solid {color}'
    estados_str  = ' · '.join(estados[:6]) + ('…' if len(estados) > 6 else '')

    callout_el = []
    if callout:
        ctitle, cbody = callout
        callout_el = [
            html.Div([
                html.Span(ctitle, style={
                    'display': 'block', 'fontSize': '10px', 'fontWeight': '700',
                    'color': color, 'marginBottom': '6px',
                    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                }),
                html.P(cbody, style={
                    'fontSize': '11px', 'color': '#b8b8cc', 'lineHeight': '1.6', 'margin': '0',
                }),
            ], style={
                'marginTop': '12px',
                'borderTop': f'1px solid {color}44',
                'background': f'{color}0a',
                'borderRadius': '6px', 'padding': '10px 12px',
            }),
        ]

    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(code, style={
                    'fontWeight': '800', 'fontSize': '18px', 'color': color,
                    'marginRight': '10px', 'fontFamily': 'monospace',
                }),
                html.Span(name, style={
                    'fontWeight': '600', 'fontSize': '12px', 'color': color,
                    'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                }),
                html.Span(f'n={n}', style={
                    'marginLeft': 'auto', 'fontSize': '10px', 'color': '#5c5c74',
                }),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

            html.P(desc, style={
                'fontSize': '11.5px', 'color': '#c8c8d8', 'lineHeight': '1.55',
                'marginBottom': '10px',
            }),

            html.Div([
                html.Small('Estados: ', style={'color': '#5c5c74', 'fontSize': '9px',
                                               'textTransform': 'uppercase', 'letterSpacing': '0.07em'}),
                html.Small(estados_str, style={'color': color, 'fontSize': '9.5px'}),
            ]),

            *callout_el,
        ], style={'padding': '16px'}),
    ], style={'border': border_style, 'borderRadius': '8px',
              'background': '#16161f', 'height': '100%'}),
    md=6)


layout = html.Div([
    sidebar('/slide_11'),

    html.Div([

        # ── Page header ───────────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Infraestructura Digital × Bienestar · Perfiles de Inversión', className='page-title'),
            html.P(
                'El IDDE predice salarios (r²=0.54), confianza social (r=0.78) y densidad económica — '
                '32 estados · 134 variables · K-Means k=4 revela 4 perfiles con necesidades y retornos distintos',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('Fraudes r=+0.63', className='badge-green me-2',
                          title='Mayor correlación positiva entre IDDE y tipo de delito'),
                html.Span('Conf. social r=+0.78', className='badge-cyan me-2',
                          title='Variable de seguridad con mayor asociación con infraestructura digital'),
                html.Span('Panel r≈0', className='badge-gray me-2',
                          title='Sin causalidad a corto plazo entre digitalización y crimen (2022-2025)'),
                html.Span('4 Clusters', className='badge-gold',
                          title='K-Means k=4 — 4 perfiles diferenciados de estados'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='s11-init', interval=400, max_intervals=1),
        dcc.Store(id='s11-loaded', data=0),

        # ── Scrollable body ───────────────────────────────────────────
        html.Div([

            html.P(
                '32 estados · 134 variables · corte transversal 2025. '
                'Se cruzan ~28 variables de infraestructura digital del IDDE '
                '(conectividad, velocidad, economía digital, capital humano, pilares) '
                'con tasas de crimen por tipo de delito, percepción de seguridad, '
                'confianza institucional y social (ENVIPE) y salarios (ENOE).',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_insight_card(
                    _INSIGHTS[0]['icon'], _INSIGHTS[0]['color'],
                    _INSIGHTS[0]['title'], _INSIGHTS[0]['desc'], 'animate-in-delay-1'), md=4),
                dbc.Col(_insight_card(
                    _INSIGHTS[1]['icon'], _INSIGHTS[1]['color'],
                    _INSIGHTS[1]['title'], _INSIGHTS[1]['desc'], 'animate-in-delay-2'), md=4),
                dbc.Col(_insight_card(
                    _INSIGHTS[2]['icon'], _INSIGHTS[2]['color'],
                    _INSIGHTS[2]['title'], _INSIGHTS[2]['desc'], 'animate-in-delay-3'), md=4),
            ], className='g-3 mb-3'),

            # ── Crime type correlations ───────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('¿Qué delitos se asocian con mayor digitalización?',
                        className='section-block-title'),
                html.P(
                    'Correlación de Pearson entre el IDDE 2025 y las tasas de cada tipo de delito '
                    '(delitos por 100,000 habitantes). Verde = correlación positiva (más digital, más reportes). '
                    'Rojo = correlación negativa. El fraude lidera con r=+0.63 — la digitalización '
                    'financiera expone más vectores de fraude y mejora los sistemas de denuncia.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-crime-corrs',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '320px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in card-expandable'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # ── Grouped heatmap ───────────────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Matriz de correlación agrupada — Infra digital × Seguridad',
                        className='section-block-title'),
                html.P(
                    'Cada celda: correlación de Pearson entre una variable de infraestructura (filas) '
                    'y una de seguridad (columnas). Filas y columnas ordenadas por grupo — '
                    'las líneas blancas separan bloques temáticos. '
                    'Verde = positiva · Rojo = negativa · Brillo = intensidad. '
                    'El bloque más brillante: Conectividad → Confianza social (r hasta 0.78). '
                    'El más rojo: Economía digital → Confianza institucional (r hasta −0.50).',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-heatmap',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '620px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean animate-in card-expandable'),
                    md=12,
                ),
            ], className='g-3 mb-2'),

            # Heatmap key findings
            dbc.Card([
                dbc.CardBody([
                    html.P('5 patrones que destacan en el mapa de calor', style={
                        'fontWeight': '700', 'fontSize': '11px', 'color': '#4fc3f7',
                        'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                        'marginBottom': '10px',
                    }),
                    html.Ul([
                        html.Li([
                            html.Strong('Conectividad → Confianza social (r = 0.6–0.78): '),
                            'La relación más fuerte del análisis. Fibra óptica y cobertura BB '
                            'se asocian con mayor confianza entre amigos, familia y vecinos. '
                            'La conectividad parece fortalecer el tejido social.',
                        ], style={'marginBottom': '7px'}),
                        html.Li([
                            html.Strong('IDDE → crimen reportado (r = 0.5–0.6): artefacto, no causalidad. '),
                            'Los estados más digitalizados no tienen más crimen — '
                            'tienen mejores sistemas de denuncia. El panel 2022–2025 lo confirma (r ≈ 0).',
                        ], style={'marginBottom': '7px'}),
                        html.Li([
                            html.Strong('IDDE vs Homicidios: r ≈ 0. '),
                            'La violencia letal no tiene ninguna relación con la infraestructura digital. '
                            'Depende del crimen organizado y la capacidad institucional, no del WiFi.',
                        ], style={'marginBottom': '7px'}),
                        html.Li([
                            html.Strong('Digitalización financiera → menor confianza institucional: '),
                            'Penetración de tarjeta de débito correlaciona negativamente con '
                            'confianza en jueces (−0.40) y Ministerio Público (−0.50). '
                            'Más acceso digital = más exposición a las fallas del Estado.',
                        ], style={'marginBottom': '7px'}),
                        html.Li([
                            html.Strong('Velocidad móvil → salarios (r = 0.54): '),
                            'La calidad de la conexión —no solo la cobertura— predice productividad económica. '
                            'R² de velocidad vs salarios: 0.29; R² de cobertura: apenas 0.003.',
                        ]),
                    ], style={
                        'fontSize': '11.5px', 'color': '#b8c8d8', 'lineHeight': '1.65',
                        'paddingLeft': '18px', 'margin': '0',
                    }),
                ], style={'padding': '16px 20px'}),
            ], className='card-clean mb-3',
               style={'borderLeft': '3px solid #4fc3f744'}),

            # ── IDDE scatter por grupo (merged from slide_6) ───────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('IDDE vs crimen — por grupo de digitalización',
                        className='section-block-title'),
                html.P(
                    'Cada punto es un estado, coloreado por su grupo IDDE (Básico → Líder). '
                    'Selecciona el año y la categoría de crimen en el eje Y para explorar distintas relaciones.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            html.Div([
                html.Span('Año', className='filter-label'),
                dcc.Dropdown(
                    id='s11-dd-anio',
                    options=[{'label': str(a), 'value': a} for a in _IDDE_ANIOS],
                    value=2024, clearable=False,
                    className='dropdown-hw', style={'width': '120px'},
                ),
                html.Span('Crimen (eje Y)', className='filter-label'),
                dcc.Dropdown(
                    id='s11-dd-tasa',
                    options=[{'label': l, 'value': v} for v, l in _IDDE_TASAS],
                    value='tasa_Sociedad', clearable=False,
                    className='dropdown-hw', style={'width': '200px'},
                ),
            ], className='filter-bar mb-3'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-scatter-idde',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '380px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in card-expandable'),
                    md=12,
                ),
            ], className='g-3 mb-3'),
            # ── 6 scatter plots ───────────────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('3 relaciones clave — zoom en los vínculos más reveladores',
                        className='section-block-title'),
                html.P(
                    'Cada panel muestra una relación bivariada con su coeficiente r. '
                    'Línea punteada = regresión lineal. El panel completo de cambios 2022→2025 '
                    'se presenta en la sección de análisis de panel más abajo.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-6scatters',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '460px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean animate-in card-expandable'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # ── Clustering ────────────────────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('K-Means k=4 — cuatro perfiles de estados',
                        className='section-block-title'),
                html.P(
                    'K-Means con k=4 agrupa los 32 estados usando IDDE, crimen total, homicidios, '
                    'percepción de seguridad, confianza familiar y confianza policial. '
                    'Cada cluster tiene una narrativa estratégica propia.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        html.P('Dispersión: IDDE vs crimen coloreado por cluster',
                               className='chart-label'),
                        html.P('Cada punto es un estado. El color indica el cluster asignado.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-cluster-scatter',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '420px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in card-expandable'),
                    md=7,
                ),
                dbc.Col(
                    dbc.Card([
                        html.P('Distribución por cluster — IDDE, crimen y percepción',
                               className='chart-label'),
                        html.P('Cada caja resume la distribución dentro del cluster. Puntos = estados individuales.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s11-cluster-profiles',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '420px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean animate-in card-expandable'),
                    md=5,
                ),
            ], className='g-3 mb-3'),

            # Cluster cards
            html.Div(id='s11-cluster-cards', className='mb-4'),

            # Limitations box
            dbc.Card([
                dbc.CardBody([
                    html.P('Limitaciones del análisis', style={
                        'fontWeight': '700', 'fontSize': '11px', 'color': '#c9922a',
                        'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                        'marginBottom': '8px',
                    }),
                    html.P(
                        'n=32 estados — poder estadístico bajo para modelos complejos. '
                        'El crimen registrado tiene sesgo de subregistro heterogéneo por estado (más digital = más denuncia). '
                        'Datos de panel solo 4 años: efectos de largo plazo no son capturables. '
                        'Correlación transversal refleja co-desarrollo histórico, no causalidad contemporánea. '
                        'ENVIPE 2023 puede no reflejar cambios post-2024.',
                        style={'fontSize': '11px', 'color': '#888', 'margin': '0', 'lineHeight': '1.6'},
                    ),
                ], style={'padding': '14px 18px'}),
            ], className='card-clean mb-4',
               style={'borderLeft': '3px solid #c9922a44'}),

        ], className='main-scroll'),

    ], className='section-profundo',
       style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


# ── Callbacks ─────────────────────────────────────────────────────────────────

def _safe(fn):
    try:
        return fn()
    except Exception:
        traceback.print_exc()
        return go.Figure()


def _build_cluster_cards():
    try:
        d         = get_data_11()
        label_map = d['label_map']
        stats     = d['cluster_stats']

        cards = []
        for c_id, (code, name, color, desc) in label_map.items():
            s      = stats.get(c_id, {})
            estados = s.get('estados', [])
            n       = s.get('n', 0)
            is_c1   = (code == 'C1')
            cards.append(_cluster_card(code, name, color, desc, estados, n, is_c1))

        # Re-order so C1 appears second (after C0)
        order = {'C0': 0, 'C1': 1, 'C2': 2, 'C3': 3}
        cards.sort(key=lambda col: order.get(
            col.children.children[0].children[0].children[0].children, 99)
            if hasattr(col, 'children') else 99
        )
        return dbc.Row(cards, className='g-3')
    except Exception:
        traceback.print_exc()
        return html.Div()


def _build_cluster_cards_safe():
    try:
        d         = get_data_11()
        label_map = d['label_map']
        stats     = d['cluster_stats']

        order = {'C0': 0, 'C1': 1, 'C2': 2, 'C3': 3}
        items = sorted(label_map.items(),
                       key=lambda x: order.get(x[1][0], 99))

        cards = []
        for c_id, (code, name, color, desc) in items:
            s       = stats.get(int(c_id), {})
            estados = s.get('estados', [])
            n       = s.get('n', 0)
            callout = _CLUSTER_CALLOUTS.get(code)
            cards.append(_cluster_card(code, name, color, desc, estados, n, callout))

        return dbc.Row(cards, className='g-3')
    except Exception:
        traceback.print_exc()
        return html.Div()


@dash.callback(
    Output('s11-crime-corrs',    'figure'),
    Output('s11-heatmap',        'figure'),
    Output('s11-6scatters',      'figure'),
    Output('s11-cluster-scatter','figure'),
    Output('s11-cluster-profiles','figure'),
    Output('s11-cluster-cards',  'children'),
    Output('s11-loaded',         'data'),
    Input('s11-init', 'n_intervals'),
)
def load_all(_):
    return (
        _safe(fig_crime_type_corrs),
        _safe(fig_corr_heatmap),
        _safe(fig_6_scatters),
        _safe(fig_clustering_scatter),
        _safe(fig_cluster_profiles),
        _build_cluster_cards_safe(),
        1,
    )


@dash.callback(
    Output('s11-scatter-idde', 'figure'),
    Input('s11-dd-anio',       'value'),
    Input('s11-dd-tasa',       'value'),
)
def update_idde_scatter(anio, tasa):
    return fig_scatter_idde(anio or 2024, tasa or 'tasa_Sociedad')
