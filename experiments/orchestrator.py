"""
Orchestrator — Runs all 4 experiment agents, collects results,
generates consolidated report, and identifies top findings.
"""
import sys
import json
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.data_utils import RESULTS_DIR, run_agent_safely


def run_all():
    """Run all 4 agents sequentially and aggregate results."""
    print('='*70)
    print('  MULTI-AGENT EXPERIMENT ORCHESTRATOR')
    print(f'  Started: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70)

    agents = [
        ('experiments.agent_structural',   'Agent 1: Structural (municipal-level)'),
        ('experiments.agent_robustness',   'Agent 2: Robustness (stress-tests)'),
        ('experiments.agent_ml_discovery', 'Agent 3: ML Discovery (nonlinear)'),
        ('experiments.agent_unorthodox',   'Agent 4: Unorthodox (novel approaches)'),
    ]

    all_results = []
    agent_summaries = []

    for module_name, desc in agents:
        print(f'\n{"─"*70}')
        print(f'  Launching: {desc}')
        print(f'{"─"*70}')
        start = time.time()
        try:
            mod = __import__(module_name, fromlist=['run'])
            session = mod.run()
            if session:
                all_results.extend(session.results)
                agent_summaries.append({
                    'agent_id': session.agent_id,
                    'objective': session.objective,
                    'duration': round(time.time() - start, 1),
                    'total': len(session.results),
                    'promising': sum(1 for r in session.results if r.is_promising()),
                })
                print(f'  ✓ {desc}: {len(session.results)} experiments, '
                      f'{sum(1 for r in session.results if r.is_promising())} promising')
            else:
                print(f'  ✗ {desc}: returned None')
                agent_summaries.append({
                    'agent_id': module_name.split('.')[-1],
                    'objective': desc,
                    'duration': round(time.time() - start, 1),
                    'total': 0,
                    'promising': 0,
                    'error': 'Agent returned None',
                })
        except Exception as e:
            print(f'  ✗ {desc}: ERROR — {e}')
            traceback.print_exc()
            agent_summaries.append({
                'agent_id': module_name.split('.')[-1],
                'objective': desc,
                'duration': round(time.time() - start, 1),
                'total': 0,
                'promising': 0,
                'error': str(e),
            })

    # ── Aggregate & rank ──────────────────────────────────────────────
    promising = sorted([r for r in all_results if r.is_promising()],
                       key=lambda r: r.score(), reverse=True)
    all_sorted = sorted(all_results, key=lambda r: r.score(), reverse=True)

    # ── Generate consolidated report ──────────────────────────────────
    report_path = Path(__file__).parent / 'consolidated_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('# Multi-Agent Experiment Report\n\n')
        f.write(f'**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S")}  \n')
        f.write(f'**Total experiments:** {len(all_results)}  \n')
        f.write(f'**Promising findings:** {len(promising)}  \n\n')

        f.write('---\n\n')
        f.write('## Agent Summary\n\n')
        f.write('| Agent | Experiments | Promising | Duration |\n')
        f.write('|-------|-----------|----------|----------|\n')
        for s in agent_summaries:
            error = f' ⚠ {s.get("error", "")}' if 'error' in s else ''
            f.write(f'| {s["agent_id"]} | {s["total"]} | {s["promising"]} | '
                    f'{s["duration"]}s{error} |\n')

        f.write('\n---\n\n')
        f.write('## Top 20 Findings (ranked by score)\n\n')
        for i, r in enumerate(all_sorted[:20]):
            marker = '★' if r.is_promising() else '○'
            f.write(f'### {marker} #{i+1}: {r.title}\n\n')
            f.write(f'**Agent:** {r.agent_id} | **Exp:** {r.exp_id} | '
                    f'**Score:** {r.score():.0f} '
                    f'(conf={r.confidence}, nov={r.novelty}, narr={r.narrative_value})\n\n')
            f.write(f'**Description:** {r.description}\n\n')
            f.write(f'**Finding:** {r.finding}\n\n')
            if r.stat_value is not None:
                f.write(f'**Statistic:** {r.stat_name}={r.stat_value}')
                if r.p_value is not None:
                    f.write(f', p={r.p_value}')
                f.write('\n\n')
            if r.recommendation:
                f.write(f'**Recommendation:** {r.recommendation}\n\n')
            f.write('---\n\n')

        f.write('\n## All Promising Findings\n\n')
        for r in promising:
            f.write(f'- **[{r.agent_id}:{r.exp_id}]** {r.title} '
                    f'(score={r.score():.0f}) — {r.finding[:120]}\n')

    # ── Save raw JSON ─────────────────────────────────────────────────
    json_path = RESULTS_DIR / 'consolidated_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_experiments': len(all_results),
            'promising_count': len(promising),
            'agent_summaries': agent_summaries,
            'top_findings': [r.to_dict() for r in all_sorted[:30]],
            'promising': [r.to_dict() for r in promising],
        }, f, indent=2, ensure_ascii=False, default=str)

    # ── Print final summary ───────────────────────────────────────────
    print(f'\n{"="*70}')
    print(f'  ORCHESTRATOR COMPLETE')
    print(f'  Total experiments: {len(all_results)}')
    print(f'  Promising findings: {len(promising)}')
    print(f'  Report: {report_path}')
    print(f'  JSON: {json_path}')
    print(f'{"="*70}')

    print(f'\n  TOP 10 FINDINGS:')
    print(f'  {"─"*60}')
    for i, r in enumerate(all_sorted[:10]):
        marker = '★' if r.is_promising() else '○'
        print(f'  {marker} [{i+1}] [{r.agent_id}:{r.exp_id}] {r.title}')
        print(f'      score={r.score():.0f} (conf={r.confidence} nov={r.novelty} narr={r.narrative_value})')
        print(f'      {r.finding[:100]}')

    return all_results, promising


if __name__ == '__main__':
    run_all()
