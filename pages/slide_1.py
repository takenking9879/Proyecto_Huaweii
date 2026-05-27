import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.get_figures.get_figures_1 import fig_tendencia, fig_estacionalidad, fig_top_estados_lineas
from pages.get_figures.get_figures_4 import fig_heatmap
from pages.get_data.get_data_1 import get_entidades, get_anios, get_kpis
from pages.components import sidebar

dash.register_page(__name__, path='/slide_1')

entidades = get_entidades()
anios     = get_anios()
kpis_ini  = get_kpis()

_CFG = {'displayModeBar': False, 'responsive': True}


def _card(title, body, desc=None):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(body, style={'padding': '6px 8px 10px'}))
    return dbc.Card(children, className='card-clean card-pop animate-in h-100 card-expandable')


def _ins(icon, color, title, desc, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Span(icon, className='insight-icon'),
            html.P(title, className='insight-title'),
            html.P(desc, className='insight-desc'),
        ], style={'padding': '16px 18px'}),
    ], className=f'animate-in h-100 {color} {delay}'.strip())


layout = html.Div([
    sidebar('/slide_1'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Tendencias de Incidencia · Diagnóstico Base', className='page-title'),
            html.P(
                '10 años de datos oficiales SESNSP — tendencia anual, estacionalidad mensual '
                'y comparativo entre estados. Diagnóstico base para identificar rezagos y oportunidades · 2015–2024',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'{kpis_ini["total"]:,.0f} delitos registrados', className='badge-cyan me-2'),
                html.Span(f'Pico: {kpis_ini["anio_pico"]}', className='badge-red me-2'),
                html.Span(f'Último año: {kpis_ini["variacion"]:+.1f}%',
                          className='badge-red' if kpis_ini['variacion'] > 0 else 'badge-green'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'Este análisis usa datos oficiales del SESNSP (2015–2024) para mostrar cómo ha '
                'evolucionado la incidencia delictiva en México. La gráfica de tendencia revela '
                'el comportamiento anual, el patrón mensual detecta estacionalidad, y el '
                'comparativo de estados identifica dónde se concentra el crimen. '
                'Usa los filtros para explorar un estado o período específico.',
                className='page-context',
            ),

            # Insight cards — primary insight first, then supporting
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Patrimonio lidera la incidencia nacional',
                    'Los delitos contra el patrimonio (robo, fraude) representan más del 50 % '
                    'del total de la incidencia delictiva nacional — y el fraude es el subtipo '
                    'que más crece con la digitalización.', 'animate-in-delay-1'), md=4),
                dbc.Col(_ins('◎', 'card-gold', 'Pico histórico 2018',
                    f'La incidencia alcanzó su máximo en {kpis_ini["anio_pico"]} con '
                    f'{kpis_ini["total"]:,.0f} delitos; desde entonces la tendencia es mixta.', 'animate-in-delay-2'), md=4),
                dbc.Col(_ins('⬡', 'card-cyan', 'Estacionalidad y geografía',
                    'Julio y agosto concentran la mayor incidencia. Cinco estados acumulan '
                    'más del 40 % de todos los delitos — la criminalidad tiene ritmo y lugar.',
                    'animate-in-delay-3'), md=4),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Filtros', className='filter-label'),
                dcc.Dropdown(
                    id='s1-dd-estado',
                    options=[{'label': e, 'value': e} for e in entidades],
                    value='Nacional', clearable=False,
                    className='dropdown-hw', style={'width': '200px'},
                ),
                html.Span('Período', className='filter-label'),
                dcc.Dropdown(
                    id='s1-dd-inicio',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[0], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
                html.Span('—', style={'color': 'var(--text-muted)'}),
                dcc.Dropdown(
                    id='s1-dd-fin',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[-1], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
            ], className='filter-bar'),

            # Tendencia
            dbc.Row([
                dbc.Col(
                    _card('Evolución anual de la incidencia delictiva',
                          dcc.Graph(id='s1-graph-tendencia', figure=fig_tendencia(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Total de delitos por año en la selección. Un pico indica el año con mayor criminalidad del período; la sombra roja muestra el área acumulada.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Estacionalidad + Top estados
            dbc.Row([
                dbc.Col(
                    _card('Estacionalidad mensual promedio',
                          dcc.Graph(id='s1-graph-estacionalidad', figure=fig_estacionalidad(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Promedio de delitos por mes sumando todos los años del filtro. El mes con barra más alta es el pico estacional histórico.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Top 5 estados — comparativo histórico',
                          dcc.Graph(id='s1-graph-top-estados', figure=fig_top_estados_lineas(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Tasa de delitos por 100,000 hab. — permite comparar estados de distinto tamaño. Las líneas muestran si cada estado sube o baja con el tiempo.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

            # Heatmap mes × año
            dbc.Row([
                dbc.Col(
                    _card('Intensidad del crimen: mes × año',
                          dcc.Graph(id='s1-graph-heatmap', figure=fig_heatmap(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Más rojo = más delitos. Lee por filas (mismo mes en distintos años) para ver si el patrón estacional se mantiene, o por columnas para ver tendencia anual.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-exploratorio', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s1-graph-tendencia',      'figure'),
    Output('s1-graph-estacionalidad', 'figure'),
    Output('s1-graph-heatmap',        'figure'),
    Input('s1-dd-estado', 'value'),
    Input('s1-dd-inicio', 'value'),
    Input('s1-dd-fin',    'value'),
)
def actualizar(estado, inicio, fin):
    return fig_tendencia(estado, inicio, fin), fig_estacionalidad(estado, inicio, fin), fig_heatmap(estado)
