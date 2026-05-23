import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.get_figures.get_figures_3 import fig_donut_bienes, fig_treemap_subtipos, fig_tendencia_bienes
from pages.get_data.get_data_3 import get_entidades, get_anios
from pages.components import sidebar

dash.register_page(__name__, path='/slide_3')

entidades = get_entidades()
anios     = get_anios()

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
    sidebar('/slide_3'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Clasificación por Bien Jurídico Afectado', className='page-title'),
            html.P(
                'El crimen según lo que protege la ley — composición y evolución de '
                '7 categorías jurídicas: Patrimonio, Vida, Sociedad, Libertad, Familia, Sexual y Estado',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('7 categorías legales', className='badge-gray me-2'),
                html.Span('50+ subtipos de delito', className='badge-cyan'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'El Código Penal clasifica los delitos según qué bien jurídico protegen: '
                'Patrimonio (robo, fraude, extorsión), Vida (homicidio, lesiones), Sociedad '
                '(narcomenudeo, trata), entre otros. Entender esta composición revela las '
                'prioridades del crimen en cada estado y cómo han evolucionado a lo largo del tiempo. '
                'El treemap muestra los subtipos específicos dentro de cada categoría.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Patrimonio domina',
                    'Los delitos patrimoniales (robo, fraude, extorsión) representan '
                    'consistentemente más del 50 % del total de la incidencia nacional.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-gold', 'Sociedad en alza',
                    'El crimen de tipo Sociedad (narcomenudeo, trata) aumenta como porcentaje '
                    'del total — reflejo del avance del crimen organizado a nivel local.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Vida: menos volumen, alto impacto',
                    'Homicidio y lesiones representan menos del 10 % del total, '
                    'pero tienen el mayor impacto en percepción de inseguridad ciudadana.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Composición estable',
                    'La distribución porcentual entre categorías varía menos del 5 % '
                    'año a año — el patrón estructural del crimen es relativamente estable.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Estado', className='filter-label'),
                dcc.Dropdown(
                    id='s3-dd-estado',
                    options=[{'label': e, 'value': e} for e in entidades],
                    value='Nacional', clearable=False,
                    className='dropdown-hw', style={'width': '200px'},
                ),
                html.Span('Período', className='filter-label'),
                dcc.Dropdown(
                    id='s3-dd-inicio',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[0], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
                html.Span('—', style={'color': 'var(--text-muted)'}),
                dcc.Dropdown(
                    id='s3-dd-fin',
                    options=[{'label': str(a), 'value': a} for a in anios],
                    value=anios[-1], clearable=False,
                    className='dropdown-hw', style={'width': '110px'},
                ),
            ], className='filter-bar'),

            # Donut + Treemap
            dbc.Row([
                dbc.Col(
                    _card('Proporción por categoría jurídica',
                          dcc.Graph(id='s3-graph-donut', figure=fig_donut_bienes(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Patrimonio = bienes materiales (robo, fraude). Vida = integridad física (homicidio, lesiones). Sociedad = orden público (narcomenudeo).'),
                    md=5,
                ),
                dbc.Col(
                    _card('Subtipos de delito por categoría',
                          dcc.Graph(id='s3-graph-treemap', figure=fig_treemap_subtipos(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Bloques más grandes = delitos más frecuentes. Haz clic en una categoría (ej. Patrimonio) para ver sus subtipos específicos (robo a casa, robo de vehículo, etc.).'),
                    md=7,
                ),
            ], className='g-3 mb-3'),

            # Tendencia bienes
            dbc.Row([
                dbc.Col(
                    _card('Composición del crimen a lo largo del tiempo',
                          dcc.Graph(id='s3-graph-tendencia', figure=fig_tendencia_bienes(),
                                    config=_CFG, style={'height': '300px'}),
                          desc='Área apilada: el total de todas las franjas es el crimen nacional. El grosor de cada franja muestra cuánto aporta esa categoría por año.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-exploratorio', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s3-graph-donut',     'figure'),
    Output('s3-graph-treemap',   'figure'),
    Output('s3-graph-tendencia', 'figure'),
    Input('s3-dd-estado', 'value'),
    Input('s3-dd-inicio', 'value'),
    Input('s3-dd-fin',    'value'),
)
def actualizar(estado, inicio, fin):
    return (
        fig_donut_bienes(estado, inicio, fin),
        fig_treemap_subtipos(estado, inicio, fin),
        fig_tendencia_bienes(estado),
    )
