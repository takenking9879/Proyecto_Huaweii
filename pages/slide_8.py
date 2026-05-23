import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from pages.components import sidebar
from pages.get_figures.get_figures_8 import (
    fig_salario_educacion, fig_salario_estado, fig_roc, fig_shap,
)
from pages.get_data.get_data_8 import get_kpis, predict_salario, get_representativos_8
from pages.db import query

dash.register_page(__name__, path='/slide_8')

kpis = get_kpis()

_instr_opts = query("""
    SELECT instruction_level_id, instruction_level
    FROM dim_instruction_level ORDER BY instruction_level_id
""")
_instr_levels = [{'label': r['instruction_level'], 'value': int(r['instruction_level_id'])}
                 for _, r in _instr_opts.iterrows()]
_school_max = int(query("SELECT MAX(schooling_years) as mx FROM dim_schooling_years")['mx'].iloc[0])

_CFG = {'displayModeBar': False, 'responsive': True}


def _card(title, body, desc=None, extra=''):
    children = [html.P(title, className='chart-label')]
    if desc:
        children.append(html.P(desc, className='chart-desc'))
    children.append(dbc.CardBody(body, style={'padding': '6px 8px 10px'}))
    return dbc.Card(children, className=f'card-clean card-pop animate-in h-100 card-expandable {extra}'.strip())


def _ins(icon, color, title, desc, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Span(icon, className='insight-icon'),
            html.P(title, className='insight-title'),
            html.P(desc, className='insight-desc'),
        ], style={'padding': '16px 18px'}),
    ], className=f'animate-in h-100 {color} {delay}'.strip())


layout = html.Div([
    sidebar('/slide_8'),

    html.Div([

        # ── Page header ──────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Mercado Laboral y Predicción Salarial · ENOE + Modelo', className='page-title'),
            html.P(
                '¿Qué determina un salario alto en México? — Modelos de clasificación entrenados '
                'con ENOE: Random Forest · XGBoost · Red Neuronal · Regresión Logística',
                className='page-subtitle',
            ),
            html.Div([
                html.Span(f'Mediana: ${kpis["mediana_salario"]:,.0f}/mes',
                          className='badge-cyan me-2',
                          title='Salario mensual neto mediano del conjunto de entrenamiento (ENOE)'),
                html.Span(f'Promedio: ${kpis["promedio_salario"]:,.0f}/mes',
                          className='badge-gold me-2',
                          title='Salario mensual neto promedio — más sensible a outliers altos que la mediana'),
                html.Span(f'{kpis["n_registros"]:,} registros ENOE',
                          className='badge-gray',
                          title='Total de trabajadores asalariados en el dataset de entrenamiento y validación'),
            ]),
        ], className='page-header'),

        dcc.Interval(id='s8-init', interval=400, max_intervals=1),

        # ── Scrollable body ──────────────────────────────────────
        html.Div([

            # Context
            html.P(
                'Se entrenaron 4 modelos de clasificación con datos de la ENOE (Encuesta Nacional '
                'de Ocupación y Empleo) para predecir si un trabajador gana por encima de la '
                'mediana salarial nacional. Las Curvas ROC comparan el desempeño de cada modelo '
                '(área AUC más cercana a 1 = mejor). SHAP muestra qué variables influyeron más '
                'en las predicciones del Random Forest. Al final encontrarás un simulador interactivo.',
                className='page-context',
            ),

            # Insight cards
            dbc.Row([
                dbc.Col(_ins('◈', 'card-gold', 'Educación es el predictor clave',
                    'Los años de escolaridad y el nivel educativo son las variables con mayor '
                    'peso SHAP — determinan más del 60 % de la predicción de salario alto.', 'animate-in-delay-1'), md=3),
                dbc.Col(_ins('◎', 'card-cyan', 'RF AUC = 0.902',
                    'El Random Forest clasifica si un trabajador está sobre o bajo la mediana '
                    'salarial con AUC = 0.902 — alta capacidad discriminatoria.', 'animate-in-delay-2'), md=3),
                dbc.Col(_ins('⬡', 'card-danger', 'Brecha 3× por educación',
                    f'El salario promedio con posgrado es ~3× el de educación básica completa. '
                    f'La mediana nacional es ${kpis["mediana_salario"]:,.0f} MXN/mes.', 'animate-in-delay-3'), md=3),
                dbc.Col(_ins('⌬', 'card-success', 'Digitalización importa',
                    'El nivel de digitalización del estado (Básico→Líder) es predictor relevante según SHAP '
                    '— estados más digitalizados concentran empleos mejor remunerados.', 'animate-in-delay-4'), md=3),
            ], className='g-3 mb-3'),

            # Salario por educación + por estado
            dbc.Row([
                dbc.Col(
                    _card('Salario promedio por nivel educativo',
                          dcc.Graph(figure=fig_salario_educacion(),
                                    config=_CFG, style={'height': '300px'}),
                          desc='Cada escalón educativo representa un salto salarial. Los postgraduados tienen salario ~3× mayor que quienes solo completaron educación básica.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Salario promedio por estado',
                          dcc.Graph(figure=fig_salario_estado(),
                                    config=_CFG, style={'height': '300px'}),
                          desc='Las diferencias entre estados reflejan el costo de vida y la estructura económica local. CDMX y Nuevo León lideran consistentemente.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

            # ROC + SHAP (lazy load)
            dbc.Row([
                dbc.Col(
                    _card('Curvas ROC — desempeño de cada modelo (AUC más alto = mejor)',
                          dcc.Loading(dcc.Graph(id='s8-roc',
                                               config=_CFG, style={'height': '300px'})),
                          desc='Curvarse hacia la esquina superior izquierda = mejor modelo. La diagonal es un clasificador aleatorio (AUC = 0.5). AUC = 1 es clasificación perfecta.'),
                    md=6,
                ),
                dbc.Col(
                    _card('Importancia SHAP — qué variables explican más la predicción',
                          dcc.Loading(dcc.Graph(id='s8-shap',
                                               config=_CFG, style={'height': '300px'})),
                          desc='Barra más larga = esa variable tuvo más peso en las predicciones. SHAP explica el PORQUÉ del modelo, no solo su precisión global.'),
                    md=6,
                ),
            ], className='g-3 mb-3'),

            # ── Representative profiles ───────────────────────────
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Perfiles representativos — ¿quién supera la mediana?', className='section-block-title'),
                html.P(
                    'Cuatro perfiles típicos de trabajadores mexicanos con distintos niveles '
                    'educativos y estados. La barra muestra la probabilidad predicha por el '
                    'Random Forest de que ese perfil supere la mediana salarial nacional.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            html.Div(id='s8-reps', className='mb-3'),

            # Simulator
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Simulador — ¿Supera la mediana salarial?', className='section-block-title'),
                html.P(
                    'Configura el perfil de un trabajador (nivel educativo, años de escolaridad '
                    'y nivel de digitalización del estado donde labora) y el Random Forest devuelve '
                    'la probabilidad de que su salario supere la mediana nacional.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dcc.Store(id='s8-preset-store', data=None),

            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P('Perfiles predeterminados:', className='metric-label',
                                   style={'marginBottom': '8px'}),
                            dbc.Button('⭐ Posgrado · Líder',       id='s8-pre-0', size='sm',
                                       className='btn-hw-secondary me-2 mb-2', n_clicks=0),
                            dbc.Button('◈ Licenciatura · Avanzado', id='s8-pre-1', size='sm',
                                       className='btn-hw-secondary me-2 mb-2', n_clicks=0),
                            dbc.Button('◎ Preparatoria · Emp.',  id='s8-pre-2', size='sm',
                                       className='btn-hw-secondary me-2 mb-2', n_clicks=0),
                            dbc.Button('⌬ Primaria · Básico',    id='s8-pre-3', size='sm',
                                       className='btn-hw-secondary mb-2',      n_clicks=0),
                        ]),
                    ], className='mb-3'),
                    dbc.Row([
                        dbc.Col([
                            html.P('Nivel educativo', className='metric-label'),
                            dcc.Dropdown(id='s8-instr', options=_instr_levels,
                                         value=4, clearable=False, className='dropdown-hw'),
                        ], md=4),
                        dbc.Col([
                            html.P(f'Años de escolaridad (0–{_school_max})', className='metric-label'),
                            dcc.Slider(id='s8-school', min=0, max=_school_max, step=1,
                                       value=9, marks={0: '0', 6: '6', 9: '9', 12: '12', 16: '16'},
                                       tooltip={'placement': 'bottom'}),
                        ], md=4),
                        dbc.Col([
                            html.P('Nivel digitalización del estado', className='metric-label'),
                            dcc.Dropdown(
                                id='s8-grupo-nivel',
                                options=[
                                    {'label': '⌬ Básico (nivel 1)',        'value': 1},
                                    {'label': '◎ Emprendedor (nivel 2)',   'value': 2},
                                    {'label': '◈ Avanzado (nivel 3)',       'value': 3},
                                    {'label': '⭐ Líder (nivel 4)',          'value': 4},
                                ],
                                value=4,
                                clearable=False,
                                className='dropdown-hw',
                            ),
                        ], md=4),
                    ], className='g-3 mb-4'),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button('Calcular', id='s8-btn', color='danger',
                                       className='btn-hw-primary px-4'),
                            width='auto',
                        ),
                        dbc.Col(
                            html.Div(id='s8-result', className='sim-result'),
                            width='auto', style={'alignSelf': 'center'},
                        ),
                    ], className='g-3 align-items-center'),
                ], style={'padding': '20px 24px'}),
            ], className='card-clean animate-in mb-4'),

        ], className='main-scroll'),

    ], className='section-modelos', style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}),

], style={'height': '100vh', 'width': '100vw', 'display': 'flex'})


def _rep_card_8(d):
    prob      = d['prob']
    above     = prob >= 50
    pct       = min(100, max(0, prob))
    color     = '#2ca02c' if above else '#d62728'
    group_cls = {'Líder': 'card-success', 'Avanzado': 'card-cyan',
                 'Transición': 'card-gold', 'Básico': 'card-danger'}.get(d['group'], 'card-clean')

    def _lv(lbl, val, val_color='#e8e8f0'):
        return html.Div([
            html.Span(lbl, style={
                'color': '#5c5c74', 'fontSize': '9px', 'textTransform': 'uppercase',
                'letterSpacing': '0.06em', 'display': 'block', 'marginBottom': '2px',
            }),
            html.Span(val, style={'color': val_color, 'fontSize': '12px', 'fontWeight': '600'}),
        ], style={'flex': '1', 'minWidth': '0'})

    return dbc.Col(dbc.Card([
        dbc.CardBody([
            # Group header
            html.Div([
                html.Span(d['icon'], style={'fontSize': '18px', 'marginRight': '8px'}),
                html.Span(d['group'], style={
                    'fontWeight': '700', 'fontSize': '10px',
                    'letterSpacing': '0.07em', 'textTransform': 'uppercase',
                    'color': color,
                }),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),

            # Value grid 2 × 2
            html.Div([
                _lv('Educación',   d['educacion']),
                _lv('Estado',      d['estado']),
            ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '8px'}),
            html.Div([
                _lv('Escolaridad', f'{d["school"]} años'),
                _lv('Año',         str(d['year'])),
            ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '14px'}),

            # Probability
            html.Div([
                html.Span('Prob. sobre mediana', style={
                    'color': '#5c5c74', 'fontSize': '9px', 'display': 'block',
                    'textTransform': 'uppercase', 'letterSpacing': '0.06em', 'marginBottom': '4px',
                }),
                html.Span(f'{prob:.1f}%', style={
                    'color': color, 'fontWeight': '700', 'fontSize': '26px', 'lineHeight': '1',
                }),
            ], style={'marginBottom': '10px'}),

            # Progress bar
            html.Div(style={
                'height': '5px', 'background': 'rgba(255,255,255,0.08)',
                'borderRadius': '3px', 'overflow': 'hidden',
            }, children=[
                html.Div(style={
                    'height': '100%', 'width': f'{pct:.0f}%',
                    'background': f'linear-gradient(90deg, {color}cc, {color})',
                    'borderRadius': '3px', 'transition': 'width 1s ease',
                }),
            ]),
            html.Small(
                '✓ Sobre mediana' if above else '✗ Bajo mediana',
                style={'color': color, 'fontSize': '10px', 'marginTop': '6px', 'display': 'block'},
            ),
        ], style={'padding': '16px 18px'}),
    ], className=f'h-100 animate-in {group_cls}'), md=3)


@dash.callback(
    Output('s8-roc',  'figure'),
    Output('s8-shap', 'figure'),
    Output('s8-reps', 'children'),
    Input('s8-init',  'n_intervals'),
)
def load_ml_8(_):
    reps_data = get_representativos_8()
    reps_row  = dbc.Row([_rep_card_8(d) for d in reps_data], className='g-3')
    return fig_roc(), fig_shap(), reps_row


@dash.callback(
    Output('s8-result', 'children'),
    Input('s8-btn', 'n_clicks'),
    State('s8-instr',       'value'),
    State('s8-school',      'value'),
    State('s8-grupo-nivel', 'value'),
    prevent_initial_call=True,
)
def predict(n, instr, school, grupo_nivel):
    prob = predict_salario(school, instr, 1, grupo_nivel or 2, 2023)
    color = '#00b4cc' if prob >= 50 else '#cf0a2c'
    verdict = 'sobre la mediana' if prob >= 50 else 'bajo la mediana'
    return html.Span(f'{prob:.1f}% de probabilidad — {verdict}', style={'color': color})


@dash.callback(
    Output('s8-instr',       'value'),
    Output('s8-school',      'value'),
    Output('s8-grupo-nivel', 'value'),
    Input('s8-pre-0', 'n_clicks'),
    Input('s8-pre-1', 'n_clicks'),
    Input('s8-pre-2', 'n_clicks'),
    Input('s8-pre-3', 'n_clicks'),
    prevent_initial_call=True,
)
def load_preset_8(_0, _1, _2, _3):
    from dash import ctx
    from dash.exceptions import PreventUpdate
    _PRESETS = {
        's8-pre-0': (7, 16, 4),   # Posgrado · Líder
        's8-pre-1': (6, 16, 3),   # Licenciatura · Avanzado
        's8-pre-2': (4, 12, 2),   # Preparatoria · Emprendedor
        's8-pre-3': (2,  6, 1),   # Primaria · Básico
    }
    trig = ctx.triggered_id
    if trig in _PRESETS:
        return _PRESETS[trig]
    raise PreventUpdate
