import plotly.graph_objects as go
from pages.get_data.get_data_2 import get_ranking_estados, get_top_municipios, get_evolucion_estados

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

# ── 1. Ranking de los 32 estados ─────────────────────────────────
def fig_ranking_estados(anio=None):
    df = get_ranking_estados(anio)
    max_v = df['total'].max()
    colors = [C_RED if v == max_v
              else f'rgba(207,10,44,{max(0.18, 0.18 + 0.72*(v/max_v)):.2f})'
              for v in df['total']]
    fig = go.Figure(go.Bar(
        x           = df['total'],
        y           = df['estado'],
        orientation = 'h',
        marker      = dict(color=colors, line=dict(width=0)),
        text        = df['total'].apply(lambda x: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'),
        textposition = 'outside',
        textfont     = dict(size=9, color=C_MUTED),
        hovertemplate = '<b>%{y}</b><br>%{x:,.0f} delitos<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f'),
        yaxis  = dict(showgrid=False, color=C_TEXT, tickfont=dict(size=10)),
        bargap = 0.12,
    )
    return fig

# ── 2. Top 15 municipios ─────────────────────────────────────────
def fig_top_municipios(anio=None, n=15):
    df = get_top_municipios(anio, n=n)
    df['label'] = df['municipio'] + ', ' + df['estado']
    df = df.sort_values('total', ascending=True)
    max_v = df['total'].max()
    colors = [C_CYAN if v == max_v
              else f'rgba(0,180,204,{max(0.20, 0.20 + 0.65*(v/max_v)):.2f})'
              for v in df['total']]
    fig = go.Figure(go.Bar(
        x           = df['total'],
        y           = df['label'],
        orientation = 'h',
        marker      = dict(color=colors, line=dict(width=0)),
        hovertemplate = '<b>%{y}</b><br>%{x:,.0f} delitos<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f'),
        yaxis  = dict(showgrid=False, color=C_TEXT, tickfont=dict(size=10)),
        bargap = 0.18,
    )
    return fig

# ── 3. Evolución top 5 estados (multi-línea) ─────────────────────
def fig_evolucion_estados():
    df, top = get_evolucion_estados(5)
    fig = go.Figure()
    for i, estado in enumerate(top):
        sub = df[df['estado'] == estado].sort_values('anio')
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x    = sub['anio'],
            y    = sub['total'],
            name = estado,
            mode = 'lines+markers',
            line = dict(color=color, width=2),
            marker = dict(size=5),
            hovertemplate = f'<b>{estado}</b> %{{x}}: %{{y:,.0f}}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        yaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f'),
        legend = dict(font=dict(size=10, color=C_TEXT), bgcolor='rgba(0,0,0,0)',
                      x=0, y=1),
    )
    return fig
