import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_6 import fig_scatter_idde, fig_pilares_por_grupo, fig_crimen_por_grupo
from pages.get_data.get_data_6 import get_kpis

dash.register_page(__name__, path='/slide_6')

kpis_ini = get_kpis(2022)

_ANIOS = [2022, 2023, 2024]
_TASAS = [
    ('tasa_Sociedad',   'Tasa Sociedad'),
    ('tasa_Patrimonio', 'Tasa Patrimonio'),
    ('tasa_Vida',       'Tasa Vida'),
    ('tasa_Familia',    'Tasa Familia'),
    ('tasa_x100k',      'Tasa Total'),
]

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
    sidebar('/slide_6'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Crimen y Desarrollo Digital (IDDE)', className='page-title'),
            html.P(
                '¿Los estados más digitalizados tienen menos crimen? — Correlación IDDE '
                'vs tasas de delito · pilares por grupo de digitalización · 2022–2024',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'Corr. IDDE–Sociedad: {kpis_ini["correlacion"]}', className='badge-cyan me-2'),
                html.Span(f'Mejor IDDE 2022: {kpis_ini["mejor_estado"][:16]}', className='badge-gold me-2'),
                html.Span(f'{kpis_ini["n_lideres"]} estados líderes', className='badge-green'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'El IDDE (Índice de Desarrollo Digital Estatal) clasifica a los 32 estados en '
                '4 grupos: Básico, Emprendedor, Avanzado y Líder, según su infraestructura '
                'digital, uso de internet, innovación empresarial y habilidades tecnológicas. '
                'Encontramos que los estados más digitalizados registran significativamente '
                'menos crimen societal (narcomenudeo, trata de personas). Cambia el eje Y '
                'del scatter para explorar otras categorías de crimen.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-gold', f'Correlación r = {kpis_ini["correlacion"]}',
                    'Los estados más digitalizados registran menores tasas de crimen societal — '
                    'la digitalización y el crimen de narcomenudeo se mueven en direcciones opuestas.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-danger', 'Brecha de grupos 2–3×',
                    'El grupo "Rezago" tiene 2–3 veces más crimen societal por 100k habitantes '
                    'que el grupo "Líderes". La brecha se mantiene en 2022, 2023 y 2024.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Pilar Innovación: mayor diferencia',
                    'Entre los 4 pilares IDDE, el de Innovación es el que muestra mayor '
                    'separación entre grupos — explica en parte las diferencias en crimen.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', f'{kpis_ini["n_lideres"]} estados líderes',
                    f'{kpis_ini["mejor_estado"]} destaca como el estado con mayor IDDE. '
                    'Estos estados concentran infraestructura digital y menores tasas societales.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Año', className='filter-label'),
                dcc.Dropdown(
                    id='s6-dd-anio',
                    options=[{'label': str(a), 'value': a} for a in _ANIOS],
                    value=2022, clearable=False,
                    className='dropdown-hw', style={'width': '120px'},
                ),
                html.Span('Crimen (eje Y)', className='filter-label'),
                dcc.Dropdown(
                    id='s6-dd-tasa',
                    options=[{'label': l, 'value': v} for v, l in _TASAS],
                    value='tasa_Sociedad', clearable=False,
                    className='dropdown-hw', style={'width': '200px'},
                ),
            ], className='filter-bar'),

            # Scatter
            dbc.Row([
                dbc.Col(
                    _card('IDDE vs tasa de crimen — por grupo de digitalización',
                          dcc.Graph(id='s6-scatter',
                                    figure=fig_scatter_idde(2022, 'tasa_Sociedad'),
                                    config=_CFG, style={'height': '380px'}),
                          desc='Cada punto es un estado, coloreado por su grupo IDDE (Básico → Líder). Cambia el eje Y con el filtro para explorar distintas categorías de crimen.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Pilares + Crimen
            dbc.Row([
                dbc.Col(
                    _card('Pilares IDDE por grupo de digitalización',
                          dcc.Graph(id='s6-pilares', figure=fig_pilares_por_grupo(2022),
                                    config=_CFG, style={'height': '320px'}),
                          desc='4 pilares: Infraestructura, Uso de internet, Innovación empresarial y Habilidades digitales. El pilar más bajo indica el área de mejora de cada grupo.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Tasas de crimen por grupo de digitalización',
                          dcc.Graph(id='s6-crimen', figure=fig_crimen_por_grupo(2022),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Delitos por 100k hab. promedio de cada grupo IDDE. La brecha entre Básico y Líder cuantifica cuánto más crimen tienen los estados menos digitalizados.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-profundo', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s6-scatter', 'figure'),
    Output('s6-pilares', 'figure'),
    Output('s6-crimen',  'figure'),
    Input('s6-dd-anio',  'value'),
    Input('s6-dd-tasa',  'value'),
)
def update(anio, tasa):
    return (
        fig_scatter_idde(anio, tasa),
        fig_pilares_por_grupo(anio),
        fig_crimen_por_grupo(anio),
    )
