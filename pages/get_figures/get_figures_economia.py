"""
Figures for slide_economia — EXP-15, EXP-07, EXP-02, EXP-18.
"""
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from pages.get_data.get_data_economia import (
    get_digital_wages_scatter,
    get_data_centers_quintiles,
    get_investment_lag_data,
    get_sustained_investment_data,
)

C_CYAN   = '#00b4cc'
C_GOLD   = '#c9922a'
C_GREEN  = '#2bb573'
C_RED    = '#d15b4a'
C_BLUE   = '#3891c7'
C_PAPER  = '#1a1a24'
C_PLOT   = '#111118'
C_TEXT   = '#e8e8f0'
C_MUTED  = '#5c5c74'

_CLUSTER_COLORS = {'C0': C_RED, 'C1': C_BLUE, 'C2': C_GREEN, 'C3': C_GOLD}

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
    'San Luis Potosí': 'SLP',
    'Quintana Roo': 'Q. Roo',
}


def _abbrev(s):
    return _ABBREV.get(s, s)


def fig_digital_wages_scatter():
    """EXP-15: e-banking adoption vs avg_wage, R²≈0.594. States colored by cluster."""
    df = get_digital_wages_scatter()
    if df.empty:
        return go.Figure()

    x_col = 'empresas_que_utilizan_banca_electronica_por'
    if x_col not in df.columns:
        return go.Figure()

    x = df[x_col].values
    y = df['avg_wage'].values
    labels = df['estado'].map(_abbrev).fillna(df['estado']).values

    has_cluster = 'cluster_label' in df.columns
    if has_cluster:
        colors = [_CLUSTER_COLORS.get(str(c)[:2], C_CYAN) for c in df['cluster_label']]
    else:
        colors = [C_CYAN] * len(df)

    slope, intercept, r, _, _ = stats.linregress(x, y)
    r2 = r ** 2
    xi = np.linspace(x.min(), x.max(), 100)

    fig = go.Figure()

    # Regression band
    band_y = slope * xi + intercept
    fig.add_trace(go.Scatter(
        x=np.concatenate([xi, xi[::-1]]),
        y=np.concatenate([band_y + 600, (band_y - 600)[::-1]]),
        fill='toself', fillcolor='rgba(0,180,204,0.06)',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))

    # Regression line
    fig.add_trace(go.Scatter(
        x=xi, y=band_y, mode='lines',
        line=dict(color=C_CYAN, width=1.8, dash='dash'),
        name=f'R² = {r2:.3f}', hoverinfo='skip',
    ))

    # Points
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        text=labels,
        textposition='top center',
        textfont=dict(size=7.5, color='rgba(184,184,204,0.75)'),
        marker=dict(color=colors, size=10, opacity=0.88,
                    line=dict(color=C_PAPER, width=1.2)),
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Empresas con banca digital: %{x:.1f}%<br>'
            'Salario promedio: $%{y:,.0f}<extra></extra>'
        ),
        showlegend=False,
    ))

    # R² annotation box
    fig.add_annotation(
        xref='paper', yref='paper', x=0.02, y=0.97,
        text=f'<b>R² = {r2:.3f}</b><br>La adopción digital explica<br>el {r2*100:.0f}% de la varianza salarial',
        showarrow=False, align='left',
        bgcolor='rgba(0,180,204,0.12)', bordercolor=C_CYAN, borderwidth=1,
        font=dict(size=10, color=C_TEXT),
    )

    fig.update_layout(
        **_BASE,
        margin=dict(l=70, r=30, t=20, b=60),
        xaxis=dict(
            title=dict(text='% empresas con banca electrónica', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
        ),
        yaxis=dict(
            title=dict(text='Salario promedio mensual (MXN)', font=dict(size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            tickformat='$,.0f',
        ),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.98, y=0.05,
                    xanchor='right', yanchor='bottom'),
        showlegend=True,
    )
    return fig


def fig_data_centers_wages():
    """EXP-07: median wage by data center quintile — the step-up pattern."""
    df = get_data_centers_quintiles()
    if df.empty or 'quintile' not in df.columns:
        return go.Figure()

    summary = (df.groupby('quintile', observed=True)['avg_wage']
               .agg(['median', 'count']).reset_index())
    summary.columns = ['quintile', 'median_wage', 'n']

    colors = [C_CYAN if i < len(summary) - 1 else C_GREEN for i in range(len(summary))]

    fig = go.Figure(go.Bar(
        x=summary['quintile'],
        y=summary['median_wage'],
        marker=dict(
            color=colors,
            opacity=0.88,
            line=dict(color=C_PAPER, width=0),
        ),
        text=[f'${v:,.0f}' for v in summary['median_wage']],
        textposition='outside',
        textfont=dict(size=10, color=C_TEXT),
        hovertemplate='<b>%{x}</b><br>Salario mediano: $%{y:,.0f}<br><extra></extra>',
    ))

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=30, t=20, b=50),
        xaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=9)),
        yaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            title=dict(text='Salario mediano mensual (MXN)', font=dict(size=10)),
            tickformat='$,.0f',
        ),
        bargap=0.28,
    )
    return fig


def fig_investment_lag():
    """EXP-02: R² of IDDE at lag-0, lag-1, lag-2 vs 2025 wages.
    Shows that the 2-year lag has the highest predictive power."""
    rows = get_investment_lag_data()
    if not rows:
        # Fallback to reported values from experiment report
        rows = [
            {'lag': 0, 'year': 2025, 'r2': 0.247, 'label': 'Mismo año\n(IDDE 2025)'},
            {'lag': 1, 'year': 2024, 'r2': 0.310, 'label': 'Año anterior\n(IDDE 2024)'},
            {'lag': 2, 'year': 2022, 'r2': 0.372, 'label': '2 años antes\n(IDDE 2022)'},
        ]
    else:
        label_map = {
            0: 'Mismo año\n(IDDE 2025)',
            1: 'Año anterior\n(IDDE 2024)',
            2: '2 años antes\n(IDDE 2022)',
        }
        for r in rows:
            r['label'] = label_map.get(r['lag'], f'Lag {r["lag"]}')

    labels = [r['label'] for r in rows]
    r2s    = [r['r2'] for r in rows]
    max_r2 = max(r2s)

    colors = [C_GREEN if v == max_r2 else C_CYAN for v in r2s]
    opacities = [1.0 if v == max_r2 else 0.55 for v in r2s]

    fig = go.Figure(go.Bar(
        x=labels, y=r2s,
        marker=dict(color=colors, opacity=opacities, line=dict(width=0)),
        text=[f'R²={v:.3f}' for v in r2s],
        textposition='outside',
        textfont=dict(size=11, color=C_TEXT),
        hovertemplate='<b>%{x}</b><br>R² = %{y:.3f}<extra></extra>',
    ))

    fig.add_annotation(
        xref='paper', yref='paper', x=0.98, y=0.97,
        text='↑ Mayor R² en lag-2<br>La inversión paga<br>en el año 2',
        showarrow=False, align='right',
        bgcolor='rgba(46,204,113,0.12)', bordercolor=C_GREEN, borderwidth=1,
        font=dict(size=10, color=C_TEXT),
    )

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=30, t=20, b=60),
        xaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=10)),
        yaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            title=dict(text='R² (IDDE → salario)', font=dict(size=10)),
            range=[0, max_r2 * 1.25],
        ),
        bargap=0.35,
    )
    return fig


def fig_sustained_investment():
    """EXP-18: sustained vs inconsistent IDDE investors — wage comparison."""
    summary = get_sustained_investment_data()
    if summary.empty:
        # Fallback to reported values
        import pandas as pd
        summary = pd.DataFrame([
            {'grupo': 'Inversión sostenida',     'n': 15, 'avg_wage': 11893.0},
            {'grupo': 'Inversión inconsistente', 'n': 16, 'avg_wage': 11103.0},
        ])

    summary = summary.sort_values('avg_wage', ascending=False)
    diff = float(summary.iloc[0]['avg_wage']) - float(summary.iloc[1]['avg_wage'])

    colors = [C_GREEN, C_MUTED]

    fig = go.Figure(go.Bar(
        x=summary['grupo'],
        y=summary['avg_wage'],
        marker=dict(color=colors, opacity=[1.0, 0.65], line=dict(width=0)),
        text=[f'${v:,.0f}/mes<br>(n={int(n)})' for v, n in
              zip(summary['avg_wage'], summary['n'])],
        textposition='inside',
        textfont=dict(size=11, color='#fff'),
        hovertemplate='<b>%{x}</b><br>Salario promedio: $%{y:,.0f}<extra></extra>',
    ))

    fig.add_annotation(
        xref='paper', yref='paper', x=0.5, y=1.08,
        text=f'+${diff:,.0f}/mes más para estados con inversión consistente',
        showarrow=False, align='center',
        font=dict(size=11, color=C_GREEN),
    )

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=30, t=48, b=50),
        xaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=10)),
        yaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            title=dict(text='Salario promedio mensual (MXN)', font=dict(size=10)),
            tickformat='$,.0f',
            range=[10000, max(summary['avg_wage']) * 1.18],
        ),
        bargap=0.40,
    )
    return fig
