import traceback
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from pages.components import sidebar
from pages.get_data.get_data_inversion import (
    get_estados_list, get_state_profile, get_state_investment_table,
    _CLUSTER_INVESTMENT,
)

dash.register_page(__name__, path='/slide_perfil_estado')

_CFG = {'displayModeBar': False, 'responsive': True}
_DEFAULT_ESTADO = 'Ciudad de México'

_CLUSTER_CLASSES = {'C0': 'card-danger', 'C1': 'card-cyan', 'C2': 'card-success', 'C3': 'card-gold'}


def _safe(fn):
    try:
        return fn()
    except Exception:
        traceback.print_exc()
        return go.Figure()


estados = get_estados_list()

layout = html.Div([
    sidebar('/slide_perfil_estado'),

    html.Div([

        # ── Page header ──────────────────────────────────────────────
        html.Div([
            html.Div(className='page-accent-line'),
            html.H1('Diagnóstico Ejecutivo · Perfil por Estado', className='page-title'),
            html.P(
                'Selecciona cualquier estado para ver su cluster de inversión, brecha de IDDE, '
                'retorno proyectado y posicionamiento frente a la media nacional y su cluster',
                className='page-subtitle',
            ),
            html.Div([
                html.Span('32 estados', className='badge-gray me-2'),
                html.Span('K-Means k=4', className='badge-cyan me-2'),
                html.Span('Datos IDDE 2025 + ENOE + ENVIPE', className='badge-gold'),
            ]),
        ], className='page-header'),

        # ── Scrollable body ──────────────────────────────────────────
        html.Div([

            # State selector
            html.Div([
                html.Label('Selecciona un estado', style={
                    'fontSize': '10px', 'fontWeight': '700', 'color': '#5c5c74',
                    'textTransform': 'uppercase', 'letterSpacing': '0.12em',
                    'marginBottom': '6px', 'display': 'block',
                }),
                dcc.Dropdown(
                    id='sperfil-dd-estado',
                    options=[{'label': e, 'value': e} for e in estados],
                    value=_DEFAULT_ESTADO,
                    clearable=False,
                    style={'width': '320px'},
                    className='dash-dropdown',
                ),
            ], className='filter-bar', style={'marginBottom': '20px'}),

            # Dynamic profile content
            html.Div(id='sperfil-content'),

        ], className='main-scroll'),

    ], className='main-content'),
], className='page-root')


def _build_profile_layout(estado):
    profile = get_state_profile(estado)
    if profile is None:
        return html.P('Estado no encontrado.', style={'color': '#5c5c74'})

    code  = profile['cluster_code']
    color = profile['cluster_color']
    name  = profile['cluster_name']
    cls   = _CLUSTER_CLASSES.get(code, 'card-cyan')
    inv   = _CLUSTER_INVESTMENT.get(code, {})

    pct_inseguro = round((1 - profile['percepcion_segura']) * 100, 1) if profile['percepcion_segura'] else 0

    # KPI cards
    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.P('IDDE 2025', className='insight-title'),
                html.H2(f'{profile["idde"]:.1f}',
                        style={'color': color, 'fontWeight': '800', 'margin': '4px 0'}),
                html.P(f'Media nacional: {profile["idde_national_mean"]:.1f}',
                       className='insight-desc'),
            ], style={'padding': '14px 16px', 'textAlign': 'center'}),
        ], className=f'card-clean animate-in h-100 {cls}'), md=3),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.P('Posición nacional', className='insight-title'),
                html.H2(f'#{profile["national_rank"]}',
                        style={'color': color, 'fontWeight': '800', 'margin': '4px 0'}),
                html.P('de 32 estados en IDDE', className='insight-desc'),
            ], style={'padding': '14px 16px', 'textAlign': 'center'}),
        ], className='card-clean animate-in h-100 card-cyan animate-in-delay-1'), md=3),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.P('Brecha al nivel C2', className='insight-title'),
                html.H2(
                    '✓ Desarrollado' if code == 'C2' else f'+{profile["gap_to_c2"]:.1f} pts',
                    style={'color': '#00b87a' if code == 'C2' else '#c9922a',
                           'fontWeight': '800', 'margin': '4px 0'},
                ),
                html.P(
                    'Ya en perfil Desarrollado' if code == 'C2' else 'para alcanzar perfil Desarrollado',
                    className='insight-desc',
                ),
            ], style={'padding': '14px 16px', 'textAlign': 'center'}),
        ], className='card-clean animate-in h-100 card-gold animate-in-delay-2'), md=3),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.P('Ganancia salarial proyectada', className='insight-title'),
                html.H2(
                    '—' if code == 'C2' else f'${profile["projected_wage_gain"]:,.0f}',
                    style={'color': '#00b87a', 'fontWeight': '800', 'margin': '4px 0'},
                ),
                html.P(
                    'ya en nivel de referencia' if code == 'C2' else 'si cierra brecha a C2',
                    className='insight-desc',
                ),
            ], style={'padding': '14px 16px', 'textAlign': 'center'}),
        ], className='card-clean animate-in h-100 card-success animate-in-delay-3'), md=3),
    ], className='g-3 mb-3')

    # Cluster profile card
    cluster_card = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(f'{code} · {name}', style={
                    'fontWeight': '800', 'fontSize': '14px', 'color': color,
                    'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                }),
            ], style={'marginBottom': '10px'}),
            html.P(inv.get('description', ''),
                   style={'fontSize': '12px', 'color': '#c8c8d8', 'lineHeight': '1.6',
                          'marginBottom': '8px'}),
            html.Div([
                html.Span('Prioridad de inversión: ', style={
                    'fontSize': '10px', 'fontWeight': '700', 'color': '#5c5c74',
                    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                }),
                html.Span(inv.get('priority', ''), style={
                    'fontSize': '11px', 'color': color, 'fontWeight': '600',
                }),
            ]),
            html.Div([
                html.Span('Tipo de retorno: ', style={
                    'fontSize': '10px', 'fontWeight': '700', 'color': '#5c5c74',
                    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
                }),
                html.Span(inv.get('roi_label', ''), style={
                    'fontSize': '11px', 'color': '#00b87a', 'fontWeight': '600',
                }),
            ], style={'marginTop': '4px'}),
            html.Div([
                html.Span(f'Percepción: {100 - pct_inseguro:.0f}% se siente seguro · ', style={
                    'fontSize': '10px', 'color': '#5c5c74',
                }),
                html.Span(f'Salario promedio: ${profile["avg_wage"]:,.0f}/mes', style={
                    'fontSize': '10px', 'color': '#5c5c74',
                }),
            ], style={'marginTop': '8px'}),
        ], style={'padding': '16px'}),
    ], style={'border': f'2px solid {color}', 'borderRadius': '8px',
              'background': '#16161f'})

    # Insight sentence
    if code == 'C2':
        _insight_text = (
            f'{estado} ya pertenece al perfil Desarrollado-seguro (C2). '
            f'IDDE actual: {profile["idde"]:.1f} pts — posición #{profile["national_rank"]} nacional. '
            f'Mantener la inversión para consolidar el liderazgo digital.'
        )
    else:
        _insight_text = (
            f'Aumentar {profile["gap_to_c2"]:.1f} pts de IDDE proyecta '
            f'${profile["projected_wage_gain"]:,.0f}/mes de ganancia salarial '
            f'y fortalecería la confianza social al nivel del cluster C2.'
        )

    insight = html.Div([
        html.Span('◈ ', style={'color': color, 'fontWeight': '700'}),
        html.Span(
            _insight_text,
            style={'fontSize': '12px', 'color': '#c8c8d8', 'lineHeight': '1.6'},
        ),
    ], style={
        'background': f'{color}11',
        'border': f'1px solid {color}44',
        'borderRadius': '8px', 'padding': '12px 16px', 'marginBottom': '16px',
    })

    # Radar chart
    radar_row = dbc.Row([
        dbc.Col(dbc.Card([
            html.P('Perfil multidimensional · Estado vs cluster vs media nacional',
                   className='chart-label'),
            html.P('6 dimensiones normalizadas 0–1: IDDE, velocidad móvil, '
                   'usuarios internet, salario, percepción de seguridad, confianza social',
                   className='chart-desc'),
            dbc.CardBody(
                dcc.Graph(
                    id='sperfil-radar',
                    config=_CFG,
                    style={'height': '380px'},
                ),
                style={'padding': '6px 8px 10px'},
            ),
        ], className='card-clean card-pop animate-in card-expandable'), md=6),

        dbc.Col(dbc.Card([
            html.P('Posición en el ranking nacional de IDDE', className='chart-label'),
            html.P('Todos los estados ordenados por IDDE 2025 — posición del estado seleccionado resaltada',
                   className='chart-desc'),
            dbc.CardBody(
                dcc.Graph(
                    id='sperfil-ranking',
                    config=_CFG,
                    style={'height': '380px'},
                ),
                style={'padding': '6px 8px 10px'},
            ),
        ], className='card-clean card-pop animate-in card-expandable'), md=6),
    ], className='g-3 mb-4')

    return html.Div([kpi_cards, cluster_card, html.Div(style={'height': '12px'}), insight, radar_row])


@dash.callback(
    Output('sperfil-content', 'children'),
    Input('sperfil-dd-estado', 'value'),
)
def update_profile(estado):
    if not estado:
        return html.P('Selecciona un estado.', style={'color': '#5c5c74'})
    return _build_profile_layout(estado)


@dash.callback(
    Output('sperfil-radar',   'figure'),
    Output('sperfil-ranking', 'figure'),
    Input('sperfil-dd-estado', 'value'),
)
def update_charts(estado):
    if not estado:
        return go.Figure(), go.Figure()

    from pages.get_figures.get_figures_inversion import fig_state_radar
    from pages.get_data.get_data_11 import get_data_11, _IDDE_COL

    radar = _safe(lambda: fig_state_radar(estado))

    # Ranking chart — horizontal bars colored by cluster
    try:
        d = get_data_11()
        cross_cl = d['cross_cl'].copy().sort_values(_IDDE_COL, ascending=True)
        is_selected = cross_cl['estado'] == estado

        colors = [
            row['cluster_color'] if row['estado'] != estado else '#ffffff'
            for _, row in cross_cl.iterrows()
        ]
        sizes = [9 if row['estado'] != estado else 12
                 for _, row in cross_cl.iterrows()]

        ranking_fig = go.Figure(go.Bar(
            x=cross_cl[_IDDE_COL],
            y=cross_cl['estado'],
            orientation='h',
            marker=dict(
                color=colors,
                opacity=[1.0 if e == estado else 0.55 for e in cross_cl['estado']],
            ),
            text=cross_cl[_IDDE_COL].round(1),
            textposition='outside',
            textfont=dict(size=8),
            hovertemplate='%{y}: IDDE %{x:.1f}<extra></extra>',
        ))
        ranking_fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Sans, sans-serif', color='#c8c8d8', size=9),
            margin=dict(l=12, r=40, t=28, b=12),
            xaxis=dict(title='IDDE 2025', gridcolor='rgba(255,255,255,0.06)', range=[0, cross_cl[_IDDE_COL].max() * 1.2]),
            yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=8)),
            title=dict(text=f'Posición nacional · {estado} resaltado', font=dict(size=11), x=0.01),
        )
    except Exception:
        traceback.print_exc()
        ranking_fig = go.Figure()

    return radar, ranking_fig
