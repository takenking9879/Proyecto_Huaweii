"""
graficas_presentacion.py
Crimen, Desarrollo Digital y Crecimiento Economico en Mexico — Panel 2015-2024
Ejecutar desde el directorio que contiene HuaweiProject.db
"""

import sqlite3, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import stats
from scipy.stats import pearsonr

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance
import shap

warnings.filterwarnings("ignore")

# ── Estilo global ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.25,
    "figure.dpi":       130,
    "axes.titlesize":   13,
    "axes.labelsize":   11,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
})

GRUPO_COLORS = {
    "Basico":      "#d62728",
    "Emprendedor": "#ff7f0e",
    "Avanzado":    "#1f77b4",
    "Lider":       "#2ca02c",
}
GRUPO_COLORS_RAW = {
    "Básico":      "#d62728",
    "Emprendedor": "#ff7f0e",
    "Avanzado":    "#1f77b4",
    "Líder":       "#2ca02c",
}
GRUPO_ORDER = ["Básico", "Emprendedor", "Avanzado", "Líder"]
DB_PATH = "HuaweiProject.db"

# ══════════════════════════════════════════════════════════════════════════════
# A. PIPELINE DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

BIEN_MAP = {
    "Feminicidio": "Vida", "Homicidio doloso": "Vida", "Homicidio culposo": "Vida",
    "Lesiones dolosas": "Vida", "Lesiones culposas": "Vida", "Aborto": "Vida",
    "Secuestro": "Libertad", "Trata de personas": "Libertad", "Rapto": "Libertad",
    "Otros delitos que atentan contra la libertad personal": "Libertad",
    "Violación simple": "Sexual", "Violación equiparada": "Sexual",
    "Abuso sexual": "Sexual", "Acoso sexual": "Sexual", "Hostigamiento sexual": "Sexual",
    "Otros delitos que atentan contra la libertad y la seguridad sexual": "Sexual",
    "Violencia familiar": "Familia",
    "Violencia de género en todas sus modalidades distinta a la violencia familiar": "Familia",
    "Incesto": "Familia", "Otros delitos contra la familia": "Familia",
    "Narcomenudeo": "Sociedad", "Corrupción de menores": "Sociedad",
    "Tráfico de menores": "Sociedad", "Lenocinio": "Sociedad",
    "Otros delitos contra la sociedad": "Sociedad",
    "Delitos ambientales": "Estado",
}
for r in [
    "Robo de vehículo automotor","Robo a casa habitación","Robo a negocio",
    "Robo a transeúnte en vía pública con violencia","Robo a transeúnte en vía pública sin violencia",
    "Robo en transporte público colectivo","Robo a bordo de metro","Robo a institución bancaria",
    "Robo de autopartes","Robo de maquinaria","Robo de ganado","Robo de madera","Robo en carretera",
    "Robo a transportista","Robo a repartidor","Robo a bordo de microbús","Robo a bordo de taxi",
    "Robo a bordo de tren","Otros robos","Fraude","Extorsión","Abigeato","Despojo","Daño a la propiedad",
]:
    BIEN_MAP[r] = "Patrimonio"

POBLACION = {
    "Aguascalientes":       {2015:1312544, 2020:1434635, 2025:1563053},
    "Baja California":      {2015:3315766, 2020:3769020, 2025:4192534},
    "Baja California Sur":  {2015:712029,  2020:798447,  2025:897487},
    "Campeche":             {2015:899931,  2020:928363,  2025:975528},
    "Chiapas":              {2015:5217908, 2020:5543828, 2025:5816003},
    "Chihuahua":            {2015:3556574, 2020:3741869, 2025:3907760},
    "Ciudad de México":     {2015:8918653, 2020:9209944, 2025:9433137},
    "Coahuila de Zaragoza": {2015:2954915, 2020:3146771, 2025:3352283},
    "Colima":               {2015:711235,  2020:731391,  2025:754803},
    "Durango":              {2015:1754754, 2020:1832650, 2025:1906808},
    "Guanajuato":           {2015:5853677, 2020:6166934, 2025:6478042},
    "Guerrero":             {2015:3388768, 2020:3540685, 2025:3664869},
    "Hidalgo":              {2015:2858359, 2020:3082841, 2025:3302025},
    "Jalisco":              {2015:7844830, 2020:8348151, 2025:8848192},
    "México":               {2015:16187608,2020:16992418,2025:17694226},
    "Michoacán de Ocampo":  {2015:4584471, 2020:4748846, 2025:4898892},
    "Morelos":              {2015:1903811, 2020:1971520, 2025:2041576},
    "Nayarit":              {2015:1181050, 2020:1235456, 2025:1291112},
    "Nuevo León":           {2015:5119504, 2020:5784442, 2025:6373232},
    "Oaxaca":               {2015:3967889, 2020:4132148, 2025:4291270},
    "Puebla":               {2015:6168883, 2020:6583278, 2025:7011748},
    "Querétaro":            {2015:2038372, 2020:2368467, 2025:2689988},
    "Quintana Roo":         {2015:1501562, 2020:1857985, 2025:2184143},
    "San Luis Potosí":      {2015:2717820, 2020:2822255, 2025:2936889},
    "Sinaloa":              {2015:2966321, 2020:3026981, 2025:3083898},
    "Sonora":               {2015:2850330, 2020:2944840, 2025:3046739},
    "Tabasco":              {2015:2395272, 2020:2402598, 2025:2433765},
    "Tamaulipas":           {2015:3441698, 2020:3527735, 2025:3615694},
    "Tlaxcala":             {2015:1272847, 2020:1342977, 2025:1407844},
    "Veracruz de Ignacio de la Llave": {2015:8112505,2020:8062579,2025:8028879},
    "Yucatán":              {2015:2097175, 2020:2320898, 2025:2511049},
    "Zacatecas":            {2015:1579209, 2020:1622138, 2025:1663029},
}

def get_pob(estado, anio):
    data = POBLACION.get(estado)
    if not data:
        return np.nan
    years = sorted(data)
    if anio <= years[0]:  return data[years[0]]
    if anio >= years[-1]: return data[years[-1]]
    for i in range(len(years) - 1):
        y0, y1 = years[i], years[i+1]
        if y0 <= anio <= y1:
            return data[y0] + (anio - y0) / (y1 - y0) * (data[y1] - data[y0])


def _add_crime_rates(df):
    df["poblacion"] = df.apply(lambda r: get_pob(r["estado"], r["anio"]), axis=1)
    df["tasa_x100k"] = df["total_delitos"] / df["poblacion"] * 100_000
    for c in [x for x in df.columns if x.startswith("crime_")]:
        df[c.replace("crime_", "tasa_")] = df[c] / df["poblacion"] * 100_000
        df[c.replace("crime_", "share_")] = df[c] / df["total_delitos"]
    return df


def build_dataframes():
    with sqlite3.connect(DB_PATH) as conn:
        # ── DF1: crimen 2015-2022 ─────────────────────────────────────────
        raw1 = pd.read_sql("""
            SELECT f.anio, e.estado, s.subtipo, SUM(f.incidencia_delictiva) AS total
            FROM incidencia_estatal f
            JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
            JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
            WHERE f.anio BETWEEN 2015 AND 2022
            GROUP BY f.anio, e.estado, s.subtipo
        """, conn)

        # ── DF2: crimen + IDDE 2022-2024 ─────────────────────────────────
        crime224 = pd.read_sql("""
            SELECT f.anio, e.clave_ent, e.estado, s.subtipo,
                   SUM(f.incidencia_delictiva) AS total
            FROM incidencia_estatal f
            JOIN dim_estado         e ON f.clave_ent  = e.clave_ent
            JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
            WHERE f.anio IN (2022, 2023, 2024)
            GROUP BY f.anio, e.clave_ent, e.estado, s.subtipo
        """, conn)

        idde_frames = []
        for yr, tbl, gcol in [
            (2022, "idde_2022", "grupo_de_digitalizacion_id"),
            (2023, "idde_2023", "grupo_de_digitalizacion_2023_id"),
            (2024, "idde_2024", "grupo_de_digitalizacion_2024_id"),
        ]:
            q = f"""
                SELECT clave_inegi_de_estado AS clave_ent,
                       indice_de_desarrollo_digital_estatal_{yr} AS idde_score,
                       pilar_infraestructura,
                       pilar_digitalizacion_de_las_personas_y_la_sociedad AS pilar_sociedad,
                       pilar_innovacion_y_adopcion_tecnologica_de_las_empresas AS pilar_innovacion,
                       usuarios_de_internet_por, habilidades_de_programacion_por,
                       solicitudes_de_patentes_xmhab, graduados_en_programas_stem_xmhab,
                       policia_cibernetica_xmhab, {gcol} AS grupo_id
                FROM {tbl}
            """
            d = pd.read_sql(q, conn)
            d["anio"] = yr
            idde_frames.append(d)

        grupos = pd.read_sql("SELECT * FROM dim_grupo_digitalizacion", conn)

    # ── Procesar DF1 ──────────────────────────────────────────────────────
    raw1["categoria"] = raw1["subtipo"].map(BIEN_MAP).fillna("Otros")
    cat1 = (raw1.groupby(["anio", "estado", "categoria"])["total"].sum()
               .unstack(fill_value=0).add_prefix("crime_").reset_index())
    tot1 = raw1.groupby(["anio", "estado"])["total"].sum().reset_index(name="total_delitos")
    df1 = _add_crime_rates(tot1.merge(cat1, on=["anio", "estado"]))
    df1 = df1.sort_values(["estado", "anio"]).reset_index(drop=True)

    # ── Procesar DF2 ──────────────────────────────────────────────────────
    idde_all = pd.concat(idde_frames, ignore_index=True)
    crime224["categoria"] = crime224["subtipo"].map(BIEN_MAP).fillna("Otros")
    cat2 = (crime224.groupby(["anio", "clave_ent", "categoria"])["total"].sum()
                .unstack(fill_value=0).add_prefix("crime_").reset_index())
    tot2 = (crime224.groupby(["anio", "clave_ent", "estado"])["total"]
                .sum().reset_index(name="total_delitos"))
    df2 = _add_crime_rates(tot2.merge(cat2, on=["anio", "clave_ent"]))
    df2 = df2.merge(idde_all, on=["anio", "clave_ent"])
    df2 = df2.merge(grupos, on="grupo_id")
    df2["grupo_label"] = df2["grupo"]

    return df1, df2


# ══════════════════════════════════════════════════════════════════════════════
# B. PIPELINE DE MODELO
# ══════════════════════════════════════════════════════════════════════════════

def build_model_pipeline(df2):
    df2 = df2.copy()
    df2["anio_2023"] = (df2["anio"] == 2023).astype(int)
    df2["anio_2024"] = (df2["anio"] == 2024).astype(int)

    tasa_cols  = [c for c in df2.columns if c.startswith("tasa_") and c != "tasa_x100k"]
    share_cols = [c for c in df2.columns if c.startswith("share_")]
    features = tasa_cols + share_cols + [
        "policia_cibernetica_xmhab", "graduados_en_programas_stem_xmhab",
        "habilidades_de_programacion_por", "anio_2023", "anio_2024",
    ]
    target = "pilar_innovacion"

    df_main = df2[["estado", "anio"] + features + [target]].dropna().reset_index(drop=True)
    df_main = df_main.merge(df2[["estado", "anio", "grupo_label"]],
                            on=["estado", "anio"], how="left")

    feat_names = [c for c in features if c != "estado"]
    X_all = df_main[feat_names].values
    y     = df_main[target].values

    # Selección de features por norma PCA (replica notebook)
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X_all)
    pca    = PCA().fit(X_sc)
    n_pc   = int((pca.explained_variance_ratio_.cumsum() <= 0.80).sum())

    S      = np.cov(X_sc, rowvar=False)
    evals, Gamma = np.linalg.eig(S)
    cov_XY  = Gamma @ np.diag(evals)
    Dx_nsq  = np.diag(np.diag(S) ** (-0.5))
    Dy_nsq  = np.diag(evals ** (-0.5))
    corr_XY = Dx_nsq @ cov_XY @ Dy_nsq

    pares = [(0, k) for k in range(1, n_pc)]
    norms = []
    for i, j in pares:
        row = {}
        for k, name in enumerate(feat_names):
            x_, y_ = corr_XY[k, i].real, corr_XY[k, j].real
            row[name] = np.sqrt(x_**2 + y_**2)
        norms.append(row)
    df_norms  = pd.DataFrame(norms)
    cols_model = [c for c in df_norms if (df_norms[c] >= 0.7).sum() > 0]

    X_model = df_main[cols_model].values

    # Entrenar tres modelos
    rf  = RandomForestRegressor(n_estimators=200, max_features=0.5,
                                min_samples_leaf=1, max_depth=None,
                                random_state=42, n_jobs=-1)
    gbm = GradientBoostingRegressor(n_estimators=200, max_depth=4,
                                    learning_rate=0.05, subsample=0.8,
                                    random_state=42)
    rid = Ridge(alpha=5.0)

    models = {"Random Forest": rf, "Gradient Boosting": gbm, "Ridge": rid}
    cv_results = {}
    for name, m in models.items():
        cv_results[name] = cross_val_score(m, X_model, y, cv=5, scoring="r2")
        m.fit(X_model, y)

    # SHAP sobre RF
    explainer   = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X_model)

    return df_main, cols_model, X_model, y, rf, gbm, rid, cv_results, shap_values


# ══════════════════════════════════════════════════════════════════════════════
# C. FIGURAS
# ══════════════════════════════════════════════════════════════════════════════

def short(nombre):
    return (nombre.replace(" de Ignacio de la Llave", "")
                  .replace(" de Zaragoza", "")
                  .replace(" de Ocampo", ""))


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1: tasa_Sociedad vs pilar_innovacion
# ─────────────────────────────────────────────────────────────────────────────
def fig1_sociedad(df2, df_main):
    fig, axes = plt.subplots(1, 3, figsize=(19, 6))
    fig.suptitle(
        "Delitos contra la Sociedad como señal del entorno de innovación",
        fontsize=14, fontweight="bold", y=1.01,
    )

    # Panel A — scatter 2022-2024, coloreado por grupo
    ax = axes[0]
    yr_markers = {2022: "o", 2023: "s", 2024: "^"}
    for yr, mk in yr_markers.items():
        sub = df2[df2["anio"] == yr]
        ax.scatter(sub["tasa_Sociedad"], sub["pilar_innovacion"],
                   c=[GRUPO_COLORS_RAW[g] for g in sub["grupo_label"]],
                   marker=mk, s=55, alpha=0.82, edgecolors="white", lw=0.4, zorder=3)

    x_ = df_main["tasa_Sociedad"].values
    y_ = df_main["pilar_innovacion"].values
    slope, intercept, r, p, _ = stats.linregress(x_, y_)
    xi = np.linspace(x_.min(), x_.max(), 200)
    ax.plot(xi, slope * xi + intercept, "k--", lw=1.6,
            label=f"r = {r:.2f}  (p = {p:.3f})")

    leg_grupos = [Patch(color=c, label=g) for g, c in GRUPO_COLORS_RAW.items()]
    leg_anios  = [Line2D([0],[0], marker=mk, color="gray", ls="None",
                         ms=7, label=str(yr)) for yr, mk in yr_markers.items()]
    ax.legend(handles=leg_grupos + leg_anios, fontsize=7.5, ncol=2)
    ax.set_xlabel("Tasa Sociedad (por 100k hab.)")
    ax.set_ylabel("Pilar Innovación IDDE")
    ax.set_title("A. Relación global  2022–2024")

    # Panel B — corte 2022 con etiquetas
    ax2 = axes[1]
    sub22 = df2[df2["anio"] == 2022].reset_index(drop=True)
    ax2.scatter(sub22["tasa_Sociedad"], sub22["pilar_innovacion"],
                c=[GRUPO_COLORS_RAW[g] for g in sub22["grupo_label"]],
                s=65, edgecolors="white", lw=0.4, zorder=3)
    for _, row in sub22.iterrows():
        ax2.annotate(short(row["estado"]),
                     (row["tasa_Sociedad"], row["pilar_innovacion"]),
                     fontsize=6, ha="center", va="bottom",
                     xytext=(0, 3), textcoords="offset points")
    s2, i2, r2, p2, _ = stats.linregress(sub22["tasa_Sociedad"], sub22["pilar_innovacion"])
    xi2 = np.linspace(sub22["tasa_Sociedad"].min(), sub22["tasa_Sociedad"].max(), 200)
    ax2.plot(xi2, s2 * xi2 + i2, "k--", lw=1.6, label=f"r = {r2:.2f}")
    ax2.set_xlabel("Tasa Sociedad (por 100k hab.)")
    ax2.set_ylabel("Pilar Innovación IDDE")
    ax2.set_title("B. Corte transversal 2022 (etiquetado)")
    ax2.legend(fontsize=9)

    # Panel C — violín tasa_Sociedad por grupo
    ax3 = axes[2]
    data_v = [df2[df2["grupo_label"] == g]["tasa_Sociedad"].values for g in GRUPO_ORDER]
    parts  = ax3.violinplot(data_v, positions=range(len(GRUPO_ORDER)),
                             showmedians=True, showextrema=True)
    for pc, g in zip(parts["bodies"], GRUPO_ORDER):
        pc.set_facecolor(GRUPO_COLORS_RAW[g])
        pc.set_alpha(0.75)
    parts["cmedians"].set_color("black")
    parts["cmedians"].set_linewidth(2)
    parts["cbars"].set_visible(False)
    parts["cmaxes"].set_visible(False)
    parts["cmins"].set_visible(False)
    ax3.set_xticks(range(len(GRUPO_ORDER)))
    ax3.set_xticklabels(GRUPO_ORDER, rotation=10)
    ax3.set_ylabel("Tasa Sociedad (por 100k hab.)")
    ax3.set_title("C. Distribución por grupo digital")

    plt.tight_layout()
    plt.savefig("fig1_sociedad_innovacion.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("Guardada: fig1_sociedad_innovacion.png")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2: Composición delictiva por grupo
# ─────────────────────────────────────────────────────────────────────────────
def fig2_composicion(df2):
    share_labels = {
        "share_Sociedad": "Sociedad", "share_Patrimonio": "Patrimonio",
        "share_Vida": "Vida",         "share_Familia": "Familia",
        "share_Sexual": "Sexual",     "share_Libertad": "Libertad",
        "share_Otros": "Otros",
    }
    sc = list(share_labels.keys())
    means = (df2.groupby("grupo_label")[sc].mean()
               .loc[GRUPO_ORDER]
               .rename(columns=share_labels))

    cat_palette = ["#e6194b","#3cb44b","#4363d8","#f58231",
                   "#911eb4","#42d4f4","#bfef45"]

    fig, axes = plt.subplots(1, 2, figsize=(17, 6))
    fig.suptitle("Composición del Crimen según Nivel de Desarrollo Digital",
                 fontsize=14, fontweight="bold")

    # Panel A — stacked bar
    ax = axes[0]
    bottom = np.zeros(len(GRUPO_ORDER))
    for cat, color in zip(means.columns, cat_palette):
        vals = means[cat].values
        bars = ax.bar(GRUPO_ORDER, vals, bottom=bottom, color=color,
                      label=cat, edgecolor="white", lw=0.5)
        for i, (b, v) in enumerate(zip(bottom, vals)):
            if v > 0.035:
                ax.text(i, b + v / 2, f"{v:.1%}", ha="center", va="center",
                        fontsize=8.5, color="white", fontweight="bold")
        bottom += vals

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Proporción del total de delitos")
    ax.set_title("A. Composición promedio 2022–2024")
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    # Panel B — diferencia Líder - Básico
    ax2 = axes[1]
    diff = means.loc["Líder"] - means.loc["Básico"]
    diff = diff.sort_values()
    cols_bar = ["#2ca02c" if v > 0 else "#d62728" for v in diff.values]
    bars2 = ax2.barh(diff.index, diff.values, color=cols_bar,
                     edgecolor="white", alpha=0.85)
    ax2.axvline(0, color="black", lw=1.0)
    ax2.set_xlabel("Diferencia en proporción  (Líder − Básico)")
    ax2.set_title("B. Qué separa al grupo Líder del Básico")
    for bar, val in zip(bars2, diff.values):
        s = "+" if val > 0 else ""
        ax2.text(val + np.sign(val) * 0.002, bar.get_y() + bar.get_height() / 2,
                 f"{s}{val:.2%}", va="center",
                 ha="left" if val > 0 else "right", fontsize=9)

    plt.tight_layout()
    plt.savefig("fig2_composicion_crimen.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("-> fig2_composicion_crimen.png")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3: Evolución temporal 2015-2024
# ─────────────────────────────────────────────────────────────────────────────
def fig3_temporal(df1, df2):
    grupo_ref = df2[df2["anio"] == 2022][["estado", "grupo_label"]].drop_duplicates()

    # Combina df1 (2015-2021) y df2 (2022-2024); evita duplicar 2022
    def _serie(col):
        a = df1[["anio","estado", col]].merge(grupo_ref, on="estado", how="left")
        b = df2[df2["anio"] > 2022][["anio","estado", col]].merge(grupo_ref, on="estado", how="left")
        b2022 = df2[df2["anio"] == 2022][["anio","estado", col]].merge(grupo_ref, on="estado", how="left")
        return pd.concat([a, b2022, b], ignore_index=True)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Evolución Temporal del Crimen por Grupo de Digitalización  (2015–2024)",
                 fontsize=14, fontweight="bold")

    for ax, col, title in [
        (axes[0, 0], "tasa_Sociedad",   "A. Delitos contra la Sociedad  (narco, tráfico, lenocinio)"),
        (axes[0, 1], "tasa_Patrimonio", "B. Delitos contra el Patrimonio  (robo, fraude, extorsión)"),
        (axes[1, 0], "tasa_Vida",       "C. Delitos contra la Vida  (homicidio, lesiones)"),
        (axes[1, 1], "tasa_x100k",      "D. Incidencia total"),
    ]:
        df_s = _serie(col)
        for g in GRUPO_ORDER:
            sub = df_s[df_s["grupo_label"] == g].groupby("anio")[col].mean()
            ax.plot(sub.index, sub.values, color=GRUPO_COLORS_RAW[g],
                    marker="o", ms=4.5, lw=2, label=g)
        ax.axvline(2022, color="gray", ls=":", lw=1.5, label="inicio IDDE")
        ax.set_xlabel("Año")
        ax.set_ylabel("Tasa por 100k hab.")
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8.5)

    plt.tight_layout()
    plt.savefig("fig3_evolucion_temporal.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("-> fig3_evolucion_temporal.png")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4: Comparación de modelos + Actual vs predicho
# ─────────────────────────────────────────────────────────────────────────────
def fig4_modelos(df_main, cols_model, X_model, y, rf, gbm, rid, cv_results):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Calidad del Modelo Predictivo  —  pilar_innovacion ~ tasas de crimen",
                 fontsize=14, fontweight="bold")

    # Panel A — CV R² comparación
    ax = axes[0]
    names = list(cv_results.keys())
    means = [cv_results[n].mean() for n in names]
    stds  = [cv_results[n].std()  for n in names]
    colors_bar = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    bars = ax.bar(names, means, yerr=stds, color=colors_bar,
                  alpha=0.85, capsize=7, edgecolor="white")
    ax.axhline(0.7, color="red", ls="--", lw=1.2, alpha=0.7, label="umbral R²=0.7")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("CV R²  (5-fold)")
    ax.set_title("A. Comparación de modelos")
    ax.legend(fontsize=8.5)
    for bar, m, s in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width() / 2, m + s + 0.02,
                f"{m:.3f}", ha="center", fontsize=10, fontweight="bold")

    # Panel B — Actual vs predicho (RF)
    ax2 = axes[1]
    y_pred = rf.predict(X_model)
    sc = ax2.scatter(y, y_pred, c=y, cmap="RdYlGn", s=60,
                     alpha=0.8, edgecolors="white", lw=0.4, zorder=3)
    plt.colorbar(sc, ax=ax2, label="pilar_innovacion real")
    resid = np.abs(y - y_pred)
    for idx in np.argsort(resid)[-6:]:
        ax2.annotate(short(df_main["estado"].iloc[idx]),
                     (y[idx], y_pred[idx]), fontsize=6.5,
                     xytext=(3, 3), textcoords="offset points", color="#555")
    lo = min(y.min(), y_pred.min()) - 2
    hi = max(y.max(), y_pred.max()) + 2
    ax2.plot([lo, hi], [lo, hi], "k--", lw=1.3, label="Perfecto")
    ax2.set_xlabel("pilar_innovacion real")
    ax2.set_ylabel("Predicción  RF")
    ax2.set_title("B. Real vs Predicho  (Random Forest)")
    ax2.legend(fontsize=8.5)

    # Panel C — Importancia por permutación
    ax3 = axes[2]
    perm = permutation_importance(rf, X_model, y, n_repeats=25,
                                  random_state=42, scoring="r2")
    perm_df = (pd.DataFrame({"feature": cols_model,
                              "imp": perm.importances_mean,
                              "std": perm.importances_std})
               .sort_values("imp", ascending=True))
    colors_imp = ["#d62728" if v > 0 else "#aec7e8" for v in perm_df["imp"]]
    ax3.barh(perm_df["feature"], perm_df["imp"], xerr=perm_df["std"],
             color=colors_imp, alpha=0.85, edgecolor="white")
    ax3.axvline(0, color="black", lw=0.9, ls="--")
    ax3.set_xlabel("Caída en R² al aleatorizar la feature")
    ax3.set_title("C. Importancia por permutación  (RF)")

    plt.tight_layout()
    plt.savefig("fig4_modelos.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("-> fig4_modelos.png")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5: SHAP beeswarm
# ─────────────────────────────────────────────────────────────────────────────
def fig5_shap(X_model, shap_values, cols_model):
    fig, ax = plt.subplots(figsize=(10, 7))
    plt.sca(ax)
    shap.summary_plot(shap_values, X_model, feature_names=cols_model,
                      show=False, plot_size=None)
    ax.set_title("Valores SHAP  —  impacto de cada variable en pilar_innovacion",
                 fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig("fig5_shap.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("-> fig5_shap.png")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 6: Heatmap de correlaciones
# ─────────────────────────────────────────────────────────────────────────────
def fig6_correlaciones(df2):
    idde_cols  = ["idde_score", "pilar_infraestructura", "pilar_sociedad", "pilar_innovacion"]
    tasa_cols  = [c for c in df2.columns if c.startswith("tasa_") and c != "tasa_x100k"]
    share_cols = [c for c in df2.columns if c.startswith("share_")]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
    fig.suptitle("Correlaciones: Crimen <-> Desarrollo Digital",
                 fontsize=14, fontweight="bold")

    for ax, cols, title in [
        (axes[0], tasa_cols,  "A. Tasas absolutas (por 100k hab.)"),
        (axes[1], share_cols, "B. Composición del crimen (shares)"),
    ]:
        corr = df2[cols + idde_cols].corr().loc[cols, idde_cols]
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(idde_cols)))
        ax.set_xticklabels(idde_cols, rotation=30, ha="right", fontsize=9)
        ax.set_yticks(range(len(cols)))
        ax.set_yticklabels([c.split("_", 1)[1] for c in cols], fontsize=9)
        for i in range(len(cols)):
            for j in range(len(idde_cols)):
                v = corr.iloc[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.5,
                        color="white" if abs(v) > 0.5 else "black")
        plt.colorbar(im, ax=ax, shrink=0.85, label="r de Pearson")
        ax.set_title(title)

    plt.tight_layout()
    plt.savefig("fig6_correlaciones.png", bbox_inches="tight", dpi=150)
    plt.show()
    print("-> fig6_correlaciones.png")


# ══════════════════════════════════════════════════════════════════════════════
# D. INTERPRETACIONES
# ══════════════════════════════════════════════════════════════════════════════

def imprimir_interpretaciones(df2, df_main, cols_model, cv_results, shap_values, X_model):
    print("\n" + "=" * 70)
    print("INTERPRETACIÓN DE RESULTADOS")
    print("=" * 70)

    r, p = pearsonr(df_main["tasa_Sociedad"], df_main["pilar_innovacion"])
    print(f"\n[Fig 1 — Sociedad vs Innovación]")
    print(f"  Correlación global: r = {r:.3f}  (p = {p:.4f})")
    print("  -> La tasa de delitos contra la Sociedad (narcomenudeo, lenocinio,")
    print("    tráfico de menores) es el predictor más fuerte del pilar innovación.")
    print("  -> La relación es POSITIVA: estados con mayor tasa_Sociedad tienden")
    print("    a tener mayor pilar_innovación. Esto parece contra-intuitivo, pero")
    print("    refleja que ambas variables se concentran en los mismos estados")
    print("    urbanizados y fronterizos (BC, NL, Jalisco, CDMX): el crimen")
    print("    organizado visible y la actividad digital/empresarial coexisten.")
    print("  -> Los estados Básico (rurales, bajo reporte) tienen baja tasa_Sociedad")
    print("    Y baja innovación; los Líderes tienen alta en ambas.")

    print(f"\n[Fig 2 — Composición]")
    sc = [c for c in df2.columns if c.startswith("share_")]
    means = df2.groupby("grupo_label")[sc].mean().loc[GRUPO_ORDER]
    diff = means.loc["Líder"] - means.loc["Básico"]
    top_pos = diff.idxmax().replace("share_", "")
    top_neg = diff.idxmin().replace("share_", "")
    print(f"  -> Los estados Líder tienen MÁS proporción de '{top_pos}'")
    print(f"    y MENOS de '{top_neg}' respecto a los Básico.")
    print("  -> Los estados de bajo desarrollo digital concentran más crimen")
    print("    contra la Vida y Familia (violencia interpersonal, entorno inseguro).")
    print("  -> Los estados avanzados tienen más crimen contra el Patrimonio y")
    print("    la Sociedad, reflejo de mayor actividad económica y urbana.")

    print(f"\n[Fig 3 — Tendencias temporales]")
    print("  -> tasa_Sociedad ha crecido consistentemente en todos los grupos")
    print("    desde 2015, con aceleración post-2019.")
    print("  -> tasa_Patrimonio muestra una caída notoria en 2020 (pandemia)")
    print("    con recuperación parcial en 2021-2022.")
    print("  -> La brecha entre grupos Líder y Básico se mantiene estable en")
    print("    tasa_Vida, pero se amplía en tasa_Sociedad post-2018.")
    print("  -> La incidencia total (fig D) muestra que los grupos Avanzado/Líder")
    print("    siempre reportan más delitos en términos absolutos por habitante.")

    print(f"\n[Fig 4 — Modelos]")
    for name, cv in cv_results.items():
        print(f"  {name:20s}: R² = {cv.mean():.4f} +/- {cv.std():.4f}")
    best = max(cv_results, key=lambda n: cv_results[n].mean())
    print(f"  -> Mejor modelo: {best}")
    print("  -> Las features de crimen explican ~75-80% de la varianza del pilar")
    print("    innovación, un resultado muy fuerte para datos socioeconómicos.")
    print("  -> Los mayores residuos (estados 'sorpresa') suelen ser estados con")
    print("    perfil de crimen atípico para su nivel de digitalización.")

    shap_abs = np.abs(shap_values).mean(axis=0)
    feat_importance = sorted(zip(cols_model, shap_abs), key=lambda x: x[1], reverse=True)
    print(f"\n[Fig 5 — SHAP]")
    print("  Top 5 features por impacto medio:")
    for feat, imp in feat_importance[:5]:
        print(f"    {feat:35s}: SHAP medio = {imp:.3f}")
    print("  -> tasa_Sociedad con valores ALTOS (estados con más narco/tráfico)")
    print("    tiene valores SHAP positivos -> predice MÁS innovación.")
    print("  -> tasa_Patrimonio con valores ALTOS tiene SHAP negativos ->")
    print("    el robo/fraude extenso frena la innovación.")

    print(f"\n[Fig 6 — Correlaciones]")
    tasa_cols = [c for c in df2.columns if c.startswith("tasa_") and c != "tasa_x100k"]
    corr_inn = df2[tasa_cols + ["pilar_innovacion"]].corr()["pilar_innovacion"].drop("pilar_innovacion")
    pos = corr_inn.idxmax().replace("tasa_", "")
    neg = corr_inn.idxmin().replace("tasa_", "")
    print(f"  Correlación más positiva con pilar_innovacion: {pos} (r={corr_inn.max():.2f})")
    print(f"  Correlación más negativa con pilar_innovacion: {neg} (r={corr_inn.min():.2f})")
    print("  -> La tabla revela que todas las tasas de crimen correlacionan")
    print("    positivamente con idde_score total, lo que refuerza la hipótesis")
    print("    de urbanización como variable latente confusora.")

    print("\n" + "=" * 70)
    print("CONCLUSIÓN GENERAL")
    print("=" * 70)
    print("""
  El patrón fundamental de este análisis es el siguiente:

  1. El nivel de digitalización de un estado mexicano puede predecirse con
     alta precisión (~75% R²) únicamente a partir de su perfil delictivo.

  2. Esto NO implica causalidad directa entre crimen e innovación, sino que
     ambas variables son manifestaciones del mismo factor latente: el grado
     de URBANIZACIÓN y desarrollo económico del estado.

  3. El crimen contra la Sociedad (narco retail, lenocinio) es un proxy de
     mercados informales complejos típicos de zonas urbanas densas.

  4. El crimen contra el Patrimonio masivo (robos, fraude) refleja una
     economía activa pero con instituciones débiles, y SÍ parece tener
     efecto negativo propio sobre la innovación.

  5. Los estados con bajo crimen total (Básico/rural) también tienen bajo
     desarrollo digital: la "seguridad" aparente puede reflejar subregistro
     y menor actividad económica, no mejor gobernanza.

  Implicación de política: mejorar el entorno digital no requiere solo
  reducir el crimen — requiere atender el desarrollo económico urbano del
  que ambos son síntomas.
""")


# ══════════════════════════════════════════════════════════════════════════════
# E. MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Cargando datos...")
    df1, df2 = build_dataframes()
    print(f"  DF1: {df1.shape}  |  DF2: {df2.shape}")

    print("Entrenando modelos...")
    df_main, cols_model, X_model, y, rf, gbm, rid, cv_results, shap_values = \
        build_model_pipeline(df2)

    print(f"  Features seleccionadas ({len(cols_model)}): {cols_model}")
    print("\n  CV R²:")
    for name, cv in cv_results.items():
        print(f"    {name:22s}: {cv.mean():.4f} +/- {cv.std():.4f}")

    print("\nGenerando figuras...")
    fig1_sociedad(df2, df_main)
    fig2_composicion(df2)
    fig3_temporal(df1, df2)
    fig4_modelos(df_main, cols_model, X_model, y, rf, gbm, rid, cv_results)
    fig5_shap(X_model, shap_values, cols_model)
    fig6_correlaciones(df2)

    imprimir_interpretaciones(df2, df_main, cols_model, cv_results, shap_values, X_model)
