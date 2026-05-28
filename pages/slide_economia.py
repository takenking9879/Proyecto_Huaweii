import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_data.get_data_economia import get_economia_r2

_r2 = get_economia_r2()

dash.register_page(__name__, path='/slide_economia')

C_CYAN = '#00b4cc'

_CFG = {'displayModeBar': False, 'responsive': True}


def _chart_card(title, graph_id, desc=None, height='360px'):
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
    sidebar('/slide_economia'),

    html.Div([

        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Economía Digital · El Retorno Medible', className='page-title'),
            html.P(
                f'La adopción de servicios digitales predice salarios con R²={_r2:.3f} — '
                'los estados más digitalizados pagan sueldos un 10% más altos, '
                'y el retorno de la inversión se materializa con un rezago de 2 años',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'R² = {_r2:.3f} banca digital → salarios', className='badge-green me-2'),
                html.Span('+$790/mes inversión sostenida', className='badge-cyan me-2'),
                html.Span('Lag 2 años para ROI máximo', className='badge-gold'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='seco-init', interval=350, max_intervals=1),

        html.Div([

            html.P(
                f'Dos canales económicos medibles: (1) la adopción de banca electrónica y '
                f'pagos digitales predice con R²={_r2:.3f} los salarios promedios estatales — '
                'el canal más fuerte del análisis. (2) La densidad de centros de datos '
                'correlaciona positivamente con salarios medianos. '
                'La inversión en infraestructura digital no paga el mismo año: '
                'el R² máximo se alcanza con un rezago de 2 años.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-success', f'R² = {_r2:.3f} — señal económica más fuerte',
                    f'La proporción de empresas con banca electrónica explica el {_r2*100:.0f}% '
                    'de la varianza en salarios estatales. Es la correlación económica '
                    'más robusta del análisis, superando conectividad y cobertura.',
                    'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-cyan', 'Centros de datos = ancla económica',
                    'Los estados del quintil más alto en densidad de centros de datos '
                    'tienen salarios medios $1,192 más altos que el quintil inferior. '
                    'La infraestructura de datos es infraestructura económica.',
                    'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⌬', 'card-gold', 'El retorno llega 2 años después',
                    'R²=0.247 con IDDE del mismo año, pero R²=0.372 con IDDE de hace '
                    '2 años. La infraestructura digital precede el crecimiento salarial — '
                    'invertir hoy es el ingreso de 2026.',
                    'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⬡', 'card-success', '+$790/mes por consistencia',
                    'Estados con inversión digital sostenida (crecimiento IDDE 3 años '
                    'consecutivos) promedian $790/mes más que estados con inversión '
                    'errática del mismo periodo. Consistencia supera magnitud.',
                    'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Main: wages scatter (full-width)
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('La digitalización financiera predice salarios — 32 estados',
                        className='section-block-title'),
                html.P(
                    'Cada punto es un estado. Eje X = % de empresas que usan banca electrónica. '
                    'Eje Y = salario promedio mensual (ENOE 2025). La línea punteada es la regresión; '
                    'estados por encima del promedio están generando más valor de su digitalización.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Banca electrónica vs salario promedio estatal',
                        'seco-wages-scatter',
                        desc=f'R²={_r2:.3f} — la relación más fuerte entre digitalización y retorno económico en el análisis.',
                        height='380px',
                    ),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Data centers + lag row
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Infraestructura de datos y horizonte de retorno',
                        className='section-block-title'),
                html.P(
                    'Izquierda: los estados con más centros de datos pagan salarios más altos. '
                    'Derecha: el R² del IDDE sobre salarios crece con el tiempo — '
                    'el mayor poder predictivo está en el IDDE de hace 2 años.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Centros de datos → salario mediano por quintil',
                        'seco-dc-wages',
                        desc='Q1 = menor densidad de centros de datos · Q5 = mayor. Patrón de escalera ascendente.',
                        height='320px',
                    ),
                    md=6,
                ),
                dbc.Col(
                    _chart_card(
                        'IDDE vs salarios — poder predictivo por año de rezago',
                        'seco-lag',
                        desc='La inversión en infraestructura digital paga salarios 2 años después, no en el mismo año.',
                        height='320px',
                    ),
                    md=6,
                ),
            ], className='g-3 mb-3'),

            # Sustained investment
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Consistencia de inversión: la diferencia está en $790/mes',
                        className='section-block-title'),
                html.P(
                    'Los estados que aumentaron su IDDE durante 3 años consecutivos '
                    'superan en salarios a los que invirtieron de forma errática — '
                    'incluso con niveles de IDDE similares. La continuidad del compromiso importa.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'Inversión sostenida vs inversión inconsistente',
                        'seco-sustained',
                        desc='Promedios salariales 2025 por tipo de trayectoria de IDDE 2022–2025.',
                        height='280px',
                    ),
                    md=8,
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.P('Conclusión para gobernadores', style={
                                'fontWeight': '700', 'fontSize': '11px', 'color': C_CYAN,
                                'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                                'marginBottom': '12px',
                            }),
                            html.P(
                                'La inversión en digitalización NO paga el año en que se hace. '
                                'El retorno económico es real pero llega en el año 2.',
                                style={'fontSize': '12px', 'color': '#e8e8f0',
                                       'lineHeight': '1.65', 'marginBottom': '12px'},
                            ),
                            html.P(
                                'Las dos preguntas que importan no son "¿cuánto invierto?" '
                                'sino "¿cuándo empiezo?" y "¿puedo mantenerlo?".',
                                style={'fontSize': '12px', 'color': '#b8b8cc', 'lineHeight': '1.65'},
                            ),
                        ], style={'padding': '18px'}),
                    ], className='card-clean h-100',
                       style={'borderLeft': f'3px solid {C_CYAN}44'}),
                    md=4,
                ),
            ], className='g-3 mb-4'),

        ], className='main-scroll'),

    ], className='main-content'),
], className='page-root')


@dash.callback(
    dash.Output('seco-wages-scatter', 'figure'),
    dash.Output('seco-dc-wages',      'figure'),
    dash.Output('seco-lag',           'figure'),
    dash.Output('seco-sustained',     'figure'),
    dash.Input('seco-init', 'n_intervals'),
)
def load_charts(_):
    import traceback
    import plotly.graph_objects as go
    from pages.get_figures.get_figures_economia import (
        fig_digital_wages_scatter, fig_data_centers_wages,
        fig_investment_lag, fig_sustained_investment,
    )

    def _safe(fn):
        try:
            return fn()
        except Exception:
            traceback.print_exc()
            return go.Figure()

    return (
        _safe(fig_digital_wages_scatter),
        _safe(fig_data_centers_wages),
        _safe(fig_investment_lag),
        _safe(fig_sustained_investment),
    )
