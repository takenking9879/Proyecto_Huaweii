"""
Investment opportunity figures — ROI projections, cluster comparison, state table.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pages.get_data.get_data_inversion import (
    get_cluster_profiles, get_roi_projections,
    get_state_investment_table, get_radar_data,
)
from pages.get_data.get_data_11 import get_data_11, _IDDE_COL

_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans, sans-serif', color='#c8c8d8', size=11),
    margin=dict(l=12, r=12, t=28, b=12),
)


def fig_roi_projections():
    """Grouped bar chart: projected % change in wages, trust, perception per +10 pts IDDE."""
    profiles = get_cluster_profiles()
    roi      = get_roi_projections(delta_idde=10.0)

    codes  = [p['code'] for p in profiles]
    colors = [p['color'] for p in profiles]
    names  = [f"{p['code']} {p['name']}" for p in profiles]

    wage_pcts  = [roi[c]['delta_wage_pct']  for c in codes]
    trust_pcts = [roi[c]['delta_trust_pct'] for c in codes]
    perc_pcts  = [roi[c]['delta_perc_pct']  for c in codes]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Salario promedio',
        x=names, y=wage_pcts,
        marker_color='#00b87a',
        text=[f'+{v:.1f}%' if v >= 0 else f'{v:.1f}%' for v in wage_pcts],
        textposition='outside',
    ))
    fig.add_trace(go.Bar(
        name='Confianza social',
        x=names, y=trust_pcts,
        marker_color='#00b4cc',
        text=[f'+{v:.1f}%' if v >= 0 else f'{v:.1f}%' for v in trust_pcts],
        textposition='outside',
    ))
    fig.add_trace(go.Bar(
        name='Percepción segura',
        x=names, y=perc_pcts,
        marker_color='#c9922a',
        text=[f'+{v:.1f}%' if v >= 0 else f'{v:.1f}%' for v in perc_pcts],
        textposition='outside',
    ))

    fig.update_layout(
        **_LAYOUT,
        barmode='group',
        yaxis=dict(
            title='Cambio proyectado (%)',
            gridcolor='rgba(255,255,255,0.06)',
            zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
        ),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
        showlegend=True,
    )
    return fig


def fig_idde_vs_wage_scatter():
    """Scatter: IDDE vs avg_wage, colored by cluster, with regression line."""
    d        = get_data_11()
    cross_cl = d['cross_cl'].copy()

    if 'avg_wage' not in cross_cl.columns or _IDDE_COL not in cross_cl.columns:
        return go.Figure()

    fig = go.Figure()

    for code in sorted(cross_cl['cluster_code'].unique()):
        sub = cross_cl[cross_cl['cluster_code'] == code]
        color = sub['cluster_color'].iloc[0]
        name  = sub['cluster_name'].iloc[0]
        fig.add_trace(go.Scatter(
            x=sub[_IDDE_COL], y=sub['avg_wage'],
            mode='markers+text',
            name=f'{code} {name}',
            text=sub['estado'].apply(lambda s: s[:10]),
            textposition='top center',
            textfont=dict(size=9, color='#8888a8'),
            marker=dict(color=color, size=9, opacity=0.85,
                        line=dict(color='#0a0a0f', width=1)),
        ))

    # Global regression line
    valid = cross_cl[[_IDDE_COL, 'avg_wage']].dropna()
    if len(valid) >= 5:
        x_range = np.linspace(valid[_IDDE_COL].min(), valid[_IDDE_COL].max(), 60)
        from sklearn.linear_model import LinearRegression
        lr = LinearRegression()
        lr.fit(valid[[_IDDE_COL]], valid['avg_wage'])
        y_range = lr.predict(x_range.reshape(-1, 1))
        fig.add_trace(go.Scatter(
            x=x_range, y=y_range,
            mode='lines', name='Tendencia nacional',
            line=dict(color='rgba(255,255,255,0.3)', dash='dot', width=1.5),
            hoverinfo='skip',
        ))

    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(title='IDDE 2025', gridcolor='rgba(255,255,255,0.06)'),
        yaxis=dict(title='Salario promedio mensual ($)', gridcolor='rgba(255,255,255,0.06)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=9)),
    )
    return fig


def fig_idde_vs_trust_scatter():
    """Scatter: IDDE vs confianza social avg, colored by cluster."""
    d        = get_data_11()
    cross_cl = d['cross_cl'].copy()

    trust_cols = ['conf_familia', 'conf_amigos', 'conf_vecinos']
    available = [c for c in trust_cols if c in cross_cl.columns]
    if not available or _IDDE_COL not in cross_cl.columns:
        return go.Figure()

    cross_cl['avg_trust'] = cross_cl[available].mean(axis=1)

    fig = go.Figure()

    for code in sorted(cross_cl['cluster_code'].unique()):
        sub = cross_cl[cross_cl['cluster_code'] == code]
        color = sub['cluster_color'].iloc[0]
        name  = sub['cluster_name'].iloc[0]
        fig.add_trace(go.Scatter(
            x=sub[_IDDE_COL], y=sub['avg_trust'],
            mode='markers+text',
            name=f'{code} {name}',
            text=sub['estado'].apply(lambda s: s[:10]),
            textposition='top center',
            textfont=dict(size=9, color='#8888a8'),
            marker=dict(color=color, size=9, opacity=0.85,
                        line=dict(color='#0a0a0f', width=1)),
        ))

    valid = cross_cl[[_IDDE_COL, 'avg_trust']].dropna()
    if len(valid) >= 5:
        x_range = np.linspace(valid[_IDDE_COL].min(), valid[_IDDE_COL].max(), 60)
        from sklearn.linear_model import LinearRegression
        lr = LinearRegression()
        lr.fit(valid[[_IDDE_COL]], valid['avg_trust'])
        y_range = lr.predict(x_range.reshape(-1, 1))
        fig.add_trace(go.Scatter(
            x=x_range, y=y_range,
            mode='lines', name='Tendencia nacional',
            line=dict(color='rgba(0,180,204,0.5)', dash='dot', width=1.5),
            hoverinfo='skip',
        ))

    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(title='IDDE 2025', gridcolor='rgba(255,255,255,0.06)'),
        yaxis=dict(title='Confianza social promedio (1–4)', gridcolor='rgba(255,255,255,0.06)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=9)),
    )
    return fig


def fig_cluster_idde_bars():
    """Horizontal bars: avg IDDE by cluster with gap annotation."""
    profiles = get_cluster_profiles()

    c2 = next((p for p in profiles if p['code'] == 'C2'), None)
    c2_idde = c2['avg_idde'] if c2 else 60.0

    profiles_sorted = sorted(profiles, key=lambda p: p['avg_idde'], reverse=True)

    fig = go.Figure(go.Bar(
        x=[p['avg_idde'] for p in profiles_sorted],
        y=[f"{p['code']} {p['name']}" for p in profiles_sorted],
        orientation='h',
        marker_color=[p['color'] for p in profiles_sorted],
        text=[f"IDDE {p['avg_idde']:.1f} · {p['n']} estados" for p in profiles_sorted],
        textposition='outside',
        hovertemplate='%{y}<br>IDDE: %{x:.1f}<extra></extra>',
    ))

    fig.add_vline(
        x=c2_idde,
        line_dash='dot', line_color='rgba(46,204,113,0.6)', line_width=1.5,
        annotation_text='Nivel C2',
        annotation_font_color='#2ecc71',
        annotation_font_size=9,
    )

    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(title='IDDE 2025', gridcolor='rgba(255,255,255,0.06)', range=[0, max(p['avg_idde'] for p in profiles) * 1.25]),
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)'),
    )
    return fig


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def fig_state_radar(estado):
    """Radar chart: state vs cluster avg vs national mean, 6 dimensions."""
    data = get_radar_data(estado)
    if data is None:
        return go.Figure()

    labels  = data['labels'] + [data['labels'][0]]
    state   = data['state']  + [data['state'][0]]
    cluster = data['cluster']+ [data['cluster'][0]]
    nat     = data['national']+ [data['national'][0]]
    color   = data['cluster_color']
    code    = data['cluster_code']

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=nat, theta=labels,
        fill=None, name='Media nacional',
        line=dict(color='rgba(255,255,255,0.25)', dash='dot', width=1),
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatterpolar(
        r=cluster, theta=labels,
        fill='toself', name=f'Media {code}',
        fillcolor=_hex_rgba(color, 0.13),
        line=dict(color=_hex_rgba(color, 0.47), width=1.5),
    ))
    fig.add_trace(go.Scatterpolar(
        r=state, theta=labels,
        fill='toself', name=estado,
        fillcolor=_hex_rgba(color, 0.27),
        line=dict(color=color, width=2),
    ))

    fig.update_layout(
        **_LAYOUT,
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True, range=[0, 1],
                gridcolor='rgba(255,255,255,0.08)',
                tickfont=dict(size=8), showticklabels=False,
            ),
            angularaxis=dict(
                gridcolor='rgba(255,255,255,0.08)',
                tickfont=dict(size=10, color='#c8c8d8'),
            ),
        ),
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=9)),
        title=dict(text=f'Perfil de {estado}', font=dict(size=12), x=0.5, xanchor='center'),
    )
    return fig
