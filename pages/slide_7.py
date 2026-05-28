import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_7 import (
    fig_idde_vs_percepcion,
    fig_percepcion_inseguridad,
    fig_infra_vs_trust,
    fig_percepcion_vs_incidencia,
)
from pages.get_data.get_data_7 import get_kpis
from pages.get_data.get_data_1 import get_entidades

dash.register_page(__name__, path='/slide_7')

kpis      = get_kpis()
entidades = get_entidades()

_CFG = {'displayModeBar': False, 'responsive': True}


def _chart_card(title, graph_id, desc=None, height='380px'):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(
        dcc.Graph(id=graph_id, config=_CFG, style={'height': height}),
        style={'padding': '6px 8px 10px'},
    ))
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

        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Percepción e Infraestructura · Brecha de Confianza', className='page-title'),
            html.P(
                'La infraestructura digital explica el 44% de la varianza en percepción de seguridad '
                '(R²=0.445) — los ciudadanos en estados más digitalizados se sienten más seguros, '
                'independientemente de la tasa de crimen real',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'R² = 0.445 IDDE → percepción', className='badge-cyan me-2'),
                html.Span(f'{kpis["pct_inseguro_nac"]:.1f}% se sienten inseguros', className='badge-red me-2'),
                html.Span(f'Confianza social r = +0.78', className='badge-gold'),
            ]),
        ], className='page-header'),

        html.Div([

            html.P(
                'ENVIPE mide percepción de inseguridad y confianza institucional por estado. '
                'Al cruzarlos con el IDDE 2025 emerge una relación robusta: '
                'la infraestructura digital cierra la brecha entre realidad y percepción ciudadana. '
                'Selecciona un estado para ver sus datos específicos.',
                className='page-context',
            ),

            dbc.Row([
                dbc.Col(_ins('◈', 'card-cyan', 'R² = 0.445 — relación más fuerte',
                    'La infraestructura digital explica el 44% de por qué los ciudadanos '
                    'se sienten seguros o inseguros — independientemente del crimen real. '
                    'Es el vínculo más sólido entre inversión y percepción ciudadana.',
                    'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-danger', f'{kpis["pct_inseguro_nac"]:.1f}% — 7 de cada 10',
                    f'Más de 7 de cada 10 mexicanos se siente inseguro. '
                    f'{kpis["estado_mas_inseguro"][:16]} encabeza la percepción de inseguridad. '
                    'La percepción es el problema operativo — la infraestructura es la solución.',
                    'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⌬', 'card-gold', 'El mecanismo: lazos sociales primero',
                    'La infraestructura digital actúa INDIRECTAMENTE: '
                    'fortalece la confianza entre ciudadanos (r=+0.75) y esa confianza '
                    'es lo que genera percepción de seguridad (r=+0.42). '
                    'La vía directa infraestructura→seguridad es estadísticamente débil sin este puente.',
                    'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⬡', 'card-success', 'Percepción ≠ incidencia real',
                    'Algunos estados con alta percepción de inseguridad no encabezan '
                    'la incidencia real. La brecha se cierra con mejor infraestructura '
                    'de comunicación y gobierno digital.',
                    'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # State selector
            html.Div([
                html.Span('Estado', className='filter-label'),
                dcc.Dropdown(
                    id='s7-dd-estado',
                    options=[{'label': 'Nacional', 'value': 'Nacional'}] +
                            [{'label': e, 'value': e} for e in entidades],
                    value='Nacional', clearable=False,
                    className='dropdown-hw', style={'width': '280px'},
                ),
            ], className='filter-bar mb-3'),

            # MAIN: IDDE vs percepcion (full width)
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Infraestructura digital → percepción de seguridad (R² = 0.445)',
                        className='section-block-title'),
                html.P(
                    'Cada punto es un estado. Los estados sobre la línea de tendencia '
                    'obtienen más percepción de seguridad de lo que su IDDE predice (verde). '
                    'Los que están por debajo están sub-rindiendo — su potencial de mejora es mayor (rojo).',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'IDDE 2025 vs % que se siente seguro',
                        's7-graph-percepcion-gap',
                        desc='R²=0.445: la infraestructura digital explica el 44% de la varianza en percepción de seguridad.',
                        height='400px',
                    ),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Second row: perception bar + trust scatter
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Percepción e infraestructura — detalle estatal',
                        className='section-block-title'),
                html.P(
                    'Izquierda: % de ciudadanos que se sienten inseguros por estado. '
                    'Derecha: IDDE vs confianza en amigos (r=+0.78) — '
                    'los estados más digitalizados reportan mayor confianza social.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Percepción de inseguridad por estado (%)',
                        's7-graph-percepcion',
                        desc='% de la población que se siente insegura. Selecciona un estado para destacarlo.',
                        height='600px',
                    ),
                    md=6,
                ),
                dbc.Col(
                    _chart_card(
                        'Infraestructura digital vs confianza social (r = +0.78)',
                        's7-graph-infra-trust',
                        desc='Cada punto = un estado. r=+0.78: la correlación más fuerte del análisis entre IDDE y bienestar social.',
                        height='440px',
                    ),
                    md=6,
                ),
            ], className='g-3 mb-4'),

            # Perception gap chart
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Brecha de percepción — la percepción no siempre refleja el crimen real',
                        className='section-block-title'),
                html.P(
                    'Cada punto es un estado. Eje X = tasa real de crimen. Eje Y = % que se siente inseguro. '
                    'Los estados sobre la línea tienen más percepción de inseguridad de la que predice el crimen real. '
                    'El color indica IDDE: rojo = bajo IDDE (mayor brecha), verde = alto IDDE (percepción más alineada).',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Crimen real vs % que se siente inseguro · 32 estados',
                        's7-graph-percepcion-gap2',
                        desc='Sobre la línea = percepción peor que el crimen real. Bajo la línea = percepción mejor. Color: rojo = bajo IDDE, verde = alto IDDE.',
                        height='400px',
                    ),
                    md=12,
                ),
            ], className='g-3 mb-4'),

        ], className='main-scroll'),

    ], className='section-profundo',
       style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


@callback(
    Output('s7-graph-percepcion-gap', 'figure'),
    Output('s7-graph-percepcion',     'figure'),
    Output('s7-graph-infra-trust',    'figure'),
    Output('s7-graph-percepcion-gap2', 'figure'),
    Input('s7-dd-estado', 'value'),
)
def update_charts(estado):
    highlight = estado if estado and estado != 'Nacional' else None
    return (
        fig_idde_vs_percepcion(highlight),
        fig_percepcion_inseguridad(highlight),
        fig_infra_vs_trust(highlight),
        fig_percepcion_vs_incidencia(highlight),
    )
