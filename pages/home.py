import dash
from dash import html, dcc, Input, Output, State

dash.register_page(__name__, path='/')

SECTIONS = [
    {
        'key': 'exploratorio', 'icon': '◈', 'label': 'EXPLORATORIO',
        'num': '01 – 04', 'tagline': 'Tendencias · Geografía · Categorías · Comparativo',
        'color': '#00b4cc', 'glow': 'rgba(0,180,204,0.22)',
        'bg': 'rgba(0,180,204,0.04)', 'border': 'rgba(0,180,204,0.25)',
        'slides': [
            {'num': 1, 'label': 'Tendencias',  'title': 'Evolución anual',
             'desc': 'Incidencia por entidad federativa · 2015–2024', 'href': '/slide_1'},
            {'num': 2, 'label': 'Geografía',   'title': 'Distribución estatal',
             'desc': 'Ranking de estados y municipios más afectados', 'href': '/slide_2'},
            {'num': 3, 'label': 'Categorías',  'title': 'Bienes jurídicos',
             'desc': 'Composición del crimen por tipo de delito', 'href': '/slide_3'},
            {'num': 4, 'label': 'Comparativo', 'title': 'Análisis temporal',
             'desc': 'Heatmap mensual, víctimas por sexo y variación', 'href': '/slide_4'},
        ],
    },
    {
        'key': 'profundo', 'icon': '◎', 'label': 'PROFUNDO',
        'num': '05 – 07 · 11', 'tagline': 'Economía · Digitalización · Percepción · Infra × Seguridad',
        'color': '#c9922a', 'glow': 'rgba(201,146,42,0.22)',
        'bg': 'rgba(201,146,42,0.04)', 'border': 'rgba(201,146,42,0.25)',
        'slides': [
            {'num': 5,  'label': 'Crimen × PIB',  'title': 'Economía y crimen',
             'desc': 'Correlación delito-crecimiento por estado', 'href': '/slide_5'},
            {'num': 6,  'label': 'Crimen × IDDE', 'title': 'Desarrollo digital',
             'desc': 'Digitalización vs tasas de criminalidad estatal', 'href': '/slide_6'},
            {'num': 7,  'label': 'ENVIPE',         'title': 'Percepción seguridad',
             'desc': 'Confianza institucional y gasto en protección', 'href': '/slide_7'},
            {'num': 11, 'label': 'Infra × Seg',    'title': 'Infra Digital × Seguridad',
             'desc': 'Correlaciones · Panel 2022-25 · K-Means k=4 · 134 variables', 'href': '/slide_11'},
        ],
    },
    {
        'key': 'modelos', 'icon': '⬡', 'label': 'MODELOS',
        'num': '08 – 10', 'tagline': 'ENOE · DENUE · Innovación Digital',
        'color': '#00b87a', 'glow': 'rgba(0,184,122,0.22)',
        'bg': 'rgba(0,184,122,0.04)', 'border': 'rgba(0,184,122,0.25)',
        'slides': [
            {'num': 8,  'label': 'ENOE · Modelo',   'title': 'Mercado laboral',
             'desc': 'Predicción salarial con Random Forest y XGBoost', 'href': '/slide_8'},
            {'num': 9,  'label': 'DENUE · Modelo',  'title': 'Densidad empresarial',
             'desc': 'Clasificación de estados · SHAP · Curvas ROC', 'href': '/slide_9'},
            {'num': 10, 'label': 'Análisis Modelo', 'title': 'Innovación vs Crimen',
             'desc': 'R²=0.77 · Clustering K-Means · PCA · Simulador', 'href': '/slide_10'},
        ],
    },
]


def _slide_card(s, color, border):
    return html.A(
        href=s['href'],
        style={
            'display': 'flex', 'flexDirection': 'column',
            'textDecoration': 'none', 'color': '#e8e8f0',
            'background': 'rgba(17,17,24,0.78)',
            'border': f'1px solid {border}',
            'borderTop': f'2px solid {color}',
            'borderRadius': '8px', 'overflow': 'hidden',
            'backdropFilter': 'blur(12px)',
            'transition': 'transform 260ms ease, box-shadow 260ms ease',
            'cursor': 'pointer',
        },
        children=[
            html.Div([
                html.Div([
                    html.Span(s['label'], style={
                        'fontSize': '9px', 'fontWeight': '700',
                        'letterSpacing': '0.14em', 'textTransform': 'uppercase',
                        'color': color,
                    }),
                    html.Span(f'{s["num"]:02d}', style={
                        'fontFamily': 'DM Mono, monospace', 'fontSize': '11px',
                        'color': f'{color}55',
                    }),
                ], style={'display': 'flex', 'justifyContent': 'space-between',
                          'marginBottom': '6px'}),
                html.P(s['title'], style={
                    'fontSize': '14px', 'fontWeight': '600', 'color': '#e8e8f0',
                    'letterSpacing': '-0.01em', 'margin': '0 0 4px',
                }),
                html.P(s['desc'], style={
                    'fontSize': '11px', 'color': '#5c5c74',
                    'lineHeight': '1.55', 'margin': '0', 'flex': '1',
                }),
            ], style={'padding': '14px 16px 10px', 'flex': '1'}),
            html.Span('→', style={
                'display': 'block', 'fontSize': '14px', 'color': color,
                'padding': '7px 16px 9px',
                'borderTop': '1px solid rgba(255,255,255,0.06)',
            }),
        ],
    )


def _section_panel(s):
    color  = s['color']
    border = s['border']
    grid_cls = 'sec-slides-grid' if len(s['slides']) == 4 else 'sec-slides-grid grid-3'
    return html.Div([
        html.Div([
            html.Div([
                html.Span(s['icon'], style={
                    'fontSize': '26px', 'marginRight': '12px', 'opacity': '0.85',
                }),
                html.Div([
                    html.Span(s['label'], className='sec-label', style={'color': color}),
                    html.P(s['tagline'], className='sec-tagline'),
                ]),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Span(s['num'], style={
                'fontFamily': 'DM Mono, monospace', 'fontSize': '12px',
                'color': color, 'opacity': '0.6', 'fontWeight': '500',
                'border': f'1px solid {color}55', 'padding': '2px 10px',
                'borderRadius': '12px',
            }),
        ], style={'display': 'flex', 'justifyContent': 'space-between',
                  'alignItems': 'center', 'marginBottom': '16px'}),
        html.Div(
            [_slide_card(slide, color, border) for slide in s['slides']],
            className=grid_cls,
        ),
    ], className='section-panel', style={'padding': '0 12px'})


layout = html.Div(
    className='intro-root',
    children=[
        html.Div(className='intro-bg',
                 style={'backgroundImage': "url('/assets/hero-bg.jpg')"}),
        html.Div(className='intro-overlay'),
        html.Div(
            className='intro-content',
            children=[
                html.Div(
                    className='intro-hero-text animate-in',
                    children=[
                        html.P('Panel de Seguridad Pública · México',
                               className='intro-eyebrow'),
                        html.H1(
                            ['Datos que revelan', html.Br(),
                             'el panorama de seguridad'],
                            className='intro-titulo',
                        ),
                        html.P(
                            'Transformamos datos oficiales de seguridad en conocimiento '
                            'claro y accionable para apoyar decisiones basadas en evidencia.',
                            className='intro-subtitulo',
                        ),
                    ],
                ),

                dcc.Store(id='home-section', data=0),

                html.Div([
                    html.Div([
                        html.Div(
                            [_section_panel(s) for s in SECTIONS],
                            id='carousel-track',
                            className='carousel-track',
                        ),
                    ], className='carousel-viewport'),

                    html.Div([
                        html.Button('←', id='home-prev', className='carousel-btn',
                                    n_clicks=0),
                        html.Div([
                            html.Button(
                                '', id=f'home-dot-{i}', n_clicks=0,
                                className='carousel-dot active' if i == 0 else 'carousel-dot',
                                style={
                                    'background': SECTIONS[i]['color'] if i == 0
                                    else 'rgba(255,255,255,0.2)',
                                },
                            )
                            for i in range(len(SECTIONS))
                        ], style={'display': 'flex', 'gap': '8px', 'alignItems': 'center'}),
                        html.Button('→', id='home-next', className='carousel-btn',
                                    n_clicks=0),
                    ], className='carousel-nav'),
                ], style={'width': '100%', 'maxWidth': '1120px'}),
            ],
        ),
    ],
)


@dash.callback(
    Output('home-section', 'data'),
    Input('home-prev',   'n_clicks'),
    Input('home-next',   'n_clicks'),
    Input('home-dot-0',  'n_clicks'),
    Input('home-dot-1',  'n_clicks'),
    Input('home-dot-2',  'n_clicks'),
    State('home-section', 'data'),
    prevent_initial_call=True,
)
def navigate_section(_prev, _nxt, _d0, _d1, _d2, current):
    from dash import ctx
    trig = ctx.triggered_id
    if trig == 'home-prev':
        return max(0, current - 1)
    if trig == 'home-next':
        return min(len(SECTIONS) - 1, current + 1)
    if trig == 'home-dot-0':
        return 0
    if trig == 'home-dot-1':
        return 1
    if trig == 'home-dot-2':
        return 2
    return current


@dash.callback(
    Output('carousel-track', 'style'),
    Output('home-prev', 'disabled'),
    Output('home-next', 'disabled'),
    Input('home-section', 'data'),
)
def update_track(idx):
    pct = idx * (100 / len(SECTIONS))
    return (
        {
            'display': 'flex', 'width': '300%',
            'transform': f'translateX(-{pct:.4f}%)',
            'transition': 'transform 400ms cubic-bezier(0.4,0,0.2,1)',
        },
        idx == 0,
        idx == len(SECTIONS) - 1,
    )


@dash.callback(
    Output('home-dot-0', 'className'),
    Output('home-dot-1', 'className'),
    Output('home-dot-2', 'className'),
    Output('home-dot-0', 'style'),
    Output('home-dot-1', 'style'),
    Output('home-dot-2', 'style'),
    Input('home-section', 'data'),
)
def update_dots(idx):
    classes = []
    styles  = []
    for i, s in enumerate(SECTIONS):
        if i == idx:
            classes.append('carousel-dot active')
            styles.append({
                'background': s['color'],
                'width': '8px', 'height': '8px', 'borderRadius': '50%',
                'border': 'none', 'cursor': 'pointer',
                'transform': 'scale(1.35)', 'transition': 'all 220ms ease',
                'padding': '0',
            })
        else:
            classes.append('carousel-dot')
            styles.append({
                'background': 'rgba(255,255,255,0.2)',
                'width': '8px', 'height': '8px', 'borderRadius': '50%',
                'border': 'none', 'cursor': 'pointer',
                'transition': 'all 220ms ease',
                'padding': '0',
            })
    return (*classes, *styles)
