import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
from pages.get_data.get_data_5 import get_scatter_pib, get_tendencia_nacional, get_ranking_doble

C_RED   = '#cf0a2c'
C_CYAN  = '#00b4cc'
C_GOLD  = '#c9922a'
C_GRAY  = '#9090a8'
C_PAPER = '#1a1a24'
C_PLOT  = '#111118'
C_TEXT  = '#e8e8f0'
C_MUTED = '#5c5c74'

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    hoverlabel=dict(bgcolor=C_PAPER, font_color=C_TEXT),
)


def fig_scatter_pib(anio=None):
    df = get_scatter_pib(anio)
    x = df['tasa_x100k'].values
    y = df['variacion_pib'].values
    slope, intercept, r, p, _ = stats.linregress(x, y)
    xi = np.linspace(x.min(), x.max(), 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['tasa_x100k'], y=df['variacion_pib'],
        mode='markers+text', text=df['abrev'],
        textposition='top center', textfont=dict(size=8, color=C_MUTED),
        marker=dict(color=C_CYAN, size=9, opacity=0.85,
                    line=dict(color=C_PAPER, width=1)),
        hovertemplate='<b>%{text}</b><br>Crimen: %{x:,.0f}/100k<br>PIB: %{y:.1f}%<extra></extra>',
        name='Estado',
    ))
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept,
        mode='lines', line=dict(color=C_RED, width=2, dash='dash'),
        name=f'Tendencia  r={r:.2f}',
        hoverinfo='skip',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Tasa de crimen (por 100k hab.)', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Variación PIB (%)', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.01, y=0.99),
        showlegend=True,
    )
    return fig


def fig_tendencia_dual():
    df = get_tendencia_nacional()
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Scatter(
        x=df['anio'], y=df['tasa_crimen'],
        mode='lines+markers', name='Tasa crimen',
        line=dict(color=C_RED, width=2.5),
        marker=dict(size=7, line=dict(color=C_PAPER, width=2)),
        hovertemplate='<b>%{x}</b><br>Crimen: %{y:,.1f}/100k<extra></extra>',
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df['anio'], y=df['pib_crecimiento'],
        mode='lines+markers', name='Crecimiento PIB',
        line=dict(color=C_GOLD, width=2.5, dash='dot'),
        marker=dict(size=7, symbol='square', line=dict(color=C_PAPER, width=2)),
        hovertemplate='<b>%{x}</b><br>PIB: %{y:.1f}%<extra></extra>',
    ), secondary_y=True)
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=False, color=C_MUTED, tickformat='d', dtick=1),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.01, y=0.99),
    )
    fig.update_yaxes(title_text='Crimen / 100k', color=C_MUTED,
                     showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                     secondary_y=False)
    fig.update_yaxes(title_text='Var. PIB %', color=C_MUTED,
                     showgrid=False, secondary_y=True)
    return fig


def fig_ranking_doble(anio=None):
    df = get_ranking_doble(anio).head(15)
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=['Tasa de crimen (por 100k)', 'Var. PIB (%)'])
    fig.add_trace(go.Bar(
        y=df['abrev'], x=df['tasa_crimen'], orientation='h',
        marker_color=C_RED, opacity=0.85,
        hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        y=df['abrev'], x=df['pib_crecimiento'], orientation='h',
        marker_color=[C_CYAN if v >= 0 else C_RED for v in df['pib_crecimiento']],
        opacity=0.85,
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>',
    ), row=1, col=2)
    fig.update_layout(
        **_BASE, showlegend=False,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED),
        xaxis2=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED),
        yaxis=dict(color=C_MUTED),
        bargap=0.3,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=28, b=10))
    return fig
