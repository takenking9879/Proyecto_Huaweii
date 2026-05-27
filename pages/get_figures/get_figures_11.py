"""
get_figures_11.py — Infraestructura Digital × Seguridad en México
Figures for personal_analysis.ipynb → slide_11
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pages.get_data.get_data_11 import (
    get_data_11, INFRA_VARS, INFRA_GROUPS, SEC_COL_LABELS, SEC_GROUPS,
)

# ── Colour palette ────────────────────────────────────────────────────────────
C_RED    = '#cf0a2c'
C_CYAN   = '#00b4cc'
C_GOLD   = '#c9922a'
C_GREEN  = '#2ca02c'
C_PAPER  = '#1a1a24'
C_PLOT   = '#111118'
C_TEXT   = '#e8e8f0'
C_MUTED  = '#5c5c74'
C_BLUE   = '#3891c7'
C_ORANGE = '#e4982e'

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=44, b=10),
    hoverlabel=dict(bgcolor='#0f0f18', font_color=C_TEXT,
                    bordercolor='rgba(255,255,255,0.1)'),
)

_GRID  = dict(showgrid=True,  gridcolor='rgba(255,255,255,0.05)', zeroline=False, color=C_MUTED)
_NOGRID = dict(showgrid=False, zeroline=False, color=C_MUTED)

_rgba = lambda h, a=0.22: f'rgba({int(h[1:3],16)},{int(h[3:5],16)},{int(h[5:7],16)},{a})'

_GROUP_Y_COLORS = {
    'Conectividad':        C_CYAN,
    'Velocidad/Calidad':   C_BLUE,
    'Datos/Nube':          C_GOLD,
    'Economía digital':    C_GREEN,
    'Cap. humano/Digital': '#9b59b6',
    'IDDE/Pilares':        C_RED,
}
_GROUP_X_COLORS = {
    'Crimen (tasas)':      C_RED,
    'Percepción':          C_GOLD,
    'Conf. institucional': C_CYAN,
    'Conf. social':        C_GREEN,
    'Económico':           C_ORANGE,
}

_IDDE_COL = 'indice_de_desarrollo_digital_estatal_2025'


def _abbrev(s: str) -> str:
    return (str(s)
            .replace(' de Ignacio de la Llave', '')
            .replace(' de Ocampo', '')
            .replace('Ciudad de México', 'CDMX')
            .replace('Baja California Sur', 'BCS')
            .replace('Baja California', 'BC')
            .replace('Nuevo León', 'NL'))


# ── 1. Crime type correlations ────────────────────────────────────────────────
def fig_crime_type_corrs():
    d   = get_data_11()
    ctc = d['crime_type_corrs']
    if not ctc:
        return go.Figure()

    items  = sorted(ctc.items(), key=lambda x: abs(x[1]['r']))
    labels = [k for k, _ in items]
    rs     = [v['r'] for _, v in items]
    rates  = [v['mean_rate'] for _, v in items]
    colors = [C_GREEN if r >= 0 else C_RED for r in rs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=rs, orientation='h',
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        customdata=[[round(rate, 1)] for rate in rates],
        hovertemplate='<b>%{y}</b><br>r con IDDE: %{x:.3f}<br>Tasa media: %{customdata[0]}/100k<extra></extra>',
    ))

    fig.add_vline(x=0, line=dict(color='rgba(255,255,255,0.25)', width=1))
    for xv in (0.3, -0.3):
        fig.add_vline(
            x=xv, line=dict(color=C_GOLD, width=1, dash='dash'),
            annotation_text='  r=0.3' if xv > 0 else None,
            annotation_position='top right',
            annotation_font=dict(color=C_GOLD, size=9),
        )

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=140, r=20, t=56, b=44)},
        title=dict(
            text='Correlación IDDE 2025 × tipo de delito — ¿cuál crimen se asocia con más digitalización?',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        xaxis=dict(**_GRID, title=dict(text='Correlación de Pearson (r)', font=dict(size=10)),
                   range=[-0.75, 0.75]),
        yaxis=dict(**_NOGRID, tickfont=dict(size=11)),
        height=340,
    )
    return fig


# ── 2. Grouped correlation heatmap ────────────────────────────────────────────
def fig_corr_heatmap():
    d   = get_data_11()
    corr         = d['corr_matrix']
    infra_gsizes = d['infra_group_sizes']
    sec_gsizes   = d['sec_group_sizes']

    if corr.empty:
        return go.Figure()

    y_labs = list(corr.index)
    x_labs = list(corr.columns)

    # Ordered group lists (preserve insertion order from sorted labels)
    infra_groups_ordered = list(dict.fromkeys(
        INFRA_GROUPS.get(lbl, 'Otro') for lbl in y_labs))
    sec_groups_ordered = list(dict.fromkeys(
        SEC_GROUPS.get(lbl, 'Otro') for lbl in x_labs))

    fig = go.Figure(go.Heatmap(
        z=corr.values.tolist(),
        x=x_labs,
        y=y_labs,
        zmin=-1, zmax=1,
        colorscale=[
            [0.0,  '#c0392b'],
            [0.25, '#e74c3c'],
            [0.48, '#2a2a38'],
            [0.52, '#2a2a38'],
            [0.75, '#27ae60'],
            [1.0,  '#2ecc71'],
        ],
        colorbar=dict(
            title=dict(text='r', font=dict(size=11, color=C_MUTED)),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=['-1', '-0.5', '0', '0.5', '1'],
            tickfont=dict(size=9, color=C_MUTED),
            len=0.65, thickness=12, x=1.01,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(255,255,255,0.08)',
        ),
        hovertemplate='<b>%{y}</b> × <b>%{x}</b><br>r = %{z:.3f}<extra></extra>',
        xgap=0.5, ygap=0.5,
    ))

    # Group separator shapes
    shapes = []
    row_cum = 0
    for grp in infra_groups_ordered:
        n = infra_gsizes.get(grp, 0)
        row_cum += n
        shapes.append(dict(
            type='line', xref='paper', yref='y',
            x0=0, x1=1,
            y0=row_cum - 0.5, y1=row_cum - 0.5,
            line=dict(color='rgba(255,255,255,0.22)', width=1.5),
        ))
    col_cum = 0
    for grp in sec_groups_ordered:
        n = sec_gsizes.get(grp, 0)
        col_cum += n
        shapes.append(dict(
            type='line', xref='x', yref='paper',
            x0=col_cum - 0.5, x1=col_cum - 0.5,
            y0=0, y1=1,
            line=dict(color='rgba(255,255,255,0.22)', width=1.5),
        ))

    # Group label annotations
    annotations = []
    row_pos = 0
    for grp in infra_groups_ordered:
        n   = infra_gsizes.get(grp, 0)
        mid = row_pos + n / 2 - 0.5
        color = _GROUP_Y_COLORS.get(grp, C_MUTED)
        annotations.append(dict(
            x=-0.01, y=mid, xref='paper', yref='y',
            text=f'<b>{grp}</b>',
            font=dict(size=7.5, color=color),
            textangle=-90, showarrow=False, xanchor='right',
        ))
        row_pos += n

    col_pos = 0
    for grp in sec_groups_ordered:
        n   = sec_gsizes.get(grp, 0)
        mid = col_pos + n / 2 - 0.5
        color = _GROUP_X_COLORS.get(grp, C_MUTED)
        annotations.append(dict(
            x=mid, y=1.02, xref='x', yref='paper',
            text=f'<b>{grp}</b>',
            font=dict(size=7.5, color=color),
            showarrow=False, yanchor='bottom',
        ))
        col_pos += n

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=130, r=60, t=80, b=110)},
        title=dict(
            text='Matriz de correlación agrupada — Infraestructura digital × Seguridad (32 estados, 2025)',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(tickfont=dict(size=8, color=C_MUTED), tickangle=-45,
                   showgrid=False, zeroline=False),
        yaxis=dict(tickfont=dict(size=8, color=C_MUTED), showgrid=False,
                   zeroline=False, autorange='reversed'),
        height=640,
    )
    return fig


# ── 3. Six key scatter plots (2×3 grid) ──────────────────────────────────────
def fig_6_scatters():
    d       = get_data_11()
    cross   = d['cross']

    _PAIRS = [
        (_IDDE_COL, 'fraude_rate_100k',
         'IDDE 2025', 'Fraudes /100k hab',    C_GREEN, 'IDDE × Fraudes'),
        ('cobertura_de_banda_ancha_fija_por', 'conf_amigos',
         'Cobertura BB fija (%)', 'Conf. Amigos',    C_CYAN,  'Cobertura × Confianza social'),
        ('velocidad_de_descarga_de_banda_ancha_movil_mbps', 'avg_wage',
         'Vel. BB móvil (Mbps)', 'Salario prom. ($)', C_BLUE, 'Velocidad × Salarios'),
    ]

    titles = [p[5] for p in _PAIRS]
    fig = make_subplots(rows=1, cols=3, subplot_titles=titles,
                        horizontal_spacing=0.10, vertical_spacing=0.12)

    for idx, (xc, yc, xl, yl, color, _) in enumerate(_PAIRS):
        r = 1
        c = idx + 1

        cols_need = [xc, yc] + (['estado'] if 'estado' in cross.columns else [])
        sub = cross[cols_need].dropna()
        if len(sub) < 5:
            continue
        xs    = sub[xc].tolist()
        ys    = sub[yc].tolist()
        texts = [_abbrev(s) for s in sub['estado'].tolist()] if 'estado' in sub.columns else [''] * len(xs)
        r_val = float(sub[xc].corr(sub[yc]))

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers', text=texts,
            marker=dict(color=color, size=7, opacity=0.78,
                        line=dict(color=C_PAPER, width=0.8)),
            hovertemplate=f'<b>%{{text}}</b><br>{xl}: %{{x:.1f}}<br>{yl}: %{{y:.1f}}<extra></extra>',
            showlegend=False,
        ), row=r, col=c)

        x_arr = np.array(xs, dtype=float)
        y_arr = np.array(ys, dtype=float)
        if len(x_arr) > 2 and np.std(x_arr) > 0:
            m, b2 = np.polyfit(x_arr, y_arr, 1)
            xl2 = [float(x_arr.min()), float(x_arr.max())]
            yl2 = [m * xl2[0] + b2, m * xl2[1] + b2]
            fig.add_trace(go.Scatter(
                x=xl2, y=yl2, mode='lines',
                line=dict(color=color, width=1.8, dash='dot'),
                showlegend=False, hoverinfo='skip',
            ), row=r, col=c)

        fig.add_annotation(
            row=r, col=c,
            x=0.96, y=0.06, xref='x domain', yref='y domain',
            text=f'r={r_val:.2f}',
            font=dict(size=10, color=color),
            showarrow=False, xanchor='right',
        )

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=52, b=10)},
        height=340,
        title=dict(
            text='3 relaciones clave — Infraestructura digital × Seguridad en México',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        showlegend=False,
    )
    for i in range(1, 4):
        suf = '' if i == 1 else str(i)
        fig.update_layout(**{
            f'xaxis{suf}': dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                zeroline=False, color=C_MUTED, tickfont=dict(size=8)),
            f'yaxis{suf}': dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                zeroline=False, color=C_MUTED, tickfont=dict(size=8)),
        })
    return fig


# ── 4. K-Means clustering scatter ────────────────────────────────────────────
def fig_clustering_scatter():
    d         = get_data_11()
    cross_cl  = d['cross_cl']
    label_map = d['label_map']

    if cross_cl.empty:
        return go.Figure()

    fig = go.Figure()
    for c_id, (code, name, color, _desc) in label_map.items():
        sub = cross_cl[cross_cl['cluster'] == c_id]
        if sub.empty:
            continue
        texts = [_abbrev(e) for e in sub['estado'].tolist()]
        fig.add_trace(go.Scatter(
            x=sub[_IDDE_COL].tolist(),
            y=sub['crime_rate_100k'].tolist(),
            mode='markers+text',
            name=f'{code} · {name}',
            text=texts,
            textfont=dict(size=7.5, color=color),
            textposition='top center',
            marker=dict(color=color, size=11, opacity=0.85,
                        line=dict(color=C_PAPER, width=1.5)),
            hovertemplate=(
                f'<b>%{{text}}</b><br>IDDE: %{{x:.1f}}<br>'
                f'Crimen /100k: %{{y:.0f}}<br>{code} · {name}<extra></extra>'
            ),
        ))

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=44, b=70)},
        title=dict(
            text='K-Means k=4 — 4 perfiles de estados según digitalización + seguridad',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        xaxis=dict(**_GRID, title=dict(text='IDDE 2025', font=dict(size=10))),
        yaxis=dict(**_GRID, title=dict(text='Crimen total /100k hab', font=dict(size=10))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0.5, xanchor='center', y=-0.18),
        height=440,
    )
    return fig


# ── 5. Cluster box profiles (IDDE / crimen / percepción) ─────────────────────
def fig_cluster_profiles():
    d         = get_data_11()
    cross_cl  = d['cross_cl']
    label_map = d['label_map']

    if cross_cl.empty:
        return go.Figure()

    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=['IDDE 2025', 'Crimen /100k', 'Percepción seg. (0-1)'],
                        horizontal_spacing=0.06)

    for c_id, (code, name, color, _) in label_map.items():
        sub = cross_cl[cross_cl['cluster'] == c_id]
        if sub.empty:
            continue
        kw_base = dict(
            name=f'{code}', marker_color=color,
            fillcolor=_rgba(color, 0.25), line_color=color,
            boxpoints='all', pointpos=0, jitter=0.4,
            marker=dict(size=6, opacity=0.7),
        )

        fig.add_trace(go.Box(
            y=sub[_IDDE_COL].tolist(),
            showlegend=False, **kw_base,
        ), row=1, col=1)

        fig.add_trace(go.Box(
            y=sub['crime_rate_100k'].tolist(),
            showlegend=False, **kw_base,
        ), row=1, col=2)

        perc_col = 'percepcion_segura'
        if perc_col in sub.columns:
            fig.add_trace(go.Box(
                y=sub[perc_col].dropna().tolist(),
                showlegend=False, **kw_base,
            ), row=1, col=3)

    # Legend
    for c_id, (code, name, color, _) in label_map.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(color=color, size=10, symbol='square'),
            name=f'{code} · {name}', showlegend=True,
        ))

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=44, b=80)},
        title=dict(
            text='Perfil por cluster — distribución de variables clave',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0.5, xanchor='center', y=-0.26),
        height=360,
    )
    for i in range(1, 4):
        suf = '' if i == 1 else str(i)
        fig.update_layout(**{
            f'xaxis{suf}': dict(showgrid=False, zeroline=False, color=C_MUTED),
            f'yaxis{suf}': dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                zeroline=False, color=C_MUTED, tickfont=dict(size=8)),
        })
    return fig


# ── 6. Panel scatter ΔIDDE × ΔCrimen ─────────────────────────────────────────
def fig_panel_scatter():
    d          = get_data_11()
    changes_df = d['changes_df']
    panel_r    = d['panel_r_overall']

    if changes_df.empty:
        return go.Figure()

    dx    = changes_df['didde'].tolist()
    dy    = changes_df['dcrime'].tolist()
    texts = [_abbrev(s) for s in changes_df['estado'].tolist()]

    x_arr = np.array(dx, dtype=float)
    y_arr = np.array(dy, dtype=float)
    if len(x_arr) > 2 and np.std(x_arr) > 0:
        m, b = np.polyfit(x_arr, y_arr, 1)
        xl = [float(x_arr.min()), float(x_arr.max())]
        yl = [m * xl[0] + b, m * xl[1] + b]
    else:
        xl, yl = [], []

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dx, y=dy, mode='markers+text',
        text=texts,
        textfont=dict(size=7.5, color=C_MUTED),
        textposition='top center',
        marker=dict(color=C_CYAN, size=9, opacity=0.82,
                    line=dict(color=C_PAPER, width=1.2)),
        hovertemplate='<b>%{text}</b><br>ΔIDDE: %{x:.1f}<br>ΔCrimen/100k: %{y:.0f}<extra></extra>',
        showlegend=False,
    ))
    if xl:
        fig.add_trace(go.Scatter(
            x=xl, y=yl, mode='lines',
            line=dict(color=C_GOLD, width=2, dash='dash'),
            hoverinfo='skip', showlegend=False,
        ))

    fig.add_hline(y=0, line=dict(color='rgba(255,255,255,0.16)', width=1))
    fig.add_vline(x=0, line=dict(color='rgba(255,255,255,0.16)', width=1))

    fig.add_annotation(
        x=0.98, y=0.95, xref='paper', yref='paper',
        text=f'r = {panel_r:.3f}',
        font=dict(size=14, color=C_GOLD), showarrow=False, xanchor='right',
        bgcolor='rgba(0,0,0,0.45)', bordercolor=C_GOLD, borderwidth=1, borderpad=6,
    )

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=60, r=20, t=56, b=56)},
        title=dict(
            text='Panel 2022→2025 — ΔDigitalización vs ΔCrimen dentro del mismo estado',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        xaxis=dict(**_GRID, title=dict(text='ΔIDDE (2025 − 2022)', font=dict(size=10))),
        yaxis=dict(**_GRID, title=dict(text='ΔCrimen por 100k hab', font=dict(size=10))),
        height=400,
    )
    return fig


# ── 7. Velocity vs Coverage R² bars ──────────────────────────────────────────
def fig_velocity_vs_coverage():
    d    = get_data_11()
    r2df = d['r2_df']

    if r2df.empty:
        return go.Figure()

    targets = r2df['target'].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Solo Cobertura', x=targets, y=r2df['r2_cob'].tolist(),
        marker=dict(color=C_CYAN, opacity=0.82),
        hovertemplate='%{x}<br>Cobertura R²: %{y:.3f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Solo Velocidad', x=targets, y=r2df['r2_vel'].tolist(),
        marker=dict(color=C_GOLD, opacity=0.82),
        hovertemplate='%{x}<br>Velocidad R²: %{y:.3f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Ambas', x=targets, y=r2df['r2_amb'].tolist(),
        marker=dict(color=C_GREEN, opacity=0.82),
        hovertemplate='%{x}<br>Ambas R²: %{y:.3f}<extra></extra>',
    ))

    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=56, b=60)},
        title=dict(
            text='¿Velocidad o cobertura? — R² al predecir salarios, crimen y homicidios',
            font=dict(size=12, color=C_TEXT), x=0.5,
        ),
        barmode='group',
        xaxis=dict(**_NOGRID, tickfont=dict(size=11)),
        yaxis=dict(**_GRID, title=dict(text='R²', font=dict(size=10)), range=[0, 0.75]),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0.5, xanchor='center', y=-0.24),
        height=340,
    )
    return fig
