import traceback
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from pages.components import sidebar
from pages.get_data.get_data_inversion import get_cluster_profiles, get_roi_projections

dash.register_page(__name__, path='/slide_inversion')

_CFG = {'displayModeBar': False, 'responsive': True}

_CLUSTER_ICONS = {'C0': '▲', 'C1': '◎', 'C2': '✦', 'C3': '⚡'}
_CLUSTER_CLASSES = {'C0': 'card-danger', 'C1': 'card-cyan', 'C2': 'card-success', 'C3': 'card-gold'}


def _safe(fn):
    try:
        return fn()
    except Exception:
        traceback.print_exc()
        return go.Figure()


def _cluster_inv_card(profile, roi, delay=''):
    code  = profile['code']
    color = profile['color']
    cls   = _CLUSTER_CLASSES.get(code, 'card-cyan')
    icon  = _CLUSTER_ICONS.get(code, '◈')
    delta = roi.get(code, {})
    wage_pct = delta.get('delta_wage_pct', 0)

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(icon, className='insight-icon',
                          style={'color': color, 'fontSize': '20px', 'marginRight': '8px'}),
                html.Span(f'{code} · {profile["name"]}',
                          style={'fontWeight': '700', 'fontSize': '12px', 'color': color,
                                 'textTransform': 'uppercase', 'letterSpacing': '0.06em'}),
                html.Span(f'{profile["n"]} estados', style={
                    'marginLeft': 'auto', 'fontSize': '10px', 'color': '#5c5c74',
                }),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),

            html.P(profile['priority'],
                   style={'fontWeight': '600', 'fontSize': '11px', 'color': '#e8e8f0',
                          'margin': '0 0 4px'}),
            html.P(profile['description'],
                   className='insight-desc', style={'margin': '0 0 8px'}),

            html.Div([
                html.Span('IDDE avg', style={'fontSize': '9px', 'color': '#5c5c74',
                                              'textTransform': 'uppercase', 'letterSpacing': '0.07em'}),
                html.Span(f'{profile["avg_idde"]:.1f}', style={
                    'fontSize': '15px', 'fontWeight': '700', 'color': color, 'marginLeft': '6px',
                }),
                html.Span(' ·', style={'color': '#5c5c74', 'margin': '0 6px'}),
                html.Span('+10 pts IDDE →', style={'fontSize': '9px', 'color': '#5c5c74',
                                                     'textTransform': 'uppercase', 'letterSpacing': '0.07em'}),
                html.Span(f' +{wage_pct:.1f}% salario',
                          style={'fontSize': '11px', 'fontWeight': '600', 'color': '#00b87a',
                                 'marginLeft': '4px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '2px'}),
        ], style={'padding': '14px 16px'}),
    ], className=f'animate-in h-100 {cls} {delay}'.strip())


def _chart_card(title, graph_id, desc=None, height='340px'):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(
        dcc.Loading(dcc.Graph(id=graph_id, config=_CFG, style={'height': height})),
        style={'padding': '6px 8px 10px'},
    ))
    return dbc.Card(children, className='card-clean card-pop animate-in h-100 card-expandable')


profiles = get_cluster_profiles()
roi_data = get_roi_projections()

layout = html.Div([
    sidebar('/slide_inversion'),

    html.Div([

        # ── Page header ──────────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Oportunidad de Inversión · 4 Perfiles de Retorno', className='page-title'),
            html.P(
                'K-Means k=4 sobre 32 estados revela perfiles con necesidades y retornos distintos — '
                'cada +10 pts de IDDE proyecta ganancias medibles en salarios, confianza social y percepción ciudadana',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('32 estados analizados', className='badge-gray me-2'),
                html.Span('4 perfiles de inversión', className='badge-cyan me-2'),
                html.Span('R²=0.77 modelo predictivo', className='badge-green me-2'),
                html.Span('IDDE → salario r²=0.29', className='badge-gold'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='sinv-init', interval=400, max_intervals=1),

        # ── Scrollable body ──────────────────────────────────────────
        html.Div([

            html.P(
                'El Índice de Desarrollo Digital Estatal (IDDE) predice con R²=0.29 los salarios, '
                'con r=+0.78 la confianza social y con r≈+0.45 la percepción de seguridad. '
                'Los 4 clusters identificados tienen brechas y palancas de retorno distintas: '
                'desde estados que necesitan infraestructura básica (C0) hasta los que tienen '
                'conectividad pero requieren soluciones de gobernanza (C1).',
                className='page-context',
            ),

            # 4 Cluster investment cards
            dbc.Row([
                dbc.Col(_cluster_inv_card(p, roi_data,
                    delay=f'animate-in-delay-{i+1}'), md=6, className='mb-3')
                for i, p in enumerate(profiles)
            ], className='g-3 mb-3'),

            # ROI projections bar chart
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Retorno proyectado por +10 puntos de IDDE',
                        className='section-block-title'),
                html.P(
                    'Cambio porcentual proyectado en tres indicadores clave si el IDDE del cluster '
                    'sube 10 puntos. Basado en regresión lineal sobre los 32 estados (corte 2025). '
                    'El retorno en salarios es el canal económico más robusto (R²=0.29).',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card(
                        'ROI proyectado · +10 pts IDDE por perfil',
                        'sinv-roi-bars',
                        height='320px',
                    ),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Two scatters
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Las dos palancas más sólidas del IDDE',
                        className='section-block-title'),
                html.P(
                    'Izquierda: IDDE vs salario mensual (R²≈0.29 — la calidad de la conexión '
                    'predice productividad económica). Derecha: IDDE vs confianza social (r=+0.78 — '
                    'la correlación más fuerte del análisis: conectividad fortalece el tejido social).',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card('IDDE 2025 × Salario promedio mensual', 'sinv-wage-scatter',
                                desc='Cada punto = un estado. R²≈0.29 — los estados más digitalizados pagan salarios más altos.',
                                height='340px'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Cluster IDDE bars
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Brecha IDDE por perfil vs nivel desarrollado (C2)',
                        className='section-block-title'),
                html.P(
                    'Línea punteada = IDDE promedio del cluster C2 (Desarrollados-seguros). '
                    'La distancia de cada cluster a esa línea es la brecha de inversión. '
                    'C0 tiene la mayor brecha — y el mayor retorno potencial por peso invertido.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    _chart_card('Brecha de IDDE · Perfiles vs Referencia C2', 'sinv-idde-bars',
                                height='260px'),
                    md=12,
                ),
            ], className='g-3 mb-4'),

        ], className='main-scroll'),

    ], className='main-content'),
], className='page-root')


@dash.callback(
    Output('sinv-roi-bars',    'figure'),
    Output('sinv-wage-scatter', 'figure'),
    Output('sinv-idde-bars',   'figure'),
    Input('sinv-init', 'n_intervals'),
)
def load_charts(_):
    from pages.get_figures.get_figures_inversion import (
        fig_roi_projections, fig_idde_vs_wage_scatter, fig_cluster_idde_bars,
    )
    return (
        _safe(fig_roi_projections),
        _safe(fig_idde_vs_wage_scatter),
        _safe(fig_cluster_idde_bars),
    )
