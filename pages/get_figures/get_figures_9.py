import plotly.graph_objects as go
from pages.get_data.get_data_9 import (
    get_empresas_por_estado, get_distribucion_tamano,
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
    (C_CYAN,    'solid',   3.5),
    (C_GOLD,    'dash',    2.5),
    ('#7b2fbe', 'dot',     2.5),
    ('#2ca02c', 'dashdot', 2.5),
]

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    hoverlabel=dict(bgcolor=C_PAPER, font_color=C_TEXT),
)


def fig_empresas_por_estado(year=None):
    df = get_empresas_por_estado(year)
    median = df['companies'].median()
    fig = go.Figure(go.Bar(
        y=df['estado'], x=df['companies'], orientation='h',
        marker=dict(
            color=[C_GOLD if v > median else C_CYAN for v in df['companies']],
            line=dict(width=0),
        ),
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} empresas<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, tickformat=',.0f',
                   title=dict(text='Total de empresas', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED, tickfont=dict(size=9)),
        height=560, bargap=0.15,
    )
    return fig


def fig_distribucion_tamano(year=None):
    df = get_distribucion_tamano(year)
    palette = [C_CYAN, C_GOLD, C_RED, '#7b2fbe', '#2ca02c']
    fig = go.Figure(go.Bar(
        x=df['company_size'], y=df['companies'],
        marker=dict(color=palette[:len(df)], line=dict(width=0)),
        hovertemplate='<b>%{x}</b><br>%{y:,.0f} empresas<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        xaxis=dict(showgrid=False, color=C_MUTED,
                   title=dict(text='Tamaño de empresa (empleados)', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                   color=C_MUTED, tickformat=',.0f',
                   title=dict(text='Número de empresas', font=dict(size=11))),
        bargap=0.2,
    )
    return fig


def fig_roc():
    roc_train, roc_cv, aucs_tr, aucs_cv = get_roc_data()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dot'),
        name='Azar', hoverinfo='skip',
    ))
    for i, name in enumerate(roc_cv):
        fpr, tpr = roc_cv[name]
        clr, dsh, wid = _ROC_STYLES[i % len(_ROC_STYLES)]
        auc_cv = aucs_cv[name]
        auc_tr = aucs_tr[name]
        lbl    = f'{name}  CV={auc_cv}' + (f' (train={auc_tr})' if auc_tr != auc_cv else '')
        fig.add_trace(go.Scatter(
            x=fpr, y=tpr, mode='lines',
            name=lbl,
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
        legend=dict(font=dict(size=9), bgcolor='rgba(0,0,0,0)', x=0.33, y=0.05),
        annotations=[dict(
            text='AUC validación cruzada 5-fold  (train AUC entre paréntesis = sobreajuste)',
            xref='paper', yref='paper', x=0.5, y=1.02,
            showarrow=False, font=dict(size=9, color=C_MUTED), align='center',
        )],
    )
    return fig


def fig_shap():
    df = get_shap_data()
    df['label'] = df['feature'].str.replace('size_', 'Empresas t. ').str.replace('_', ' ')
    max_imp      = df['importance'].max()
    arrow_colors = [('#2ca02c' if d == '↑' else '#cf0a2c' if d == '↓' else C_MUTED)
                    for d in df['direction']]
    hover_dir    = ['mayor proporción → más probable alta densidad' if d == '↑'
                    else 'mayor proporción → menos probable alta densidad' if d == '↓'
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
        hovertemplate='<b>%{y}</b><br>SHAP: %{x:.4f}<br>Dirección: %{customdata}<extra></extra>',
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
