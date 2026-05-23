import traceback
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from pages.components import sidebar
from pages.get_figures.get_figures_10 import (
    fig_real_vs_pred, fig_shap, fig_cv_scores, fig_clustering,
    fig_pc_scatter, fig_pc_loadings, pc_display_name,
    fig_cluster_boxplots, fig_feature_scatter_poly,
)
from pages.get_data.get_data_10 import get_kpis, get_ml, predict_pilar, get_representatives_10

dash.register_page(__name__, path='/slide_10')

_TASA_COLS = ['tasa_Sociedad', 'tasa_Patrimonio', 'tasa_Vida',
              'tasa_Familia', 'tasa_Sexual', 'tasa_Estado']

_LABELS = {
    'tasa_Sociedad': 'Tasa Sociedad', 'tasa_Patrimonio': 'Tasa Patrimonio',
    'tasa_Vida': 'Tasa Vida', 'tasa_Familia': 'Tasa Familia',
    'tasa_Sexual': 'Tasa Sexual', 'tasa_Estado': 'Tasa Estado',
}

_INSIGHTS = [
    {
        'icon': '◈', 'color': 'card-gold',
        'title': 'Tasa Sociedad domina',
        'desc': 'El crimen societal (narcomenudeo) es el predictor más relevante del pilar de innovación según SHAP — con 3× más peso que el siguiente.',
    },
    {
        'icon': '◎', 'color': 'card-cyan',
        'title': 'R² = 0.777 — Alta predictibilidad',
        'desc': 'Gradient Boosting predice el pilar de innovación IDDE con R²=0.777 en validación cruzada 5-fold; Random Forest alcanza 0.774.',
    },
    {
        'icon': '⬡', 'color': 'card-danger',
        'title': '2 clusters diferenciados',
        'desc': 'K-Means (k=2) separa los estados en dos grupos claros: alta innovación / bajo crimen social vs baja innovación / alto crimen social.',
    },
    {
        'icon': '⌬', 'color': 'card-success',
        'title': '12 features via PCA',
        'desc': 'De todas las tasas de crimen, 12 variables superan el umbral de norma ≥0.7 en el espacio de los primeros PCs (80% varianza).',
    },
]


def _insight_card(icon, color, title, desc, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Span(icon, className='insight-icon'),
            html.P(title, className='insight-title'),
            html.P(desc, className='insight-desc'),
        ], style={'padding': '16px 18px'}),
    ], className=f'animate-in h-100 {color} {delay}')


_sliders = [
    dbc.Col([
        html.P(_LABELS[col], className='metric-label'),
        dcc.Slider(
            id=f's10-{col}', min=0, max=500, step=5, value=100,
            marks={0: '0', 250: '250', 500: '500'},
            tooltip={'placement': 'bottom'},
        ),
    ], md=4)
    for col in _TASA_COLS
]

_pc_options = [{'label': f'Componente Principal {i}', 'value': i} for i in range(1, 7)]

_CHART_H = '310px'

layout = html.Div([
    sidebar('/slide_10'),

    html.Div([

        # ── Page header ──────────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Innovación Digital vs Crimen', className='page-title'),
            html.P(
                '¿Puede el crimen predecir la innovación digital de un estado? — R²=0.77 con '
                'Random Forest · Gradient Boosting · PCA · K-Means clustering · SHAP',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(id='s10-badge-r2',
                          className='badge-cyan me-2',
                          title='R² del Random Forest en validación cruzada 5-fold — fracción de varianza del pilar innovación explicada por el modelo'),
                html.Span(id='s10-badge-best',
                          className='badge-gold me-2',
                          title='Modelo con mayor R² en validación cruzada entre RF, Gradient Boosting, Ridge y XGBoost'),
                html.Span(id='s10-badge-feats',
                          className='badge-gray',
                          title='Número de variables de crimen seleccionadas vía PCA (norma ≥ 0.7 en los primeros PCs que explican 80% de varianza)'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='s10-init', interval=400, max_intervals=1),
        dcc.Store(id='s10-trained', data=0),

        # ── Scrollable body ──────────────────────────────────────────
        html.Div([

            # Context
            html.P(
                '¿Puede el perfil criminal de un estado predecir qué tan innovador es '
                'digitalmente? Sí. Un Random Forest entrenado con tasas de criminalidad estatal '
                'logra R²=0.77 al predecir el pilar de innovación del IDDE. El clustering '
                'K-Means agrupa estados con perfiles crimen–innovación similares. El Análisis '
                'de Componentes Principales (PCA) comprime las variables de crimen en ejes '
                'ortogonales para revelar la estructura subyacente de los datos. Al final hay '
                'un simulador: ajusta tasas de crimen y ve qué pilar de innovación predice el modelo.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_insight_card(
                    _INSIGHTS[0]['icon'], _INSIGHTS[0]['color'],
                    _INSIGHTS[0]['title'], _INSIGHTS[0]['desc'],
                    'animate-in-delay-1'), md=3),
                dbc.Col(_insight_card(
                    _INSIGHTS[1]['icon'], _INSIGHTS[1]['color'],
                    _INSIGHTS[1]['title'], _INSIGHTS[1]['desc'],
                    'animate-in-delay-2'), md=3),
                dbc.Col(_insight_card(
                    _INSIGHTS[2]['icon'], _INSIGHTS[2]['color'],
                    _INSIGHTS[2]['title'], _INSIGHTS[2]['desc'],
                    'animate-in-delay-3'), md=3),
                dbc.Col(_insight_card(
                    _INSIGHTS[3]['icon'], _INSIGHTS[3]['color'],
                    _INSIGHTS[3]['title'], _INSIGHTS[3]['desc'],
                    'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # ── Scatter: features vs pilar innovación (polynomial regression) ──
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        html.P('Variables de crimen vs pilar innovación — mejor regresión polinomial (grado 1-3)',
                               className='chart-label'),
                        html.P('Línea roja = lineal · dorada = cuadrática · morada = cúbica. Se muestra el grado con menor RMSE sobre los datos.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-scatter-poly',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': '520px'},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in card-expandable'),
                    md=12,
                ),
            ], className='g-3 mb-3'),

            # Clustering + CV scores
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        html.P('Agrupación K-Means (k=2) — estados con perfil crimen–innovación similar',
                               className='chart-label'),
                        html.P('Estados más cercanos tienen perfiles similares. El color indica el cluster asignado. Busca si los estados de un mismo grupo comparten ubicación geográfica.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-cluster',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in h-100 card-expandable'),
                    md=5,
                ),
                dbc.Col(
                    dbc.Card([
                        html.P('R² validación cruzada 5-fold — qué modelo predice mejor el pilar innovación',
                               className='chart-label'),
                        html.P('R² en cada una de las 5 particiones. Puntuaciones similares entre folds = modelo estable. R² = 1 es predicción perfecta; R² = 0 es sin poder predictivo.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-cv',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in h-100 card-expandable'),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card([
                        html.P('Distribución por cluster — pilar innovación y crimen social',
                               className='chart-label'),
                        html.P('Cada caja resume la distribución dentro del cluster. Puntos = estados individuales.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-boxplots',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in h-100 card-expandable'),
                    md=4,
                ),
            ], className='g-3 mb-3'),

            # Real vs Pred + SHAP
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        html.P('Valor real vs predicción Random Forest — cada punto es un estado/año',
                               className='chart-label'),
                        html.P('Los puntos idealmente estarían sobre la diagonal (pred = real). La dispersión indica el error — puntos alejados son los estados más difíciles de predecir.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-rvp',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in h-100 card-expandable'),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card([
                        html.P('Importancia SHAP — qué tasas de crimen explican más la innovación',
                               className='chart-label'),
                        html.P('Barras más largas = esa tasa de crimen influyó más en las predicciones del modelo. SHAP explica el porqué, no solo la precisión global.',
                               className='chart-desc'),
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-shap',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-pop animate-in h-100 card-expandable'),
                    md=6,
                ),
            ], className='g-3 mb-4'),

            # ── Representative states by IDDE group ──────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Estados representativos por grupo IDDE', className='section-block-title'),
                html.P(
                    'Un estado representativo de cada grupo de digitalización (Básico, Emprendedor, '
                    'Avanzado, Líder) con su pilar de innovación real vs el valor predicho por '
                    'Random Forest. Δ pequeño = predicción precisa.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            html.Div(id='s10-reps', className='mb-4'),

            # ── PC Analysis section ──────────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Análisis de Componentes Principales (PCA)',
                        className='section-block-title'),
                html.P(
                    'El PCA comprime las múltiples tasas de crimen en componentes ortogonales '
                    '(PC1, PC2 …). Cada PC captura una dimensión independiente de variación. '
                    'Selecciona un componente para ver su correlación con el pilar de innovación '
                    'y qué variables de crimen tienen mayor peso en ese eje.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id='s10-pc-dd',
                        options=_pc_options,
                        value=1,
                        clearable=False,
                        placeholder='Selecciona un PC…',
                    ),
                    md=4,
                ),
                dbc.Col(
                    html.Div(id='s10-pc-interp', className='pc-interp'),
                    md=8,
                ),
            ], className='g-3 align-items-center mb-3'),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-pc-scatter',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean card-cyan animate-in h-100 card-expandable'),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(
                                id='s10-pc-loadings',
                                config={'displayModeBar': False, 'responsive': True},
                                style={'height': _CHART_H},
                            )),
                            style={'padding': '8px'},
                        ),
                    ], className='card-clean animate-in h-100 card-expandable'),
                    md=6,
                ),
            ], className='g-3 mb-4'),

            # ── Simulator ────────────────────────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Simulador — ¿Qué innovación predice el modelo?', className='section-block-title'),
                html.P(
                    'Ajusta las tasas de crimen por categoría (delitos por cada 100,000 habitantes) '
                    'y el Random Forest predice el pilar de innovación IDDE correspondiente. '
                    'Las tasas promedio nacionales rondan los 100–200 por 100k hab.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P('Perfiles predeterminados:', className='metric-label',
                                   style={'marginBottom': '8px'}),
                            dbc.Button('Estado promedio',    id='s10-pre-0', size='sm',
                                       className='btn-hw-secondary me-2 mb-2', n_clicks=0),
                            dbc.Button('Alta innovación',    id='s10-pre-1', size='sm',
                                       className='btn-hw-secondary me-2 mb-2', n_clicks=0),
                            dbc.Button('Alto crimen social', id='s10-pre-2', size='sm',
                                       className='btn-hw-secondary mb-2',      n_clicks=0),
                        ]),
                    ], className='mb-3'),
                    dbc.Row(_sliders, className='g-3 mb-4'),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button('Predecir', id='s10-btn', color='danger',
                                       className='btn-hw-primary px-4'),
                            width='auto',
                        ),
                        dbc.Col(
                            html.Div(id='s10-result', className='sim-result'),
                            width='auto',
                            style={'alignSelf': 'center'},
                        ),
                    ], className='g-3 align-items-center'),
                ], style={'padding': '20px 24px'}),
            ], className='card-clean animate-in mb-4'),

        ], className='main-scroll'),

    ], className='section-modelos', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


# ── Callbacks ─────────────────────────────────────────────────────────────

def _pc_mini_bars(pc_zscores, color):
    """Mini centered bar chart for PC z-scores — pure HTML/CSS, no callback needed."""
    _PC_LABELS = ['PC1 · Escala Crimen', 'PC2 · Estructura', 'PC3 · Contraste']
    bars = []
    for i, z in enumerate(pc_zscores[:3]):
        bar_w = min(48, abs(z) * 18)
        pos_col = color
        neg_col = '#00b4cc'
        bar_col = pos_col if z >= 0 else neg_col
        sign_str = f'+{z:.1f}σ' if z >= 0 else f'{z:.1f}σ'
        bars.append(html.Div([
            html.Span(_PC_LABELS[i], style={
                'color': '#5c5c74', 'fontSize': '9px', 'width': '90px',
                'flexShrink': '0', 'whiteSpace': 'nowrap', 'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            }),
            html.Div(style={
                'flex': '1', 'height': '5px', 'position': 'relative',
                'background': 'rgba(255,255,255,0.06)', 'borderRadius': '3px',
                'overflow': 'hidden',
            }, children=[
                html.Div(style={'position': 'absolute', 'left': '50%', 'top': '0',
                                'height': '100%', 'width': '1px',
                                'background': 'rgba(255,255,255,0.18)'}),
                html.Div(style={
                    'position': 'absolute', 'height': '100%',
                    'width': f'{bar_w:.0f}%',
                    'left': '50%' if z >= 0 else f'{50 - bar_w:.0f}%',
                    'background': bar_col, 'borderRadius': '3px', 'opacity': '0.85',
                }),
            ]),
            html.Span(sign_str, style={
                'color': bar_col, 'fontSize': '9px', 'width': '30px',
                'textAlign': 'right', 'flexShrink': '0',
            }),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px', 'marginBottom': '4px'}))
    return html.Div([
        html.Small('Perfil PCA (σ = desv. est. respecto al promedio nacional)', style={
            'color': '#5c5c74', 'fontSize': '9px', 'display': 'block',
            'letterSpacing': '0.07em', 'textTransform': 'uppercase', 'marginBottom': '6px',
        }),
        *bars,
    ], style={'paddingTop': '10px', 'marginTop': '10px',
              'borderTop': '1px solid rgba(255,255,255,0.07)'})


def _rep_card_10(d):
    delta     = d['pred'] - d['real']
    delta_str = f'+{delta:.1f}' if delta >= 0 else f'{delta:.1f}'
    delta_col = '#2ca02c' if abs(delta) < 3 else ('#ff7f0e' if abs(delta) < 8 else '#cf0a2c')
    color     = d['color']
    pct_bar   = min(100, max(0, d['real'] / 100 * 100))
    group_cls = {'Líder': 'card-success', 'Avanzado': 'card-cyan',
                 'Emprendedor': 'card-gold', 'Básico': 'card-danger'}.get(d['grupo'], 'card-clean')
    pc_section = _pc_mini_bars(d.get('pc_zscore', []), color)
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(d['icon'], style={'fontSize': '20px', 'marginRight': '8px'}),
                html.Span(d['grupo'], style={'fontWeight': '600', 'fontSize': '11px',
                          'letterSpacing': '0.07em', 'textTransform': 'uppercase', 'color': color}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
            html.P(d['estado'], style={'color': '#e8e8f0', 'fontWeight': '600',
                                       'fontSize': '15px', 'margin': '0 0 12px'}),
            html.Div([
                html.Div([
                    html.Span('Real', style={'color': '#5c5c74', 'fontSize': '10px', 'display': 'block'}),
                    html.Span(f'{d["real"]:.1f}', style={'color': '#e8e8f0', 'fontWeight': '700',
                                                          'fontSize': '22px', 'lineHeight': '1'}),
                ], style={'marginRight': '18px'}),
                html.Div([
                    html.Span('RF Pred.', style={'color': '#5c5c74', 'fontSize': '10px', 'display': 'block'}),
                    html.Span(f'{d["pred"]:.1f}', style={'color': '#00b4cc', 'fontWeight': '700',
                                                          'fontSize': '22px', 'lineHeight': '1'}),
                ]),
                html.Div([
                    html.Span('Δ', style={'color': '#5c5c74', 'fontSize': '10px', 'display': 'block'}),
                    html.Span(delta_str, style={'color': delta_col, 'fontWeight': '600',
                                                'fontSize': '14px', 'lineHeight': '1.4'}),
                ], style={'marginLeft': 'auto'}),
            ], style={'display': 'flex', 'alignItems': 'flex-end', 'marginBottom': '10px'}),
            html.Div(style={'height': '4px', 'background': 'rgba(255,255,255,0.08)',
                            'borderRadius': '2px', 'overflow': 'hidden'}, children=[
                html.Div(style={'height': '100%', 'width': f'{pct_bar:.0f}%',
                                'background': f'linear-gradient(90deg, {color}88, {color})',
                                'borderRadius': '2px'}),
            ]),
            html.Small(f'Año {d["anio"]}', style={'color': '#5c5c74', 'fontSize': '10px',
                                                   'marginTop': '5px', 'display': 'block'}),
            pc_section,
        ], style={'padding': '14px 16px'}),
    ], className=f'h-100 animate-in {group_cls}'), md=3)


def _safe(fn):
    try:
        return fn()
    except Exception:
        traceback.print_exc()
        return go.Figure()


@dash.callback(
    Output('s10-cluster',      'figure'),
    Output('s10-cv',           'figure'),
    Output('s10-rvp',          'figure'),
    Output('s10-shap',         'figure'),
    Output('s10-badge-r2',     'children'),
    Output('s10-badge-best',   'children'),
    Output('s10-badge-feats',  'children'),
    Output('s10-reps',         'children'),
    Output('s10-boxplots',     'figure'),
    Output('s10-scatter-poly', 'figure'),
    Output('s10-trained',      'data'),
    Input('s10-init', 'n_intervals'),
)
def load_main_charts(_):
    try:
        kpis      = get_kpis()
        reps_data = get_representatives_10()
    except Exception:
        traceback.print_exc()
        kpis      = {'rf_r2': '?', 'best_model': '?', 'best_r2': '?', 'n_features': '?'}
        reps_data = []
    reps_row = dbc.Row([_rep_card_10(d) for d in reps_data], className='g-3') if reps_data else html.Div()
    return (
        _safe(fig_clustering), _safe(fig_cv_scores), _safe(fig_real_vs_pred), _safe(fig_shap),
        f'RF R² = {kpis["rf_r2"]}',
        f'Mejor: {kpis["best_model"]}  R²={kpis["best_r2"]}',
        f'{kpis["n_features"]} features (PCA)',
        reps_row,
        _safe(fig_cluster_boxplots), _safe(fig_feature_scatter_poly),
        1,
    )


@dash.callback(
    Output('s10-pc-scatter',  'figure'),
    Output('s10-pc-loadings', 'figure'),
    Output('s10-pc-interp',   'children'),
    Input('s10-trained', 'data'),
    Input('s10-pc-dd',   'value'),
)
def update_pc(trained, pc_num):
    from dash.exceptions import PreventUpdate
    if not trained:
        raise PreventUpdate
    pc_num = pc_num or 1
    ml = get_ml()
    interp = ''
    if 'pc_var' in ml and (pc_num - 1) < len(ml['pc_var']):
        var = ml['pc_var'][pc_num - 1]
        name = pc_display_name(pc_num - 1)
        interp = f'PC{pc_num} · {var:.1%} varianza  ·  {name}'
    return fig_pc_scatter(pc_num), fig_pc_loadings(pc_num), interp


@dash.callback(
    Output('s10-result', 'children'),
    Input('s10-btn', 'n_clicks'),
    [State(f's10-{c}', 'value') for c in _TASA_COLS],
    prevent_initial_call=True,
)
def simulate(n, *vals):
    crime_dict = {col: float(v or 0) for col, v in zip(_TASA_COLS, vals)}
    pred = predict_pilar(crime_dict)
    return f'Pilar Innovación predicho: {pred}'


@dash.callback(
    Output('s10-tasa_Sociedad',   'value'),
    Output('s10-tasa_Patrimonio', 'value'),
    Output('s10-tasa_Vida',       'value'),
    Output('s10-tasa_Familia',    'value'),
    Output('s10-tasa_Sexual',     'value'),
    Output('s10-tasa_Estado',     'value'),
    Input('s10-pre-0', 'n_clicks'),
    Input('s10-pre-1', 'n_clicks'),
    Input('s10-pre-2', 'n_clicks'),
    prevent_initial_call=True,
)
def load_preset_10(_0, _1, _2):
    from dash import ctx
    from dash.exceptions import PreventUpdate
    _PRESETS = {
        's10-pre-0': [100, 400, 200, 150,  40, 100],
        's10-pre-1': [ 50, 200, 100,  80,  20,  50],
        's10-pre-2': [300, 400, 200, 150,  40, 100],
    }
    trig = ctx.triggered_id
    if trig in _PRESETS:
        return _PRESETS[trig]
    raise PreventUpdate
