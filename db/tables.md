# Esquema de tablas

Guía de referencia para consultas SQL. Los nombres de columna son exactamente
los que aparecen en la base — úsalos con comillas dobles si contienen mayúsculas
o caracteres especiales.

---

## Por qué hay 33 tablas si solo son 11 datasets

La base usa un **star schema**: todas las columnas de texto categórico se
extrajeron a tablas de dimensión separadas y se reemplazaron por claves enteras
(`int32`). Esto elimina duplicación, reduce peso y permite JOINs eficientes.

No es 1 dim por dataset — algunas dims son **compartidas** por varios datasets:

| Tabla de dimensión | Usada por |
|-------------------|-----------|
| `dim_estado` | **todos** los datasets |
| `dim_subtipo_delito` | `incidencia_municipal`, `incidencia_estatal`, `victimas_fuero_comun` |
| `dim_modalidad` | `incidencia_municipal`, `incidencia_estatal`, `victimas_fuero_comun` |
| `dim_bien_juridico_afectado` | `incidencia_municipal`, `incidencia_estatal`, `victimas_fuero_comun` |
| `dim_municipio` | `incidencia_municipal` |
| `dim_sexo` | `victimas_fuero_comun` |
| `dim_rango_edad` | `victimas_fuero_comun` |
| `dim_nivel_confianza` | `datamexico_envipe` (7 cols `confidence_*`) |
| `dim_nivel_confianza_personal` | `datamexico_envipe` (4 cols `trust_*`) |
| `dim_percepcion_seguridad` | `datamexico_envipe` |
| `dim_estrato_sociodemografico` | `datamexico_envipe` |
| `dim_gastos_proteccion` | `datamexico_envipe` |
| `dim_company_size` | `datamexico_denue` |
| `dim_month` | `datamexico_denue` |
| `dim_quarter` | `datamexico_enoe` |
| `dim_economically_active_population` | `datamexico_enoe` |
| `dim_instruction_level` | `datamexico_enoe` |
| `dim_job_situation` | `datamexico_enoe` |
| `dim_schooling_years` | `datamexico_enoe` |
| `dim_occupation` | `datamexico_enoe` |
| `dim_grupo_digitalizacion` | `idde_2022`, `idde_2023`, `idde_2024`, `idde_2025` |
| `dim_rango_porcentaje` | `idde_2022` (columnas `*_rango_id`) |

Total: **11 tablas de hechos + 22 tablas de dimensión = 33 tablas**.

### Cómo reconstruir la tabla original con texto

Para recuperar cualquier tabla en su forma original (con texto en vez de IDs),
basta hacer JOIN con las dims correspondientes.

**`incidencia_estatal`**

```sql
SELECT
    e.estado,
    s.subtipo       AS subtipo_delito,
    m.modalidad,
    b.bien_juridico_afectado,
    f.anio,
    f.mes_num,
    f.incidencia_delictiva
FROM incidencia_estatal f
JOIN dim_estado          e ON f.clave_ent    = e.clave_ent
JOIN dim_subtipo_delito  s ON f.subtipo_id   = s.subtipo_id
JOIN dim_modalidad       m ON f.modalidad_id = m.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id;
```

**`incidencia_municipal`**

```sql
SELECT
    e.estado,
    mu.municipio,
    s.subtipo       AS subtipo_delito,
    m.modalidad,
    b.bien_juridico_afectado,
    f.anio,
    f.enero, f.febrero, f.marzo, f.abril, f.mayo, f.junio,
    f.julio, f.agosto, f.septiembre, f.octubre, f.noviembre, f.diciembre
FROM incidencia_municipal f
JOIN dim_estado          e  ON f.clave_ent    = e.clave_ent
JOIN dim_municipio       mu ON f.clave_ent    = mu.clave_ent
                           AND f.cve_municipio = mu.cve_municipio
JOIN dim_subtipo_delito  s  ON f.subtipo_id   = s.subtipo_id
JOIN dim_modalidad       m  ON f.modalidad_id = m.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id;
```

**`victimas_fuero_comun`**

```sql
SELECT
    e.estado,
    s.subtipo       AS subtipo_delito,
    m.modalidad,
    b.bien_juridico_afectado,
    x.sexo,
    r.rango_edad,
    f.anio,
    f.enero, f.febrero, f.marzo, f.abril, f.mayo, f.junio,
    f.julio, f.agosto, f.septiembre, f.octubre, f.noviembre, f.diciembre
FROM victimas_fuero_comun f
JOIN dim_estado          e ON f.clave_ent      = e.clave_ent
JOIN dim_subtipo_delito  s ON f.subtipo_id     = s.subtipo_id
JOIN dim_modalidad       m ON f.modalidad_id   = m.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id
JOIN dim_sexo            x ON f.sexo_id        = x.sexo_id
JOIN dim_rango_edad      r ON f.rango_edad_id  = r.rango_edad_id;
```

**`datamexico_denue`** (ejemplo: empresas por tamano y mes)

```sql
SELECT
    e.estado,
    m.month,
    s.company_size,
    f.companies
FROM datamexico_denue f
JOIN dim_estado       e ON f.state_id = e.clave_ent
JOIN dim_month        m ON f.month_id = m.month_id
JOIN dim_company_size s ON f.company_size_id = s.company_size_id;
```

**`datamexico_enoe`** (ejemplo: fuerza laboral por trimestre y nivel de instruccion)

```sql
SELECT
    e.estado,
    q.quarter,
    il.instruction_level,
    f.workforce
FROM datamexico_enoe f
JOIN dim_estado            e  ON f.state_id = e.clave_ent
JOIN dim_quarter           q  ON f.quarter_id = q.quarter_id
JOIN dim_instruction_level il ON f.instruction_level_id = il.instruction_level_id;
```

**`datamexico_envipe`** (ejemplo: confianza en policía estatal + percepción de seguridad)

```sql
SELECT
    e.estado,
    nc.nivel_confianza   AS confianza_policia_estatal,
    ps.percepcion        AS percepcion_seguridad,
    es.estrato           AS estrato_sociodemografico,
    f.age,
    f.homes,
    f.people
FROM datamexico_envipe f
JOIN dim_estado                  e  ON f.state_id                       = e.clave_ent
JOIN dim_nivel_confianza         nc ON f.confidence_in_state_police_id  = nc.nivel_confianza_id
JOIN dim_percepcion_seguridad    ps ON f.security_perception_in_their_state_id = ps.percepcion_id
JOIN dim_estrato_sociodemografico es ON f.sociodemographic_stratum_id   = es.estrato_id;
```

---

## Índice

**Tablas de dimensión** (lookups para joins):
- `dim_estado`
- `dim_municipio`
- `dim_subtipo_delito`
- `dim_modalidad`
- `dim_bien_juridico_afectado`
- `dim_sexo`
- `dim_rango_edad`
- `dim_nivel_confianza`
- `dim_nivel_confianza_personal`
- `dim_percepcion_seguridad`
- `dim_estrato_sociodemografico`
- `dim_gastos_proteccion`
- `dim_company_size`
- `dim_month`
- `dim_quarter`
- `dim_economically_active_population`
- `dim_instruction_level`
- `dim_job_situation`
- `dim_schooling_years`
- `dim_occupation`
- `dim_grupo_digitalizacion`
- `dim_rango_porcentaje`

**Tablas de hechos**:
- `idde_2022`
- `idde_2023`
- `idde_2024`
- `idde_2025`
- `incidencia_municipal`
- `incidencia_estatal`
- `victimas_fuero_comun`
- `datamexico_crimes`
- `datamexico_envipe`
- `datamexico_denue`
- `datamexico_enoe`


---
# Tablas de dimensión


## dim_estado

32 estados mexicanos. PK: clave_ent (INEGI). Referenciada por todas las tablas de hechos. state_id=0 indica desconocido (p.ej. 'No Informado').

**Filas:** 32


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_ent` | INTEGER | 1 |
| `estado` | TEXT | Aguascalientes |
| `abrev` | TEXT | AGS |

## dim_municipio

2486 municipios únicos (clave_ent, cve_municipio). Mismo nombre puede aparecer en varios estados. Referenciada por incidencia_municipal.

**Filas:** 2486


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_ent` | INTEGER | 1 |
| `cve_municipio` | INTEGER | 1001 |
| `municipio` | TEXT | Aguascalientes |

## dim_subtipo_delito

55 subtipos de delito. Compartida por incidencia_municipal, incidencia_estatal, victimas_fuero_comun.

**Filas:** 55


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `subtipo_id` | INTEGER | 1 |
| `subtipo` | TEXT | Aborto |

## dim_modalidad

59 modalidades de delito. Compartida por incidencia_municipal, incidencia_estatal, victimas_fuero_comun.

**Filas:** 59


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `modalidad_id` | INTEGER | 1 |
| `modalidad` | TEXT | Aborto |

## dim_bien_juridico_afectado

Categorias de bien juridico afectado. Compartida por incidencia_municipal, incidencia_estatal, victimas_fuero_comun.

**Filas:** 7


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `bien_juridico_afectado_id` | INTEGER | 1 |
| `bien_juridico_afectado` | TEXT | El patrimonio |

## dim_sexo

3 valores (Hombre=1, Mujer=2, No identificado=3). IDs alineados con envipe sex_id.

**Filas:** 3


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `sexo_id` | INTEGER | 1 |
| `sexo` | TEXT | Hombre |

## dim_rango_edad

4 rangos de edad. Referenciada por victimas_fuero_comun.

**Filas:** 4


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `rango_edad_id` | INTEGER | 1 |
| `rango_edad` | TEXT | Adultos (18 y más) |

## dim_nivel_confianza

5 niveles (1=Mucha Confianza … 4=Mucha Desconfianza, 9=No sabe). Compartida por 7 columnas confidence_*_id de datamexico_envipe.

**Filas:** 5


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `nivel_confianza_id` | INTEGER | 1 |
| `nivel_confianza` | TEXT | Mucha Confianza |

## dim_nivel_confianza_personal

6 niveles (1=Mucha … 5=No Aplica, 9=No sabe). Compartida por 4 columnas trust_*_id de datamexico_envipe.

**Filas:** 6


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `nivel_confianza_personal_id` | INTEGER | 1 |
| `nivel_confianza_personal` | TEXT | Mucha |

## dim_percepcion_seguridad

3 valores: Seguro=1, Inseguro=2, No sabe=9. Referenciada por datamexico_envipe.

**Filas:** 3


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `percepcion_id` | INTEGER | 1 |
| `percepcion` | TEXT | Seguro |

## dim_estrato_sociodemografico

4 estratos: Bajo=1, Medio bajo=2, Medio alto=3, Alto=4. Referenciada por datamexico_envipe.

**Filas:** 4


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `estrato_id` | INTEGER | 1 |
| `estrato` | TEXT | Bajo |

## dim_gastos_proteccion

41 rangos de gasto en protección contra el crimen. Referenciada por datamexico_envipe.

**Filas:** 41


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `gastos_id` | INTEGER | 1 |
| `gastos_rango` | TEXT | < $1k |

## dim_company_size

Company size categories (DENUE). PK: company_size_id.

**Filas:** 7


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `company_size_id` | INTEGER | 1 |
| `company_size` | TEXT | 0 - 5 |

## dim_month

Month lookup from DENUE. PK: month_id.

**Filas:** 19


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `month_id` | INTEGER | 20150225 |
| `month` | INTEGER | 2 |

## dim_quarter

Quarter lookup from ENOE. PK: quarter_id.

**Filas:** 60


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `quarter_id` | INTEGER | 20101 |
| `quarter` | TEXT | 2010-Q1 |

## dim_economically_active_population

Economically active population categories (ENOE). PK: economically_active_population_id.

**Filas:** 1


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `economically_active_population_id` | INTEGER | 1 |
| `economically_active_population` | TEXT | Población Económicamente Activa |

## dim_instruction_level

Instruction level categories (ENOE). PK: instruction_level_id.

**Filas:** 11


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `instruction_level_id` | INTEGER | 0 |
| `instruction_level` | TEXT | Ninguno |

## dim_job_situation

Job situation categories (ENOE). PK: job_situation_id.

**Filas:** 1


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `job_situation_id` | INTEGER | 1 |
| `job_situation` | TEXT | Posee un Trabajo o Negocio |

## dim_schooling_years

Schooling years categories (ENOE). PK: schooling_years_id.

**Filas:** 26


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `schooling_years_id` | INTEGER | 1 |
| `schooling_years` | INTEGER | 0 |

## dim_occupation

Occupation categories (ENOE). PK: occupation_id.

**Filas:** 462


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `occupation_id` | INTEGER | 1111 |
| `occupation` | TEXT | Altas Autoridades Gubernamentales y Jurisdiccionales |

## dim_grupo_digitalizacion

4 grupos de madurez digital (Básico=1, Emprendedor=2, Avanzado=3, Líder=4). Referenciada por todas las tablas idde_*.

**Filas:** 4


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `grupo_id` | INTEGER | 1 |
| `grupo` | TEXT | Básico |

## dim_rango_porcentaje

10 rangos de porcentaje en buckets de 10 pts ('Entre 0 y 10'…'Entre 90 y 100'). Usada por columnas *_rango_id de idde_2022.

**Filas:** 10


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `rango_id` | INTEGER | 1 |
| `rango` | TEXT | Entre 0 y 10 |

---
# Tablas de hechos


## idde_2022

Índice de Desarrollo Digital Estatal, edición 2022. Una fila por estado. FK: clave_inegi_de_estado → dim_estado.clave_ent. Sufijos de columnas: `_por`=%, `_x100hab`=por 100 hab, `_xmhab`=por millón de hab, `_percap`=per cápita, `_xmil`=por mil, `_xmpib`=por millón de PIB, `_bps`=bits/s, `_mbps`=Mbps, `_dif_por`=diferencia en %, `_log`=log-escala.

**Fuente:** Centro México Digital — IDDE 2022  
**Filas aprox:** 32  
**Archivo CSV:** `data/clean/idde/idde_2022.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_inegi_de_estado` | INTEGER | 1 |
| `indice_de_desarrollo_digital_estatal_2022` | REAL | 167.98875 |
| `pilar_infraestructura` | REAL | 65.31 |
| `subpilar_de_cobertura_acceso_y_calidad` | REAL | 61.86 |
| `cobertura_de_redes_moviles_por` | REAL | 98.51 |
| `cobertura_de_banda_ancha_fija_por` | REAL | 89.51 |
| `conexiones_de_banda_ancha_fija_con_fibra_optica_por` | REAL | 37.1 |
| `penetracion_de_banda_ancha_fija_x100hab` | INTEGER | 68 |
| `penetracion_de_banda_ancha_movil_x100hab` | INTEGER | 72 |
| `hogares_con_computadoras_por` | REAL | 49.76 |
| `usuarios_de_telefonos_inteligentes_por` | REAL | 84.7 |
| `velocidad_de_descarga_de_banda_ancha_fija_bps` | REAL | 34453.867 |
| `velocidad_de_descarga_de_banda_ancha_movil_bps` | REAL | 31731.508 |
| `certificacion_de_simplificacion_de_despliegue_de_infraestru_por` | REAL | 0.0 |
| `despliegue_de_5g_xmhab` | REAL | 0.0 |
| `subpilar_de_asequibilidad` | REAL | 76.36 |
| `asequibilidad_de_telefono_inteligente_por` | REAL | 22.3 |
| `asequibilidad_de_internet_por` | REAL | 3.89 |
| `asequibilidad_de_internet_primer_quintil_por` | REAL | 6.58 |
| `asequibilidad_de_servicios_moviles_primer_quintil_por` | REAL | 3.91 |
| `desigualdad_en_la_proporcion_del_gasto_de_internet_entre_quinti` | REAL | 3.5 |
| `nivel_de_competencia_de_banda_ancha_fija` | REAL | 3708.17 |
| `subpilar_de_infraestructura_de_datos` | REAL | 47.16 |
| `centros_de_datos_edge_xmuint` | REAL | 0.0 |
| `centros_de_datos_hiper_scale_y_colocation_hosting_xmpib` | REAL | 4.88 |
| `centros_de_datos_certificados_xmpib` | REAL | 4.88 |
| `pilar_digitalizacion_de_las_personas_y_la_sociedad` | REAL | 51.51 |
| `subpilar_de_usuarios_y_usos_de_las_tic` | REAL | 53.67 |
| `usuarios_de_internet_por` | REAL | 80.35 |
| `usuarios_de_internet_en_zonas_rurales_por` | REAL | 71.8 |
| `usuarios_adultos_mayores_de_internet_por` | REAL | 33.71 |
| `usuarios_de_computadora_laptop_o_tableta_por` | REAL | 39.55 |
| `uso_de_internet_para_compras_por` | REAL | 28.35 |
| `uso_de_banca_electronica_por` | REAL | 20.04 |
| `uso_de_internet_para_educacion_por` | REAL | 34.42 |
| `uso_de_internet_para_interactuar_con_el_gobierno_por` | REAL | 43.54 |
| `ciberacoso_por` | REAL | 22.24 |
| `subpilar_de_capacidades_y_habilidades_digitales` | REAL | 55.34 |
| `habilidades_de_correo_electronico_por` | REAL | 36.93 |
| `habilidades_de_hoja_de_calculo_por` | REAL | 26.7 |
| `habilidades_de_programacion_por` | REAL | 5.32 |
| `brecha_de_genero_en_uso_de_hoja_de_calculo` | REAL | 1.95 |
| `subpilar_de_digitalizacion_de_los_servicios_prioritarios` | REAL | 39.43 |
| `penetracion_de_tarjeta_de_debito_x100hab` | REAL | 123.17 |
| `digitalizacion_del_registro_publico` | REAL | 60.14 |
| `participacion_ciudadana_por` | REAL | 100.0 |
| `sistema_de_gestion_ambiental_y_manejo_de_residuos_electronicos` | INTEGER | 1 |
| `subpilar_de_gobierno_digital_y_entorno_regulatorio` | REAL | 55.25 |
| `incorporacion_de_estrategias_digitales_en_planes_estatales` | REAL | 81.25 |
| `accesibilidad_en_portales_estatales_por` | REAL | 52.3 |
| `comisiones_de_ti_y_proteccion_de_datos_personales` | INTEGER | 0 |
| `policia_cibernetica_xmhab` | REAL | 9.12 |
| `gobierno_abierto` | REAL | 0.56 |
| `sistemas_de_estadistica_o_geografia` | REAL | 67.86 |
| `gestion_documental_estatal_y_municipal` | REAL | 54.2 |
| `pilar_innovacion_y_adopcion_tecnologica_de_las_empresas` | REAL | 51.16 |
| `subpilar_de_adopcion_de_nuevas_tecnologias` | REAL | 38.71 |
| `subpilar_de_ciberseguridad` | REAL | 69.64 |
| `subpilar_de_comercio_electronico` | REAL | 53.59 |
| `compras_por_internet_por` | REAL | 7.89 |
| `ventas_por_internet_por` | REAL | 5.43 |
| `volumen_de_ventas_por_internet_por` | REAL | 8.12 |
| `subpilar_de_economia_digital` | REAL | 52.49 |
| `microempresas_con_internet_por` | REAL | 26.8 |
| `penetracion_de_banda_ancha_fija_no_residencial_x100hab` | INTEGER | 41 |
| `p3ecdi_gentopdo_22` | REAL | 13.19 |
| `empresas_que_utilizan_banca_electronica_por` | REAL | 19.21 |
| `penetracion_de_terminales_punto_de_venta_x100adu` | REAL | 1.29 |
| `empleados_con_profesiones_stem_x100hab` | REAL | 5.57 |
| `empleados_de_nuevas_empresas_tic` | REAL | 79.4 |
| `gasto_del_gobierno_servicios_de_telecomunicaciones_y_sof_percap` | REAL | 18.49 |
| `subpilar_de_innovacion` | REAL | 48.72 |
| `solicitudes_de_patentes_xmhab` | REAL | 7.01 |
| `graduados_en_programas_stem_xmhab` | REAL | 2845.1 |
| `mujeres_graduadas_en_programas_stem_por` | REAL | 28.33 |
| `presupuesto_para_instituciones_de_ciencia_tecnologia_e_i_percap` | REAL | 26.09 |
| `grupo_de_digitalizacion_id` | INTEGER | 3 |
| `personal_con_herramientas_tecnologicas_basicas_rango_id` | INTEGER | 7 |
| `empresas_con_herramientas_tecnologicas_basicas_rango_id` | INTEGER | 7 |
| `empresas_con_herramientas_tecnologicas_intermedias_rango_id` | INTEGER | 6 |
| `empresas_con_herramientas_tecnologicas_avanzadas_rango_id` | INTEGER | 3 |
| `empresas_con_herramientas_tecnologicas_innovadoras_rango_id` | INTEGER | 1 |
| `usos_de_internet_en_las_empresas_rango_id` | INTEGER | 8 |
| `especialistas_en_ti_y_ciberseguridad_en_las_empresas_rango_id` | INTEGER | 6 |
| `acciones_de_ciberseguridad_en_las_empresas_rango_id` | INTEGER | 4 |

**Ejemplo SQL:**

```sql
SELECT e.estado, i.indice_de_desarrollo_digital_estatal_2022
FROM idde_2022 i JOIN dim_estado e ON i.clave_inegi_de_estado = e.clave_ent
ORDER BY 2 DESC;
```

## idde_2023

Índice de Desarrollo Digital Estatal, edición 2023. Una fila por estado. FK: clave_inegi_de_estado → dim_estado.clave_ent. Ver idde_2022 para leyenda de sufijos de unidades.

**Fuente:** Centro México Digital — IDDE 2023  
**Filas aprox:** 32  
**Archivo CSV:** `data/clean/idde/idde_2023.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_inegi_de_estado` | INTEGER | 1 |
| `indice_de_desarrollo_digital_estatal_2023` | REAL | 183.11552 |
| `pilar_infraestructura` | REAL | 68.73 |
| `subpilar_de_cobertura_acceso_y_calidad` | REAL | 66.42 |
| `cobertura_de_redes_moviles_por` | REAL | 99.5 |
| `cobertura_de_banda_ancha_fija_por` | REAL | 92.91 |
| `conexiones_de_banda_ancha_fija_con_fibra_optica_por` | REAL | 43.1 |
| `penetracion_de_banda_ancha_fija_x100hab` | INTEGER | 72 |
| `penetracion_de_banda_ancha_movil_x100hab` | INTEGER | 85 |
| `hogares_con_computadoras_por` | REAL | 52.0 |
| `usuarios_de_telefonos_inteligentes_por` | REAL | 87.5 |
| `velocidad_de_descarga_de_banda_ancha_fija_bps` | REAL | 50767.074 |
| `velocidad_de_descarga_de_banda_ancha_movil_bps` | REAL | 41715.812 |
| `certificacion_de_simplificacion_de_despliegue_de_infraestru_por` | REAL | 0.0 |
| `despliegue_de_5g_xmhab` | REAL | 18.9 |
| `subpilar_de_asequibilidad` | REAL | 77.69 |
| `asequibilidad_de_telefono_inteligente_por` | REAL | 19.98 |
| `asequibilidad_de_internet_por` | REAL | 3.77 |
| `asequibilidad_de_internet_primer_quintil_por` | REAL | 5.97 |
| `asequibilidad_de_servicios_moviles_primer_quintil_por` | REAL | 3.42 |
| `nivel_de_competencia_de_banda_ancha_fija` | REAL | 3574.45 |
| `subpilar_de_infraestructura_de_datos` | REAL | 56.27 |
| `centros_de_datos_edge_xmuint` | REAL | 0.0 |
| `centros_de_datos_hiper_scale_y_colocation_hosting_xmpib` | REAL | 4.84 |
| `centros_de_datos_certificados_xmpib` | REAL | 4.84 |
| `pilar_digitalizacion_de_las_personas_y_la_sociedad` | REAL | 63.82 |
| `subpilar_de_usuarios_y_usos_de_las_tic` | REAL | 57.25 |
| `usuarios_de_internet_por` | REAL | 86.91 |
| `usuarios_de_internet_en_zonas_rurales_por` | REAL | 82.15 |
| `usuarios_adultos_mayores_de_internet_por` | REAL | 50.46 |
| `usuarios_de_computadora_laptop_o_tableta_por` | REAL | 38.37 |
| `uso_de_internet_para_compras_por` | REAL | 32.14 |
| `uso_de_banca_electronica_por` | REAL | 21.54 |
| `uso_de_internet_para_educacion_por` | REAL | 30.66 |
| `uso_de_internet_para_interactuar_con_el_gobierno_por` | REAL | 37.43 |
| `uso_de_internet_para_entretenimiento_por` | REAL | 34.74 |
| `ciberacoso_por` | REAL | 21.26 |
| `subpilar_de_capacidades_y_habilidades_digitales` | REAL | 48.52 |
| `habilidades_de_correo_electronico_por` | REAL | 35.39 |
| `habilidades_de_hoja_de_calculo_por` | REAL | 25.41 |
| `habilidades_de_programacion_por` | REAL | 8.47 |
| `brecha_de_genero_en_habilidades_digitales_dif_por` | REAL | 8.1 |
| `subpilar_de_digitalizacion_de_los_servicios_prioritarios` | REAL | 67.7 |
| `penetracion_de_tarjeta_de_debito_x100hab` | REAL | 131.35 |
| `digitalizacion_del_registro_publico` | REAL | 80.32 |
| `participacion_ciudadana_por` | REAL | 100.0 |
| `sistema_de_gestion_ambiental_y_manejo_de_residuos_electronicos` | INTEGER | 1 |
| `escuelas_con_computadoras_por` | REAL | 79.4 |
| `escuelas_con_internet_por` | REAL | 68.8 |
| `digitalizacion_en_centros_de_salud_por` | REAL | 51.52 |
| `subpilar_de_gobierno_digital_y_entorno_regulatorio` | REAL | 85.74 |
| `incorporacion_de_estrategias_digitales_en_planes_estatales` | REAL | 81.25 |
| `evaluacion_de_politica_digital_por` | INTEGER | 33 |
| `accesibilidad_en_portales_estatales_por` | REAL | 69.0 |
| `comisiones_de_ti_y_proteccion_de_datos_personales` | INTEGER | 0 |
| `policia_cibernetica_xmhab` | REAL | 25.98 |
| `gobierno_abierto` | REAL | 0.56 |
| `sistemas_de_estadistica_o_geografia` | REAL | 36.46 |
| `gestion_documental_estatal_y_municipal` | REAL | 54.2 |
| `pilar_innovacion_y_adopcion_tecnologica_de_las_empresas` | REAL | 50.57 |
| `subpilar_de_adopcion_de_nuevas_tecnologias` | REAL | 37.82 |
| `personal_con_herramientas_tecnologicas_basicas_por` | REAL | 68.334 |
| `empresas_con_herramientas_tecnologicas_basicas_por` | INTEGER | 65 |
| `empresas_con_herramientas_tecnologicas_intermedias_por` | INTEGER | 55 |
| `empresas_con_herramientas_tecnologicas_avanzadas_por` | INTEGER | 25 |
| `empresas_con_herramientas_tecnologicas_innovadoras_por` | INTEGER | 5 |
| `usos_de_internet_en_las_empresas_por` | INTEGER | 75 |
| `subpilar_de_ciberseguridad` | REAL | 21.71 |
| `especialistas_en_ti_y_ciberseguridad_en_las_empresas_por` | INTEGER | 45 |
| `acciones_de_ciberseguridad_en_las_empresas_por` | INTEGER | 25 |
| `subpilar_de_comercio_electronico` | REAL | 58.78 |
| `compras_por_internet_por` | REAL | 7.89 |
| `ventas_por_internet_por` | REAL | 5.43 |
| `volumen_de_ventas_por_internet_por` | REAL | 8.12 |
| `subpilar_de_economia_digital` | REAL | 58.37 |
| `microempresas_con_internet_por` | REAL | 26.8 |
| `penetracion_de_banda_ancha_fija_no_residencial_x100hab` | INTEGER | 45 |
| `p3ecdi_gentopdo_23` | REAL | 15.49 |
| `empresas_que_utilizan_banca_electronica_por` | REAL | 19.21 |
| `penetracion_de_terminales_punto_de_venta_x100adu` | REAL | 4.9 |
| `empleados_con_profesiones_stem_x100hab` | REAL | 1.69 |
| `gasto_del_gobierno_servicios_de_telecomunicaciones_y_sof_percap` | REAL | 20.88 |
| `subpilar_de_innovacion` | REAL | 52.55 |
| `solicitudes_de_patentes_xmhab` | REAL | 4.21 |
| `graduados_en_programas_stem_xmhab` | REAL | 2625.5483 |
| `mujeres_graduadas_en_programas_stem_por` | REAL | 30.72 |
| `presupuesto_para_instituciones_de_ciencia_tecnologia_e_i_percap` | REAL | 28.2 |
| `grupo_de_digitalizacion_2023_id` | INTEGER | 3 |
| `grupo_de_digitalizacion_2022_id` | INTEGER | 3 |

**Ejemplo SQL:**

```sql
SELECT e.estado, i.indice_de_desarrollo_digital_estatal_2023
FROM idde_2023 i JOIN dim_estado e ON i.clave_inegi_de_estado = e.clave_ent
ORDER BY 2 DESC;
```

## idde_2024

Índice de Desarrollo Digital Estatal, edición 2024. Una fila por estado. FK: clave_inegi_de_estado → dim_estado.clave_ent. Ver idde_2022 para leyenda de sufijos de unidades.

**Fuente:** Centro México Digital — IDDE 2024  
**Filas aprox:** 32  
**Archivo CSV:** `data/clean/idde/idde_2024.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_inegi_de_estado` | INTEGER | 1 |
| `cobertura_de_redes_moviles_por` | REAL | 99.57 |
| `cobertura_de_banda_ancha_fija_por` | REAL | 92.31 |
| `conexiones_de_banda_ancha_fija_con_fibra_optica_por` | REAL | 47.17 |
| `penetracion_de_banda_ancha_fija_x100hab` | INTEGER | 73 |
| `penetracion_de_banda_ancha_movil_x100hab` | INTEGER | 88 |
| `hogares_con_computadoras_por` | REAL | 52.82 |
| `usuarios_de_telefonos_inteligentes_por` | REAL | 86.42 |
| `velocidad_de_descarga_de_banda_ancha_fija_bps` | REAL | 74.21443 |
| `velocidad_de_descarga_de_banda_ancha_movil_bps` | REAL | 39.22293 |
| `certificacion_de_simplificacion_de_despliegue_de_infraestru_por` | REAL | 0.0 |
| `despliegue_de_5g_xmhab` | REAL | 18.9 |
| `asequibilidad_de_telefono_inteligente_por` | REAL | 16.07 |
| `asequibilidad_de_laptop_por` | REAL | 19.54 |
| `asequibilidad_de_internet_por` | REAL | 3.52 |
| `asequibilidad_de_internet_primer_quintil_por` | REAL | 5.85 |
| `asequibilidad_de_servicios_moviles_primer_quintil_por` | REAL | 3.29 |
| `nivel_de_competencia_de_banda_ancha_fija` | REAL | 3024.36 |
| `centros_de_datos_edge_xmuint` | REAL | 3.5 |
| `centros_de_datos_hiper_scale_y_colocation_hosting_xmpib` | REAL | 4.8 |
| `centros_de_datos_certificados_xmpib` | REAL | 4.8 |
| `usuarios_de_internet_por` | REAL | 84.62 |
| `usuarios_de_internet_en_zonas_rurales_por` | REAL | 79.93 |
| `usuarios_adultos_mayores_de_internet_por` | REAL | 54.69 |
| `usuarios_de_computadora_laptop_o_tableta_por` | REAL | 40.1 |
| `uso_de_internet_para_compras_por` | REAL | 33.96 |
| `uso_de_banca_electronica_por` | REAL | 20.91 |
| `uso_de_internet_para_educacion_por` | REAL | 32.28 |
| `uso_de_internet_para_interactuar_con_el_gobierno_por` | REAL | 30.1 |
| `ciberacoso_por` | REAL | 21.26 |
| `uso_de_internet_para_entretenimiento_por` | REAL | 37.48 |
| `habilidades_de_correo_electronico_por` | REAL | 36.69 |
| `habilidades_de_hoja_de_calculo_por` | REAL | 26.66 |
| `habilidades_de_programacion_por` | REAL | 6.12 |
| `brecha_de_genero_en_habilidades_digitales_dif_por` | REAL | 4.04 |
| `penetracion_de_tarjeta_de_debito_x100hab` | REAL | 153.72 |
| `escuelas_con_computadoras_por` | REAL | 68.93 |
| `escuelas_con_internet_por` | REAL | 72.78 |
| `digitalizacion_en_centros_de_salud_por` | REAL | 54.2 |
| `digitalizacion_del_registro_publico` | REAL | 80.32 |
| `participacion_ciudadana_por` | REAL | 63.89 |
| `gestion_ambiental_manejo_de_residuos_electronicos_y_atlas_de_ri` | INTEGER | 2 |
| `incorporacion_de_estrategias_digitales_en_planes_estatales` | REAL | 81.25 |
| `accesibilidad_en_portales_estatales_por` | REAL | 77.5 |
| `comisiones_de_ti_y_proteccion_de_datos_personales` | INTEGER | 0 |
| `policia_cibernetica_xmhab` | REAL | 26.66 |
| `gobierno_abierto` | REAL | 0.48 |
| `funcionarios_publicos_por_area_de_estadistica_o_geografia_xmil` | REAL | 2.4 |
| `gestion_documental_estatal_y_municipal` | REAL | 50.91 |
| `digitalizacion_de_tramites_por` | INTEGER | 100 |
| `personal_con_herramientas_tecnologicas_basicas_por` | INTEGER | 52 |
| `empresas_con_herramientas_tecnologicas_basicas_por` | INTEGER | 44 |
| `empresas_con_herramientas_tecnologicas_intermedias_por` | INTEGER | 38 |
| `empresas_con_herramientas_tecnologicas_avanzadas_por` | INTEGER | 16 |
| `empresas_con_herramientas_tecnologicas_innovadoras_por` | INTEGER | 6 |
| `usos_de_internet_en_las_empresas_por` | INTEGER | 52 |
| `especialistas_en_ti_y_ciberseguridad_en_las_empresas_por` | INTEGER | 36 |
| `acciones_de_ciberseguridad_en_las_empresas_por` | INTEGER | 20 |
| `compras_por_internet_por` | REAL | 7.89 |
| `ventas_por_internet_por` | REAL | 5.43 |
| `volumen_de_ventas_por_internet_por` | REAL | 8.12 |
| `microempresas_con_internet_por` | REAL | 26.8 |
| `penetracion_de_banda_ancha_fija_no_residencial_x100hab` | INTEGER | 51 |
| `empresas_que_utilizan_banca_electronica_por` | REAL | 19.21 |
| `penetracion_de_terminales_punto_de_venta_x100adu` | REAL | 1.68 |
| `empleados_con_profesiones_stem_x100hab` | REAL | 1.52 |
| `gasto_del_gobierno_servicios_de_telecomunicaciones_y_sof_percap` | REAL | 29.89 |
| `solicitudes_de_patentes_xmhab` | REAL | 4.91 |
| `graduados_en_programas_stem_xmhab` | REAL | 2283.24 |
| `mujeres_graduadas_en_programas_stem_por` | REAL | 29.86 |
| `presupuesto_para_instituciones_de_ciencia_tecnologia_e_i_percap` | REAL | 32.34 |
| `indice_de_desarrollo_digital_estatal_2024` | REAL | 186.051 |
| `pilar_infraestructura` | REAL | 68.34 |
| `subpilar_de_cobertura_acceso_y_calidad` | REAL | 63.69 |
| `subpilar_de_asequibilidad` | REAL | 73.87 |
| `subpilar_de_infraestructura_de_datos` | REAL | 70.59 |
| `pilar_digitalizacion_de_las_personas_y_la_sociedad` | REAL | 65.19 |
| `subpilar_de_usuarios_y_usos_de_las_tic` | REAL | 60.96 |
| `subpilar_de_capacidades_y_habilidades_digitales` | REAL | 49.53 |
| `subpilar_de_digitalizacion_de_los_servicios_prioritarios` | REAL | 66.26 |
| `subpilar_de_gobierno_digital_y_entorno_regulatorio` | REAL | 85.63 |
| `pilar_innovacion_y_adopcion_tecnologica_de_las_empresas` | REAL | 52.52 |
| `subpilar_de_adopcion_de_nuevas_tecnologias` | REAL | 49.08 |
| `subpilar_de_ciberseguridad` | REAL | 52.21 |
| `subpilar_de_comercio_electronico` | REAL | 55.02 |
| `subpilar_de_economia_digital` | REAL | 58.36 |
| `subpilar_de_innovacion` | REAL | 48.17 |
| `grupo_de_digitalizacion_2024_id` | INTEGER | 3 |

**Ejemplo SQL:**

```sql
SELECT e.estado, i.indice_de_desarrollo_digital_estatal_2024
FROM idde_2024 i JOIN dim_estado e ON i.clave_inegi_de_estado = e.clave_ent
ORDER BY 2 DESC;
```

## idde_2025

Índice de Desarrollo Digital Estatal, edición 2025. Una fila por estado. FK: clave_inegi_de_estado → dim_estado.clave_ent. Ver idde_2022 para leyenda de sufijos de unidades.

**Fuente:** Centro México Digital — IDDE 2025  
**Filas aprox:** 32  
**Archivo CSV:** `data/clean/idde/idde_2025.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `clave_inegi_de_estado` | INTEGER | 1 |
| `cobertura_de_redes_moviles_por` | REAL | 99.54 |
| `cobertura_de_banda_ancha_fija_por` | REAL | 91.82 |
| `cobertura_5g_por` | REAL | 69.7 |
| `conexiones_de_banda_ancha_fija_con_fibra_optica_por` | REAL | 64.7 |
| `penetracion_de_banda_ancha_fija_x100hab` | INTEGER | 78 |
| `penetracion_de_banda_ancha_movil_x100hab` | INTEGER | 90 |
| `hogares_con_computadoras_por` | REAL | 51.55 |
| `usuarios_de_telefonos_inteligentes_por` | REAL | 88.54 |
| `velocidad_de_descarga_de_banda_ancha_fija_mbps` | REAL | 84.86 |
| `velocidad_de_descarga_de_banda_ancha_movil_mbps` | REAL | 57.92 |
| `asequibilidad_de_telefono_inteligente_por` | REAL | 13.77 |
| `asequibilidad_de_laptop_por` | REAL | 40.04 |
| `asequibilidad_de_internet_por` | REAL | 3.21 |
| `asequibilidad_de_internet_primer_quintil_por` | REAL | 5.31 |
| `asequibilidad_de_servicios_moviles_primer_quintil_por` | REAL | 2.67 |
| `nivel_de_competencia_de_banda_ancha_fija` | REAL | 2871.46 |
| `centros_de_datos_edge_xmuint` | REAL | 4.1 |
| `centros_de_datos_hyperscale_y_colocation_hosting_xmpib` | REAL | 4.8 |
| `centros_de_datos_certificados_xmpib` | REAL | 4.8 |
| `usuarios_de_internet_por` | REAL | 87.74 |
| `usuarios_de_internet_en_zonas_rurales_por` | REAL | 75.43 |
| `usuarios_adultos_mayores_de_internet_por` | REAL | 59.04 |
| `usuarios_de_computadora_laptop_y_tableta_por` | REAL | 39.14 |
| `uso_de_internet_para_compras_por` | REAL | 44.56 |
| `uso_de_banca_electronica_por` | REAL | 40.28 |
| `uso_de_internet_para_educacion_por` | REAL | 33.37 |
| `uso_de_internet_para_interactuar_con_el_gobierno_por` | REAL | 39.35 |
| `uso_de_internet_para_entretenimiento_por` | REAL | 38.57 |
| `ciberacoso_por` | REAL | 17.97 |
| `habilidades_digitales_basicas_por` | REAL | 36.99 |
| `habilidades_digitales_intermedias_por` | REAL | 33.46 |
| `habilidades_digitales_avanzadas_por` | REAL | 21.39 |
| `brecha_de_genero_en_habilidades_digitales_dif_por` | REAL | 3.84 |
| `penetracion_de_tarjeta_de_debito_x100adu` | REAL | 153.45 |
| `digitalizacion_del_registro_publico_por` | REAL | 83.82 |
| `participacion_ciudadana_por` | REAL | 81.82 |
| `residuos_electronicos_y_atlas_de_riesgos` | INTEGER | 2 |
| `escuelas_con_computadoras_por` | REAL | 80.53 |
| `escuelas_con_internet_por` | REAL | 81.7 |
| `digitalizacion_en_centros_de_salud_por` | REAL | 55.63 |
| `demandas_electronicas_por` | REAL | 12.1 |
| `justicia_digital_por` | INTEGER | 2 |
| `estrategias_digitales_en_planes_estatales_por` | REAL | 81.25 |
| `accesibilidad_en_portales_estatales_por` | INTEGER | 56 |
| `policia_cibernetica_xmhab` | REAL | 30.76 |
| `politica_climatica_por` | INTEGER | 65 |
| `funcionarios_publicos_por_area_de_estadistica_o_geografia_xmil` | REAL | 2.63 |
| `gestion_documental_estatal_y_municipal_por` | REAL | 50.91 |
| `digitalizacion_de_tramites_por` | REAL | 75.0 |
| `personal_con_herramientas_tecnologicas_basicas_por` | REAL | 79.28 |
| `empresas_con_herramientas_tecnologicas_basicas_por` | REAL | 53.93 |
| `empresas_con_herramientas_tecnologicas_intermedias_por` | REAL | 40.08 |
| `empresas_con_herramientas_tecnologicas_avanzadas_por` | REAL | 13.81 |
| `empresas_con_herramientas_tecnologicas_innovadoras_por` | REAL | 5.46 |
| `uso_de_internet_en_las_empresas_por` | REAL | 63.96 |
| `especialistas_de_ti_y_ciberseguridad_en_las_empresas_por` | REAL | 21.15 |
| `acciones_de_ciberseguridad_en_las_empresas_por` | REAL | 16.23 |
| `compras_por_internet_por` | REAL | 12.2 |
| `ventas_por_internet_por` | REAL | 9.91 |
| `volumen_de_ventas_por_internet_por` | REAL | 12.256512 |
| `microempresas_con_internet_por` | REAL | 39.2 |
| `penetracion_de_banda_ancha_fija_no_residencial_x100ue` | INTEGER | 58 |
| `p3ecdi_gentopdo_25` | REAL | 15.48 |
| `empresas_que_utilizan_banca_electronica_por` | REAL | 25.45 |
| `penetracion_de_terminales_punto_de_venta_x100adu` | REAL | 6.38 |
| `empleados_con_profesiones_stem_x100hab` | REAL | 1.75 |
| `empleos_detectados_en_internet_por` | REAL | 6.9 |
| `gasto_del_gobierno_en_servicios_de_telecomunicaciones_y_percap` | REAL | 21.87 |
| `inversion_extranjera_directa_en_industria_tic_log` | REAL | 17.959444 |
| `intercambio_comercial_de_electronicos_log` | REAL | 20.79 |
| `solicitudes_de_invenciones_xmhab` | REAL | 27.36 |
| `graduados_en_programas_stem_xmhab` | REAL | 2631.16 |
| `mujeres_graduadas_en_programas_stem_por` | REAL | 30.21 |
| `presupuesto_para_instituciones_de_ciencia_tecnologia_e_i_percap` | REAL | 123.79 |
| `publicaciones_cientificas_de_ia_xmpib` | REAL | 2.37 |
| `indice_de_desarrollo_digital_estatal_2025` | REAL | 193.1899 |
| `pilar_infraestructura` | REAL | 69.68 |
| `subpilar_de_cobertura_acceso_y_calidad` | REAL | 66.35 |
| `subpilar_de_asequibilidad` | REAL | 73.89 |
| `subpilar_de_infraestructura_de_datos` | REAL | 70.3 |
| `pilar_digitalizacion_de_las_personas_y_la_sociedad` | REAL | 69.23 |
| `subpilar_de_usuarios_y_usos_de_las_tic` | REAL | 73.93 |
| `subpilar_de_capacidades_y_habilidades_digitales` | REAL | 52.66 |
| `subpilar_de_digitalizacion_de_los_servicios_prioritarios` | REAL | 64.98 |
| `subpilar_de_gobierno_digital_y_entorno_regulatorio` | REAL | 85.36 |
| `pilar_innovacion_y_adopcion_tecnologica_de_las_empresas` | REAL | 54.27 |
| `subpilar_de_adopcion_de_nuevas_tecnologias` | REAL | 44.39 |
| `subpilar_de_ciberseguridad` | REAL | 49.81 |
| `subpilar_de_comercio_electronico` | REAL | 57.44 |
| `subpilar_de_economia_digital` | REAL | 64.02 |
| `subpilar_de_innovacion` | REAL | 51.53 |
| `grupo_de_digitalizacion_2025_id` | INTEGER | 4 |

**Ejemplo SQL:**

```sql
SELECT e.estado, i.idde_2025
FROM idde_2025 i JOIN dim_estado e ON i.clave_inegi_de_estado = e.clave_ent
ORDER BY 2 DESC;
```

## incidencia_municipal

Incidencia delictiva municipal, dic 2025. FKs: clave_ent→dim_estado, (clave_ent,cve_municipio)→dim_municipio, subtipo_id→dim_subtipo_delito, modalidad_id→dim_modalidad, bien_juridico_afectado_id→dim_bien_juridico_afectado.

**Fuente:** datos.gob.mx — IDM_NM_dic25.csv  
**Filas aprox:** 2,562,994  
**Archivo CSV:** `datall/IDM_NM_dic25.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `ano` | INTEGER | 2015 |
| `clave_ent` | INTEGER | 1 |
| `cve_municipio` | INTEGER | 1001 |
| `enero` | INTEGER | 2 |
| `febrero` | INTEGER | 0 |
| `marzo` | INTEGER | 1 |
| `abril` | INTEGER | 1 |
| `mayo` | INTEGER | 0 |
| `junio` | INTEGER | 1 |
| `julio` | INTEGER | 1 |
| `agosto` | INTEGER | 0 |
| `septiembre` | INTEGER | 2 |
| `octubre` | INTEGER | 1 |
| `noviembre` | INTEGER | 0 |
| `diciembre` | INTEGER | 1 |
| `subtipo_id` | INTEGER | 20 |
| `modalidad_id` | INTEGER | 8 |
| `bien_juridico_afectado_id` | INTEGER | 5 |

**Ejemplo SQL:**

```sql
SELECT e.estado, m.municipio, s.subtipo, mo.modalidad, b.bien_juridico_afectado, SUM(f.enero + f.febrero)
FROM incidencia_municipal f
JOIN dim_estado e ON f.clave_ent = e.clave_ent
JOIN dim_municipio m ON f.clave_ent = m.clave_ent AND f.cve_municipio = m.cve_municipio
JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
JOIN dim_modalidad mo ON f.modalidad_id = mo.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id
GROUP BY 1,2,3,4,5 ORDER BY 6 DESC LIMIT 20;
```

## incidencia_estatal

Incidencia delictiva estatal, dic 2025. FKs: clave_ent→dim_estado, subtipo_id→dim_subtipo_delito, modalidad_id→dim_modalidad, bien_juridico_afectado_id→dim_bien_juridico_afectado. `mes_num`=1-12 (enero-diciembre).

**Fuente:** datos.gob.mx — INM_estatal_dic25.csv  
**Filas aprox:** 413,952  
**Archivo CSV:** `datall/INM_estatal_dic25.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `anio` | INTEGER | 2015 |
| `clave_ent` | INTEGER | 1 |
| `incidencia_delictiva` | INTEGER | 22 |
| `subtipo_id` | INTEGER | 2 |
| `modalidad_id` | INTEGER | 2 |
| `bien_juridico_afectado_id` | INTEGER | 1 |
| `mes_num` | INTEGER | 4 |

**Ejemplo SQL:**

```sql
SELECT e.estado, s.subtipo, mo.modalidad, b.bien_juridico_afectado, f.anio, f.mes_num, SUM(f.incidencia_delictiva)
FROM incidencia_estatal f
JOIN dim_estado e ON f.clave_ent = e.clave_ent
JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
JOIN dim_modalidad mo ON f.modalidad_id = mo.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id
GROUP BY 1,2,3,4,5,6 ORDER BY 7 DESC LIMIT 20;
```

## victimas_fuero_comun

Víctimas del fuero común. FKs: clave_ent→dim_estado, subtipo_id→dim_subtipo_delito, modalidad_id→dim_modalidad, bien_juridico_afectado_id→dim_bien_juridico_afectado, sexo_id→dim_sexo, rango_edad_id→dim_rango_edad.

**Fuente:** datos.gob.mx — Victimas_fuero_comun.csv  
**Filas aprox:** 80,960  
**Archivo CSV:** `datall/Victimas_fuero_comun.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `ano` | INTEGER | 2015 |
| `clave_ent` | INTEGER | 1 |
| `enero` | INTEGER | 0 |
| `febrero` | INTEGER | 0 |
| `marzo` | INTEGER | 0 |
| `abril` | INTEGER | 0 |
| `mayo` | INTEGER | 0 |
| `junio` | INTEGER | 0 |
| `julio` | INTEGER | 0 |
| `agosto` | INTEGER | 0 |
| `septiembre` | INTEGER | 0 |
| `octubre` | INTEGER | 0 |
| `noviembre` | INTEGER | 0 |
| `diciembre` | INTEGER | 0 |
| `subtipo_id` | INTEGER | 20 |
| `modalidad_id` | INTEGER | 8 |
| `sexo_id` | INTEGER | 2 |
| `rango_edad_id` | INTEGER | 2 |
| `bien_juridico_afectado_id` | INTEGER | 5 |

**Ejemplo SQL:**

```sql
SELECT e.estado, s.subtipo, mo.modalidad, b.bien_juridico_afectado, x.sexo, r.rango_edad, SUM(f.enero + f.febrero)
FROM victimas_fuero_comun f
JOIN dim_estado e ON f.clave_ent = e.clave_ent
JOIN dim_subtipo_delito s ON f.subtipo_id = s.subtipo_id
JOIN dim_modalidad mo ON f.modalidad_id = mo.modalidad_id
JOIN dim_bien_juridico_afectado b ON f.bien_juridico_afectado_id = b.bien_juridico_afectado_id
JOIN dim_sexo x ON f.sexo_id = x.sexo_id
JOIN dim_rango_edad r ON f.rango_edad_id = r.rango_edad_id
GROUP BY 1,2,3,4,5,6 ORDER BY 7 DESC LIMIT 20;
```

## datamexico_crimes

> Archivo no encontrado: `data/raw/datamexico_crimes/sesnsp_crimes_state_month_subtype/data.csv`


## datamexico_envipe

ENVIPE: percepción de seguridad, confianza en instituciones y perfil sociodemográfico. Solo columnas *_id + age + homes + people. FKs: state_id→dim_estado.clave_ent. `age` es edad individual en años (int), NO joinable a dim_rango_edad.

**Fuente:** DataMéxico API — cubo inegi_envipe  
**Filas aprox:** 41,020  
**Archivo CSV:** `data/raw/datamexico_envipe/inegi_envipe_confidence_state/data.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `state_id` | INTEGER | 1 |
| `confidence_in_army_id` | INTEGER | 1 |
| `confidence_in_federal_police_id` | INTEGER | 1 |
| `confidence_in_public_ministry_and_state_prosecutors_id` | INTEGER | 1 |
| `expenses_in_protection_against_crime_id` | INTEGER | 1 |
| `security_perception_in_their_state_id` | INTEGER | 1 |
| `trust_in_family_id` | INTEGER | 1 |
| `sociodemographic_stratum_id` | INTEGER | 2 |
| `trust_in_friends_id` | INTEGER | 1 |
| `trust_in_neighborhood_id` | INTEGER | 1 |
| `confidence_in_traffic_police_id` | INTEGER | 1 |
| `confidence_in_state_police_id` | INTEGER | 1 |
| `trust_in_coworkers_id` | INTEGER | 1 |
| `sex_id` | INTEGER | 2 |
| `confidence_in_judges_id` | INTEGER | 1 |
| `confidence_in_state_prosecutor_of_the_republic_id` | INTEGER | 1 |
| `age` | INTEGER | 43 |
| `homes` | INTEGER | 202 |
| `people` | INTEGER | 405 |

**Ejemplo SQL:**

```sql
SELECT e.estado, nc.nivel_confianza, f.homes, f.people
FROM datamexico_envipe f
JOIN dim_estado e ON f.state_id = e.clave_ent
JOIN dim_nivel_confianza nc ON f.confidence_in_state_police_id = nc.nivel_confianza_id
ORDER BY f.people DESC LIMIT 20;
```

## datamexico_denue

DENUE: empresas y empleo por estado, mes y tamano de empresa. FKs: state_id→dim_estado.clave_ent, month_id→dim_month.month_id, company_size_id→dim_company_size.company_size_id.

**Fuente:** DataMexico API — cube inegi_denue  
**Filas aprox:** 4,256  
**Archivo CSV:** `data/raw/datamexico_denue/inegi_denue_state_month_company_size/data.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `state_id` | INTEGER | 1 |
| `month_id` | INTEGER | 20150225 |
| `company_size_id` | INTEGER | 1 |
| `companies` | INTEGER | 47972 |
| `number_of_employees_lci` | INTEGER | 0 |
| `number_of_employees_midpoint` | REAL | 119930.0 |
| `number_of_employees_uci` | INTEGER | 239860 |

**Ejemplo SQL:**

```sql
SELECT e.estado, m.month, s.company_size, f.companies
FROM datamexico_denue f
JOIN dim_estado e ON f.state_id = e.clave_ent
JOIN dim_month m ON f.month_id = m.month_id
JOIN dim_company_size s ON f.company_size_id = s.company_size_id
ORDER BY f.companies DESC LIMIT 20;
```

## datamexico_enoe

ENOE: indicadores laborales por estado, trimestre y categorias sociodemograficas. FKs: state_id→dim_estado.clave_ent, quarter_id→dim_quarter.quarter_id, y dimensiones ENOE para poblacion economica activa, nivel instruccion, situacion laboral, anios de escolaridad y ocupacion.

**Fuente:** DataMexico API — cube inegi_enoe  
**Filas aprox:** 190,500  
**Archivo CSV:** `data/raw/datamexico_enoe/inegi_enoe_state_quarter_eap_instruction_job_schooling_occupation/data.csv`


| Columna | Tipo POSTGRES | Ejemplo |
|---------|----------------|---------|
| `state_id` | INTEGER | 1 |
| `quarter_id` | INTEGER | 20101 |
| `economically_active_population_id` | INTEGER | 1 |
| `instruction_level_id` | INTEGER | 2 |
| `job_situation_id` | INTEGER | 1 |
| `occupation_id` | INTEGER | 5242 |
| `number_of_records` | INTEGER | 1 |
| `workforce` | INTEGER | 74 |
| `worked_hours_week` | REAL |  |
| `worked_days_week` | REAL |  |
| `monthly_wage` | REAL | 0.0 |
| `schooling_years_id` | INTEGER | 6 |

**Ejemplo SQL:**

```sql
SELECT e.estado, q.quarter, il.instruction_level, f.workforce
FROM datamexico_enoe f
JOIN dim_estado e ON f.state_id = e.clave_ent
JOIN dim_quarter q ON f.quarter_id = q.quarter_id
JOIN dim_instruction_level il ON f.instruction_level_id = il.instruction_level_id
ORDER BY f.workforce DESC LIMIT 20;
```
