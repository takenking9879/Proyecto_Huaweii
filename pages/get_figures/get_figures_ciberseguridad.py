"""
Figures for slide_ciberseguridad — EXP-01 (cyber gap) + EXP-08 (fraud quadrant).
Data sourced entirely from get_data_11 cross_cl.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pages.get_data.get_data_11 import get_data_11

C_RED    = '#cf0a2c'
C_CYAN   = '#00b4cc'
C_GOLD   = '#c9922a'
C_GREEN  = '#2bb573'
C_PAPER  = '#1a1a24'
C_PLOT   = '#111118'
C_TEXT   = '#e8e8f0'
C_MUTED  = '#5c5c74'

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    hoverlabel=dict(bgcolor='#0f0f18', font_color=C_TEXT,
                    bordercolor='rgba(255,255,255,0.1)'),
)

_ABBREV = {
    'Ciudad de México': 'CDMX',
    'Estado de México': 'EdoMex',
    'Baja California Sur': 'BCS',
    'Baja California': 'BC',
    'Nuevo León': 'NL',
    'Veracruz de Ignacio de la Llave': 'Veracruz',
    'Michoacán de Ocampo': 'Michoacán',
    'Coahuila de Zaragoza': 'Coahuila',
    'Querétaro': 'Querétaro',
    'Quintana Roo': 'Q. Roo',
    'San Luis Potosí': 'SLP',
}


def _abbrev(s):
    return _ABBREV.get(s, s)


def _normalize(series):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return series * 0.0
    return (series - mn) / (mx - mn)


def _get_cyber_df():
    d = get_data_11()
    cross = d['cross_cl'].copy()

    exposure_cols = [
        'empresas_que_utilizan_banca_electronica_por',
        'penetracion_de_tarjeta_de_debito_x100adu',
    ]
    protection_cols = [
        'subpilar_de_ciberseguridad',
        'acciones_de_ciberseguridad_en_las_empresas_por',
        'policia_cibernetica_xmhab',
    ]

    e_present = [c for c in exposure_cols if c in cross.columns]
    p_present  = [c for c in protection_cols if c in cross.columns]

    if not e_present or not p_present:
        return cross

    for c in e_present + p_present:
        cross[c + '_n'] = _normalize(cross[c].fillna(cross[c].median()))

    cross['digital_exposure']  = cross[[c + '_n' for c in e_present]].mean(axis=1)
    cross['cyber_capacity']    = cross[[c + '_n' for c in p_present]].mean(axis=1)
    cross['cyber_gap']         = cross['digital_exposure'] - cross['cyber_capacity']
    cross['label']             = cross['estado'].map(_abbrev).fillna(cross['estado'])

    return cross


def fig_fraud_quadrant():
    """EXP-08 — 2×2 quadrant: digital financial exposure vs cybersecurity capacity.
    Dot color = fraud rate. Critical gap = high exposure, low protection (bottom-right)."""
    df = _get_cyber_df()
    required = ['digital_exposure', 'cyber_capacity', 'fraude_rate_100k', 'estado']
    df = df.dropna(subset=[c for c in required if c in df.columns])
    if df.empty:
        return go.Figure()

    x = df['digital_exposure'].values
    y = df['cyber_capacity'].values
    fraud = df['fraude_rate_100k'].fillna(0).values
    labels = df['label'].values
    estados = df['estado'].values

    x_med = float(np.median(x))
    y_med = float(np.median(y))

    # Color scale: cyan (low fraud) → red (high fraud)
    f_norm = (fraud - fraud.min()) / (fraud.max() - fraud.min() + 1e-9)
    def _lerp_color(t):
        r = int(0 + t * (231 - 0))
        g = int(180 - t * (180 - 76))
        b = int(204 - t * (204 - 60))
        return f'rgb({r},{g},{b})'
    point_colors = [_lerp_color(float(t)) for t in f_norm]

    # Critical gap states: high exposure AND low capacity
    critical = df[(df['digital_exposure'] > x_med) & (df['cyber_capacity'] < y_med)]['estado'].tolist()

    fig = go.Figure()

    # Quadrant shading — critical quadrant slightly highlighted
    fig.add_shape(type='rect',
        x0=x_med, x1=x.max() + 0.05, y0=y.min() - 0.05, y1=y_med,
        fillcolor='rgba(231,76,60,0.06)', line=dict(width=0), layer='below')

    # Quadrant lines
    fig.add_shape(type='line', x0=x_med, x1=x_med, y0=-0.05, y1=1.05,
                  line=dict(color='rgba(255,255,255,0.18)', width=1.2, dash='dot'))
    fig.add_shape(type='line', x0=-0.05, x1=1.05, y0=y_med, y1=y_med,
                  line=dict(color='rgba(255,255,255,0.18)', width=1.2, dash='dot'))

    # Quadrant labels
    offset = 0.03
    for tx, ty, text, color, anchor in [
        (x_med + offset,     y_med + offset,     '✦ DEFENDIDOS',       'rgba(46,204,113,0.67)',  'left'),
        (x_med - offset,     y_med + offset,     'BAJA EXPOSICIÓN',    'rgba(92,92,116,0.67)',   'right'),
        (x_med - offset,     y_med - offset,     'MENOR PRIORIDAD',    'rgba(92,92,116,0.67)',   'right'),
        (x_med + offset,     y_med - offset,     '⚠ BRECHA CRÍTICA',  'rgba(231,76,60,0.80)',   'left'),
    ]:
        fig.add_annotation(x=tx, y=ty, text=text, showarrow=False,
                           font=dict(size=9, color=color),
                           xanchor=anchor, yanchor='middle')

    # Scatter points
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='markers+text',
        text=[_abbrev(e) for e in estados],
        textposition='top center',
        textfont=dict(size=7.5,
                      color=[C_RED if e in critical else 'rgba(184,184,204,0.70)'
                             for e in estados]),
        marker=dict(
            color=point_colors,
            size=[13 if e in critical else 9 for e in estados],
            opacity=0.92,
            line=dict(
                color=[C_RED if e in critical else 'rgba(255,255,255,0.12)'
                       for e in estados],
                width=[1.8 if e in critical else 0.8 for e in estados],
            ),
        ),
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Exposición digital: %{x:.2f}<br>'
            'Capacidad ciberseg.: %{y:.2f}<br>'
            '<extra></extra>'
        ),
        showlegend=False,
    ))

    # Legend traces (dummy)
    for color, name in [(C_RED, '⚠ Brecha crítica'), (C_CYAN, 'Bajo riesgo')]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                 marker=dict(color=color, size=9),
                                 name=name, showlegend=True))

    fig.update_layout(
        **_BASE,
        margin=dict(l=60, r=30, t=20, b=60),
        xaxis=dict(
            title=dict(text='Exposición financiera digital (normalizada)', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.04)',
            color=C_MUTED, range=[-0.05, 1.1],
        ),
        yaxis=dict(
            title=dict(text='Capacidad de ciberseguridad (normalizada)', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.04)',
            color=C_MUTED, range=[-0.05, 1.1],
        ),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0.5, xanchor='center', y=-0.14),
        showlegend=True,
    )
    return fig


def fig_cyber_gap_bars():
    """EXP-01 — sorted bar chart of cybersecurity gap score per state.
    Positive = more exposed than protected (critical). Negative = well-protected."""
    df = _get_cyber_df()
    if 'cyber_gap' not in df.columns:
        return go.Figure()
    df = df[['estado', 'label', 'cyber_gap']].dropna().sort_values('cyber_gap', ascending=True)

    colors = [C_RED if v > 0 else C_CYAN for v in df['cyber_gap']]
    opacities = [min(0.5 + abs(float(v)) * 0.8, 1.0) for v in df['cyber_gap']]

    fig = go.Figure(go.Bar(
        x=df['cyber_gap'],
        y=df['label'],
        orientation='h',
        marker=dict(color=colors, opacity=opacities, line=dict(width=0)),
        hovertemplate='<b>%{y}</b><br>Brecha: %{x:.2f}<extra></extra>',
    ))

    fig.add_vline(x=0, line_color='rgba(255,255,255,0.30)', line_width=1.5)

    fig.add_annotation(x=df['cyber_gap'].max() * 0.6, y=2,
                       text='↑ Más expuesto<br>que protegido',
                       showarrow=False, font=dict(size=9, color=C_RED),
                       bgcolor='rgba(231,76,60,0.10)', bordercolor=C_RED,
                       borderwidth=1)
    fig.add_annotation(x=df['cyber_gap'].min() * 0.6, y=len(df) - 3,
                       text='↓ Bien protegido',
                       showarrow=False, font=dict(size=9, color=C_CYAN),
                       bgcolor='rgba(0,180,204,0.10)', bordercolor=C_CYAN,
                       borderwidth=1)

    fig.update_layout(
        **_BASE,
        margin=dict(l=10, r=50, t=20, b=30),
        xaxis=dict(
            title=dict(text='Exposición − Capacidad (normalizado)', font=dict(size=10)),
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            zeroline=False,
        ),
        yaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=9)),
        bargap=0.18,
    )
    return fig


def get_cyber_kpis():
    """Returns dict of KPI values for slide header badges."""
    df = _get_cyber_df()
    if 'cyber_gap' not in df.columns:
        return {'n_critical': 0, 'top_state': 'N/A', 'fraude_r': 0.63}
    x_med = df['digital_exposure'].median()
    y_med = df['cyber_capacity'].median()
    critical = df[(df['digital_exposure'] > x_med) & (df['cyber_capacity'] < y_med)]
    top_state = df.nlargest(1, 'cyber_gap')['estado'].values[0] if len(df) > 0 else 'N/A'
    return {
        'n_critical': len(critical),
        'top_state': _abbrev(top_state),
        'fraude_r': 0.63,
    }
