# Research Scenarios Branch

**Branch:** `research-scenarios`  
**Based on:** `backend-only`  
**Purpose:** Validation framework for studying generative agent-based models — linking individual agent believability to emergent group coordination.

---

## Research Context

This branch supports the following research project:

> **Diagnosing the Believability–Validity Gap in LLM Multi-Agent Coordination**
> *(formerly: Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination)*

The goal is not to build new agent architectures but to apply a validation framework — grounded in agent-based modelling (ABM) theory — that distinguishes:

- **Micro-level validation:** Is each individual agent's behaviour believable and consistent with its persona?
- **Macro-level validation:** Does the group produce coherent, measurable emergent coordination outcomes?

This branch is built on the Park et al. (2023) generative-agent architecture. The scenario decision loop, however, does not invoke Park's full associative-memory stream and reflection pipeline directly; instead, memory and reflection are operationalised as **controlled, scenario-level modules** (a task-relevant episodic memory and a single-stage reflective synthesis) layered on top of the persona. This is a deliberate design choice that isolates the cognitive variable under test and strengthens internal validity for the ablation. What this branch adds is therefore (a) a controlled scenario layer, (b) controlled cognitive-module instantiations, and (c) a measurement framework. See `docs/DISCUSSION_NOTES_20260529.md` §3–§4 and §14 for the precise relationship to Park et al.

Important current caveat:

- the branch includes five architecture condition labels:
  `baseline`, `memory`, `memory_planning`, `full`, `full_llm_reflection`
- the experiment runner organises outputs by condition, seed, and persona sample
- behavioural gating is implemented in both Commons Dilemma and Information
  Consensus pipelines, including a weaker baseline that does not accumulate
  associative-memory traces during perception
- two scenarios are now fully implemented (Commons Dilemma, Information Consensus)
- the thesis is reframed around the *believability–validity gap* as the central
  finding; H1–H4 are supporting evidence; H5–H8 diagnostics are in development

---

## What Was Added

```
reverie/backend_server/
│
├── experiment_conditions.py      # Canonical architecture-condition definitions
├── experiment_runner.py          # Runs experiments programmatically — no manual prompts
├── measurement/
│   ├── micro.py                  # Per-agent metrics and context-aware believability proxies
│   └── macro.py                  # Group metrics, convergence, and stability summaries
│
├── scenarios/
│   ├── base_scenario.py           # Abstract interface all scenarios must implement
│   ├── commons_dilemma.py         # Scenario 1 — Shared Resource Management (implemented)
│   ├── task_assignment.py         # Scenario 2 — Collective Task Assignment (stub)
│   ├── information_consensus.py   # Scenario 3 — Information Consensus (implemented)
│   └── emergency_coordination.py  # Scenario 4 — Emergency Coordination (stub)
```

Changes to `reverie.py`:
- Added `self.scenario = None` to `ReverieServer.__init__`
- `start_server()` calls `self.scenario.step()` automatically after each simulation step
- added run metadata support for experiment manifests, seeds, selected personas,
  and LLM usage

## MRes Documentation

The repository now includes a dedicated docs folder:

- `docs/README.md`
- `docs/MRES_IMPLEMENTATION_PLAN.md`
- `docs/MRES_PROGRESS_LOG.md`
- `docs/TABLE1_IMPLEMENTATION_CHECKLIST.md`
- `docs/HUMAN_EVALUATION_PROTOCOL.md`
- `docs/EXPERIMENT_OUTPUT_SCHEMA.md`

If you are using this branch for the MRes project, read those documents
alongside this README.

---

## Setup

> This branch requires the `backend-only` setup. Complete those steps first.

```bash
# 1. Switch to this branch
git checkout research-scenarios

# 2. Activate your virtual environment
source .venv/bin/activate

# 3. Install dependencies (if not already done)
pip install -r requirements.txt

# 4. Make sure your .env file has your OpenAI key
#    OPENAI_API_KEY=sk-...
#    KEY_OWNER=your_name
```

---

## Running an Experiment

```bash
cd reverie/backend_server
python experiment_runner.py
```

This will:
1. Fork the configured base simulation (typically `base_the_ville_n25`)
2. Deterministically sample the configured agent subset if `persona_sample_size`
   is set
3. Run the Commons Dilemma scenario for the configured condition set
4. Export experiment logs, summaries, human-evaluation packets, and analysis
   outputs under `experiment_results/`

---

## Configuring the Experiment

Edit the `__main__` block at the bottom of `experiment_runner.py`:

```python
scenario = CommonsDilemma(
    initial_resource   = 1000,   # starting pool size (units)
    replenishment_rate = 50,     # units added to the pool each step
    max_request        = 100,    # max any single agent can request per step
    capacity           = 1000,   # hard upper bound on pool size
)

run_experiment_matrix(
    fork_sim_code   = "base_the_ville_n25",
    sim_code_prefix = "commons_experiment",
    scenario        = scenario,
    experimental_conditions = ["baseline", "memory", "memory_planning", "full"],
    n_steps         = 100,    # steps per trial
    n_trials        = 3,      # number of independent trials
    output_dir      = "experiment_results",
    persona_sample_size = 8,  # deterministic 5–10 agent study setup
    selection_seed  = 42,
    base_seed       = 20260430,
    export_human_eval = True,
    run_hypothesis_analysis = True,
)
```

---

## Scenario 1: Commons Dilemma (Implemented)

**Research rationale:** A shared resource pool tests whether agents coordinate
sustainably or deplete the commons — a classic collective action problem with
clear measurable outcomes at both micro and macro levels.

**Mechanism:**
- A resource pool starts at `initial_resource` units
- Each step, every agent is prompted with the pool state and asked how many units to request (0 – `max_request`)
- The agent responds based on its persona (traits, goals) plus the condition-gated controlled cognitive context (scenario-level episodic memory, plan, and reflection where enabled)
- Requests are granted proportionally if total demand exceeds availability
- The pool replenishes by `replenishment_rate` units each step
- If the pool reaches zero, the commons collapses and the simulation ends

**What gets logged per agent per step (micro):**
```json
{
  "step"     : 5,
  "time"     : "February 13, 2023, 00:50:00",
  "persona"  : "Isabella Rodriguez",
  "requested": 30,
  "granted"  : 28,
  "reasoning": "I want to keep enough for others since the cafe depends on community goodwill.",
  "memory_reference": "I remember that maintaining goodwill matters for my cafe.",
  "plan_reference": "I want to keep enough resources available for later work too.",
  "experimental_condition": "full",
  "parse_error": false,
  "fair_share": 16.667,
  "recent_memories": [
    "The town has suffered shortages before."
  ],
  "daily_goals": [
    "Preserve resources for the group"
  ]
}
```

**What gets logged per step (macro):**
```json
{
  "step"               : 5,
  "time"               : "February 13, 2023, 00:50:00",
  "resource_level_before": 870.0,
  "resource_level"     : 820.0,
  "total_requested"    : 110,
  "total_granted"      : 105,
  "coordinated"        : false,
  "oversubscription"   : 60.0,
  "sustainability_score": 0.82,
  "gini"               : 0.12,
  "collapsed"          : false
}
```

---

## Output Structure

After running, `experiment_results/` contains:

```
experiment_results/
└── commons_dilemma/
    ├── analysis/
    │   ├── feature_table.csv
    │   ├── hypothesis_report.json
    │   └── hypothesis_report.txt
    ├── experiment_config.json
    ├── matrix_results.json
    └── full/
        ├── all_results.json
        ├── condition_summary.json
        └── trial_0/
            ├── failure_traceability.json
            ├── human_eval_blind_key.json
            ├── human_eval_packets.jsonl
            ├── human_eval_ratings.csv
            ├── micro_log.json
            ├── macro_log.json
            ├── micro_summary.json
            ├── macro_summary.json
            └── run_manifest.json
```

### Micro summary example
```json
{
  "behavioural_consistency": {
    "Isabella Rodriguez": 0.78
  },
  "memory_coherence": {
    "Isabella Rodriguez": 0.64
  },
  "planning_plausibility": {
    "Isabella Rodriguez": 0.71
  },
  "composite_believability": {
    "Isabella Rodriguez": 0.72
  }
}
```

### Macro summary example
```json
{
  "sustainability_score" : 0.74,
  "coordination_score"   : 0.42,
  "coordination_success" : false,
  "convergence_step"     : null,
  "convergence_timeout"  : true,
  "collapse_step"        : null,
  "average_gini"         : 0.19,
  "demand_pressure"      : 1.31,
  "emergent_role_differentiation": {
    "normalized_role_entropy": 0.67
  },
  "total_steps"          : 100
}
```

---

## Measurement Framework

### Micro-level metrics (`measurement/micro.py`)

| Metric | Description |
|--------|-------------|
| `average_request` | Mean units requested per agent across all steps |
| `consistency_score` / `request_consistency` | 1 − coefficient_of_variation of requests (1 = perfectly consistent) |
| `cooperation_rate` | Fraction of steps where agent stayed within its fair share |
| `profile_alignment` | Lightweight overlap proxy between decision text and persona profile |
| `behavioural_consistency` | Composite automated proxy for stable, role-aligned behaviour |
| `memory_reference_rate` | Fraction of steps where the agent explicitly cited memory in its reasoning |
| `memory_coherence` | Context-aware proxy using memory opportunities, mentions, and relevance |
| `planning_reference_rate` | Fraction of steps where the agent explicitly linked the action to a goal or plan |
| `planning_plausibility` | Context-aware proxy using current goals/activity alignment |
| `planning_plausibility_rubric` | 1–5 rubric-like transform of planning plausibility |
| `response_naturalness` | Automated language-quality proxy with parse-error handling |
| `response_naturalness_proxy` | Lightweight heuristic proxy for reasoning quality |
| `composite_believability` | Canonical composite automated proxy across the current micro dimensions |
| `believability_proxy` | Backward-compatible alias for `composite_believability` |

### Macro-level metrics (`measurement/macro.py`)

| Metric | Description |
|--------|-------------|
| `sustainability_score` | Mean resource level as fraction of initial pool |
| `coordination_score` | Fraction of steps where total demand ≤ replenishment rate |
| `coordination_success` | Run-level success flag based on non-collapse and sufficient coordination |
| `convergence_step` / `convergence_speed` | First sustained coordination streak and its speed |
| `collapse_step` | Step at which pool hit zero, or `null` if it never collapsed |
| `average_gini` | Mean Gini coefficient of resource allocation per step |
| `demand_pressure` | Mean ratio of total demand to replenishment rate (>1 = unsustainable) |
| `emergent_role_differentiation` | Role-label and entropy proxy based on observed request strategies |
| `failure_traceability` | Structured critical-window summary for micro-to-macro breakdown review |
| `outcome_variance` | Coefficient-of-variation-style stability summary across trials |
| `coordination_success_rate` | Condition-level success summary across runs |

Important caveat:

- several micro metrics are currently **proxies**, not full implementations
  of the Table 1 mixed-method measures from the MRes plan
- see `docs/TABLE1_IMPLEMENTATION_CHECKLIST.md` for the exact coverage status

---

## Adding a New Scenario

1. Copy one of the existing stubs (e.g. `scenarios/task_assignment.py`)
2. Subclass `BaseScenario` and implement all abstract methods:
   - `setup(personas)` — initialise state
   - `step(personas, step_num, curr_time)` — process one simulation step
   - `get_micro_log()` — return per-agent log
   - `get_macro_log()` — return group-level log
   - `is_complete()` — return True when the scenario ends
3. Import and use it in `experiment_runner.py` the same way `CommonsDilemma` is used

---

## Available Base Simulations

| Name | Agents |
|------|--------|
| `base_the_ville_isabella_maria_klaus` | 3 agents |
| `base_the_ville_n25` | 25 agents |

> The runner now supports deterministic persona sub-sampling from the 25-agent
> world, which makes `5-10` agent experiments possible without creating a new
> base simulation.

---

## Branch Structure

```
main                  ← original Smallville with Django frontend
 └── backend-only     ← headless, no frontend required
      └── research-scenarios  ← this branch: scenario + measurement framework
```

## Current Dataset Status

| Dataset | Conditions | Trials | Status | Notes |
|---------|-----------|--------|--------|-------|
| `experiment_results_cd_primary/` | baseline, memory, memory_planning, full (CD) | 4×20=80 | ✅ Complete | Primary CD dataset |
| `experiment_results_ic_primary/` | baseline, memory, memory_planning, full (IC) | 4×10=40 | ✅ Complete | Primary IC dataset |
| `experiment_results_ic_llm_reflection/` | full_llm_reflection (IC) | 10 | ✅ Complete | Both fixes applied; saturation=58.5% (diverse) |
| `experiment_results_cd_llm_reflection/` | full_llm_reflection (CD) | 7/10 | ⏳ In progress | Both fixes applied; saturation=95.1% (focal-point norm) |
| `experiment_results_cd_llm_reflection/` | full_llm_reflection (CD) | 11 | ⚠️ Faulty — excluded | Missing persona description in reflection prompt; kept as reference only |

## Known Limitations

- `task_assignment` and `emergency_coordination` remain stubs
- human evaluation not yet collected (tooling ready; pending HREC confirmation)
- several Table 1 micro metrics are still automated proxies (no human ratings blended)
- H5 (discrepancy metric), H7 (early-warning classifier), and C4 (failure taxonomy)
  are planned but not yet implemented
- `full_llm_reflection` has 10 trials vs 20 for other CD conditions — unbalanced
  but defensible; framed as exploratory 5th condition in analysis
