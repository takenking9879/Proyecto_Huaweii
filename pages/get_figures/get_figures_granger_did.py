"""
Plotly figures for Granger causality, Difference-in-Differences, Panel Fixed Effects,
VIF, Bootstrap CIs, and Breusch-Pagan diagnostics.

Used by slide_economia.py (extended section) and potentially slide_11.py.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pages.get_data.get_data_granger_did import (
    get_granger_results,
    get_did_results,
    get_panel_fe_results,
    get_vif_results,
    get_bp_test,
    get_bootstrap_cis,
    get_loocv_results,
    get_bh_correction_results,
    get_robust_wage_gap,
)

# ── Color palette ──────────────────────────────────────────────────
C_CYAN   = '#00b4cc'
C_GOLD   = '#c9922a'
C_GREEN  = '#2bb573'
C_RED    = '#cf0a2c'
C_BLUE   = '#3891c7'
C_ORANGE = '#e4982e'
C_PURPLE = '#9b59b6'
C_PAPER  = '#1a1a24'
C_PLOT   = '#111118'
C_TEXT   = '#e8e8f0'
C_MUTED  = '#5c5c74'

_BASE = dict(
    paper_bgcolor=C_PAPER, plot_bgcolor=C_PLOT,
    font=dict(family='DM Sans, sans-serif', color=C_TEXT, size=11),
    hoverlabel=dict(bgcolor='#0f0f18', font_color=C_TEXT,
                    bordercolor='rgba(255,255,255,0.1)'),
)

_GRID = dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, color=C_MUTED)


def _inset_annotation(fig, text, x=0.02, y=0.97):
    fig.add_annotation(
        xref='paper', yref='paper', x=x, y=y,
        text=text, showarrow=False, align='left',
        bgcolor='rgba(0,180,204,0.10)', bordercolor=C_CYAN, borderwidth=1,
        font=dict(size=9.5, color=C_TEXT),
    )


# ══════════════════════════════════════════════════════════════════════
# FIGURE 1 — Granger Causality: Directional Test
# ══════════════════════════════════════════════════════════════════════

def fig_granger_test():
    """
    Horizontal bars showing Granger F-statistic for both directions.
    Higher bar = stronger temporal predictive power in that direction.
    """
    df = get_granger_results()
    if df.empty:
        return go.Figure()

    fig = go.Figure()
    colors = [C_CYAN, C_RED]

    for i, (_, row) in enumerate(df.iterrows()):
        color = colors[i % len(colors)]
        sig = '★ p<0.05' if row['p'] < 0.05 else f"p={row['p']:.3f}"
        fig.add_trace(go.Bar(
            y=[row['direction']],
            x=[row['f']],
            orientation='h',
            marker=dict(color=color, opacity=0.82),
            text=[f'  F={row["f"]} · {sig} · n={row["n"]}'],
            textposition='outside',
            textfont=dict(size=10, color=C_TEXT),
            hovertemplate=(
                f'<b>{row["direction"]}</b><br>'
                f'F-statistic: {row["f"]}<br>'
                f'p-value: {row["p"]}<br>'
                f'n = {row["n"]} state-year obs<extra></extra>'
            ),
            showlegend=False,
        ))

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=120, t=40, b=20),
        title=dict(text='Granger Causality — ¿Qué dirección tiene precedencia temporal?',
                   font=dict(size=12)),
        xaxis=dict(title=dict(text='F-statistic (mayor = más evidencia de precedencia temporal)',
                              font=dict(size=9)),
                   showgrid=True, gridcolor='rgba(255,255,255,0.05)', color=C_MUTED),
        yaxis=dict(**{**dict(showgrid=False, color=C_TEXT), 'categoryorder': 'array',
                     'categoryarray': df['direction'].tolist()}),
    )

    # Add significance reference line
    fig.add_vline(x=3.84, line_dash='dash', line_color=C_MUTED, opacity=0.5,
                  annotation=dict(text='p=0.05 (approx)', font=dict(size=8, color=C_MUTED)))

    _inset_annotation(fig,
        'Granger test pooled panel (N=32×4 años).<br>'
        'H₀: la variable rezagada NO ayuda a predecir.<br>'
        'Dirección con F más alto = más sustento temporal.'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 2 — Difference-in-Differences: Wage Trajectories
# ══════════════════════════════════════════════════════════════════════

def fig_did_trajectories():
    """
    DiD parallel trends: treated (top IDDE growth) vs control wage trajectories.
    Shows group means with 95% CI ribbons.
    """
    did = get_did_results()
    traj = did.get('trajectories')
    if traj is None or traj.empty:
        return go.Figure()

    fig = go.Figure()

    for group, color, dash, name_base in [
        (1, C_CYAN, 'solid', 'Tratado'),
        (0, C_GOLD, 'dash', 'Control'),
    ]:
        grp = traj[traj['treated'] == bool(group)]
        if grp.empty:
            continue
        summary = grp.groupby('year')['wage'].agg(['mean', 'std', 'count']).reset_index()
        summary['se'] = summary['std'] / np.sqrt(summary['count'])

        label = f"{name_base} (n={did.get('n_treated' if group else 'n_control', '?')})"
        fig.add_trace(go.Scatter(
            x=summary['year'], y=summary['mean'],
            mode='lines+markers', line=dict(color=color, width=2.2, dash=dash),
            marker=dict(size=8, color=color, line=dict(color=C_PAPER, width=1.5)),
            name=label,
            legendgroup=name_base,
            hovertemplate=f'<b>{name_base}</b><br>'
                          'Año: %{x}<br>Salario: $%{y:,.0f}<extra></extra>',
        ))
        # 95% CI ribbon
        fig.add_trace(go.Scatter(
            x=summary['year'].tolist() + summary['year'].tolist()[::-1],
            y=(summary['mean'] + 1.96 * summary['se']).tolist() +
              (summary['mean'] - 1.96 * summary['se']).tolist()[::-1],
            fill='toself', fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)',
            line=dict(width=0), showlegend=False, hoverinfo='skip',
            legendgroup=name_base,
        ))

    fig.update_layout(
        **_BASE,
        margin=dict(l=70, r=30, t=40, b=40),
        title=dict(text='Diferencia-en-Diferencias — Trayectorias salariales por grupo',
                   font=dict(size=12)),
        xaxis=dict(title='Año', dtick=1, **_GRID),
        yaxis=dict(title='Salario promedio mensual (MXN)', tickformat='$,.0f', **_GRID),
        legend=dict(font=dict(size=9), bgcolor='rgba(0,0,0,0)', x=0.02, y=0.02,
                    xanchor='left', yanchor='bottom'),
    )

    _inset_annotation(fig,
        f'DiD = ${did.get("diff_in_diff", "?"):,.0f} MXN<br>'
        f'Tratados: ΔIDDE > {did.get("threshold", "?")} (2022→2024)<br>'
        f'Tratados n={did.get("n_treated", "?")}, Control n={did.get("n_control", "?")}<br>'
        f'4 años de panel — poder limitado, dirección visible.'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 3 — Panel Fixed Effects: Coefficient Forest Plot
# ══════════════════════════════════════════════════════════════════════

def fig_panel_fe_coef():
    """
    Horizontal bar showing IDDE coefficient from FE model with CI.
    """
    fe = get_panel_fe_results()

    fig = go.Figure()

    # OLS SE
    fig.add_trace(go.Bar(
        y=['IDDE → Salario (FE)'],
        x=[fe['idde_coef']],
        orientation='h',
        marker=dict(color=C_CYAN if fe['significant_05'] else C_GOLD, opacity=0.82),
        error_x=dict(
            type='data', array=[1.96 * fe['idde_se']], visible=True,
            color=C_TEXT, thickness=1.5, width=8,
        ),
        text=[f'  β={fe["idde_coef"]} ± {fe["idde_se"]} · p={fe["p_val"]}'],
        textposition='outside', textfont=dict(size=10, color=C_TEXT),
        hovertemplate=(
            'β = %{x:.1f} MXN por punto IDDE<br>'
            f'SE (OLS) = {fe["idde_se"]:.1f}<br>'
            f'SE (cluster estado) = {fe["idde_se_clustered"]:.1f}<br>'
            f'p = {fe["p_val"]}<br>'
            f'Within R² = {fe["within_r2"]}<br>'
            f'n = {fe["n_obs"]} ({fe["n_states"]} estados × {fe["n_years"]} años)<extra></extra>'
        ),
        showlegend=False,
    ))

    fig.add_vline(x=0, line_color=C_MUTED, line_width=0.8)

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=120, t=40, b=20),
        title=dict(text='Panel con Efectos Fijos — IDDE → Salario (within-estado)',
                   font=dict(size=12)),
        xaxis=dict(
            title=dict(text='Cambio en salario (MXN/mes) por +1 punto IDDE (within-estado)',
                       font=dict(size=9)),
            **_GRID,
        ),
        yaxis=dict(showgrid=False, color=C_TEXT),
    )

    _inset_annotation(fig,
        f'Modelo: wage_it = α_i + δ_t + β·IDDE_it + ε_it<br>'
        f'α_i controla características fijas por estado.<br>'
        f'δ_t controla tendencias nacionales anuales.<br>'
        f'Within-R² = {fe["within_r2"]}<br>'
        f'{"✓ Significativo al 5%" if fe["significant_05"] else "✗ No significativo al 5% (pocos años)"}'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 4 — VIF Bar Chart
# ══════════════════════════════════════════════════════════════════════

def fig_vif_bars():
    """VIF values for main regression predictors — color-coded by severity."""
    vif_data = get_vif_results()
    if not vif_data:
        return go.Figure()

    df = pd.DataFrame(vif_data).sort_values('vif', ascending=True)

    def _color(v):
        if v >= 10:
            return C_RED
        elif v >= 5:
            return C_GOLD
        return C_GREEN

    colors = [_color(r['vif']) for _, r in df.iterrows()]
    # Abbreviate variable names for display
    labels = [r['variable'].replace('empresas_que_utilizan_banca_electronica_por', 'Banca electrónica')
                              .replace('penetracion_de_banda_ancha_fija_x100hab', 'BB fija')
                              .replace('cobertura_de_redes_moviles_por', 'Cobertura móvil')
                              .replace('graduados_en_programas_stem_xmhab', 'Graduados STEM')
              for _, r in df.iterrows()]

    fig = go.Figure(go.Bar(
        y=labels, x=df['vif'].values, orientation='h',
        marker=dict(color=colors, opacity=0.85),
        text=[f'  VIF={r["vif"]:.1f}' for _, r in df.iterrows()],
        textposition='outside', textfont=dict(size=10, color=C_TEXT),
        hovertemplate='%{y}<br>VIF = %{x:.1f}<extra></extra>',
    ))

    fig.add_vline(x=5, line_dash='dash', line_color=C_GOLD, opacity=0.5,
                  annotation=dict(text='VIF=5 (moderado)', font=dict(size=8, color=C_GOLD)))
    fig.add_vline(x=10, line_dash='dash', line_color=C_RED, opacity=0.5,
                  annotation=dict(text='VIF=10 (alto)', font=dict(size=8, color=C_RED)))

    fig.update_layout(
        **_BASE,
        margin=dict(l=20, r=100, t=40, b=20),
        title=dict(text='Factor de Inflación de Varianza (VIF) — Multicolinealidad',
                   font=dict(size=11)),
        xaxis=dict(title='VIF (<5 = bajo, 5-10 = moderado, >10 = alto)', **_GRID),
        yaxis=dict(showgrid=False, color=C_TEXT),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 5 — Bootstrap Confidence Intervals
# ══════════════════════════════════════════════════════════════════════

def fig_bootstrap_cis():
    """Dumbbell plot of bootstrap 95% CIs for top correlations and R²."""
    ci_data = get_bootstrap_cis()
    if not ci_data:
        return go.Figure()

    fig = go.Figure()

    for item in ci_data:
        color = C_CYAN if item['ci_lower'] > 0 else C_RED
        fig.add_trace(go.Scatter(
            x=[item['ci_lower'], item['ci_upper']],
            y=[item['label'], item['label']],
            mode='lines+markers',
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color),
            name=item['label'],
            showlegend=False,
            hovertemplate=(
                f'<b>{item["label"]}</b><br>'
                f'{item["metric"]} = {item["point"]}<br>'
                f'IC 95%: [{item["ci_lower"]}, {item["ci_upper"]}]<br>'
                f'n = {item["n"]} estados<extra></extra>'
            ),
        ))
        # Add point estimate
        fig.add_trace(go.Scatter(
            x=[item['point']], y=[item['label']],
            mode='markers',
            marker=dict(size=9, color='white', symbol='diamond',
                       line=dict(color=color, width=1.5)),
            showlegend=False,
            hoverinfo='skip',
        ))

    fig.add_vline(x=0, line_color=C_MUTED, line_width=0.8)

    fig.update_layout(
        **_BASE,
        margin=dict(l=20, r=30, t=40, b=20),
        title=dict(text='Intervalos de Confianza Bootstrap (95%) — Correlaciones y R² Clave',
                   font=dict(size=11)),
        xaxis=dict(title='Valor del estadístico (10,000 remuestreos)', **_GRID),
        yaxis=dict(showgrid=False, color=C_TEXT),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 6 — LOOCV: Real vs Predicted (Slide 10 validation)
# ══════════════════════════════════════════════════════════════════════

def fig_loocv_scatter():
    """Leave-one-out CV: real vs predicted pilar_innovacion per state."""
    loo = get_loocv_results()
    preds = loo.get('predictions')
    if preds is None or preds.empty:
        return go.Figure()

    fig = go.Figure()

    # Perfect prediction line
    all_vals = np.concatenate([preds['real'].values, preds['pred'].values])
    rng = [all_vals.min() - 2, all_vals.max() + 2]
    fig.add_trace(go.Scatter(
        x=rng, y=rng, mode='lines',
        line=dict(color=C_MUTED, dash='dash', width=0.8),
        showlegend=False, hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=preds['real'], y=preds['pred'],
        mode='markers+text',
        text=preds['estado'].str[:6],
        textposition='top center', textfont=dict(size=7, color=C_MUTED),
        marker=dict(
            size=10, color=C_CYAN, opacity=0.8,
            line=dict(color=C_PAPER, width=1),
        ),
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Real: %{x:.2f}<br>'
            'Predicho: %{y:.2f}<br>'
            'Error: %{customdata:.2f}<extra></extra>'
        ),
        customdata=np.abs(preds['real'] - preds['pred']),
    ))

    fig.update_layout(
        **_BASE,
        margin=dict(l=60, r=20, t=40, b=60),
        title=dict(text=f'Leave-One-Out CV — Pilar Innovación (RF) · R² OOS = {loo["r2_loocv"]:.3f}',
                   font=dict(size=11)),
        xaxis=dict(title='Pilar Innovación real', **_GRID),
        yaxis=dict(title='Pilar Innovación predicho (LOOCV)', **_GRID),
    )

    _inset_annotation(fig,
        f'<b>LOOCV R² = {loo["r2_loocv"]:.3f}</b><br>'
        f'R² in-sample medio: {loo["r2_train_mean"]:.3f}<br>'
        f'32 estados — modelo entrenado en 31,<br>'
        f'predice el estado dejado fuera.<br>'
        f'{"⚠ Overfitting modesto" if abs(loo["r2_train_mean"]-loo["r2_loocv"])>0.1 else "✓ Overfitting mínimo"}'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 7 — Breusch-Pagan Diagnostic
# ══════════════════════════════════════════════════════════════════════

def fig_bp_diagnostic():
    """Residuals vs fitted plot with Breusch-Pagan test result annotated."""
    bp = get_bp_test()
    if bp['n'] == 0:
        return go.Figure()

    from sklearn.linear_model import LinearRegression as _LR
    from pages.get_data.get_data_11 import get_data_11 as _gd11
    d = _gd11()
    cross = d['cross_cl'].copy()
    x_col = 'empresas_que_utilizan_banca_electronica_por'
    df = cross[[x_col, 'avg_wage']].dropna()

    lr = _LR().fit(df[[x_col]], df['avg_wage'])
    fitted = lr.predict(df[[x_col]])
    residuals = df['avg_wage'].values - fitted

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fitted, y=residuals,
        mode='markers',
        marker=dict(size=9, color=C_CYAN, opacity=0.75,
                   line=dict(color=C_PAPER, width=1)),
        hovertemplate='Salario predicho: $%{x:,.0f}<br>Residual: %{y:+,.0f}<extra></extra>',
    ))

    fig.add_hline(y=0, line_color=C_MUTED, line_width=0.8)

    # Lowess smoothing line
    idx = np.argsort(fitted)
    from scipy.interpolate import make_interp_spline
    try:
        smooth_x = np.linspace(fitted.min(), fitted.max(), 50)
        # Simple moving average as a poor man's lowess
        window = max(5, len(df) // 8)
        smoothed = pd.Series(residuals[idx]).rolling(window=window, center=True).mean().values
        valid = ~np.isnan(smoothed)
        fig.add_trace(go.Scatter(
            x=fitted[idx][valid], y=smoothed[valid],
            mode='lines', line=dict(color=C_GOLD, width=1.8),
            name='Tendencia suavizada', showlegend=True,
            hovertemplate='Tendencia en %{x:,.0f}: %{y:+,.0f}<extra></extra>',
        ))
    except Exception:
        pass

    fig.update_layout(
        **_BASE,
        margin=dict(l=60, r=20, t=40, b=40),
        title=dict(text=f'Breusch-Pagan — Homoscedasticidad · LM={bp["lm"]:.2f} · p={bp["p"]:.3f}',
                   font=dict(size=11)),
        xaxis=dict(title='Salario predicho (MXN/mes)', **_GRID),
        yaxis=dict(title='Residual (MXN/mes)', **_GRID),
        legend=dict(font=dict(size=9), bgcolor='rgba(0,0,0,0)', x=0.02, y=0.98,
                    xanchor='left', yanchor='top'),
    )

    _inset_annotation(fig,
        f'H₀: Varianza constante (homoscedasticidad)<br>'
        f'{"✓ No se rechaza H₀ (varianza homogénea)" if bp["p"] >= 0.05 else "⚠ Se rechaza H₀ (heteroscedasticidad)"}<br>'
        f'{"OLS es válido" if bp["p"] >= 0.05 else "Usar errores estándar robustos (HC3)"}'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 8 — Robust Wage Gap: Sustained vs Inconsistent
# ══════════════════════════════════════════════════════════════════════

def fig_robust_wage_gap():
    """Boxplot-like visualization: wage gap between sustained and inconsistent investors."""
    gap = get_robust_wage_gap()
    if gap['n_sustained'] == 0:
        return go.Figure()

    fig = go.Figure()

    groups = ['Inconsistente', 'Sostenida']
    means  = [gap['mean_inconsistent'], gap['mean_sustained']]
    colors = [C_RED, C_GREEN]
    ns     = [gap['n_inconsistent'], gap['n_sustained']]

    for i, (grp, mean, color, n) in enumerate(zip(groups, means, colors, ns)):
        fig.add_trace(go.Bar(
            y=[grp], x=[mean], orientation='h',
            marker=dict(color=color, opacity=0.8),
            text=[f'  ${mean:,.0f}/mes (n={n})'],
            textposition='outside', textfont=dict(size=10, color=C_TEXT),
            hovertemplate=f'<b>{grp}</b><br>${mean:,.0f}/mes<br>n = {n} estados<extra></extra>',
            showlegend=False,
        ))

    # Gap annotation
    fig.add_annotation(
        x=(gap['mean_inconsistent'] + gap['mean_sustained']) / 2,
        y=1.2, text=f'Δ = ${gap["gap"]:,.0f}/mes<br>IC 95%: [${gap["ci_lower"]:,.0f}, ${gap["ci_upper"]:,.0f}]',
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowwidth=2, arrowcolor=C_GOLD,
        ax=0, ay=-30, font=dict(size=10, color=C_GOLD), bgcolor='rgba(201,146,42,0.12)',
        bordercolor=C_GOLD, borderwidth=1,
    )

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=120, t=50, b=20),
        title=dict(text='Inversión Sostenida vs Inconsistente — Diferencia Salarial',
                   font=dict(size=11)),
        xaxis=dict(title='Salario promedio mensual (MXN)', **_GRID, tickformat='$,.0f'),
        yaxis=dict(showgrid=False, color=C_TEXT),
    )

    _inset_annotation(fig,
        f'Sostenida = 3+ años de crecimiento IDDE consecutivo<br>'
        f'IC 95% bootstrap (10,000 remuestreos)<br>'
        f'La diferencia NO es un efecto causal —<br>'
        f'ambos grupos difieren en otras dimensiones.'
    )

    return fig


# ══════════════════════════════════════════════════════════════════════
# FIGURE 9 — Benjamini-Hochberg Summary
# ══════════════════════════════════════════════════════════════════════

def fig_bh_summary():
    """Bar chart: nominal vs BH-corrected significant correlations."""
    bh = get_bh_correction_results()
    if bh['n_total'] == 0:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=['Sin corregir (p<0.05)', 'Corrección BH (FDR=0.05)'],
        x=[bh['n_nominal'], bh['n_bh']],
        orientation='h',
        marker=dict(color=[C_RED, C_GREEN], opacity=0.8),
        text=[f'  {bh["n_nominal"]} / {bh["n_total"]}',
              f'  {bh["n_bh"]} / {bh["n_total"]}'],
        textposition='outside', textfont=dict(size=10, color=C_TEXT),
        hovertemplate='%{y}<br>%{x} correlaciones significativas<extra></extra>',
        showlegend=False,
    ))

    fig.update_layout(
        **_BASE,
        margin=dict(l=30, r=80, t=40, b=20),
        title=dict(text=f'Corrección Benjamini-Hochberg — {bh["n_total"]} correlaciones totales',
                   font=dict(size=11)),
        xaxis=dict(title='Número de correlaciones significativas', **_GRID),
        yaxis=dict(showgrid=False, color=C_TEXT),
    )

    survivors_text = '<br>'.join(
        f'{s["r"]:+.2f}: {s["infra"][:20]} × {s["sec"][:20]}'
        for s in bh.get('top_survivors', [])[:5]
    )
    _inset_annotation(fig,
        f'<b>Top 5 que sobreviven:</b><br>{survivors_text}'
    )

    return fig
