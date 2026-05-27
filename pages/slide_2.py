import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.get_figures.get_figures_2 import fig_ranking_estados, fig_top_municipios
from pages.get_data.get_data_2 import get_anios
from pages.components import sidebar

dash.register_page(__name__, path='/slide_2')

anios = get_anios()

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
    sidebar('/slide_2'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Distribución Geográfica · Brechas de Desarrollo', className='page-title'),
            html.P(
                'Concentración regional del rezago — ranking de 32 estados y municipios: '
                'dónde la inversión en infraestructura digital tiene mayor impacto potencial · 2015–2024',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('32 estados analizados', className='badge-gray me-2'),
                html.Span('2015 – 2024', className='badge-cyan'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'El crimen en México no está distribuido uniformemente entre sus 32 estados ni '
                'sus miles de municipios — hay una concentración marcada en zonas urbanas y '
                'algunos estados del norte. Esta sección muestra dónde se acumula el delito '
                'y cómo cambió esa distribución entre 2015 y 2024. '
                'Cambia el filtro de año para ver el snapshot de un año específico.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Alta concentración',
                    '5 estados concentran cerca del 45 % de todos los delitos registrados; '
                    'la distribución geográfica del crimen es marcadamente desigual.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-gold', 'Municipios urbanos',
                    'Los 15 municipios con mayor incidencia son todos metropolitanos. '
                    'La criminalidad se concentra en zonas de alta densidad poblacional.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Norte vs Sur',
                    'Estados del norte (Baja California, Chihuahua) tienen tasas per cápita '
                    'muy superiores a la media; el sureste reporta las tasas más bajas.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Guanajuato en alza',
                    'Guanajuato muestra el aumento más sostenido desde 2018, '
                    'pasando de posición media a estar entre los 5 estados más afectados.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Año', className='filter-label'),
                dcc.Dropdown(
                    id='s2-dd-anio',
                    options=[{'label': 'Histórico', 'value': 0}] +
                            [{'label': str(a), 'value': a} for a in anios],
                    value=0, clearable=False,
                    className='dropdown-hw', style={'width': '150px'},
                ),
                html.Span('Top municipios', className='filter-label'),
                dcc.Dropdown(
                    id='s2-dd-top-n',
                    options=[{'label': f'Top {n}', 'value': n} for n in [5, 10, 15, 20]],
                    value=15, clearable=False,
                    className='dropdown-hw', style={'width': '120px'},
                ),
            ], className='filter-bar'),

            # Two charts in a row
            dbc.Row([
                dbc.Col(
                    _card('Ranking de 32 estados',
                          dcc.Graph(id='s2-graph-ranking', figure=fig_ranking_estados(),
                                    config=_CFG, style={'height': '420px'}),
                          desc='Ordenados de menor a mayor incidencia. El color más intenso identifica al estado con mayor concentración de delitos en el año seleccionado.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Municipios con mayor incidencia',
                          dcc.Graph(id='s2-graph-municipios', figure=fig_top_municipios(),
                                    config=_CFG, style={'height': '420px'}),
                          desc='Los municipios con más delitos del año seleccionado. La mayoría son zonas metropolitanas — el crimen se concentra en alta densidad urbana.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-exploratorio', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s2-graph-ranking',    'figure'),
    Output('s2-graph-municipios', 'figure'),
    Input('s2-dd-anio',  'value'),
    Input('s2-dd-top-n', 'value'),
)
def actualizar(anio, top_n):
    a = anio if anio else None
    return fig_ranking_estados(a), fig_top_municipios(a, n=top_n or 15)
