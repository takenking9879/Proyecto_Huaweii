import dash
from dash import html
import dash_bootstrap_components as dbc
from pages.components import sidebar

dash.register_page(__name__, path='/slide_cta')


def _step_card(num, title, subtitle, bullets, color, cls, delay=''):
    bullet_items = [
        html.Li(b, style={'fontSize': '11.5px', 'color': '#b8b8cc',
                          'lineHeight': '1.6', 'marginBottom': '4px'})
        for b in bullets
    ]
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(num, style={
                    'fontFamily': 'DM Mono, monospace',
                    'fontSize': '28px', 'fontWeight': '800', 'color': color,
                    'opacity': '0.25', 'marginRight': '12px', 'lineHeight': '1',
                }),
                html.Div([
                    html.P(title, style={
                        'fontWeight': '700', 'fontSize': '13px', 'color': color,
                        'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                        'margin': '0 0 2px',
                    }),
                    html.P(subtitle, style={
                        'fontSize': '11px', 'color': '#5c5c74', 'margin': '0',
                    }),
                ]),
            ], style={'display': 'flex', 'alignItems': 'flex-start', 'marginBottom': '12px'}),
            html.Ul(bullet_items, style={'paddingLeft': '16px', 'margin': '0'}),
        ], style={'padding': '20px 22px'}),
    ], className=f'animate-in h-100 {cls} {delay}'.strip())


def _tier_card(code, name, color, states_ex, investment, returns, delay=''):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(code, style={
                    'fontFamily': 'DM Mono, monospace',
                    'fontSize': '22px', 'fontWeight': '800', 'color': color,
                    'marginRight': '8px',
                }),
                html.Span(name, style={
                    'fontSize': '11px', 'fontWeight': '600', 'color': color,
                    'textTransform': 'uppercase', 'letterSpacing': '0.06em',
                }),
            ], style={'marginBottom': '8px'}),
            html.P(states_ex, style={'fontSize': '10px', 'color': '#5c5c74', 'marginBottom': '8px'}),
            html.Div([
                html.Span('Inversión prioritaria: ', style={
                    'fontSize': '9px', 'fontWeight': '700', 'color': '#5c5c74',
                    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                }),
                html.Span(investment, style={'fontSize': '11px', 'color': color}),
            ], style={'marginBottom': '4px'}),
            html.Div([
                html.Span('Retorno esperado: ', style={
                    'fontSize': '9px', 'fontWeight': '700', 'color': '#5c5c74',
                    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                }),
                html.Span(returns, style={'fontSize': '11px', 'color': '#00b87a'}),
            ]),
        ], style={'padding': '14px 16px'}),
    ], style={'border': f'1px solid {color}44', 'borderTop': f'2px solid {color}',
              'borderRadius': '8px', 'background': '#16161f', 'height': '100%'},
    className=f'animate-in {delay}')


layout = html.Div([
    sidebar('/slide_cta'),

    html.Div([

        # ── Page header ──────────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('De los Datos a la Acción', className='page-title'),
            html.P(
                'La evidencia está clara: la brecha digital es la mayor oportunidad de desarrollo '
                'en México. Aquí está el camino de tres fases para convertirla en resultados.',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('32 estados · 4 perfiles', className='badge-gray me-2'),
                html.Span('3 fases de acción', className='badge-cyan me-2'),
                html.Span('Piloto en 90 días', className='badge-green'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────────
        html.Div([

            html.P(
                'Los análisis de este dashboard demuestran que el IDDE predice salarios (R²=0.29), '
                'confianza social (r=0.78) y percepción de seguridad. Los 4 perfiles de inversión '
                'definen dónde invertir y qué tipo de retorno esperar. La siguiente pregunta no es '
                '"¿vale la pena?" — los datos responden que sí. La pregunta es "¿por dónde empezamos?"',
                className='page-context',
            ),

            # 3-step framework
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Hoja de ruta de 3 fases', className='section-block-title'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(_step_card(
                    '01', 'Diagnóstico', 'Completado · Este dashboard',
                    [
                        '32 estados analizados con 134 variables del IDDE',
                        '4 perfiles identificados con K-Means (k=4)',
                        'Correlaciones IDDE → salarios, confianza y percepción validadas',
                        'ROI proyectado por cluster disponible por estado',
                    ],
                    '#00b4cc', 'card-cyan',
                ), md=4),

                dbc.Col(_step_card(
                    '02', 'Diseño de inversión', 'Semanas 1–8 · Selección y priorización',
                    [
                        'Selección de estados piloto por perfil de inversión (uno por cluster)',
                        'Definición de indicadores clave: IDDE target, salario meta, confianza base',
                        'Diseño de solución técnica por perfil',
                        'Acuerdo de gobernanza y mecanismo de medición',
                    ],
                    '#c9922a', 'card-gold', 'animate-in-delay-1',
                ), md=4),

                dbc.Col(_step_card(
                    '03', 'Piloto de 90 días', 'Mes 3–5 · Implementación y medición',
                    [
                        'Despliegue de infraestructura en 1–2 estados por perfil',
                        'Medición mensual: IDDE, salarios formales, percepción ciudadana',
                        'Ajuste de modelo y proyecciones con datos reales',
                        'Informe ejecutivo para escalar a los demás estados del cluster',
                    ],
                    '#00b87a', 'card-success', 'animate-in-delay-2',
                ), md=4),
            ], className='g-3 mb-3'),

            # Investment tiers
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('4 perfiles · 4 estrategias de inversión', className='section-block-title'),
                html.P(
                    'Cada cluster tiene una estrategia diferenciada. No hay una solución única para los 32 estados.',
                    className='section-block-subtitle'),
            ], className='section-block-header'),

            dbc.Row([
                dbc.Col(_tier_card(
                    'C0', 'Tradicionales', '#d15b4a',
                    'Guerrero · Chiapas · Oaxaca + 4 estados',
                    'Conectividad básica: fibra, cobertura móvil, banda ancha fija',
                    'Máximo ROI por peso: mayor brecha → mayor retorno en salarios y visibilidad',
                ), md=3),
                dbc.Col(_tier_card(
                    'C1', 'Inseguros-urbanos', '#3891c7',
                    'CDMX · Estado de México · Jalisco + 3 estados',
                    'Gobernanza digital y analítica avanzada',
                    'Recuperación de confianza ciudadana e institucional',
                    'animate-in-delay-1',
                ), md=3),
                dbc.Col(_tier_card(
                    'C2', 'Desarrollados', '#2bb573',
                    'Nuevo León · Baja California + 5 estados',
                    'Infraestructura avanzada: 5G, nube, centros de datos',
                    'Productividad y competitividad internacional',
                    'animate-in-delay-2',
                ), md=3),
                dbc.Col(_tier_card(
                    'C3', 'Violentos-conectados', '#e4982e',
                    'Colima · Zacatecas + 2 estados',
                    'Tecnología especializada: datos + instituciones',
                    'Reducción de homicidios vía capacidad institucional',
                    'animate-in-delay-3',
                ), md=3),
            ], className='g-3 mb-3'),

            # Contact placeholder
            html.Div([
                html.Div(className='section-accent-cyan'),
                html.H3('Siguiente paso', className='section-block-title'),
            ], className='section-block-header'),

            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P('¿Tu estado en qué perfil está?', style={
                                'fontWeight': '700', 'fontSize': '14px', 'color': '#e8e8f0',
                                'marginBottom': '8px',
                            }),
                            html.P(
                                'Usa el módulo "Perfil de Estado" de este dashboard para ver tu diagnóstico '
                                'ejecutivo: cluster de inversión, IDDE actual, brecha al nivel C2 '
                                'y proyección de retorno personalizada.',
                                style={'fontSize': '12px', 'color': '#b8b8cc', 'lineHeight': '1.6',
                                       'marginBottom': '12px'},
                            ),
                            html.A(
                                '→ Ver perfil por estado',
                                href='/slide_perfil_estado',
                                style={
                                    'color': '#00b4cc', 'fontSize': '12px', 'fontWeight': '600',
                                    'textDecoration': 'none',
                                    'border': '1px solid #00b4cc44',
                                    'padding': '6px 14px', 'borderRadius': '6px',
                                    'display': 'inline-block',
                                },
                            ),
                        ], md=8),
                        dbc.Col([
                            html.Div([
                                html.P('Datos utilizados', style={
                                    'fontSize': '9px', 'fontWeight': '700', 'color': '#5c5c74',
                                    'textTransform': 'uppercase', 'letterSpacing': '0.10em',
                                    'marginBottom': '8px',
                                }),
                                html.Ul([
                                    html.Li('IDDE 2022–2025 (IFT)', style={'fontSize': '10px', 'color': '#5c5c74'}),
                                    html.Li('SESNSP — Incidencia delictiva 2015–2025', style={'fontSize': '10px', 'color': '#5c5c74'}),
                                    html.Li('ENVIPE — Percepción y confianza ciudadana', style={'fontSize': '10px', 'color': '#5c5c74'}),
                                    html.Li('ENOE — Mercado laboral y salarios', style={'fontSize': '10px', 'color': '#5c5c74'}),
                                    html.Li('DENUE — Directorio de unidades económicas', style={'fontSize': '10px', 'color': '#5c5c74'}),
                                ], style={'paddingLeft': '14px', 'margin': '0'}),
                            ]),
                        ], md=4),
                    ]),
                ], style={'padding': '20px 24px'}),
            ], className='card-clean animate-in', style={'marginBottom': '32px'}),

        ], className='main-scroll'),

    ], className='main-content'),
], className='page-root')
