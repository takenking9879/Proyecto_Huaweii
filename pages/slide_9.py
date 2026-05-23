import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_9 import (
    fig_empresas_por_estado, fig_distribucion_tamano, fig_roc, fig_shap,
)
from pages.get_data.get_data_9 import get_kpis, get_anios, get_representativos_9

dash.register_page(__name__, path='/slide_9')

kpis  = get_kpis()
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
    sidebar('/slide_9'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Densidad Empresarial · DENUE + Modelo', className='page-title'),
            html.P(
                '¿Qué distingue a los estados con más empresas por habitante? — Clasificación '
                'binaria con datos DENUE: Random Forest · XGBoost · Red Neuronal + SHAP',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'{kpis["total_empresas"]:,} empresas DENUE',
                          className='badge-cyan me-2',
                          title='Total de unidades económicas registradas en el Directorio Estadístico Nacional (DENUE)'),
                html.Span(f'Más denso: {kpis["estado_mas_empresas"][:14]}',
                          className='badge-gold me-2',
                          title='Estado con mayor densidad empresarial (empresas por 1,000 habitantes)'),
                html.Span(f'Año de datos: {kpis["anio_datos"]}',
                          className='badge-gray',
                          title='Año del corte de datos DENUE utilizado para el análisis'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='s9-init', interval=400, max_intervals=1),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'Usando datos del DENUE (Directorio Estadístico Nacional de Unidades Económicas), '
                'clasificamos los 32 estados como de alta o baja densidad empresarial — medida '
                'como empresas por 1,000 habitantes. Se entrenaron 4 modelos para aprender esta '
                'clasificación. AUC = 1.0 indica clasificación perfecta, pero con solo 32 '
                'observaciones por año los modelos pueden estar sobreajustados — interpreta '
                'los resultados con precaución. SHAP revela qué tamaños de empresa son más '
                'informativos para separar estados de alta y baja densidad.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-danger', 'Concentración empresarial',
                    f'CDMX, Estado de México y Jalisco concentran más del 30 % '
                    f'del total de {kpis["total_empresas"]:,} empresas registradas en DENUE.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-cyan', 'RF y XGBoost AUC = 1.0',
                    'Ambos modelos clasifican la densidad empresarial alta/baja con AUC = 1.0. '
                    'Advertencia: el dataset pequeño (32 obs/año) puede causar sobreajuste.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-gold', 'Micro-empresas: >85 %',
                    'Más del 85 % del tejido empresarial mexicano son micro o pequeñas empresas '
                    '(0–10 empleados). Las grandes empresas son minoría pero generan más empleo.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Tamaño como predictor',
                    'La distribución por tamaño de empresa (% de micro, pequeñas, medianas) '
                    'es el predictor dominante de la densidad empresarial estatal según SHAP.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Empresas + Tamaño
            dbc.Row([
                dbc.Col(
                    _card('Empresas registradas por estado',
                          dcc.Graph(figure=fig_empresas_por_estado(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Total de unidades económicas en DENUE. CDMX, Estado de México y Jalisco concentran más del 30 % del total nacional de empresas.'),
                    md=7,
                ),
                dbc.Col(
                    _card('Distribución por tamaño de empresa',
                          dcc.Graph(figure=fig_distribucion_tamano(),
                                    config=_CFG, style={'height': '360px'}),
                          desc='Micro: 0–10 empleados · Pequeña: 11–50 · Mediana: 51–250 · Grande: 250+. Más del 85 % del tejido empresarial mexicano es micro o pequeño.'),
                    md=5,
                ),
            ], className='g-3 mb-3'),

            # ROC + SHAP (lazy load)
            dbc.Row([
                dbc.Col(
                    _card('Curvas ROC — alta vs baja densidad (AUC = 1 ideal, diagonal = azar)',
                          dcc.Loading(dcc.Graph(id='s9-roc',
                                               config=_CFG, style={'height': '320px'})),
                          desc='Curva más cercana a la esquina superior izquierda = mejor modelo. Advertencia: con solo 32 estados por año el modelo puede estar sobreajustado.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Importancia SHAP — tamaños de empresa con más peso en la predicción',
                          dcc.Loading(dcc.Graph(id='s9-shap',
                                               config=_CFG, style={'height': '320px'})),
                          desc='Qué proporción de cada tamaño de empresa (micro, pequeña, mediana) distingue mejor entre estados de alta y baja densidad empresarial.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

            # ── Representative states ─────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Estados representativos — ¿alta o baja densidad?', className='section-block-title'),
                html.P(
                    'Un estado representativo de cada cuartil de densidad empresarial '
                    '(empresas por 1,000 hab.). Se muestra la clasificación real, la '
                    'predicción del Random Forest y la confianza del modelo en esa predicción.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            html.Div(id='s9-reps', className='mb-3'),

        ], className='main-scroll'),

    ], className='section-modelos', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


def _rep_card_9(d):
    is_alta   = d['pred_class'] == 1
    correct   = d['real_class'] == d['pred_class']
    color     = d['color']
    # Confidence = probability of the PREDICTED class (not always prob_alta)
    conf      = d['prob_alta'] if is_alta else (100 - d['prob_alta'])
    conf      = min(100, max(0, conf))
    class_lbl = 'Alta densidad' if is_alta else 'Baja densidad'
    class_col = '#00b4cc' if is_alta else '#9090a8'
    real_lbl  = 'Alta densidad' if d['real_class'] == 1 else 'Baja densidad'
    check     = '✓ Predicción correcta' if correct else '✗ Predicción incorrecta'
    chk_col   = '#2ca02c' if correct else '#cf0a2c'
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            # Group label
            html.Div([
                html.Span(d['icon'], style={'fontSize': '18px', 'marginRight': '8px'}),
                html.Span(d['grupo'], style={'fontWeight': '600', 'fontSize': '10px',
                          'letterSpacing': '0.07em', 'textTransform': 'uppercase',
                          'color': color}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
            # State name + density
            html.P(d['estado'], style={'color': '#e8e8f0', 'fontWeight': '600',
                                       'fontSize': '15px', 'margin': '0 0 2px'}),
            html.P(f'{d["densidad"]:.1f} empresas por 1,000 hab. · {d["year"]}',
                   style={'color': '#5c5c74', 'fontSize': '11px', 'margin': '0 0 12px'}),
            # Real vs predicted
            html.Div([
                html.Div([
                    html.Span('Densidad real', style={'color': '#5c5c74', 'fontSize': '9px',
                                                      'display': 'block', 'textTransform': 'uppercase',
                                                      'letterSpacing': '0.06em'}),
                    html.Span(real_lbl, style={'color': '#e8e8f0', 'fontWeight': '500', 'fontSize': '12px'}),
                ], style={'marginRight': '14px'}),
                html.Div([
                    html.Span('Modelo predice', style={'color': '#5c5c74', 'fontSize': '9px',
                                                   'display': 'block', 'textTransform': 'uppercase',
                                                   'letterSpacing': '0.06em'}),
                    html.Span(class_lbl, style={'color': class_col, 'fontWeight': '600', 'fontSize': '12px'}),
                ], style={'marginRight': '14px'}),
                html.Div([
                    html.Span('Confianza', style={'color': '#5c5c74', 'fontSize': '9px',
                                                  'display': 'block', 'textTransform': 'uppercase',
                                                  'letterSpacing': '0.06em'}),
                    html.Span(f'{conf:.0f}%', style={'color': color, 'fontWeight': '700', 'fontSize': '20px',
                                                      'lineHeight': '1'}),
                ]),
            ], style={'display': 'flex', 'alignItems': 'flex-end', 'marginBottom': '10px'}),
            # Confidence bar
            html.Div(style={'height': '4px', 'background': 'rgba(255,255,255,0.08)',
                            'borderRadius': '2px', 'overflow': 'hidden'}, children=[
                html.Div(style={'height': '100%', 'width': f'{conf:.0f}%',
                                'background': f'linear-gradient(90deg, {color}99, {color})',
                                'borderRadius': '2px'}),
            ]),
            html.Small(check, style={'color': chk_col, 'fontSize': '10px',
                                     'marginTop': '6px', 'display': 'block', 'fontWeight': '600'}),
        ], style={'padding': '14px 16px'}),
    ], className=f'h-100 animate-in card-clean'), md=3)


@dash.callback(
    Output('s9-roc',  'figure'),
    Output('s9-shap', 'figure'),
    Output('s9-reps', 'children'),
    Input('s9-init',  'n_intervals'),
)
def load_ml_9(_):
    reps_data = get_representativos_9()
    if reps_data:
        reps_row = dbc.Row([_rep_card_9(d) for d in reps_data], className='g-3')
    else:
        reps_row = html.P('Modelos en caché anterior — recargar para ver ejemplos.',
                          style={'color': '#5c5c74', 'fontSize': '12px'})
    return fig_roc(), fig_shap(), reps_row
