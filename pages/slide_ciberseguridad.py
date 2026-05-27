import traceback
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from pages.components import sidebar
from pages.get_figures.get_figures_ciberseguridad import get_cyber_kpis

dash.register_page(__name__, path='/slide_ciberseguridad')

_CFG = {'displayModeBar': False, 'responsive': True}
C_CYAN = '#00b4cc'

kpis = get_cyber_kpis()


def _chart_card(title, graph_id, desc=None, height='400px'):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(
        dcc.Loading(dcc.Graph(id=graph_id, config=_CFG, style={'height': height})),
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
    sidebar('/slide_ciberseguridad'),

    html.Div([

        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Ciberseguridad · La Brecha que Crece con la Digitalización',
                    className='page-title'),
            html.P(
                'El fraude es el delito más correlacionado con infraestructura digital (r=+0.63) — '
                f'no porque la tecnología cause fraude, sino porque más transacciones digitales '
                f'exponen más vectores. {kpis["n_critical"]} estados tienen alta exposición financiera '
                'y baja capacidad de ciberseguridad: la brecha más urgente del país.',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('Fraude r = +0.63 con IDDE', className='badge-red me-2'),
                html.Span(f'{kpis["n_critical"]} estados en brecha crítica', className='badge-gold me-2'),
                html.Span(f'Mayor brecha: {kpis["top_state"]}', className='badge-cyan'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='sciber-init', interval=400, max_intervals=1),

        html.Div([

            html.P(
                'Análisis de 32 estados: índice de exposición financiera digital '
                '(adopción de banca electrónica + tarjeta de débito) cruzado con '
                'capacidad de ciberseguridad (subpilar IDDE + acciones empresariales + '
                'policía cibernética). Los estados en el cuadrante crítico tienen alta '
                'actividad digital pero baja defensa — el perfil de mayor riesgo.',
                className='page-context',
            ),

            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Fraude: el delito más correlacionado con IDDE',
                    'De 8 tipos de delito, el fraude es el que más claramente escala con '
                    'la infraestructura digital (r=+0.63). '
                    'Más banca electrónica → más transacciones digitales → más vectores expuestos.',
                    'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-gold',
                    f'{kpis["n_critical"]} estados con brecha crítica',
                    'Alta exposición financiera digital y baja capacidad de ciberseguridad. '
                    'Estos estados están acelerando su adopción digital sin construir '
                    'la defensa necesaria. El riesgo crece cada trimestre.',
                    'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-cyan', 'Oportunidad: ciberseguridad como servicio',
                    'La brecha no es un problema de conectividad — es un problema de seguridad '
                    'sobre conectividad existente. Esto crea demanda directa de soluciones '
                    'de ciberseguridad, sistemas antifraude y monitoreo digital.',
                    'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⚡', 'card-success', 'Homicidio y secuestro son inmunes al IDDE',
                    'De los 8 delitos analizados, solo 2 no correlacionan con la digitalización: '
                    'homicidio (r=+0.009) y secuestro (r=−0.07). La violencia letal sigue '
                    'las reglas del crimen organizado, no del WiFi.',
                    'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Main charts
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('¿Dónde están los estados más vulnerables?',
                        className='section-block-title'),
                html.P(
                    'Izquierda: cada punto es un estado. Los que están en el cuadrante inferior-derecho '
                    '(alta exposición, baja capacidad) son los de mayor prioridad. '
                    'El color refleja la tasa de fraude: rojo = más fraude. '
                    'Derecha: ranking de brecha de ciberseguridad por estado.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Exposición digital vs Capacidad de ciberseguridad',
                        'sciber-quadrant',
                        desc='Cuadrante inferior-derecho = Brecha Crítica: alta adopción digital, baja protección.',
                        height='420px',
                    ),
                    md=7,
                ),
                dbc.Col(
                    _chart_card(
                        'Ranking de brecha de ciberseguridad',
                        'sciber-gap-bars',
                        desc='Rojo = más expuesto que protegido. Azul = bien protegido. Ordenado de menor a mayor riesgo.',
                        height='420px',
                    ),
                    md=5,
                ),
            ], className='g-3 mb-3'),

            # Insight callout
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span('◈ ', style={'color': '#cf0a2c', 'fontWeight': '700',
                                               'fontSize': '16px'}),
                        html.Span('La narrativa completa', style={
                            'fontWeight': '700', 'fontSize': '12px', 'color': '#e8e8f0',
                            'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                        }),
                    ], style={'marginBottom': '10px'}),
                    html.P(
                        'Los estados que invierten en conectividad digital están haciendo '
                        'exactamente lo correcto — pero están dejando incompleto el trabajo. '
                        'Más banda ancha + más banca digital + más comercio electrónico '
                        '= más superficie de ataque sin defensas adecuadas. '
                        'La solución no es frenar la digitalización: es construir '
                        'la capa de ciberseguridad que la hace sostenible.',
                        style={'fontSize': '12px', 'color': '#c8c8d8', 'lineHeight': '1.7',
                               'margin': '0'},
                    ),
                ], style={'padding': '18px 22px'}),
            ], className='card-clean mb-4',
               style={'borderLeft': '3px solid rgba(207, 10, 44, 0.30)'}),

            # ── NEW: Crime type heterogeneity ──────────────────────────
            html.Div([
                html.Div(className='section-accent-gold'),
                html.H3('Heterogeneidad: No Todos los Delitos Responden Igual al IDDE',
                        className='section-block-title'),
                html.P(
                    'Análisis de 8 tipos de delito vs IDDE 2025 (32 estados). '
                    'La mayoría correlaciona positivamente — en gran parte porque los estados '
                    'más digitalizados tienen mejor registro de denuncias (menor cifra negra). '
                    'La excepción son homicidio y secuestro: r≈0, no significativos — '
                    'la violencia letal es independiente del nivel de digitalización.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Correlación IDDE × tipo de crimen (r de Pearson, 32 estados)',
                        'sciber-crime-types',
                        desc='Verde = correlación negativa (crimen baja con IDDE). Rojo = positiva. ● = p<0.05. La mayoría sube por mejor registro; solo homicidio y secuestro son estadísticamente planos.',
                        height='340px',
                    ),
                    md=12,
                ),
            ], className='g-3 mb-4'),

        ], className='main-scroll'),

    ], className='main-content'),
], className='page-root')


@dash.callback(
    dash.Output('sciber-quadrant',    'figure'),
    dash.Output('sciber-gap-bars',    'figure'),
    dash.Output('sciber-crime-types', 'figure'),
    dash.Input('sciber-init', 'n_intervals'),
)
def load_charts(_):
    from pages.get_figures.get_figures_ciberseguridad import (
        fig_fraud_quadrant, fig_cyber_gap_bars,
    )
    from pages.get_figures.get_figures_nuevos_evidencia import (
        fig_crime_type_heterogeneity,
    )

    def _safe(fn):
        try:
            return fn()
        except Exception:
            traceback.print_exc()
            return go.Figure()

    return (
        _safe(fig_fraud_quadrant),
        _safe(fig_cyber_gap_bars),
        _safe(fig_crime_type_heterogeneity),
    )
