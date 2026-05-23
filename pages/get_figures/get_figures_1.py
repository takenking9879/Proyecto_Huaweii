import plotly.graph_objects as go
from pages.get_data.get_data_1 import (
    get_tendencia_anual, get_estacionalidad, get_top_estados_percapita,
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
PALETTE = [C_RED, C_CYAN, C_GOLD, C_GREEN, C_GRAY]

_BASE = dict(
    paper_bgcolor = C_PAPER,
    plot_bgcolor  = C_PLOT,
    font          = dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin        = dict(l=10, r=10, t=10, b=10),
    hoverlabel    = dict(bgcolor=C_PAPER, font_color=C_TEXT, font_family='DM Sans'),
)

# ── 1. Tendencia anual (área + línea) ────────────────────────────
def fig_tendencia(estado=None, anio_inicio=None, anio_fin=None):
    df = get_tendencia_anual(estado, anio_inicio, anio_fin)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x    = df['anio'],
        y    = df['incidencia_delictiva'],
        mode = 'lines+markers',
        line = dict(color=C_RED, width=2.5),
        marker = dict(color=C_RED, size=7, line=dict(color=C_PAPER, width=2)),
        fill  = 'tozeroy',
        fillcolor = 'rgba(207,10,44,0.08)',
        hovertemplate = '<b>%{x}</b><br>%{y:,.0f} delitos<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis = dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        yaxis = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                     color=C_MUTED, tickformat=',.0f'),
    )
    return fig

# ── 2. Estacionalidad mensual (barras) ───────────────────────────
def fig_estacionalidad(estado=None, anio_inicio=None, anio_fin=None):
    df = get_estacionalidad(estado, anio_inicio, anio_fin)
    max_v = df['incidencia_delictiva'].max()
    colors = [C_RED if v == max_v else 'rgba(207,10,44,0.35)'
              for v in df['incidencia_delictiva']]
    fig = go.Figure(go.Bar(
        x = df['mes'],
        y = df['incidencia_delictiva'],
        marker = dict(color=colors, line=dict(width=0)),
        hovertemplate = '<b>%{x}</b><br>%{y:,.0f} promedio mensual<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis = dict(showgrid=False, color=C_MUTED),
        yaxis = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                     color=C_MUTED, tickformat=',.0f'),
        bargap = 0.2,
    )
    return fig

# ── 3. Top 5 estados — líneas per cápita ────────────────────────
def fig_top_estados_lineas():
    df, top = get_top_estados_percapita(5)
    fig = go.Figure()
    for i, estado in enumerate(top):
        sub = df[df['estado'] == estado].sort_values('anio')
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x    = sub['anio'],
            y    = sub['tasa'],
            name = estado,
            mode = 'lines+markers',
            line = dict(color=color, width=2),
            marker = dict(size=5),
            hovertemplate = f'<b>{estado}</b> %{{x}}: %{{y:,.1f}} por 100k hab.<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        yaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f',
                      title=dict(text='Delitos por 100,000 hab.', font=dict(size=11, color=C_MUTED))),
        legend = dict(font=dict(size=10, color=C_TEXT), bgcolor='rgba(0,0,0,0)',
                      x=0, y=1),
    )
    return fig
