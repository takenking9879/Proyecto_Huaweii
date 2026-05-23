import re
import plotly.graph_objects as go
from pages.get_data.get_data_7 import get_percepcion_estados, get_confianza_institucional, get_gastos_por_estrato

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


def fig_percepcion_inseguridad():
    df = get_percepcion_estados().sort_values('pct_inseguro', ascending=True)
    colors = [C_RED if v > 75 else (C_GOLD if v > 50 else C_CYAN)
              for v in df['pct_inseguro']]
    fig = go.Figure(go.Bar(
        y=df['estado'], x=df['pct_inseguro'], orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
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
