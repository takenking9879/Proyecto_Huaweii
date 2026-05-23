import plotly.graph_objects as go
import numpy as np
from scipy import stats
from plotly.subplots import make_subplots
from pages.get_data.get_data_10 import get_ml
from pages.get_data.get_data_6 import GRUPO_COLORS, GRUPO_ORDER

C_RED   = '#cf0a2c'
C_CYAN  = '#00b4cc'
C_GOLD  = '#c9922a'
C_PAPER = '#1a1a24'
C_PLOT  = '#111118'
C_TEXT  = '#e8e8f0'
C_MUTED = '#5c5c74'

_CLUSTER_COLORS = ['#cf0a2c', '#00b4cc', '#c9922a']

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    hoverlabel=dict(bgcolor='#0f0f18', font_color=C_TEXT, bordercolor='rgba(255,255,255,0.1)'),
)

_FEAT_LABELS = {
    'tasa_Sociedad':   'Crimen Social',
    'tasa_Patrimonio': 'Crimen Patrimonial',
    'tasa_Vida':       'Crimen Violento',
    'tasa_Familia':    'Crimen Familiar',
    'tasa_Sexual':     'Crimen Sexual',
    'tasa_Estado':     'Crimen vs Estado',
    'share_Sociedad':  '% Social',
    'share_Patrimonio':'% Patrimonial',
    'share_Vida':      '% Vida',
    'share_Familia':   '% Familia',
    'share_Sexual':    '% Sexual',
    'share_Estado':    '% Estado',
    'policia_cibernetica_xmhab':          'Policía Cibernética',
    'graduados_en_programas_stem_xmhab':  'Graduados STEM',
    'habilidades_de_programacion_por':    'Habilidades Digitales',
    'anio_2023': 'Año 2023',
    'anio_2024': 'Año 2024',
}

_PC_THEME_NAMES = [
    'Escala de Criminalidad',
    'Estructura del Crimen',
    'Crimen Violento vs Digital',
    'Innovación vs Sociedad',
    'Contraste Temporal',
    'Particularidades Locales',
]


def _short(n):
    return (str(n).replace(' de Ignacio de la Llave', '')
                  .replace(' de Zaragoza', '').replace(' de Ocampo', ''))


def pc_display_name(pc_idx):
    ml = get_ml()
    if 'pc_loadings' not in ml or pc_idx >= len(ml['pc_loadings']):
        return f'PC{pc_idx + 1}'
    loadings   = ml['pc_loadings'][pc_idx]
    feat_names = ml['feat_names']
    top3 = np.argsort(np.abs(loadings))[::-1][:3]
    parts = []
    for i in top3:
        sign = '+' if loadings[i] > 0 else '−'
        parts.append(f"{sign}{_FEAT_LABELS.get(feat_names[i], feat_names[i])}")
    theme = _PC_THEME_NAMES[pc_idx] if pc_idx < len(_PC_THEME_NAMES) else f'PC{pc_idx+1}'
    return f'{theme}  ·  {", ".join(parts)}'


def fig_real_vs_pred():
    ml = get_ml()
    df = ml['df_main']
    rf = ml['models']['Random Forest']
    X  = ml['X_model']
    y  = ml['y']
    y_pred = rf.predict(X)

    grp_map = {g: GRUPO_COLORS[g] for g in GRUPO_ORDER}
    colors  = [grp_map.get(g, C_CYAN) for g in df['grupo_label'].values]

    mn, mx = float(y.min()), float(y.max())
    slope, intercept, r, _, _ = stats.linregress(y, y_pred)
    xi = np.linspace(mn, mx, 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[mn, mx], y=[mn, mx], mode='lines',
        line=dict(color='rgba(255,255,255,0.20)', width=1.5, dash='dash'),
        name='Perfecto', hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=y, y=y_pred, mode='markers',
        text=[_short(e) for e in df['estado']],
        marker=dict(color=colors, size=9, opacity=0.85,
                    line=dict(color=C_PAPER, width=1)),
        hovertemplate='<b>%{text}</b><br>Real: %{x:.1f}<br>Pred: %{y:.1f}<extra></extra>',
        name='Estado-año',
    ))
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept, mode='lines',
        line=dict(color=C_RED, width=2, dash='dot'),
        name=f'Ajuste r={r:.2f}', hoverinfo='skip',
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text='Real vs Predicho — Pilar Innovación', font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Pilar Innovación real', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Pilar Innovación predicho', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.01, y=0.99),
    )
    return fig


def fig_shap():
    ml  = get_ml()
    df  = ml['shap_df']
    top = df.tail(12).copy()
    max_imp = top['importance'].max()

    top['label'] = top['feature'].map(_FEAT_LABELS).fillna(top['feature'])

    X_sc = ml.get('X_sc')
    y    = ml['y']
    feat_names = ml['feat_names']
    dirs = {}
    if X_sc is not None:
        for i, feat in enumerate(feat_names):
            if i < X_sc.shape[1]:
                col = X_sc[:, i]
                if np.std(col) > 0:
                    corr = float(np.corrcoef(col, y)[0, 1])
                    dirs[feat] = '↑' if corr > 0 else '↓'
                else:
                    dirs[feat] = ''
    top['direction'] = top['feature'].map(dirs).fillna('')

    arrow_colors = [('#2ca02c' if d == '↑' else C_RED if d == '↓' else C_MUTED)
                    for d in top['direction']]
    hover_dir    = ['mayor tasa → más innovación' if d == '↑'
                    else 'mayor tasa → menos innovación' if d == '↓'
                    else 'sin correlación ordinal clara'
                    for d in top['direction']]

    fig = go.Figure(go.Bar(
        y=top['label'], x=top['importance'], orientation='h',
        marker=dict(
            color=[C_GOLD if v == max_imp else C_CYAN for v in top['importance']],
            line=dict(width=0),
        ),
        text=top['direction'],
        textposition='outside',
        textfont=dict(size=15, color=arrow_colors),
        customdata=hover_dir,
        hovertemplate='<b>%{y}</b><br>SHAP |φ|: %{x:.4f}<br>Dirección: %{customdata}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text='Importancia SHAP — ¿Qué crimen importa más?', font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Importancia media |φ|', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED),
        bargap=0.25,
    )
    fig.update_layout(margin=dict(r=30))
    return fig


def fig_cv_scores():
    ml = get_ml()
    scores = ml['cv_scores']
    names  = list(scores.keys())
    vals   = list(scores.values())
    best   = max(vals)

    fig = go.Figure(go.Bar(
        x=names, y=vals,
        marker=dict(
            color=[C_GOLD if v == best else C_CYAN for v in vals],
            line=dict(width=0),
        ),
        text=[f'{v:.3f}' for v in vals],
        textposition='outside', textfont=dict(size=11, color=C_TEXT),
        hovertemplate='<b>%{x}</b><br>R² CV: %{y:.3f}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text='R² por modelo — validación cruzada 5-fold', font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=False, color=C_MUTED),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   range=[0, 1.05],
                   title=dict(text='R² (5-fold CV)', font=dict(size=11))),
        bargap=0.3,
    )
    return fig


def fig_clustering():
    ml   = get_ml()
    df22 = ml['df22']
    if 'cluster' not in df22.columns:
        return go.Figure()

    tasa_col = 'tasa_Sociedad' if 'tasa_Sociedad' in df22.columns else 'tasa_x100k'

    fig = go.Figure()
    for c in sorted(df22['cluster'].unique()):
        sub = df22[df22['cluster'] == c]
        fig.add_trace(go.Scatter(
            x=sub['pilar_innovacion'],
            y=sub[tasa_col],
            mode='markers+text',
            text=[_short(e) for e in sub['estado']],
            textposition='top center',
            textfont=dict(size=7.5, color=C_MUTED),
            marker=dict(color=_CLUSTER_COLORS[c % len(_CLUSTER_COLORS)], size=12, opacity=0.88,
                        line=dict(color=C_PAPER, width=1.5)),
            name=f'Cluster {c + 1}',
            hovertemplate='<b>%{text}</b><br>Innovación: %{x:.1f}<br>Tasa Social: %{y:.1f}<extra></extra>',
        ))
    fig.update_layout(
        **_BASE,
        title=dict(text='Clustering de estados 2022 · Innovación vs Crimen Social  (K=2)', font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Pilar Innovación IDDE', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Tasa Sociedad (por 100 k hab.)', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)', x=0.01, y=0.99),
    )
    return fig


def _rgba(hex_clr, alpha=0.27):
    r, g, b = int(hex_clr[1:3], 16), int(hex_clr[3:5], 16), int(hex_clr[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'


def fig_cluster_boxplots():
    ml   = get_ml()
    df22 = ml['df22']
    if 'cluster' not in df22.columns:
        return go.Figure()
    tasa_col = 'tasa_Sociedad' if 'tasa_Sociedad' in df22.columns else 'tasa_x100k'
    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=['Pilar Innovación por cluster',
                                        'Tasa Crimen Social por cluster'],
                        vertical_spacing=0.14)
    for c in sorted(df22['cluster'].unique()):
        sub   = df22[df22['cluster'] == c]
        color = _CLUSTER_COLORS[c % len(_CLUSTER_COLORS)]
        lbl   = f'C{c+1}'
        for row, col_name in [(1, 'pilar_innovacion'), (2, tasa_col)]:
            fig.add_trace(go.Box(
                y=sub[col_name].values,
                name=lbl,
                marker_color=color,
                line_color=color,
                fillcolor=_rgba(color),
                boxpoints='all',
                jitter=0.4,
                pointpos=0,
                marker=dict(size=5, opacity=0.8),
                showlegend=(row == 1),
            ), row=row, col=1)
    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=44, b=10)},
        boxmode='group',
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)'),
    )
    for ax in ['xaxis', 'xaxis2', 'yaxis', 'yaxis2']:
        fig.update_layout(**{ax: dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                      color=C_MUTED, zeroline=False)})
    return fig


def fig_feature_scatter_poly(max_feats=6):
    ml      = get_ml()
    df      = ml['df_main']
    shap_df = ml['shap_df']
    y_all   = df['pilar_innovacion'].values.astype(float)
    top_feats = [f for f in shap_df.tail(max_feats)['feature'].tolist()[::-1]
                 if f in df.columns]
    if not top_feats:
        return go.Figure()
    cols_n = 3
    rows_n = (len(top_feats) + cols_n - 1) // cols_n
    titles = [_FEAT_LABELS.get(f, f) for f in top_feats]
    titles += [''] * (rows_n * cols_n - len(titles))
    fig = make_subplots(rows=rows_n, cols=cols_n,
                        subplot_titles=titles,
                        horizontal_spacing=0.08,
                        vertical_spacing=0.16)
    DEG_COLORS = {1: C_RED, 2: C_GOLD, 3: '#7b2fbe'}
    for idx, feat in enumerate(top_feats):
        r = idx // cols_n + 1
        c = idx % cols_n + 1
        x_raw = df[feat].values.astype(float)
        mask  = np.isfinite(x_raw) & np.isfinite(y_all)
        x_f, y_f = x_raw[mask], y_all[mask]
        if len(x_f) < 4:
            continue
        xi = np.linspace(x_f.min(), x_f.max(), 120)
        best_deg, best_rmse, best_line = 1, np.inf, None
        for deg in [1, 2, 3]:
            coeffs = np.polyfit(x_f, y_f, deg)
            y_hat  = np.polyval(coeffs, x_f)
            rmse   = float(np.sqrt(np.mean((y_f - y_hat) ** 2)))
            if rmse < best_rmse:
                best_rmse = rmse
                best_deg  = deg
                best_line = np.polyval(coeffs, xi)
        fig.add_trace(go.Scatter(
            x=x_f, y=y_f, mode='markers',
            marker=dict(color=C_CYAN, size=5, opacity=0.65,
                        line=dict(color=C_PAPER, width=0.5)),
            hovertemplate='%{x:.1f} → %{y:.1f}<extra></extra>',
            showlegend=False,
        ), row=r, col=c)
        fig.add_trace(go.Scatter(
            x=xi, y=best_line, mode='lines',
            line=dict(color=DEG_COLORS[best_deg], width=2),
            showlegend=False,
            hoverinfo='skip',
        ), row=r, col=c)
    fig.update_layout(
        **{**_BASE, 'margin': dict(l=10, r=10, t=44, b=10)},
        showlegend=False,
        height=520,
    )
    for i in range(1, rows_n * cols_n + 1):
        suf = '' if i == 1 else str(i)
        fig.update_layout(**{
            f'xaxis{suf}': dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                color=C_MUTED, tickfont=dict(size=9)),
            f'yaxis{suf}': dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                                color=C_MUTED, tickfont=dict(size=9)),
        })
    return fig


def fig_pc_scatter(pc_num=1):
    ml = get_ml()
    if 'pc_scores' not in ml:
        return go.Figure()
    pc_idx = pc_num - 1
    if pc_idx >= ml['pc_scores'].shape[1]:
        return go.Figure()

    scores = ml['pc_scores'][:, pc_idx]
    y      = ml['y']
    df     = ml['df_main']
    var    = float(ml['pc_var'][pc_idx]) if pc_idx < len(ml['pc_var']) else 0.0

    grp_map = {g: GRUPO_COLORS[g] for g in GRUPO_ORDER}
    colors  = [grp_map.get(g, C_CYAN) for g in df['grupo_label'].values]

    slope, intercept, r, _, _ = stats.linregress(scores, y)
    xi = np.linspace(float(scores.min()), float(scores.max()), 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=scores, y=y, mode='markers',
        text=[_short(e) for e in df['estado']],
        customdata=df['anio'].values,
        marker=dict(color=colors, size=9, opacity=0.85,
                    line=dict(color=C_PAPER, width=1)),
        hovertemplate='<b>%{text}</b> %{customdata}<br>'
                      f'PC{pc_num}: %{{x:.2f}}<br>Innovación: %{{y:.1f}}<extra></extra>',
        name='Estado-año',
    ))
    fig.add_trace(go.Scatter(
        x=xi, y=slope * xi + intercept, mode='lines',
        line=dict(color=C_RED, width=2, dash='dot'),
        name=f'r = {r:.2f}', hoverinfo='skip',
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text=f'PC{pc_num} vs Pilar Innovación  ·  {var:.1%} varianza explicada',
                   font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text=f'Score PC{pc_num}', font=dict(size=11))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   title=dict(text='Pilar Innovación', font=dict(size=11))),
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)'),
        annotations=[dict(
            text=f'r = {r:.3f}', xref='paper', yref='paper',
            x=0.98, y=0.04, showarrow=False,
            font=dict(size=11, color=C_GOLD),
            align='right',
        )],
    )
    return fig


def fig_pc_loadings(pc_num=1):
    ml = get_ml()
    if 'pc_loadings' not in ml:
        return go.Figure()
    pc_idx = pc_num - 1
    if pc_idx >= len(ml['pc_loadings']):
        return go.Figure()

    loadings   = ml['pc_loadings'][pc_idx]
    feat_names = ml['feat_names']
    labels     = [_FEAT_LABELS.get(f, f) for f in feat_names]

    idx            = np.argsort(np.abs(loadings))
    sorted_labels  = [labels[i] for i in idx]
    sorted_loads   = [float(loadings[i]) for i in idx]
    colors         = [C_GOLD if v >= 0 else C_RED for v in sorted_loads]

    fig = go.Figure(go.Bar(
        y=sorted_labels,
        x=sorted_loads,
        orientation='h',
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        hovertemplate='<b>%{y}</b><br>Peso: %{x:.3f}<extra></extra>',
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text=f'Pesos (loadings) de cada variable — PC{pc_num}',
                   font=dict(size=12, color=C_TEXT), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', color=C_MUTED,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.18)', zerolinewidth=1,
                   title=dict(text='Peso en PC', font=dict(size=11))),
        yaxis=dict(showgrid=False, color=C_MUTED),
        bargap=0.22,
        annotations=[
            dict(text='● Dorado = positivo  ● Rojo = negativo',
                 xref='paper', yref='paper', x=0.5, y=-0.02,
                 showarrow=False, font=dict(size=10, color=C_MUTED), align='center'),
        ],
    )
    return fig
