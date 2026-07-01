# Experiment Output Schema

This document describes the output files currently produced by the experiment
runner.

## Current Directory Layout

The runner currently writes outputs under:

```text
experiment_results_cd_primary/<scenario>/<condition>/
```

Each trial lives in:

```text
experiment_results_cd_primary/<scenario>/<condition>/trial_<n>/
```

There is also a scenario-level matrix file:

```text
experiment_results_cd_primary/<scenario>/matrix_results.json
```

Older pilot runs may exist under `experiment_results/`. Those runs used the
pre-fix generic-memory context and should not be mixed with the corrected
scenario-memory outputs.

## Per-Trial Files

### `micro_log.json`

Produced by:
- scenario `save_results(...)`

Purpose:
- stores agent-level decisions for each step

Current commons-dilemma fields include:
- `step`
- `time`
- `persona`
- `requested`
- `granted`
- `reasoning`
- `memory_reference`
- `plan_reference`
- `experimental_condition`
- `parse_error`
- `resource_level_before`
- `pool_percent_before`
- `fair_share`
- `request_ratio_to_fair_share`
- `persona_profile`
- `recent_memories`
- `memory_scope`
- `memory_context_available`
- `planning_context_available`
- `daily_goals`
- `current_activity`
- `action_address`
- `scenario_reflections`
- `condition_capabilities`

For `commons_dilemma`, `recent_memories` now means scenario-specific episodic
memory from prior resource-allocation rounds. Examples include group demand
relative to replenishment, pool changes, fair-share deviations, and whether
the group exceeded the replenishment limit. `memory_scope` is
`scenario_episodic` when memory is enabled and `none` for baseline.

### `macro_log.json`

Produced by:
- scenario `save_results(...)`

Purpose:
- stores group-level scenario state for each step

Current commons-dilemma fields include:
- `step`
- `time`
- `resource_level`
- `total_requested`
- `total_granted`
- `sustainability_score`
- `gini`
- `collapsed`

### `micro_summary.json`

Produced by:
- `compute_micro_summary(...)`

Purpose:
- per-agent micro-level summary metrics

Current fields include:
- `average_request`
- `consistency_score`
- `behavioural_consistency`
- `cooperation_rate`
- `memory_reference_rate`
- `planning_reference_rate`
- `response_naturalness_proxy`
- `believability_proxy`

### `macro_summary.json`

Produced by:
- `compute_macro_summary(...)`

Purpose:
- per-trial macro-level summary metrics

Current fields include:
- `sustainability_score`
- `coordination_score`
- `coordination_score_band`
- `coordination_success`
- `collapse_step`
- `average_gini`
- `demand_pressure`
- `convergence_step`
- `convergence_speed`
- `convergence_timeout`
- `emergent_role_differentiation`
- `failure_traceability`
- `total_steps`
- `final_resource_level`

### `run_manifest.json`

Produced by:
- `ReverieServer.get_run_manifest()`
- trial metadata update in `experiment_runner.py`

Purpose:
- stores basic experimental metadata for the run

Current fields include:
- `fork_sim_code`
- `sim_code`
- `experimental_condition`
- `selected_personas`
- `maze_name`
- `persona_count`
- `run_seed`
- `start_time`
- `curr_time`
- `step`
- `llm_usage`
- `scenario`
- `trial`
- `output_dir`
- `selection_strategy`
- `selection_seed`
- `base_seed`
- `trial_seed`

## Condition-Level Files

### `all_results.json`

Purpose:
- stores the list of all per-trial summaries for one condition within one
  scenario

### `condition_summary.json`

Purpose:
- stores aggregated macro statistics across trials for one condition

Current fields include:
- `trial_count`
- `collapsed_runs`
- `collapse_rate`
- `mean_collapse_step`
- `coordination_success_rate`
- `coordination_success_band`
- `convergence_timeout_rate`
- `outcome_variance`
- `variance_bands`
- `failure_modes`
- `metrics`
- `scenario`
- `experimental_condition`

## Additional Per-Trial Files

### `failure_traceability.json`

Purpose:
- analyst-facing summary of the likely micro-to-macro causes around the run's
  critical step

### `human_eval_packets.jsonl`

Purpose:
- blinded decision-review packets for human raters

### `human_eval_blind_key.json`

Purpose:
- researcher-only mapping from packet IDs back to true persona and condition

### `human_eval_ratings.csv`

Purpose:
- empty rater template with rubric columns for behavioural consistency, memory
  coherence, planning plausibility, and response naturalness

## Scenario-Level Files

### `matrix_results.json`

Purpose:
- stores condition-keyed results across the experiment matrix for one scenario

### `experiment_config.json`

Purpose:
- stores the scenario parameters, condition list, seed settings, and persona
  selection strategy used for the matrix run

### `analysis/feature_table.csv`

Purpose:
- flat record-per-trial table for downstream statistical analysis

## Known Limitations

- output schemas are not yet frozen
- some metric fields are still automated proxies, not final thesis measures
- only the commons-dilemma scenario currently exercises the full export and
  measurement stack
