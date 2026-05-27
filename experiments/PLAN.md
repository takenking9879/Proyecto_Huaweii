# Plan: Multi-Agent Experiment Framework

## Goal
Create 4 specialized experiment agents + 1 orchestrator that autonomously discover new, non-obvious, insightful findings to enhance the dashboard. Each agent runs Python experiments, evaluates results, and keeps digging deeper on promising leads.

## Architecture

```
experiments/
├── __init__.py
├── data_utils.py          # Shared data loading + ExperimentResult/AgentSession
├── orchestrator.py        # Runs all 4 agents, collects results, generates report
├── agent_structural.py    # Agent 1: Municipal-level analysis (N=2,457)
├── agent_robustness.py    # Agent 2: Stress-test existing claims
├── agent_ml_discovery.py  # Agent 3: ML-driven feature discovery
├── agent_unorthodox.py    # Agent 4: Causal inference & novel approaches
└── results/               # JSON outputs per agent
```

## 4 Agent Strategies

### Agent 1: "Structural" — Municipal-Level Power
Key insight: incidencia_municipal has ~2.6M rows across ~2,457 municipalities, raising N from 32→2,457.

| Round | Experiment | Goal |
|-------|-----------|------|
| 1.1 | Aggregate IDDE to municipality using state-level IDDE + municipal urban/rural indicator | Create municipal-level dataset |
| 1.2 | Correlate municipal crime rates with digital infrastructure at municipal level | Test if r>0.5 at municipal level |
| 1.3 | Multi-level/hierarchical model (states as random intercepts, municipalities nested) | Partition variance: between-state vs within-state |
| 1.4 | Test if within-state heterogeneity in crime is explained by municipal digital access | The real question: does digital access matter within a state? |
| 1.5 | If promising: spatial lag model (neighbors' crime predicts own crime) | Spatial spillover with proper N |

### Agent 2: "Robustness" — Stress-Test Existing Claims
| Round | Experiment | Goal |
|-------|-----------|------|
| 2.1 | Leave-one-out influence: remove each state, recompute r/R² for key correlations | Find high-influence states |
| 2.2 | Cook's distance + leverage analysis on the main regressions | Identify outlier states driving results |
| 2.3 | Winsorize top/bottom 5% and re-estimate | Robustness to outliers |
| 2.4 | Permutation test: shuffle state labels 10,000× for IDDE→crime correlation | Exact p-value without distributional assumptions |
| 2.5 | Subsample bootstrap (80%) x 1000 iterations | Stability of effect sizes |
| 2.6 | Compare results with vs without outlier states | Document which states are critical |
| 2.7 | Re-estimate with different IDDE components (exclude one pillar at a time) | Which IDDE pillar drives the results? |

### Agent 3: "ML Discovery" — Nonlinear & Interaction Effects
| Round | Experiment | Goal |
|-------|-----------|------|
| 3.1 | Random Forest permutation importance on all 532 correlations | Feature importance without linearity assumption |
| 3.2 | Partial dependence plots for top 5 infra→security pairs | Nonlinear dose-response curves |
| 3.3 | Interaction effects: does connectivity amplify crime reduction? | Test synergy hypothesis |
| 3.4 | Compare R² from linear, quadratic, and RF models | Test if nonlinearity helps |
| 3.5 | Mutual information vs Pearson correlation for key pairs | Information-theoretic evidence |

### Agent 4: "Unorthodox" — Novel Causal & Descriptive Approaches
| Round | Experiment | Goal |
|-------|-----------|------|
| 4.1 | Cifra negra adjustment: weight crime by ENVIPE reporting rates by state | Test if underreporting biases IDDE-crime |
| 4.2 | Crime type heterogeneity: separate violent vs property vs cyber | Some crimes correlate differently |
| 4.3 | Lagged difference model: Δcrime(t) ~ ΔIDDE(t-1) + crime(t-1) | Dynamic panel approximation |
| 4.4 | Synthetic control (simplified): for 1-2 states | Is there a divergent treated state? |
| 4.5 | IV regression: instrument IDDE with federal telecom budget | Weak instrument test included |
| 4.6 | Denue employment: correlate new business formation with IDDE | Completely new data source |
| 4.7 | Temporal structure: ADF/KPSS on IDDE panel | If non-stationary, panel results are spurious |

## Decision Criteria
Each ExperimentResult scores: confidence x novelty x narrative_value (each 0-10).
Threshold: score >= 125 to trigger deeper investigation.

## Implementation Steps
1. Create experiments/data_utils.py
2. Create experiments/agent_structural.py (Agent 1)
3. Create experiments/agent_robustness.py (Agent 2)
4. Create experiments/agent_ml_discovery.py (Agent 3)
5. Create experiments/agent_unorthodox.py (Agent 4)
6. Create experiments/orchestrator.py
7. Test each agent independently
8. Run orchestrator
9. Integrate promising results into run_experiments.py
10. Update docs with findings
