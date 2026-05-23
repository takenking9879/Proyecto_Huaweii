import pandas as pd
import numpy as np
from pages.db import query

_cache_main  = None
_cache_confi = None


def _load():
    global _cache_main
    if _cache_main is not None:
        return _cache_main

    raw = query("""
        SELECT e.security_perception_in_their_state_id AS percepcion_id,
               e.state_id, e.sex_id,
               e.confidence_in_army_id         AS conf_army,
               e.confidence_in_federal_police_id AS conf_fed_pol,
               e.confidence_in_state_police_id   AS conf_sta_pol,
               e.confidence_in_judges_id         AS conf_judges,
               e.confidence_in_traffic_police_id AS conf_transit,
               e.confidence_in_public_ministry_and_state_prosecutors_id AS conf_mp,
               e.trust_in_family_id     AS trust_fam,
               e.trust_in_friends_id    AS trust_fri,
               e.trust_in_neighborhood_id AS trust_nei,
               e.trust_in_coworkers_id  AS trust_cow,
               e.expenses_in_protection_against_crime_id AS gastos_id,
               e.sociodemographic_stratum_id AS estrato_id,
               e.homes, e.people
        FROM datamexico_envipe e
    """)

    perc  = query("SELECT percepcion_id, percepcion FROM dim_percepcion_seguridad")
    conf  = query("SELECT nivel_confianza_id, nivel_confianza FROM dim_nivel_confianza")
    gastos = query("SELECT gastos_id, gastos_rango FROM dim_gastos_proteccion")
    estrato = query("SELECT estrato_id, estrato FROM dim_estrato_sociodemografico")
    estado = query("SELECT clave_ent AS state_id, estado FROM dim_estado")

    raw = (raw
           .merge(perc,   on='percepcion_id', how='left')
           .merge(estado, on='state_id',      how='left')
           .merge(gastos, on='gastos_id',     how='left')
           .merge(estrato, on='estrato_id',   how='left'))
    _cache_main = raw
    return raw


def _pct_inseguro_by_estado():
    df = _load()
    tot = df.groupby('estado')['homes'].sum().rename('total')
    ins = (df[df['percepcion'] == 'Inseguro']
           .groupby('estado')['homes'].sum().rename('inseguros'))
    res = pd.concat([tot, ins], axis=1).fillna(0)
    res['pct_inseguro'] = res['inseguros'] / res['total'] * 100
    return res.reset_index().sort_values('pct_inseguro', ascending=False)


def _confianza_institucional():
    df = _load()
    conf_cols = {
        'conf_army':    'Ejército',
        'conf_fed_pol': 'Pol. Federal',
        'conf_sta_pol': 'Pol. Estatal',
        'conf_judges':  'Jueces',
        'conf_transit': 'Tránsito',
        'conf_mp':      'Ministerio P.',
    }
    rows = []
    for col, label in conf_cols.items():
        conf_map = query("SELECT nivel_confianza_id, nivel_confianza FROM dim_nivel_confianza")
        merged = df[[col, 'homes']].copy()
        merged = merged.merge(
            conf_map.rename(columns={'nivel_confianza_id': col, 'nivel_confianza': 'nivel'}),
            on=col, how='left'
        )
        tot = merged['homes'].sum()
        pct_positiva = (merged[merged['nivel'].isin(['Mucha Confianza', 'Algo de Confianza'])]['homes'].sum()
                        / tot * 100)
        rows.append({'institucion': label, 'pct_confianza': round(float(pct_positiva), 1)})
    return pd.DataFrame(rows).sort_values('pct_confianza', ascending=True)


def _confianza_por_estrato():
    df = _load()
    conf_map = query("SELECT nivel_confianza_id, nivel_confianza FROM dim_nivel_confianza")
    col = 'conf_army'
    merged = df[[col, 'estrato', 'homes']].merge(
        conf_map.rename(columns={'nivel_confianza_id': col, 'nivel_confianza': 'nivel'}),
        on=col, how='left'
    )
    positiva = merged[merged['nivel'].isin(['Mucha Confianza', 'Algo de Confianza'])]
    tot_est = merged.groupby('estrato')['homes'].sum()
    pos_est = positiva.groupby('estrato')['homes'].sum()
    res = (pos_est / tot_est * 100).reset_index()
    res.columns = ['estrato', 'pct_confianza']
    return res


def get_percepcion_estados():
    return _pct_inseguro_by_estado()


def get_confianza_institucional():
    return _confianza_institucional()


def get_gastos_por_estrato():
    df = _load()
    gastos_map = query("SELECT gastos_id, gastos_rango FROM dim_gastos_proteccion")
    merged = df[['gastos_id', 'estrato', 'homes']].merge(gastos_map, on='gastos_id', how='left')
    tot = merged.groupby(['estrato', 'gastos_rango'])['homes'].sum().reset_index()
    total_e = merged.groupby('estrato')['homes'].sum().rename('total')
    tot = tot.merge(total_e, on='estrato')
    tot['pct'] = tot['homes'] / tot['total'] * 100
    return tot


def get_kpis():
    df_perc = _pct_inseguro_by_estado()
    pct_nac = float(df_perc['pct_inseguro'].mean())
    mas_inseguro = df_perc.iloc[0]['estado']
    mas_seguro   = df_perc.iloc[-1]['estado']
    df_conf = _confianza_institucional()
    inst_mas_confianza = df_conf.iloc[-1]['institucion']
    return {
        'pct_inseguro_nac': round(pct_nac, 1),
        'estado_mas_inseguro': mas_inseguro,
        'estado_mas_seguro': mas_seguro,
        'institucion_mas_confianza': inst_mas_confianza,
    }
