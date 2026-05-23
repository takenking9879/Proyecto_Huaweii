import plotly.graph_objects as go
from pages.get_data.get_data_4 import (
    get_heatmap_data, get_victimas_sexo, get_comparativa_anios, MESES_NOMBRES,
)

C_RED   = '#cf0a2c'
C_CYAN  = '#00b4cc'
C_GOLD  = '#c9922a'
C_GREEN = '#00b87a'
C_GRAY  = '#9090a8'
C_PAPER = '#1a1a24'
C_PLOT  = '#111118'
C_TEXT  = '#e8e8f0'
C_MUTED = '#5c5c74'

FILL_SEXO = {
    'Hombre': 'rgba(0,180,204,0.08)',
    'Mujer':  'rgba(207,10,44,0.08)',
}

_BASE = dict(
    paper_bgcolor = C_PAPER,
    plot_bgcolor  = C_PLOT,
    font          = dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin        = dict(l=10, r=10, t=10, b=10),
    hoverlabel    = dict(bgcolor=C_PAPER, font_color=C_TEXT, font_family='DM Sans'),
)

# ── 1. Heatmap mes × año ─────────────────────────────────────────
def fig_heatmap(estado=None):
    mat = get_heatmap_data(estado)
    z   = mat.values.tolist()
    x   = [str(c) for c in mat.columns]
    y   = [MESES_NOMBRES[i] for i in mat.index]
    fig = go.Figure(go.Heatmap(
        z         = z,
        x         = x,
        y         = y,
        colorscale = [
            [0.00, '#0a0a0f'],
            [0.35, '#3d0614'],
            [0.65, '#7a0619'],
            [1.00, '#ff1a3e'],
        ],
        hovertemplate = '<b>%{y} %{x}</b><br>%{z:,.0f} delitos<extra></extra>',
        showscale  = True,
        colorbar   = dict(tickfont=dict(color=C_MUTED, size=10),
                          len=0.9, thickness=12),
        xgap = 2,
        ygap = 2,
    ))
    fig.update_layout(
        **_BASE,
        xaxis = dict(side='top', color=C_MUTED, tickfont=dict(size=10)),
        yaxis = dict(color=C_TEXT, autorange='reversed'),
    )
    return fig

# ── 2. Víctimas por sexo (líneas H vs M) ────────────────────────
def fig_victimas_sexo(estado=None):
    df = get_victimas_sexo(estado)
    COLORES_SEXO = {'Hombre': C_CYAN, 'Mujer': C_RED}
    fig = go.Figure()
    for sexo in sorted(df['sexo'].unique()):
        sub   = df[df['sexo'] == sexo].sort_values('ano')
        color = COLORES_SEXO.get(sexo, C_GRAY)
        fig.add_trace(go.Scatter(
            x    = sub['ano'],
            y    = sub['total'],
            name = sexo,
            mode = 'lines+markers',
            line = dict(color=color, width=2.5),
            marker = dict(size=6, line=dict(color=C_PAPER, width=1.5)),
            fill = 'tozeroy',
            fillcolor = FILL_SEXO.get(sexo, 'rgba(144,144,168,0.08)'),
            hovertemplate = f'<b>{sexo}</b> %{{x}}: %{{y:,.0f}}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        yaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f'),
        legend = dict(font=dict(size=11, color=C_TEXT), bgcolor='rgba(0,0,0,0)'),
    )
    return fig

# ── 3. Delta entre dos años por bien jurídico ────────────────────
def fig_comparativa(anio1, anio2, estado=None):
    df = get_comparativa_anios(anio1, anio2, estado)
    if 'delta' not in df.columns or df.empty:
        return go.Figure(layout=dict(**_BASE))
    colors = [C_RED if d > 0 else C_GREEN for d in df['delta']]
    fig = go.Figure(go.Bar(
        x           = df['delta'],
        y           = df['bien_juridico'],
        orientation = 'h',
        marker      = dict(color=colors, line=dict(width=0)),
        customdata  = df[['delta_pct']].values if 'delta_pct' in df.columns else None,
        hovertemplate = '<b>%{y}</b><br>Δ %{x:+,.0f}  (%{customdata[0]:+.1f}%)<extra></extra>',
    ))
    fig.add_vline(x=0, line_color=C_MUTED, line_width=1, line_dash='dot')
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat='+,.0f'),
        yaxis  = dict(showgrid=False, color=C_TEXT, tickfont=dict(size=11)),
        bargap = 0.22,
    )
    return fig
