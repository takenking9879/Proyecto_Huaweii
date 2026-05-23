import plotly.graph_objects as go
from pages.get_data.get_data_3 import (
    get_distribucion_bienes, get_subtipos_detalle, get_tendencia_bienes,
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
PALETTE = [C_RED, C_CYAN, C_GOLD, C_GREEN, '#f97316', '#a855f7', '#06b6d4', C_GRAY]

PASTEL  = ['#e8919e', '#7dd4e8', '#e8c97a', '#7de8b4',
           '#f9b07a', '#c49af5', '#7ecfdf', '#b8b8cc']

_BASE = dict(
    paper_bgcolor = C_PAPER,
    plot_bgcolor  = C_PLOT,
    font          = dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin        = dict(l=10, r=10, t=10, b=10),
    hoverlabel    = dict(bgcolor=C_PAPER, font_color=C_TEXT, font_family='DM Sans'),
)

def _hex_to_rgba(hex_color, alpha=0.7):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f'rgba({r},{g},{b},{alpha})'

# ── 1. Donut por bien jurídico ───────────────────────────────────
def fig_donut_bienes(estado=None, anio_inicio=None, anio_fin=None):
    df = get_distribucion_bienes(estado, anio_inicio, anio_fin)
    fig = go.Figure(go.Pie(
        labels    = df['bien_juridico'],
        values    = df['total'],
        hole      = 0.55,
        marker    = dict(colors=PALETTE[:len(df)],
                         line=dict(color=C_PLOT, width=2)),
        textfont  = dict(size=11),
        hovertemplate = '<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        legend = dict(font=dict(size=10, color=C_TEXT),
                      bgcolor='rgba(0,0,0,0)', x=1.02, y=0.5),
    )
    return fig

# ── 2. Treemap subtipos anidados en bien jurídico ────────────────
def fig_treemap_subtipos(estado=None, anio_inicio=None, anio_fin=None):
    df = get_subtipos_detalle(estado, anio_inicio, anio_fin)
    bienes = df['bien_juridico'].unique().tolist()

    bienes_totals = df.groupby('bien_juridico')['total'].sum()
    total_sum     = int(df['total'].sum())

    # Colores pastel por categoría, subtipos en versión más sólida del mismo tono
    bien_color = {b: PASTEL[i % len(PASTEL)] for i, b in enumerate(bienes)}

    labels  = ['México'] + bienes + df['subtipo'].tolist()
    parents = ['']       + ['México'] * len(bienes) + df['bien_juridico'].tolist()
    values  = ([total_sum]
               + [int(bienes_totals.get(b, 0)) for b in bienes]
               + df['total'].tolist())
    colors  = ([C_PAPER]
               + [bien_color[b] for b in bienes]
               + [_hex_to_rgba(bien_color[b], 0.75) for b in df['bien_juridico']])

    fig = go.Figure(go.Treemap(
        labels      = labels,
        parents     = parents,
        values      = values,
        branchvalues = 'total',
        marker      = dict(
            colors = colors,
            line   = dict(color=C_PAPER, width=2),
        ),
        textfont    = dict(size=11, color='#1a1a24'),
        hovertemplate = '<b>%{label}</b><br>%{value:,.0f}<extra></extra>',
    ))
    fig.update_layout(**_BASE)
    return fig

# ── 3. Área apilada — composición del delito por año ────────────
def fig_tendencia_bienes(estado=None):
    df = get_tendencia_bienes(estado)
    top6 = (df.groupby('bien_juridico')['total'].sum()
              .nlargest(6).index.tolist())
    df = df[df['bien_juridico'].isin(top6)]
    fig = go.Figure()
    for i, bien in enumerate(top6):
        sub   = df[df['bien_juridico'] == bien].sort_values('anio')
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x         = sub['anio'],
            y         = sub['total'],
            name      = bien,
            mode      = 'lines',
            stackgroup = 'one',
            line      = dict(color=color, width=1),
            fillcolor = _hex_to_rgba(color, 0.65),
            hovertemplate = f'<b>{bien}</b> %{{x}}: %{{y:,.0f}}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        xaxis  = dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        yaxis  = dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                      color=C_MUTED, tickformat=',.0f'),
        legend = dict(font=dict(size=10, color=C_TEXT), bgcolor='rgba(0,0,0,0)',
                      x=0, y=1, orientation='h'),
    )
    return fig
