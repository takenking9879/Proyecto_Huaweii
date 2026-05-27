import re
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from pages.get_data.get_data_7 import (
    get_percepcion_estados, get_confianza_institucional,
    get_confianza_institucional_por_estado,
    get_gastos_por_estrato,
    get_infra_vs_trust,
    get_idde_vs_percepcion,
)

C_RED   = '#cf0a2c'
C_CYAN  = '#00b4cc'
C_GOLD  = '#c9922a'
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


def fig_percepcion_inseguridad(highlight_state=None):
    df = get_percepcion_estados().sort_values('pct_inseguro', ascending=True)
    h = highlight_state if highlight_state and highlight_state != 'Nacional' else None

    if h:
        marker_color = []
        for _, row in df.iterrows():
            e = row['estado']
            v = row['pct_inseguro']
            if e == h:
                marker_color.append(C_RED if v > 75 else (C_GOLD if v > 50 else C_CYAN))
            else:
                marker_color.append('rgba(92,92,116,0.25)')
    else:
        marker_color = [C_RED if v > 75 else (C_GOLD if v > 50 else C_CYAN)
                        for v in df['pct_inseguro']]

    fig = go.Figure(go.Bar(
        y=df['estado'], x=df['pct_inseguro'], orientation='h',
        marker=dict(color=marker_color, line=dict(width=0)),
        hovertemplate='<b>%{y}</b><br>%{x:.1f}% inseguro<extra></extra>',
    ))
    fig.add_vline(x=75, line_dash='dash', line_color='rgba(255,255,255,0.3)',
                  annotation_text='75%', annotation_font_color=C_MUTED,
                  annotation_position='top right')

    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 100],
                   title=dict(text='% que se siente inseguro', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=9)),
        height=580, bargap=0.15,
    )
    return fig


def fig_confianza_institucional_estado(estado=None):
    """Confidence in institutions: state-level if estado given, national otherwise."""
    df = get_confianza_institucional_por_estado(estado if estado and estado != 'Nacional' else None)
    colors = [C_CYAN if v >= 60 else (C_GOLD if v >= 40 else C_RED)
              for v in df['pct_confianza']]
    title = f'Confianza en instituciones — {estado}' if estado and estado != 'Nacional' else 'Confianza en instituciones (% positiva)'

    fig = go.Figure(go.Bar(
        y=df['institucion'], x=df['pct_confianza'], orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate='<b>%{y}</b><br>%{x:.1f}% confía<extra></extra>',
        text=[f'{v:.1f}%' for v in df['pct_confianza']],
        textposition='outside',
        textfont=dict(size=10, color=C_TEXT),
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text=title, font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 100],
                   title=dict(text='% con confianza positiva', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED),
        bargap=0.25,
    )
    return fig


def fig_confianza_institucional():
    df = get_confianza_institucional()
    fig = go.Figure(go.Bar(
        y=df['institucion'], x=df['pct_confianza'], orientation='h',
        marker=dict(
            color=[C_CYAN if v >= 60 else (C_GOLD if v >= 40 else C_RED)
                   for v in df['pct_confianza']],
            line=dict(width=0),
        ),
        hovertemplate='<b>%{y}</b><br>%{x:.1f}% confía<extra></extra>',
        text=[f'{v:.1f}%' for v in df['pct_confianza']],
        textposition='outside',
        textfont=dict(size=10, color=C_TEXT),
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 100],
                   title=dict(text='% con confianza positiva', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED),
        bargap=0.25,
    )
    return fig


def fig_gastos_por_estrato():
    df = get_gastos_por_estrato()
    estratos_order = ['Bajo', 'Medio bajo', 'Medio alto', 'Alto']

    def _bucket(rango):
        if not isinstance(rango, str) or rango.strip() == '':
            return ('0', 'Sin gasto')
        low = rango.lower().strip()
        if low in ('undefined', 'no aplica', 'no especificado'):
            return ('0', 'Sin gasto')
        if '<' in rango and '$' in rango:
            return ('1', 'Hasta $1k')
        nums = re.findall(r'\d+', rango.replace(',', ''))
        v = int(nums[0]) if nums else 0
        if v == 0:
            return ('0', 'Sin gasto')
        if v < 10:
            return ('2', '$1k – $10k')
        if v < 20:
            return ('3', '$10k – $20k')
        if v < 35:
            return ('4', '$20k – $35k')
        return ('5', '> $35k')

    bk = df['gastos_rango'].apply(_bucket)
    df = df.copy()
    df['_bk'] = [t[0] for t in bk]
    df['_bl'] = [t[1] for t in bk]

    agg = df.groupby(['estrato', '_bk', '_bl'])['pct'].sum().reset_index()

    bucket_order = [
        ('0', 'Sin gasto',     C_MUTED),
        ('1', 'Hasta $1k',     '#2a3a5a'),
        ('2', '$1k – $10k',    '#2d5a8e'),
        ('3', '$10k – $20k',   C_CYAN),
        ('4', '$20k – $35k',   C_GOLD),
        ('5', '> $35k',        C_RED),
    ]

    fig = go.Figure()
    for key, label, color in bucket_order:
        sub = agg[agg['_bk'] == key]
        y_vals = [float(sub[sub['estrato'] == e]['pct'].values[0])
                  if len(sub[sub['estrato'] == e]) > 0 else 0.0
                  for e in estratos_order]
        if sum(y_vals) == 0:
            continue
        fig.add_trace(go.Bar(
            name=label, x=estratos_order, y=y_vals,
            marker_color=color, opacity=0.88,
            hovertemplate=f'<b>{label}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        barmode='stack',
        xaxis=dict(showgrid=False, color=C_MUTED),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 100],
                   title=dict(text='% de hogares', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0.5, xanchor='center', y=1.06),
        bargap=0.3,
    )
    return fig


def fig_idde_vs_percepcion(highlight_state=None):
    """EXP-09: IDDE vs % who feel safe — R²≈0.445. Main chart for slide_7."""
    df = get_idde_vs_percepcion()
    if df.empty:
        return go.Figure()

    idde_col = 'indice_de_desarrollo_digital_estatal_2025'
    h = highlight_state if highlight_state and highlight_state != 'Nacional' else None

    df = df.copy()
    df['pct_seguro'] = df['percepcion_segura'] * 100
    x = df[idde_col].values
    y = df['pct_seguro'].values

    slope, intercept, r, _, _ = stats.linregress(x, y)
    r2 = r ** 2
    xi = np.linspace(x.min(), x.max(), 100)
    y_pred = slope * x + intercept
    residuals = y - y_pred

    labels = (df['estado']
              .str.replace(' de Ignacio de la Llave', '', regex=False)
              .str.replace(' de Zaragoza', '', regex=False)
              .str.replace(' de Ocampo', '', regex=False)
              .str.replace('Ciudad de México', 'CDMX', regex=False)
              .str.replace('Baja California Sur', 'BCS', regex=False)
              .str.replace('Nuevo León', 'NL', regex=False)
              .str.replace('Estado de México', 'EdoMex', regex=False))

    if h and h in df['estado'].values:
        marker_colors = [
            C_GOLD if e == h else
            ('rgba(92,92,116,0.55)' if abs(residuals[i]) < 6 else
             ('rgba(207,10,44,0.55)' if residuals[i] < -6 else 'rgba(0,184,122,0.55)'))
            for i, e in enumerate(df['estado'])
        ]
        marker_sizes  = [15 if e == h else 9 for e in df['estado']]
        text_colors   = [C_TEXT if e == h else 'rgba(184,184,204,0.55)' for e in df['estado']]
    else:
        marker_colors = [
            C_RED if residuals[i] < -6 else ('#2ecc71' if residuals[i] > 6 else C_CYAN)
            for i in range(len(df))
        ]
        marker_sizes  = [10] * len(df)
        text_colors   = ['rgba(184,184,204,0.75)'] * len(df)

    fig = go.Figure()

    # Regression band
    fig.add_trace(go.Scatter(
        x=np.concatenate([xi, xi[::-1]]),
        y=np.concatenate([slope * xi + intercept + 6, (slope * xi + intercept - 6)[::-1]]),
        fill='toself', fillcolor='rgba(0,180,204,0.07)',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))

    # Regression line
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept, mode='lines',
        line=dict(color=C_CYAN, width=1.8, dash='dash'),
        name=f'Tendencia (r={r:.2f})', hoverinfo='skip',
    ))

    # Points
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        text=labels, textposition='top center',
        textfont=dict(size=7.5, color=text_colors),
        marker=dict(color=marker_colors, size=marker_sizes, opacity=0.90,
                    line=dict(color=C_PAPER, width=1.2)),
        hovertemplate='<b>%{text}</b><br>IDDE: %{x:.1f}<br>% Seguro: %{y:.1f}%<extra></extra>',
        showlegend=False,
    ))

    # R² annotation
    fig.add_annotation(
        xref='paper', yref='paper', x=0.02, y=0.97,
        text=(f'<b>R² = {r2:.3f}</b><br>'
              f'La infraestructura digital explica<br>'
              f'el {r2*100:.0f}% de la varianza en<br>percepción de seguridad'),
        showarrow=False, align='left',
        bgcolor='rgba(0,180,204,0.12)', bordercolor=C_CYAN, borderwidth=1,
        font=dict(size=10, color=C_TEXT),
    )

    fig.update_layout(**_BASE)
    fig.update_layout(
        margin=dict(l=70, r=30, t=20, b=60),
        xaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            title=dict(text='IDDE 2025', font=dict(size=11)),
        ),
        yaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
            title=dict(text='% que se siente seguro (ENVIPE)', font=dict(size=11)),
        ),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.98, y=0.04,
                    xanchor='right'),
        showlegend=True,
    )
    return fig


def fig_infra_vs_trust(highlight_state=None):
    df = get_infra_vs_trust()
    h = highlight_state if highlight_state and highlight_state != 'Nacional' else None

    x = df['idde_score'].values
    y = df['conf_amigos'].values
    labels = df['estado'].str.replace(' de Ignacio de la Llave', '')\
                          .str.replace(' de Zaragoza', '')\
                          .str.replace(' de Ocampo', '')

    if h and h in df['estado'].values:
        hl_idx = df[df['estado'] == h].index[0]
        marker_colors = []
        marker_sizes = []
        for i in range(len(df)):
            if i == hl_idx:
                marker_colors.append(C_GOLD)
                marker_sizes.append(16)
            else:
                marker_colors.append('rgba(92,92,116,0.55)')
                marker_sizes.append(9)
    else:
        marker_colors = [C_CYAN] * len(df)
        marker_sizes = [11] * len(df)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        text=labels,
        textposition='top center', textfont=dict(size=7.5, color=C_MUTED),
        marker=dict(color=marker_colors, size=marker_sizes, opacity=0.85,
                    line=dict(color=C_PAPER, width=1.5)),
        hovertemplate='<b>%{text}</b><br>IDDE: %{x:.1f}<br>Confianza amigos: %{y:.2f}<extra></extra>',
    ))

    slope, intercept, r, p, _ = stats.linregress(x, y)
    xi = np.linspace(x.min(), x.max(), 100)
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept,
        mode='lines',
        line=dict(color='rgba(200,200,200,0.5)', width=1.5, dash='dash'),
        name=f'r = {r:.2f}', hoverinfo='skip',
    ))

    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED,
                   title=dict(text='Índice IDDE 2024', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED,
                   title=dict(text='Confianza en amigos (score 1–4)', font=dict(size=11))),
    )
    return fig
