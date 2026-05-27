import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
from pages.get_data.get_data_6 import (
    get_df, get_df_all, get_pilares_por_grupo, get_crimen_por_grupo,
    GRUPO_COLORS, GRUPO_ORDER,
)

C_PAPER = '#1a1a24'
C_PLOT  = '#111118'
C_TEXT  = '#e8e8f0'
C_MUTED = '#5c5c74'
C_CYAN  = '#00b4cc'

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=20, b=10),
    hoverlabel=dict(bgcolor=C_PAPER, font_color=C_TEXT),
)


def fig_scatter_idde(anio=2022, cat='tasa_Sociedad'):
    df = get_df(anio)
    if cat not in df.columns:
        cat = 'tasa_x100k'
    fig = go.Figure()
    for grupo in GRUPO_ORDER:
        sub = df[df['grupo_label'] == grupo]
        if sub.empty:
            continue
        x = sub['idde_score'].values
        y = sub[cat].values
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='markers+text',
            text=sub['estado'].str.replace(' de Ignacio de la Llave', '')
                              .str.replace(' de Zaragoza', '')
                              .str.replace(' de Ocampo', ''),
            textposition='top center', textfont=dict(size=7.5, color=C_MUTED),
            marker=dict(color=GRUPO_COLORS[grupo], size=11, opacity=0.88,
                        line=dict(color=C_PAPER, width=1.5)),
            name=grupo,
            hovertemplate=f'<b>%{{text}}</b> ({grupo})<br>IDDE: %{{x:.1f}}<br>{cat}: %{{y:.1f}}<extra></extra>',
        ))

    all_x = df['idde_score'].values
    all_y = df[cat].values
    slope, intercept, r, p, _ = stats.linregress(all_x, all_y)
    xi = np.linspace(all_x.min(), all_x.max(), 100)
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept,
        mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1.5, dash='dash'),
        name=f'Tendencia r={r:.2f}', hoverinfo='skip',
    ))

    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Índice IDDE', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text=cat.replace('tasa_', 'Tasa ') + ' (por 100k)', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.01, y=0.99),
    )
    return fig


def fig_pilares_por_grupo(anio=2022):
    df = get_pilares_por_grupo(anio)
    pilares = ['pilar_infraestructura', 'pilar_sociedad', 'pilar_innovacion']
    labels  = ['Infraestructura', 'Sociedad Digital', 'Innovación']
    fig = go.Figure()
    for grupo in GRUPO_ORDER:
        row = df[df['grupo_label'] == grupo]
        if row.empty:
            continue
        vals = [float(row[p].iloc[0]) for p in pilares]
        fig.add_trace(go.Bar(
            name=grupo, x=labels, y=vals,
            marker_color=GRUPO_COLORS[grupo], opacity=0.85,
            hovertemplate=f'<b>{grupo}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        barmode='group',
        xaxis=dict(showgrid=False, color=C_MUTED),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Puntuación pilares', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', orientation='h',
                    x=0.5, xanchor='center', y=1.12),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig


def fig_crimen_por_grupo(anio=2022):
    df = get_crimen_por_grupo(anio)
    df_raw = get_df(anio)
    tasa_cols = [c for c in df.columns if c.startswith('tasa_') and c != 'tasa_x100k']
    labels = [c.replace('tasa_', '') for c in tasa_cols]
    national_median = float(df_raw['tasa_x100k'].median())

    fig = go.Figure()
    for grupo in GRUPO_ORDER:
        row = df[df['grupo_label'] == grupo]
        if row.empty:
            continue
        vals = [float(row[c].iloc[0]) if c in row.columns else 0 for c in tasa_cols]
        fig.add_trace(go.Bar(
            name=grupo, x=labels, y=vals,
            marker_color=GRUPO_COLORS[grupo], opacity=0.85,
            hovertemplate=f'<b>{grupo}</b><br>%{{x}}: %{{y:.1f}}/100k<extra></extra>',
        ))
    fig.add_hline(
        y=national_median,
        line_dash='dot',
        line_color='#9090a8',
        line_width=1.5,
        annotation_text=f'Mediana nacional: {national_median:,.0f}',
        annotation_font_color='#9090a8',
        annotation_font_size=10,
    )
    fig.update_layout(
        **_BASE,
        barmode='group',
        xaxis=dict(showgrid=False, color=C_MUTED),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Tasa por 100k hab.', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', orientation='h',
                    x=0.5, xanchor='center', y=1.12),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig
