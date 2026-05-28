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


def fig_idde_crime_scatter():
    """
    Scatter: IDDE 2025 vs total crime rate per 100k — 32 states.
    Highlights Yucatán and Nuevo León as low-crime + high-IDDE reference states.
    Used in Slide 2 to show the IDDE-crime trajectory connection.
    """
    try:
        from pages.get_data.get_data_11 import get_data_11
        import numpy as np
        from scipy import stats
    except ImportError:
        return go.Figure()

    d = get_data_11()
    cross = d['cross_cl'].copy()
    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    y_col = 'crime_rate_100k'

    if idde_col not in cross.columns or y_col not in cross.columns:
        return go.Figure()

    sub = cross[['estado', idde_col, y_col]].dropna()

    C_PAPER = '#1a1a24'
    C_TEXT  = '#e8e8f0'
    C_MUTED = '#5c5c74'
    C_CYAN  = '#00b4cc'
    C_RED   = '#cf0a2c'
    C_GOLD  = '#c9922a'
    C_GREEN = '#00b87a'

    HIGHLIGHT = {'Yucatán', 'Nuevo León'}

    x = sub[idde_col].values
    y = sub[y_col].values
    slope, intercept, r, p, _ = stats.linregress(x, y)
    xi = np.linspace(x.min(), x.max(), 100)

    fig = go.Figure()

    # Regression band
    band_y = slope * xi + intercept
    fig.add_trace(go.Scatter(
        x=np.concatenate([xi, xi[::-1]]),
        y=np.concatenate([band_y * 1.15, (band_y * 0.85)[::-1]]),
        fill='toself', fillcolor='rgba(0,180,204,0.05)',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))

    # Regression line
    fig.add_trace(go.Scatter(
        x=xi, y=band_y, mode='lines',
        line=dict(color=C_CYAN, width=1.5, dash='dash'),
        name=f'r = {r:+.2f}', hoverinfo='skip',
    ))

    # All non-highlighted states
    normal = sub[~sub['estado'].isin(HIGHLIGHT)]
    fig.add_trace(go.Scatter(
        x=normal[idde_col], y=normal[y_col],
        mode='markers',
        marker=dict(color=C_CYAN, size=8, opacity=0.55,
                    line=dict(color=C_PAPER, width=1)),
        text=normal['estado'],
        hovertemplate='<b>%{text}</b><br>IDDE: %{x:.1f}<br>Crimen: %{y:.0f} por 100k<extra></extra>',
        showlegend=False,
    ))

    # Highlighted states (Yucatan, NL)
    hl = sub[sub['estado'].isin(HIGHLIGHT)]
    fig.add_trace(go.Scatter(
        x=hl[idde_col], y=hl[y_col],
        mode='markers+text',
        marker=dict(color=C_GREEN, size=14, opacity=1.0,
                    symbol='diamond',
                    line=dict(color='white', width=1.5)),
        text=hl['estado'],
        textposition='top center',
        textfont=dict(size=10, color=C_GREEN),
        hovertemplate='<b>%{text}</b><br>IDDE: %{x:.1f}<br>Crimen: %{y:.0f} por 100k<extra></extra>',
        showlegend=False,
    ))

    # Annotation for highlighted states
    fig.add_annotation(
        xref='paper', yref='paper', x=0.98, y=0.97,
        text='◆ Yucatán y NL: IDDE alto<br>+ trayectoria favorable',
        showarrow=False, align='right',
        bgcolor='rgba(0,184,122,0.12)', bordercolor=C_GREEN, borderwidth=1,
        font=dict(size=10, color=C_TEXT),
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
        margin=dict(l=65, r=20, t=20, b=60),
        xaxis=dict(
            title=dict(text='IDDE 2025', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.05)', color=C_MUTED,
        ),
        yaxis=dict(
            title=dict(text='Crimen por 100k hab.', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.05)', color=C_MUTED,
        ),
        hoverlabel=dict(bgcolor='#0f0f18', font_color=C_TEXT),
    )
    return fig
