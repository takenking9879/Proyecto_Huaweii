import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.get_figures.get_figures_4 import fig_heatmap, fig_victimas_sexo, fig_comparativa
from pages.get_data.get_data_4 import get_entidades, get_anios
from pages.components import sidebar

dash.register_page(__name__, path='/slide_4')

entidades = get_entidades()
anios     = get_anios()

_CFG = {'displayModeBar': False, 'responsive': True}


def _card(title, body, desc=None, extra=''):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(body, style={'padding': '6px 8px 10px'}))
    return dbc.Card(children, className=f'card-clean card-pop animate-in h-100 card-expandable {extra}'.strip())


def _ins(icon, color, title, desc, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Span(icon, className='insight-icon'),
            html.P(title, className='insight-title'),
            html.P(desc, className='insight-desc'),
        ], style={'padding': '16px 18px'}),
    ], className=f'animate-in h-100 {color} {delay}'.strip())


layout = html.Div([
    sidebar('/slide_4'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Análisis Comparativo y Patrones Temporales', className='page-title'),
            html.P(
                '¿Hay meses más peligrosos? ¿El crimen afecta igual a hombres y mujeres? '
                '¿Qué cambió en 2020? — Heatmap mensual, víctimas por sexo y variación entre años',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('Heatmap mensual', className='badge-gray me-2'),
                html.Span('Víctimas por sexo', className='badge-cyan me-2'),
                html.Span('Variación entre años', className='badge-gold'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'Más allá del total anual, ¿hay meses sistemáticamente más peligrosos? '
                '¿Afecta igual el crimen a hombres y mujeres? ¿Qué cambió antes y después de '
                'la pandemia de 2020? El heatmap muestra la intensidad delictiva por mes y año, '
                'el gráfico de víctimas desagrega por sexo, y el comparativo de variación '
                'cuantifica qué categorías crecieron o cayeron entre los dos años seleccionados.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Julio — pico histórico',
                    'El heatmap muestra julio como el mes más violento de forma consistente '
                    'en casi todos los años del período analizado.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-gold', '~65 % víctimas hombres',
                    'La gran mayoría de víctimas formalmente registradas son masculinas; '
                    'los delitos sexuales presentan la proporción más alta de víctimas femeninas.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Patrimonio aumenta',
                    'La variación entre años muestra que los delitos patrimoniales '
                    'son los que más crecen en términos absolutos en el período reciente.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Pandemia: ruptura 2020',
                    '2020 rompe el patrón estacional histórico — diciembre de 2020 '
                    'muestra caídas atípicas en casi todas las categorías delictivas.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Estado', className='filter-label'),
                dcc.Dropdown(
                    id='s4-dd-estado',
                    options=[{'label': e, 'value': e} for e in entidades],
                    value='Nacional', clearable=False,
                    className='dropdown-hw', style={'width': '200px'},
                ),
                html.Span('Comparar', className='filter-label'),
                dcc.Dropdown(
                    id='s4-dd-anio1',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[0], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
                html.Span('vs', style={'color': 'var(--text-muted)'}),
                dcc.Dropdown(
                    id='s4-dd-anio2',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[-1], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
            ], className='filter-bar'),

            # Heatmap + Sexo
            dbc.Row([
                dbc.Col(
                    _card('Intensidad del crimen: mes × año',
                          dcc.Graph(id='s4-graph-heatmap', figure=fig_heatmap(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Más rojo = más delitos. Lee por filas (mismo mes en distintos años) para ver si el patrón estacional se mantiene, o por columnas para ver tendencia anual.'),
                    md=7,
                ),
                dbc.Col(
                    _card('Víctimas registradas por sexo',
                          dcc.Graph(id='s4-graph-sexo', figure=fig_victimas_sexo(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Conteo de víctimas formalmente registradas por sexo (SESNSP). La brecha varía según tipo de delito; los sexuales tienen mayor proporción femenina.'),
                    md=5,
                ),
            ], className='g-3 mb-3'),

            # Variación
            dbc.Row([
                dbc.Col(
                    _card('Variación por categoría jurídica entre años seleccionados',
                          dcc.Graph(id='s4-graph-delta',
                                    figure=fig_comparativa(anios[0], anios[-1]),
                                    config=_CFG, style={'height': '300px'}),
                          desc='Barras a la derecha = delitos que aumentaron; a la izquierda = disminuyeron. El porcentaje indica la magnitud relativa del cambio entre los dos años.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-exploratorio', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s4-graph-heatmap', 'figure'),
    Output('s4-graph-sexo',    'figure'),
    Output('s4-graph-delta',   'figure'),
    Input('s4-dd-estado', 'value'),
    Input('s4-dd-anio1',  'value'),
    Input('s4-dd-anio2',  'value'),
)
def actualizar(estado, anio1, anio2):
    return (
        fig_heatmap(estado),
        fig_victimas_sexo(estado),
        fig_comparativa(anio1, anio2, estado),
    )
