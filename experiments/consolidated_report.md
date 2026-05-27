# Multi-Agent Experiment Report

**Generated:** 2026-05-26 23:33:31  
**Total experiments:** 146  
**Promising findings:** 99  

---

## Agent Summary

| Agent | Experiments | Promising | Duration |
|-------|-----------|----------|----------|
| structural | 21 | 17 | 3.0s |
| robustness | 49 | 29 | 3.4s |
| ml_discovery | 53 | 37 | 77.4s |
| unorthodox | 23 | 16 | 0.3s |

---

## Top 20 Findings (ranked by score)

### ★ #1: Crime type × IDDE correlation breakdown

**Agent:** structural | **Exp:** 1.14 | **Score:** 448 (conf=7, nov=8, narr=8)

**Description:** Which specific crime types correlate most/least with IDDE?

**Finding:** Most negative (crime ↓ with IDDE): Electorales: r=-0.319; Robo a institución bancaria: r=-0.256; Robo a transportista: r=-0.149. Most positive (crime ↑ with IDDE): Violencia familiar: r=0.576; Abuso sexual: r=0.583; Fraude: r=0.596.

**Statistic:** median_r=0.2878

**Recommendation:** Crime type heterogeneity reveals which crimes digitalization might address.

---

### ★ #2: Permutation test: IDDE → municipal crime (N=5000)

**Agent:** structural | **Exp:** 1.16 | **Score:** 432 (conf=9, nov=6, narr=8)

**Description:** Exact p-value from label-shuffling permutation test, no distributional assumptions

**Finding:** Observed r=0.1945. Permutation p=0.0000 (5000 permutations). Significant — this is the most honest p-value possible.

**Statistic:** r=0.1945, p=0.0

**Recommendation:** Permutation test is the gold standard for non-parametric inference. Report this number.

---

### ★ #3: State IDDE → Municipal crime change (2022→latest)

**Agent:** structural | **Exp:** 1.9 | **Score:** 392 (conf=7, nov=7, narr=8)

**Description:** Does IDDE predict crime reduction at the municipal level?

**Finding:** r=-0.0418, p=0.0373, N=2479. Higher IDDE → crime reduction.

**Statistic:** r=-0.0418, p=0.0373

**Recommendation:** This is the strongest possible evidence: same municipality, crime change predicted by state IDDE.

---

### ★ #4: Top predictor → Homicide

**Agent:** ml_discovery | **Exp:** 3.11 | **Score:** 384 (conf=6, nov=8, narr=8)

**Description:** Which digital feature best predicts each crime type?

**Finding:** Homicide: #1 predictor = graduados_en_programas_stem_xm (importance=0.276). Top 3: graduados_en_programas_st, velocidad_de_descarga_de_, cobertura_de_banda_ancha_

**Statistic:** top_importance=0.276

**Recommendation:** Different crime types have different predictors. This is a powerful narrative for the dashboard.

---

### ★ #5: Top predictor → Robbery

**Agent:** ml_discovery | **Exp:** 3.11 | **Score:** 384 (conf=6, nov=8, narr=8)

**Description:** Which digital feature best predicts each crime type?

**Finding:** Robbery: #1 predictor = penetracion_de_banda_ancha_fij (importance=0.225). Top 3: penetracion_de_banda_anch, graduados_en_programas_st, velocidad_de_descarga_de_

**Statistic:** top_importance=0.225

**Recommendation:** Different crime types have different predictors. This is a powerful narrative for the dashboard.

---

### ★ #6: Top predictor → Fraud

**Agent:** ml_discovery | **Exp:** 3.11 | **Score:** 384 (conf=6, nov=8, narr=8)

**Description:** Which digital feature best predicts each crime type?

**Finding:** Fraud: #1 predictor = indice_de_desarrollo_digital_e (importance=0.299). Top 3: indice_de_desarrollo_digi, graduados_en_programas_st, penetracion_de_banda_anch

**Statistic:** top_importance=0.299

**Recommendation:** Different crime types have different predictors. This is a powerful narrative for the dashboard.

---

### ★ #7: Top predictor → Domestic violence

**Agent:** ml_discovery | **Exp:** 3.11 | **Score:** 384 (conf=6, nov=8, narr=8)

**Description:** Which digital feature best predicts each crime type?

**Finding:** Domestic violence: #1 predictor = empresas_que_utilizan_banca_el (importance=0.324). Top 3: empresas_que_utilizan_ban, cobertura_de_banda_ancha_, graduados_en_programas_st

**Statistic:** top_importance=0.324

**Recommendation:** Different crime types have different predictors. This is a powerful narrative for the dashboard.

---

### ★ #8: Top predictor → Drug trafficking

**Agent:** ml_discovery | **Exp:** 3.11 | **Score:** 384 (conf=6, nov=8, narr=8)

**Description:** Which digital feature best predicts each crime type?

**Finding:** Drug trafficking: #1 predictor = empresas_que_utilizan_banca_el (importance=0.415). Top 3: empresas_que_utilizan_ban, graduados_en_programas_st, cobertura_de_redes_movile

**Statistic:** top_importance=0.415

**Recommendation:** Different crime types have different predictors. This is a powerful narrative for the dashboard.

---

### ★ #9: Cifra negra: adjusted vs raw IDDE→crime

**Agent:** unorthodox | **Exp:** 4.1 | **Score:** 360 (conf=5, nov=9, narr=8)

**Description:** Adjusting crime rates for underreporting using perception as proxy

**Finding:** Raw r=0.5984 (p=0.0004). Adjusted r=0.1863 (p=0.3157). Δ=-0.4121. Underreporting inflates the IDDE-crime correlation.

**Statistic:** r_adjusted=0.1863, p=0.3157

**Recommendation:** If delta is large, the dashboard MUST acknowledge cifra negra as a confounder.

---

### ★ #10: MI vs Pearson: Average wage

**Agent:** ml_discovery | **Exp:** 3.2 | **Score:** 343 (conf=7, nov=7, narr=7)

**Description:** Mutual information (nonlinear) vs Pearson (linear) feature ranking

**Finding:** MI top 3: empresas_que_utilizan_ban, penetracion_de_banda_anch, velocidad_de_descarga_de_. Pearson top 3: empresas_que_utilizan_ban, indice_de_desarrollo_digi, penetracion_de_banda_anch. Overlap=2/3. 1 features are nonlinear-only.

**Statistic:** top3_overlap=2

**Recommendation:** Features that rank high in MI but not in Pearson have nonlinear relationships.

---

### ★ #11: MI vs Pearson: Crime rate

**Agent:** ml_discovery | **Exp:** 3.2 | **Score:** 343 (conf=7, nov=7, narr=7)

**Description:** Mutual information (nonlinear) vs Pearson (linear) feature ranking

**Finding:** MI top 3: cobertura_de_redes_movile, penetracion_de_banda_anch, cobertura_de_banda_ancha_. Pearson top 3: indice_de_desarrollo_digi, penetracion_de_banda_anch, empresas_que_utilizan_ban. Overlap=1/3. 2 features are nonlinear-only.

**Statistic:** top3_overlap=1

**Recommendation:** Features that rank high in MI but not in Pearson have nonlinear relationships.

---

### ★ #12: MI vs Pearson: Homicide rate

**Agent:** ml_discovery | **Exp:** 3.2 | **Score:** 343 (conf=7, nov=7, narr=7)

**Description:** Mutual information (nonlinear) vs Pearson (linear) feature ranking

**Finding:** MI top 3: graduados_en_programas_st, cobertura_de_redes_movile, cobertura_de_banda_ancha_. Pearson top 3: graduados_en_programas_st, velocidad_de_descarga_de_, penetracion_de_banda_anch. Overlap=1/3. 2 features are nonlinear-only.

**Statistic:** top3_overlap=1

**Recommendation:** Features that rank high in MI but not in Pearson have nonlinear relationships.

---

### ★ #13: MI vs Pearson: Fraud rate

**Agent:** ml_discovery | **Exp:** 3.2 | **Score:** 343 (conf=7, nov=7, narr=7)

**Description:** Mutual information (nonlinear) vs Pearson (linear) feature ranking

**Finding:** MI top 3: indice_de_desarrollo_digi, graduados_en_programas_st, penetracion_de_banda_anch. Pearson top 3: indice_de_desarrollo_digi, penetracion_de_banda_anch, empresas_que_utilizan_ban. Overlap=2/3. 1 features are nonlinear-only.

**Statistic:** top3_overlap=2

**Recommendation:** Features that rank high in MI but not in Pearson have nonlinear relationships.

---

### ★ #14: Threshold effect: IDDE → Wage

**Agent:** ml_discovery | **Exp:** 3.7 | **Score:** 336 (conf=6, nov=8, narr=7)

**Description:** Piecewise linear regression with optimal breakpoint in IDDE

**Finding:** Best threshold=130.5, R²_piecewise=0.214, R²_linear=0.163, Δ=+0.050. Threshold effect detected.

**Statistic:** delta_R2_threshold=0.05

**Recommendation:** If threshold found, the dashboard can say "above IDDE=X, the relationship changes."

---

### ★ #15: IDDE → Cyber crime group

**Agent:** unorthodox | **Exp:** 4.2 | **Score:** 336 (conf=6, nov=7, narr=8)

**Description:** Composite rate of cyber crimes vs IDDE

**Finding:** Cyber: r=0.6286, p=0.0002. Positive (crime ↑ with IDDE).

**Statistic:** r=0.6286, p=0.0002

**Recommendation:** If Cyber crime shows different direction than total crime, this is a key finding.

---

### ★ #16: IDDE → Domestic crime group

**Agent:** unorthodox | **Exp:** 4.2 | **Score:** 336 (conf=6, nov=7, narr=8)

**Description:** Composite rate of domestic crimes vs IDDE

**Finding:** Domestic: r=0.5948, p=0.0004. Positive (crime ↑ with IDDE).

**Statistic:** r=0.5948, p=0.0004

**Recommendation:** If Domestic crime shows different direction than total crime, this is a key finding.

---

### ★ #17: IDDE → Large company share (DENUE)

**Agent:** unorthodox | **Exp:** 4.6 | **Score:** 336 (conf=6, nov=8, narr=7)

**Description:** Does digital development correlate with having more large companies?

**Finding:** r(IDDE, large_share)=0.8229, p=0.0000.

**Statistic:** r=0.8229, p=0.0

**Recommendation:** DENUE is completely unused in the dashboard. If significant, adds economic depth.

---

### ★ #18: Permutation test: BB coverage → Friend trust (r=0.78)

**Agent:** robustness | **Exp:** 2.4 | **Score:** 315 (conf=9, nov=5, narr=7)

**Description:** Exact p-value from 1000 label-shuffling permutations

**Finding:** r=0.7786, permutation p=0.0000 (1000 perms). Confirmed significant.

**Statistic:** r=0.7786, p=0.0

---

### ★ #19: Permutation test: IDDE → Family trust (r=0.65)

**Agent:** robustness | **Exp:** 2.4 | **Score:** 315 (conf=9, nov=5, narr=7)

**Description:** Exact p-value from 1000 label-shuffling permutations

**Finding:** r=0.6530, permutation p=0.0000 (1000 perms). Confirmed significant.

**Statistic:** r=0.653, p=0.0

---

### ★ #20: Permutation test: IDDE → Fraud (r=0.63)

**Agent:** robustness | **Exp:** 2.4 | **Score:** 315 (conf=9, nov=5, narr=7)

**Description:** Exact p-value from 1000 label-shuffling permutations

**Finding:** r=0.6286, permutation p=0.0000 (1000 perms). Confirmed significant.

**Statistic:** r=0.6286, p=0.0

---


## All Promising Findings

- **[structural:1.14]** Crime type × IDDE correlation breakdown (score=448) — Most negative (crime ↓ with IDDE): Electorales: r=-0.319; Robo a institución bancaria: r=-0.256; Robo a transportista: r
- **[structural:1.16]** Permutation test: IDDE → municipal crime (N=5000) (score=432) — Observed r=0.1945. Permutation p=0.0000 (5000 permutations). Significant — this is the most honest p-value possible.
- **[structural:1.9]** State IDDE → Municipal crime change (2022→latest) (score=392) — r=-0.0418, p=0.0373, N=2479. Higher IDDE → crime reduction.
- **[ml_discovery:3.11]** Top predictor → Homicide (score=384) — Homicide: #1 predictor = graduados_en_programas_stem_xm (importance=0.276). Top 3: graduados_en_programas_st, velocidad_
- **[ml_discovery:3.11]** Top predictor → Robbery (score=384) — Robbery: #1 predictor = penetracion_de_banda_ancha_fij (importance=0.225). Top 3: penetracion_de_banda_anch, graduados_e
- **[ml_discovery:3.11]** Top predictor → Fraud (score=384) — Fraud: #1 predictor = indice_de_desarrollo_digital_e (importance=0.299). Top 3: indice_de_desarrollo_digi, graduados_en_
- **[ml_discovery:3.11]** Top predictor → Domestic violence (score=384) — Domestic violence: #1 predictor = empresas_que_utilizan_banca_el (importance=0.324). Top 3: empresas_que_utilizan_ban, c
- **[ml_discovery:3.11]** Top predictor → Drug trafficking (score=384) — Drug trafficking: #1 predictor = empresas_que_utilizan_banca_el (importance=0.415). Top 3: empresas_que_utilizan_ban, gr
- **[unorthodox:4.1]** Cifra negra: adjusted vs raw IDDE→crime (score=360) — Raw r=0.5984 (p=0.0004). Adjusted r=0.1863 (p=0.3157). Δ=-0.4121. Underreporting inflates the IDDE-crime correlation.
- **[ml_discovery:3.2]** MI vs Pearson: Average wage (score=343) — MI top 3: empresas_que_utilizan_ban, penetracion_de_banda_anch, velocidad_de_descarga_de_. Pearson top 3: empresas_que_u
- **[ml_discovery:3.2]** MI vs Pearson: Crime rate (score=343) — MI top 3: cobertura_de_redes_movile, penetracion_de_banda_anch, cobertura_de_banda_ancha_. Pearson top 3: indice_de_desa
- **[ml_discovery:3.2]** MI vs Pearson: Homicide rate (score=343) — MI top 3: graduados_en_programas_st, cobertura_de_redes_movile, cobertura_de_banda_ancha_. Pearson top 3: graduados_en_p
- **[ml_discovery:3.2]** MI vs Pearson: Fraud rate (score=343) — MI top 3: indice_de_desarrollo_digi, graduados_en_programas_st, penetracion_de_banda_anch. Pearson top 3: indice_de_desa
- **[ml_discovery:3.7]** Threshold effect: IDDE → Wage (score=336) — Best threshold=130.5, R²_piecewise=0.214, R²_linear=0.163, Δ=+0.050. Threshold effect detected.
- **[unorthodox:4.2]** IDDE → Cyber crime group (score=336) — Cyber: r=0.6286, p=0.0002. Positive (crime ↑ with IDDE).
- **[unorthodox:4.2]** IDDE → Domestic crime group (score=336) — Domestic: r=0.5948, p=0.0004. Positive (crime ↑ with IDDE).
- **[unorthodox:4.6]** IDDE → Large company share (DENUE) (score=336) — r(IDDE, large_share)=0.8229, p=0.0000.
- **[robustness:2.4]** Permutation test: BB coverage → Friend trust (r=0.78) (score=315) — r=0.7786, permutation p=0.0000 (1000 perms). Confirmed significant.
- **[robustness:2.4]** Permutation test: IDDE → Family trust (r=0.65) (score=315) — r=0.6530, permutation p=0.0000 (1000 perms). Confirmed significant.
- **[robustness:2.4]** Permutation test: IDDE → Fraud (r=0.63) (score=315) — r=0.6286, permutation p=0.0000 (1000 perms). Confirmed significant.
- **[structural:1.1]** State IDDE → Municipal crime (N=2457) (score=294) — r=0.2561, p=3.75e-38, N=2461. Significant at municipal level.
- **[structural:1.4_violent]** State IDDE → Violent crime (municipal aggregation) (score=294) — Violent crime: r=0.5764, p=0.0006, N=32.
- **[structural:1.4_property]** State IDDE → Property crime (municipal aggregation) (score=294) — Property crime: r=0.5323, p=0.0017, N=32.
- **[structural:1.15]** Year-by-year municipal IDDE→crime correlation trend (score=294) — 2022: r=0.188 (p=0.000); 2023: r=0.187 (p=0.000); 2024: r=0.192 (p=0.000); 2025: r=0.195 (p=0.000). Trend in r: r_trend=
- **[unorthodox:4.4]** RANSAC robust: IDDE → Wage (score=294) — OLS β=26.4, R²=0.371. RANSAC β=21.3, R²=0.248. Inliers=20, Outliers=11: .
- **[unorthodox:4.4]** RANSAC robust: IDDE → Crime (score=294) — OLS β=13.9, R²=0.358. RANSAC β=8.6, R²=-0.015. Inliers=16, Outliers=15: .
- **[structural:1.12]** Crime variance decomposition: between vs within states (score=280) — ICC=1.780. 178.0% of municipal crime variance is BETWEEN states. -78.0% is WITHIN states. State-level analysis captures 
- **[robustness:2.16]** Holm correction: how many correlations survive? (score=280) — Nominal p<0.05: 166/532. After Holm correction: 20/532. After BH (from EXP-26): 105/532.
- **[structural:1.2]** IDDE → Within-state crime heterogeneity (score=252) — r(IDDE, CV)=-0.3863, p=0.0290. States with higher IDDE have more uniform crime rates.
- **[ml_discovery:3.3]** Linear vs RF R²: Average wage (score=252) — Linear R²=-0.068, RF R²=0.214, Δ=+0.282. Nonlinear patterns present.
- **[ml_discovery:3.3]** Linear vs RF R²: Family trust (score=252) — Linear R²=-0.443, RF R²=0.146, Δ=+0.589. Nonlinear patterns present.
- **[ml_discovery:3.3]** Linear vs RF R²: Friend trust (score=252) — Linear R²=0.109, RF R²=0.462, Δ=+0.354. Nonlinear patterns present.
- **[ml_discovery:3.4]** Interaction effects → Crime rate (score=252) — Linear R²=-0.864, With interactions R²=-0.689, Δ=+0.175. N_interactions=6.
- **[ml_discovery:3.10]** Dose-response quartiles: IDDE → Wage (score=252) — Q1=10351.5, Q2=11044.5, Q3=11685.0, Q4=12886.6. Jump Q1→Q2=693.1, Q3→Q4=1201.6. Accelerating.
- **[ml_discovery:3.13]** Per-cluster LOOCV → Wage (score=252) — 
- **[ml_discovery:3.13]** Per-cluster LOOCV → Crime (score=252) — 
- **[ml_discovery:3.16]** PDP monotonicity: IDDE → Wage (score=252) — PDP range: [9509.2, 13325.2]. Monotonic=False. 15 increasing steps, 3 decreasing steps.
- **[ml_discovery:3.16]** PDP monotonicity: IDDE → Crime (score=252) — PDP range: [465.9, 2497.3]. Monotonic=False. 14 increasing steps, 4 decreasing steps.
- **[unorthodox:4.16]** Composite score → Crime (score=252) — Composite r=0.4025 (p=0.0248) vs IDDE r=0.5984 (p=0.0004). Δ=-0.1958.
- **[unorthodox:4.16]** Composite score → Family trust (score=252) — Composite r=0.5608 (p=0.0010) vs IDDE r=0.6530 (p=0.0001). Δ=-0.0921.
- **[unorthodox:4.5]** IDDE → Male victim share (score=240) — r(IDDE, male_share)=-0.2253, p=0.2231.
- **[robustness:2.6]** Leave South out: BB coverage → Friend trust (r=0.78) (score=216) — Full r=0.7786, without South r=0.6565, Δ=-0.1221.
- **[robustness:2.6]** Leave South out: IDDE → Family trust (r=0.65) (score=216) — Full r=0.6530, without South r=0.5650, Δ=-0.0880.
- **[ml_discovery:3.8]** RFE top 3 features → Average wage (score=216) — Selected: empresas_que_utilizan_ban, velocidad_de_descarga_de_, indice_de_desarrollo_digi. R²(3 features)=0.180, R²(all)
- **[ml_discovery:3.8]** RFE top 3 features → Crime rate (score=216) — Selected: cobertura_de_banda_ancha_, penetracion_de_banda_anch, graduados_en_programas_st. R²(3 features)=-0.511, R²(all
- **[ml_discovery:3.8]** RFE top 3 features → Homicide rate (score=216) — Selected: cobertura_de_banda_ancha_, graduados_en_programas_st, velocidad_de_descarga_de_. R²(3 features)=-0.384, R²(all
- **[structural:1.6]** Population-weighted IDDE → municipal crime (score=210) — Weighted r=0.2004 vs unweighted r from 1.1. Unweighted correlation is stronger.
- **[robustness:2.8]** Spearman vs Pearson: IDDE → Safety perception (R²=0.45) (score=210) — Pearson r=0.2493, Spearman ρ=0.3738, Δ=+0.1245. Nonlinearity detected.
- **[robustness:2.9]** Panel year-by-year: IDDE → avg_wage (score=210) — 2022: r=0.6611999869346619; 2023: r=0.6495000123977661; 2024: r=0.6302000284194946; 2025: r=0.6089000105857849. Consiste
- **[robustness:2.9]** Panel year-by-year: IDDE → crime_rate_100k (score=210) — 2022: r=0.5849; 2023: r=0.5874; 2024: r=0.5606; 2025: r=0.5984. Consistent across years.
- **[ml_discovery:3.14]** Stacking → Average wage (score=210) — Stacking R²=0.513, best base R²=0.478, Δ=+0.035. Weights: LR=-0.32, RF=0.81, GB=0.44
- **[ml_discovery:3.14]** Stacking → Crime rate (score=210) — Stacking R²=0.284, best base R²=0.165, Δ=+0.119. Weights: LR=0.41, RF=-0.35, GB=0.66
- **[ml_discovery:3.14]** Stacking → Homicide rate (score=210) — Stacking R²=0.209, best base R²=-0.054, Δ=+0.263. Weights: LR=0.54, RF=-0.94, GB=0.12
- **[robustness:2.15]** R² stability (70% subsamples): IDDE → Family trust (r=0.65) (score=192) — R² median=0.4327, IQR=0.1184. Unstable — sensitive to sample composition.
- **[robustness:2.15]** R² stability (70% subsamples): IDDE → Fraud (r=0.63) (score=192) — R² median=0.4076, IQR=0.1269. Unstable — sensitive to sample composition.
- **[structural:1.11]** High vs low IDDE states: municipal crime distribution (score=180) — Mann-Whitney U=767616, p=0.0000. Cohen d=0.265. High IDDE mean=41.1, Low IDDE mean=11.1.
- **[structural:1.7_interior]** State IDDE → Crime in Interior municipalities (score=175) — Interior: r=0.2126, p=0.0000, N=2244.
- **[unorthodox:4.14]** Entropy-based: IDDE ↔ Crime (score=175) — MI=0.432, NMI=0.216 (normalized to [0,1]). Compare to Pearson r² from linear correlation.
- **[unorthodox:4.14]** Entropy-based: IDDE ↔ Wage (score=175) — MI=0.484, NMI=0.242 (normalized to [0,1]). Compare to Pearson r² from linear correlation.
- **[unorthodox:4.13]** Natural experiment: top vs bottom IDDE changers (score=168) — Top 5 crime Δ: -22.9. Bottom 5 crime Δ: -373.9. Diff: 351.0. Top IDDE changers did NOT reduce crime more.
- **[robustness:2.1]** LOO influence: BB coverage → Friend trust (r=0.78) (score=160) — Full r=0.7786. Max Δr=0.0283 (removing San Luis Potosí). Robust.
- **[robustness:2.1]** LOO influence: IDDE → Family trust (r=0.65) (score=160) — Full r=0.6530. Max Δr=0.0620 (removing Oaxaca). Robust.
- **[robustness:2.1]** LOO influence: IDDE → Fraud (r=0.63) (score=160) — Full r=0.6286. Max Δr=0.0757 (removing Ciudad de México). Robust.
- **[robustness:2.1]** LOO influence: E-banking → Wage (R²=0.43) (score=160) — Full r=0.6525. Max Δr=0.0452 (removing Querétaro). Robust.
- **[robustness:2.1]** LOO influence: IDDE → Safety perception (R²=0.45) (score=160) — Full r=0.2493. Max Δr=0.0857 (removing Ciudad de México). Robust.
- **[robustness:2.1]** LOO influence: BB coverage → Wage (r=0.67) (score=160) — Full r=0.4750. Max Δr=0.0726 (removing San Luis Potosí). Robust.
- **[robustness:2.5]** Bootstrap 80% stability: BB coverage → Friend trust (r=0.78) (score=160) — Bootstrap r: median=0.7804, 95% CI=[0.6976, 0.8372]. Range width=0.1396.
- **[robustness:2.5]** Bootstrap 80% stability: IDDE → Family trust (r=0.65) (score=160) — Bootstrap r: median=0.6536, 95% CI=[0.5398, 0.7542]. Range width=0.2144.
- **[robustness:2.5]** Bootstrap 80% stability: IDDE → Fraud (r=0.63) (score=160) — Bootstrap r: median=0.6331, 95% CI=[0.4793, 0.7361]. Range width=0.2568.
- **[structural:1.3r]** State IDDE → Crime in Rural municipalities (score=150) — Rural: r=0.1534, p=0.0000, N=882.
- **[structural:1.3u]** State IDDE → Crime in Urban municipalities (score=150) — Urban: r=0.2662, p=0.0000, N=1604.
- **[structural:1.8_lg]** State IDDE → Crime in Large (>Q75) municipalities (score=150) — Large (>Q75): r=0.3364, p=0.0000, N=699.
- **[structural:1.8_sm]** State IDDE → Crime in Small (<Q75) municipalities (score=150) — Small (<Q75): r=0.2087, p=0.0000, N=1787.
- **[ml_discovery:3.5]** Elastic Net features → Average wage (score=150) — Top 3 (last to be zeroed): cobertura_de_banda_ancha_(α=2099.2559), penetracion_de_banda_anch(α=2099.2559), cobertura_de_
- **[ml_discovery:3.5]** Elastic Net features → Crime rate (score=150) — Top 3 (last to be zeroed): cobertura_de_banda_ancha_(α=1034.8026), penetracion_de_banda_anch(α=1034.8026), cobertura_de_
- **[ml_discovery:3.5]** Elastic Net features → Homicide rate (score=150) — Top 3 (last to be zeroed): cobertura_de_banda_ancha_(α=14.9801), penetracion_de_banda_anch(α=14.9801), cobertura_de_rede
- **[ml_discovery:3.12]** Ridge+Poly → Average wage (score=150) — Linear R²=-0.068, Ridge+Poly R²=-0.179, Δ=-0.110.
- **[ml_discovery:3.12]** Ridge+Poly → Crime rate (score=150) — Linear R²=-0.492, Ridge+Poly R²=-0.243, Δ=+0.249.
- **[ml_discovery:3.12]** Ridge+Poly → Homicide rate (score=150) — Linear R²=-0.358, Ridge+Poly R²=-0.127, Δ=+0.231.
- **[unorthodox:4.10]** Rank-rank: IDDE → Wage (score=150) — Rank-rank r=0.5879 (p=0.0005), Raw r=0.6089 (p=0.0003). Δ=-0.0210.
- **[unorthodox:4.10]** Rank-rank: IDDE → Crime (score=150) — Rank-rank r=0.6355 (p=0.0001), Raw r=0.5984 (p=0.0004). Δ=+0.0371.
- **[unorthodox:4.3]** Quantile regression: IDDE → Wage (score=144) — Q25: β=15.7; Q50: β=26.4; Q75: β=38.5. Spread=22.8. Effect is similar across quantiles.
- **[structural:1.13]** Spearman rank correlation: IDDE → municipal crime (score=140) — ρ=0.4390, p=0.0000, N=2486. Compare to Pearson r from 1.1 to assess outlier influence.
- **[robustness:2.3]** Winsorized (5%): BB coverage → Friend trust (r=0.78) (score=140) — Winsorized r=0.7945 vs original r=0.7786. Δ=0.0159. Robust to outliers.
- **[robustness:2.3]** Winsorized (5%): IDDE → Family trust (r=0.65) (score=140) — Winsorized r=0.6719 vs original r=0.6530. Δ=0.0190. Robust to outliers.
- **[robustness:2.3]** Winsorized (5%): IDDE → Fraud (r=0.63) (score=140) — Winsorized r=0.6028 vs original r=0.6286. Δ=0.0258. Robust to outliers.
- **[robustness:2.3]** Winsorized (5%): E-banking → Wage (R²=0.43) (score=140) — Winsorized r=0.6509 vs original r=0.6525. Δ=0.0016. Robust to outliers.
- **[robustness:2.3]** Winsorized (5%): IDDE → Safety perception (R²=0.45) (score=140) — Winsorized r=0.3019 vs original r=0.2493. Δ=0.0526. Sensitive to outliers.
- **[robustness:2.3]** Winsorized (5%): BB coverage → Wage (r=0.67) (score=140) — Winsorized r=0.4637 vs original r=0.4750. Δ=0.0113. Robust to outliers.
- **[unorthodox:4.8]** IDDE panel stationarity check (score=140) — Trend slope=0.897/year, R²=0.442, p=0.3348. Var(diff)/Var(level)=1.691. No clear trend. With only 4 years, formal ADF is
- **[ml_discovery:3.1]** RF permutation importance → Average wage (score=126) — R²_train=0.883, R²_LOOCV=nan. Top 3: empresas_que_utilizan_banca_el=1.1522±0.2759, penetracion_de_banda_ancha_fij=0.0756
- **[ml_discovery:3.1]** RF permutation importance → Crime rate (score=126) — R²_train=0.827, R²_LOOCV=nan. Top 3: penetracion_de_banda_ancha_fij=0.3736±0.1220, graduados_en_programas_stem_xm=0.3429
- **[ml_discovery:3.1]** RF permutation importance → Homicide rate (score=126) — R²_train=0.728, R²_LOOCV=nan. Top 3: graduados_en_programas_stem_xm=0.3615±0.0941, velocidad_de_descarga_de_banda=0.2015
- **[ml_discovery:3.1]** RF permutation importance → Fraud rate (score=126) — R²_train=0.800, R²_LOOCV=nan. Top 3: indice_de_desarrollo_digital_e=0.3438±0.0866, graduados_en_programas_stem_xm=0.1685
- **[ml_discovery:3.1]** RF permutation importance → Family trust (score=126) — R²_train=0.820, R²_LOOCV=nan. Top 3: cobertura_de_banda_ancha_fija_=0.4510±0.1045, penetracion_de_banda_ancha_fij=0.0960
- **[ml_discovery:3.1]** RF permutation importance → Friend trust (score=126) — R²_train=0.880, R²_LOOCV=nan. Top 3: cobertura_de_banda_ancha_fija_=0.4886±0.1027, indice_de_desarrollo_digital_e=0.2149
- **[robustness:2.11]** subpilar_de_economia_digital... → Wage (score=125) — r=0.6955, p=0.0000.
- **[robustness:2.11]** subpilar_de_economia_digital... → Crime (score=125) — r=0.5077, p=0.0035.
- **[robustness:2.11]** subpilar_de_gobierno_digital_y... → Crime (score=125) — r=0.4864, p=0.0055.
