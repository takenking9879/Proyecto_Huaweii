"""
Shared utilities for all experiment agents.
Centralizes data loading, result tracking, and scoring.
"""
import os
import sys
import json
import time
import warnings
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy import stats

warnings.filterwarnings('ignore')

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

RESULTS_DIR = Path(__file__).parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════

_data_cache = None

def load_all_data():
    """Load all project data. Cached after first call."""
    global _data_cache
    if _data_cache is not None:
        return _data_cache

    from pages.db import query
    from pages.get_data.get_data_11 import get_data_11, INFRA_VARS, SEC_COL_LABELS

    d11 = get_data_11()
    dim_state = query('SELECT clave_ent, estado FROM dim_estado')

    # ── Municipal crime (monthly → annual) ────────────────────────────
    muni_crime = query("""
        SELECT ano, clave_ent, cve_municipio, subtipo_id, bien_juridico_afectado_id,
               (enero+febrero+marzo+abril+mayo+junio+julio+agosto+septiembre+octubre+noviembre+diciembre) AS total
        FROM incidencia_municipal
        WHERE ano BETWEEN 2022 AND 2025
    """)

    # Map crime types
    subtipo = query('SELECT subtipo_id, subtipo FROM dim_subtipo_delito')
    bien = query('SELECT bien_juridico_afectado_id, bien_juridico_afectado FROM dim_bien_juridico_afectado')
    muni_crime = muni_crime.merge(subtipo, on='subtipo_id', how='left')
    muni_crime = muni_crime.merge(bien, on='bien_juridico_afectado_id', how='left')

    # State-level population (for per-capita calculations)
    state_pop_raw = query("""
        SELECT state_id AS clave_ent, year_id AS ano, population AS pop
        FROM datamexico_population
    """)
    # Also get anchor population for more years
    pop_anchor = query("""
        SELECT estado, anio AS ano, poblacion AS pop
        FROM poblacion_ancla
    """)
    pop_anchor = pop_anchor.merge(dim_state, on='estado', how='left')
    pop_anchor = pop_anchor[['clave_ent', 'ano', 'pop']]
    # Combine both population sources
    state_pop = pd.concat([state_pop_raw, pop_anchor]).drop_duplicates(
        subset=['clave_ent', 'ano'], keep='last')
    # Interpolate population for missing years
    state_pops_interp = []
    for ent, grp in state_pop.groupby('clave_ent'):
        grp = grp.sort_values('ano')
        for yr in range(2022, 2026):
            if yr in grp['ano'].values:
                state_pops_interp.append({'clave_ent': ent, 'ano': yr,
                                          'pop': grp[grp['ano'] == yr]['pop'].iloc[0]})
            else:
                # Linear interpolation from nearest years
                lower = grp[grp['ano'] <= yr].tail(1)
                upper = grp[grp['ano'] >= yr].head(1)
                if len(lower) > 0 and len(upper) > 0:
                    frac = (yr - lower['ano'].iloc[0]) / (upper['ano'].iloc[0] - lower['ano'].iloc[0])
                    pop_val = lower['pop'].iloc[0] + frac * (upper['pop'].iloc[0] - lower['pop'].iloc[0])
                elif len(lower) > 0:
                    pop_val = lower['pop'].iloc[0]
                elif len(upper) > 0:
                    pop_val = upper['pop'].iloc[0]
                else:
                    pop_val = np.nan
                state_pops_interp.append({'clave_ent': ent, 'ano': yr, 'pop': pop_val})
    state_pop = pd.DataFrame(state_pops_interp)

    # Merge state population into muni_crime for per-capita rates
    muni_crime = muni_crime.merge(state_pop, on=['clave_ent', 'ano'], how='left')
    muni_crime = muni_crime.merge(dim_state, on='clave_ent', how='left')

    # Municipal-level annual crime (aggregate across subtypes)
    muni_annual = (muni_crime.groupby(['clave_ent', 'cve_municipio', 'ano', 'estado'])
                   .agg({'total': 'sum', 'pop': 'first'})
                   .reset_index())
    # Assign each municipality a proportion of state crime (crime share)
    state_totals = muni_annual.groupby(['clave_ent', 'ano'])['total'].sum().rename('state_total')
    muni_annual = muni_annual.merge(state_totals, on=['clave_ent', 'ano'], how='left')
    muni_annual['crime_share'] = muni_annual['total'] / muni_annual['state_total'].replace(0, np.nan)
    # Estimate municipal population as: state_pop × crime_share (rough proxy)
    muni_annual['est_pop'] = muni_annual['pop'] * muni_annual['crime_share']
    # Use per-100k relative to state population
    muni_annual['rate_100k'] = (muni_annual['total'] / muni_annual['pop'].replace(0, np.nan)) * 1e5

    # ── Victims data ──────────────────────────────────────────────────
    victims = query("""
        SELECT ano, clave_ent, subtipo_id, sexo_id, rango_edad_id, bien_juridico_afectado_id,
               (enero+febrero+marzo+abril+mayo+junio+julio+agosto+septiembre+octubre+noviembre+diciembre) AS total
        FROM victimas_fuero_comun
        WHERE ano BETWEEN 2022 AND 2025
    """)
    victims = victims.merge(dim_state, on='clave_ent', how='left')
    victims = victims.merge(subtipo, on='subtipo_id', how='left')
    victims = victims.merge(bien, on='bien_juridico_afectado_id', how='left')

    # ── DENUE (business density) ──────────────────────────────────────
    denue = query("""
        SELECT state_id, month_id, company_size_id,
               companies, number_of_employees_midpoint
        FROM datamexico_denue
    """)
    denue = denue.merge(dim_state, left_on='state_id', right_on='clave_ent', how='left')
    company_size = query('SELECT * FROM dim_company_size')
    denue = denue.merge(company_size, on='company_size_id', how='left')

    # ── ENVIPE for cifra negra ────────────────────────────────────────
    envipe = d11['cross_cl'].copy()

    # ── Panel data ────────────────────────────────────────────────────
    panel = d11['panel'].copy()
    cross_cl = d11['cross_cl'].copy()

    _data_cache = {
        'd11': d11,
        'cross_cl': cross_cl,
        'cross': d11['cross'].copy(),
        'panel': panel,
        'corr_matrix': d11['corr_matrix'],
        'INFRA_VARS': INFRA_VARS,
        'SEC_COL_LABELS': SEC_COL_LABELS,
        'muni_crime': muni_crime,
        'muni_annual': muni_annual,
        'state_pop': state_pop,
        'victims': victims,
        'denue': denue,
        'envipe': envipe,
        'dim_state': dim_state,
        'subtipo': subtipo,
        'bien': bien,
    }
    return _data_cache


# ═══════════════════════════════════════════════════════════════════════
# Experiment Result Tracking
# ═══════════════════════════════════════════════════════════════════════

class ExperimentResult:
    """Container for one experiment's findings."""
    def __init__(self, agent_id, exp_id, title, description,
                 finding, stat_value=None, stat_name=None, p_value=None,
                 confidence=0, novelty=0, narrative_value=0,
                 recommendation=None, code_snippet=None):
        self.agent_id = agent_id
        self.exp_id = exp_id
        self.title = title
        self.description = description
        self.finding = finding
        self.stat_value = stat_value
        self.stat_name = stat_name
        self.p_value = p_value
        self.confidence = confidence
        self.novelty = novelty
        self.narrative_value = narrative_value
        self.recommendation = recommendation
        self.code_snippet = code_snippet
        self.timestamp = datetime.now().isoformat()

    def score(self):
        return (self.confidence or 0) * (self.novelty or 0) * (self.narrative_value or 0)

    def is_promising(self, threshold=125):
        return self.score() >= threshold

    def to_dict(self):
        d = self.__dict__.copy()
        d['score'] = self.score()
        d['promising'] = self.is_promising()
        return d

    def __repr__(self):
        return f'[{self.agent_id}:{self.exp_id}] {self.title} (score={self.score():.0f})'


class AgentSession:
    """Tracks an agent's experiments and saves results."""
    def __init__(self, agent_id, objective):
        self.agent_id = agent_id
        self.objective = objective
        self.results = []
        self.start_time = time.time()

    def record(self, exp: ExperimentResult):
        self.results.append(exp)
        return exp

    def promising(self, top_n=10):
        return sorted(self.results, key=lambda r: r.score(), reverse=True)[:top_n]

    def save(self):
        data = {
            'agent_id': self.agent_id,
            'objective': self.objective,
            'duration_sec': round(time.time() - self.start_time, 1),
            'total_experiments': len(self.results),
            'promising_count': sum(1 for r in self.results if r.is_promising()),
            'results': [r.to_dict() for r in sorted(self.results,
                                                     key=lambda r: r.score(),
                                                     reverse=True)],
        }
        path = RESULTS_DIR / f'{self.agent_id}_results.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return path

    def summary(self):
        lines = [
            f'\n{"="*70}',
            f'  AGENT: {self.agent_id}',
            f'  Objective: {self.objective}',
            f'  Duration: {time.time() - self.start_time:.1f}s',
            f'  Experiments: {len(self.results)} total, '
            f'{sum(1 for r in self.results if r.is_promising())} promising',
            f'{"─"*70}',
        ]
        for r in sorted(self.results, key=lambda x: x.score(), reverse=True):
            marker = '★' if r.is_promising() else '·'
            lines.append(f'  {marker} [{r.exp_id}] {r.title}')
            lines.append(f'    score={r.score():.0f} '
                         f'(conf={r.confidence} nov={r.novelty} narr={r.narrative_value})')
            lines.append(f'    {r.finding[:120]}')
        lines.append(f'{"="*70}')
        return '\n'.join(lines)


def run_agent_safely(agent_fn):
    """Run an agent function, catching and reporting errors."""
    try:
        return agent_fn()
    except Exception as e:
        traceback.print_exc()
        return None
