import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_7 import (
    fig_percepcion_inseguridad, fig_confianza_institucional, fig_gastos_por_estrato,
)
from pages.get_data.get_data_7 import get_kpis

dash.register_page(__name__, path='/slide_7')

kpis = get_kpis()

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
    sidebar('/slide_7'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Percepción de Seguridad · ENVIPE', className='page-title'),
            html.P(
                'La percepción de inseguridad no siempre coincide con la incidencia real — '
                'ENVIPE: inseguridad percibida por estado, confianza en instituciones y gasto en protección',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'{kpis["pct_inseguro_nac"]:.1f}% se sienten inseguros',
                          className='badge-red me-2'),
                html.Span(f'Más inseguro: {kpis["estado_mas_inseguro"][:14]}',
                          className='badge-gold me-2'),
                html.Span(f'Mayor confianza: {kpis["institucion_mas_confianza"]}',
                          className='badge-cyan'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'La Encuesta Nacional de Victimización y Percepción sobre Seguridad Pública '
                '(ENVIPE) mide percepción de inseguridad — que no siempre coincide con la '
                'incidencia real registrada. Sentirse inseguro tiene costos económicos concretos: '
                'los hogares invierten en rejas, alarmas y guardias privados. Esta sección '
                'compara la percepción por estado, la confianza en instituciones, y el gasto en '
                'protección según el nivel socioeconómico del hogar.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', f'{kpis["pct_inseguro_nac"]:.1f}% — 7 de cada 10',
                    f'Más de 7 de cada 10 mexicanos se siente inseguro. '
                    f'{kpis["estado_mas_inseguro"]} encabeza la lista de mayor percepción '
                    f'de inseguridad a nivel estatal.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-gold', 'Ejército lidera confianza',
                    f'El {kpis["institucion_mas_confianza"]} es la institución con mayor '
                    f'confianza positiva según ENVIPE. La Policía Municipal ocupa los últimos lugares.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Brecha por estrato',
                    'Los estratos socioeconómicos más bajos destinan un mayor porcentaje '
                    'de su ingreso a gastos de protección ante el crimen — carga regresiva.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Percepción ≠ Incidencia',
                    'Algunos estados con alta percepción de inseguridad no figuran en el '
                    'top de incidencia real — la percepción tiene dinámicas propias.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Percepción por estado (full width)
            dbc.Row([
                dbc.Col(
                    _card('Percepción de inseguridad por estado (%)',
                          dcc.Graph(figure=fig_percepcion_inseguridad(),
                                    config=_CFG, style={'height': '380px'}),
                          desc='% de la población que se siente insegura según ENVIPE (INEGI). Puede diferir de la incidencia real — la percepción tiene dinámicas propias.'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Confianza + Gastos
            dbc.Row([
                dbc.Col(
                    _card('Confianza en instituciones (% positiva)',
                          dcc.Graph(figure=fig_confianza_institucional(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='% con evaluación positiva por institución (ENVIPE). La Policía Municipal recibe sistemáticamente las evaluaciones más bajas del país.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Gastos en protección vs crimen por estrato socioeconómico',
                          dcc.Graph(figure=fig_gastos_por_estrato(),
                                    config=_CFG, style={'height': '320px'}),
                          desc='Gasto promedio en rejas, alarmas y vigilancia privada por decil de ingreso. Los estratos más bajos gastan mayor % de su ingreso en protección.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

        ], className='main-scroll'),

    ], className='section-profundo', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})
