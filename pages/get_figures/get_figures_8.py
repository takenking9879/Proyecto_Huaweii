import plotly.graph_objects as go
import numpy as np
from pages.get_data.get_data_8 import (
    get_salario_por_educacion, get_salario_por_estado,
    get_roc_data, get_shap_data,
)

C_RED   = '#cf0a2c'
C_CYAN  = '#00b4cc'
C_GOLD  = '#c9922a'
C_PAPER = '#1a1a24'
C_PLOT  = '#111118'
C_TEXT  = '#e8e8f0'
C_MUTED = '#5c5c74'

_ROC_STYLES = [
    (C_CYAN,    'solid',   3.5),   # Random Forest
    (C_GOLD,    'dash',    2.5),   # Reg. Logística
    ('#7b2fbe', 'dot',     2.5),   # XGBoost
    ('#2ca02c', 'dashdot', 2.5),   # Red Neuronal
]

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    hoverlabel=dict(bgcolor=C_PAPER, font_color=C_TEXT),
)


def fig_salario_educacion():
    df = get_salario_por_educacion()
    fig = go.Figure(go.Bar(
        x=df['instruction_level'], y=df['salario_promedio'],
        marker=dict(color=C_CYAN, opacity=0.85, line=dict(width=0)),
        hovertemplate='<b>%{x}</b><br>Salario promedio: $%{y:,.0f}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=False, color=C_MUTED, tickangle=-30,
                   tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, tickprefix='$',
                   title=dict(text='Salario mensual promedio', font=dict(size=11))),
        bargap=0.25,
    )
    return fig


def fig_salario_estado():
    df = get_salario_por_estado()
    fig = go.Figure(go.Bar(
        y=df['estado'], x=df['salario_promedio'], orientation='h',
        marker=dict(
            color=[C_GOLD if v > df['salario_promedio'].median() else C_MUTED
                   for v in df['salario_promedio']],
            line=dict(width=0),
        ),
        hovertemplate='<b>%{y}</b><br>$%{x:,.0f}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, tickprefix='$',
                   title=dict(text='Salario mensual promedio', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=9)),
        height=550, bargap=0.15,
    )
    return fig


def fig_roc():
    roc, aucs = get_roc_data()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dot'),
        name='Azar', hoverinfo='skip',
    ))
    for i, (name, (fpr, tpr)) in enumerate(roc.items()):
        clr, dsh, wid = _ROC_STYLES[i % len(_ROC_STYLES)]
        fig.add_trace(go.Scatter(
            x=fpr, y=tpr, mode='lines',
            name=f'{name}  AUC={aucs[name]}',
            line=dict(color=clr, width=wid, dash=dsh),
            hovertemplate=f'<b>{name}</b><br>FPR: %{{x:.3f}}<br>TPR: %{{y:.3f}}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 1],
                   title=dict(text='Tasa de falsos positivos', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, range=[0, 1],
                   title=dict(text='Tasa de verdaderos positivos', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.55, y=0.1),
    )
    return fig


def fig_shap():
    df = get_shap_data()
    feat_labels = {
        'schooling_years':       'Años de escolaridad',
        'instruction_level_id':  'Nivel educativo',
        'job_situation_id':      'Situación laboral',
        'grupo_nivel':           'Nivel digit. estatal',
        'year':                  'Año',
    }
    df['label'] = df['feature'].map(feat_labels).fillna(df['feature'])
    max_imp      = df['importance'].max()
    arrow_colors = [('#2ca02c' if d == '↑' else '#cf0a2c' if d == '↓' else C_MUTED)
                    for d in df['direction']]
    hover_dir    = ['mayor valor → más prob. de salario alto' if d == '↑'
                    else 'mayor valor → menos prob. de salario alto' if d == '↓'
                    else 'variable no ordinal'
                    for d in df['direction']]
    fig = go.Figure(go.Bar(
        y=df['label'], x=df['importance'], orientation='h',
        marker=dict(
            color=[C_GOLD if v == max_imp else C_CYAN for v in df['importance']],
            line=dict(width=0),
        ),
        text=df['direction'],
        textposition='outside',
        textfont=dict(size=15, color=arrow_colors),
        customdata=hover_dir,
        hovertemplate='<b>%{y}</b><br>Importancia SHAP: %{x:.4f}<br>Dirección: %{customdata}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, title=dict(text='Importancia SHAP media |φ|', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED),
        bargap=0.3,
    )
    fig.update_layout(margin=dict(r=30))
    return fig
