import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_5 import fig_scatter_pib, fig_tendencia_dual, fig_ranking_doble
from pages.get_data.get_data_5 import get_anios, get_kpis

dash.register_page(__name__, path='/slide_5')

anios = get_anios()
kpis  = get_kpis()

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
    sidebar('/slide_5'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Crimen y Desarrollo Económico', className='page-title'),
            html.P(
                '¿Más riqueza = menos crimen? La correlación existe pero es débil — '
                'scatter estado × PIB · tendencia nacional dual · ranking comparativo 2022–2024',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'Correlación r = {kpis["correlacion"]}', className='badge-cyan me-2'),
                html.Span(f'Pico crimen: {kpis["anio_pico_crimen"]}', className='badge-red me-2'),
                html.Span(f'PIB promedio 2022: {kpis["avg_pib_2022"]:+.2f}%', className='badge-gold'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'Un supuesto común es que más riqueza = menos crimen. Los datos muestran una '
                'correlación negativa débil: el crecimiento del PIB explica solo una fracción '
                'de la variabilidad en crimen entre estados. Hay outliers importantes como CDMX '
                'y Jalisco que desafían esa narrativa. El scatter muestra cada estado como un '
                'punto — busca los que se alejan de la tendencia general.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-gold', f'Correlación r = {kpis["correlacion"]}',
                    'La correlación entre tasa de crimen y crecimiento del PIB es negativa — '
                    'estados con mayor criminalidad tienden a crecer económicamente menos.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-danger', f'Pico delictivo: {kpis["anio_pico_crimen"]}',
                    f'La incidencia delictiva nacional alcanzó su punto más alto en {kpis["anio_pico_crimen"]}; '
                    'desde entonces la relación con el PIB se volvió más volátil.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'PIB crece pese al crimen',
                    f'El promedio nacional de crecimiento del PIB en 2022 fue {kpis["avg_pib_2022"]:+.2f}%, '
                    'con alta variabilidad regional — los extremos no siguen el patrón general.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Outliers: CDMX y Jalisco',
                    'Algunos estados con alta actividad económica (CDMX, Jalisco) mantienen '
                    'alto crimen, sugiriendo que la riqueza no suprime la delincuencia sola.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Filter bar
            html.Div([
                html.Span('Año del scatter', className='filter-label'),
                dcc.Dropdown(
                    id='s5-dd-anio',
                    options=[{'label': 'Todos', 'value': 'all'}] +
                            [{'label': str(a), 'value': a} for a in anios],
                    value='all', clearable=False,
                    className='dropdown-hw', style={'width': '160px'},
                ),
            ], className='filter-bar'),

            # Scatter
            dbc.Row([
                dbc.Col(
                    _card('Crimen vs crecimiento del PIB por estado',
                          dcc.Graph(id='s5-scatter', figure=fig_scatter_pib(),
                                    config=_CFG, style={'height': '380px'}),
                          desc='Cada punto es un estado. La línea discontinua es la tendencia general — puntos muy alejados de ella son casos atípicos que no siguen el patrón.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Dual + Ranking
            dbc.Row([
                dbc.Col(
                    _card('Evolución nacional — crimen y PIB (doble eje)',
                          dcc.Graph(id='s5-dual', figure=fig_tendencia_dual(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Eje izquierdo = crimen (rojo), eje derecho = PIB (dorado). Si se mueven en sentidos opuestos, la relación inversa se mantiene ese año.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Top 15 estados — crimen vs PIB',
                          dcc.Graph(id='s5-ranking', figure=fig_ranking_doble(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Mismo orden de estados en ambas barras. Busca los que tienen crimen alto pero también crecimiento alto — esos desafían la narrativa "más PIB = menos crimen".'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-profundo', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@dash.callback(
    Output('s5-scatter', 'figure'),
    Input('s5-dd-anio', 'value'),
)
def update_scatter(anio):
    return fig_scatter_pib(None if anio == 'all' else anio)
