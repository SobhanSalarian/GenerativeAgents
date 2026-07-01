# Experiment Results Data Dictionary

Complete reference for every file produced by the commons dilemma experiment runner.
Each entry describes the file's structure, every field, and its direct contribution
to the MRes thesis hypotheses (H1–H4).

---

## Folder Structure

```
experiment_results_cd_primary/
└── commons_dilemma/
    ├── experiment_config.json              ← single file, whole experiment
    ├── baseline/
    │   ├── all_results.json                ← aggregated across all 20 trials
    │   ├── condition_summary.json          ← statistics across all 20 trials
    │   └── trial_N/
    │       ├── run_manifest.json
    │       ├── micro_log.json
    │       ├── micro_summary.json
    │       ├── macro_log.json
    │       ├── macro_summary.json
    │       ├── agent_step_log.jsonl
    │       ├── cognitive_process_log.jsonl  ← present from memory_planning/trial_17+ and all full trials
    │       ├── failure_traceability.json
    │       ├── human_eval_packets.jsonl
    │       ├── human_eval_blind_key.json
    │       └── human_eval_ratings.csv
    ├── memory/          ← same structure as baseline/
    ├── memory_planning/ ← same structure as baseline/
    └── full/            ← same structure as baseline/
```

Conditions map to the four experimental arms:

| Folder | Condition | Cognitive modules active |
|---|---|---|
| `baseline/` | C1 | none |
| `memory/` | C2 | memory only |
| `memory_planning/` | C3 | memory + planning |
| `full/` | C4 | memory + planning + reflection |

---

## 1. `experiment_config.json`

**Location:** `commons_dilemma/experiment_config.json` (one file for the whole experiment)

**What it is:** The master configuration that was passed to `experiment_runner.py`
at the start of the run. Captures every parameter that governs the experiment,
making the setup fully reproducible.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `fork_sim_code` | string | Name of the Smallville fork used as the starting state (`base_the_ville_n25`) |
| `sim_code_prefix` | string | Prefix applied to every trial's storage folder name |
| `scenario` | string | Scenario identifier (`commons_dilemma`) |
| `scenario_parameters.initial_resource` | int | Pool starts at 1000 credits |
| `scenario_parameters.replenishment_rate` | int | Pool replenishes by 50 credits each step |
| `scenario_parameters.max_request` | int | Maximum any agent can request per step (100) |
| `scenario_parameters.capacity` | int | Pool hard ceiling (1000) |
| `experimental_conditions` | list | The four conditions run in order |
| `n_steps` | int | Steps per trial (100) |
| `n_trials` | int | Trials per condition (20) |
| `persona_sample_size` | int | Agents per trial (8) |
| `selection_seed` | int | Seed for persona sampling (42) — same 8 agents every trial |
| `base_seed` | int | Starting seed; incremented by 1 per trial for reproducibility |
| `export_human_eval` | bool | Whether to generate human evaluation packets |

**Thesis contribution:** Cited in the Methods section to document the experimental
setup. Confirms the 4 × 20 × 100 design (conditions × trials × steps). The
`scenario_parameters` values define the sustainability threshold used in H1/H2
analysis.

---

## 2. `run_manifest.json`

**Location:** `<condition>/trial_N/run_manifest.json`

**What it is:** A per-trial record written after the trial completes. Captures
exactly what ran — the personas selected, the seed used, the final simulation
time, and LLM usage costs.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `fork_sim_code` | string | Smallville fork used |
| `sim_code` | string | Unique storage folder name for this trial |
| `experimental_condition` | string | Which of the four conditions this trial belongs to |
| `selected_personas` | list | The 8 agent names used (same across all trials due to fixed seed) |
| `maze_name` | string | Smallville world map name |
| `persona_count` | int | Number of agents (8) |
| `run_seed` | int | The specific seed used for this trial |
| `start_time` | string | Simulated world time at trial start |
| `curr_time` | string | Simulated world time at trial end |
| `step` | int | Total steps completed |
| `llm_usage.chat_requests` | int | Total LLM API calls made in this trial |
| `llm_usage.embedding_requests` | int | Total embedding API calls |
| `llm_usage.chat_prompt_tokens` | int | Input tokens consumed |
| `llm_usage.chat_completion_tokens` | int | Output tokens generated |
| `llm_usage.chat_total_tokens` | int | Total tokens (input + output) |
| `llm_usage.estimated_cost_usd` | float | Estimated API cost for this trial |
| `llm_usage.models` | dict | Per-model breakdown of the above |

**Thesis contribution:** Used to verify trial integrity (confirms `step: 100`
for completed trials). The `llm_usage` section documents API cost for the
thesis Methods section and provides evidence of scale (e.g. ~832 calls/trial
for baseline, ~1,000+ for memory_planning and full).

---

## 3. `micro_log.json`

**Location:** `<condition>/trial_N/micro_log.json`

**What it is:** The primary raw data file. One JSON entry per agent per step —
800 entries per trial (100 steps × 8 agents). Records every individual
resource-allocation decision with full context.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `step` | int | Simulation step (0–99) |
| `time` | string | Simulated wall-clock time of this decision |
| `persona` | string | Agent name |
| `requested` | int | Credits the agent requested this step |
| `reasoning` | string | Agent's free-text explanation of its decision (LLM output) |
| `memory_reference` | string | Memory the agent cited when making the decision (empty in baseline/memory-disabled conditions) |
| `plan_reference` | string | How the decision fits the agent's current goals (empty when planning disabled) |
| `experimental_condition` | string | Condition label for filtering |
| `parse_error` | bool | `true` if the LLM response could not be parsed; the agent received 0 credits |
| `resource_level_before` | float | Pool level at the start of this step, before any allocations |
| `pool_percent_before` | float | Pool level as a percentage of the 1000-credit maximum |
| `fair_share` | float | Equal share if the pool were divided evenly: `resource_level / n_agents` |
| `request_ratio_to_fair_share` | float | `requested / fair_share` — values > 1 mean above-fair-share requests |
| `granted` | int | Credits actually allocated (≤ requested; capped by pool availability) |
| `persona_profile` | string | Full agent persona text injected into the prompt |
| `recent_memories` | list | Scenario-specific episodic memories injected into the agent's prompt at this step (empty when memory disabled). Grows step by step within a trial — empty at step 0, accumulates thereafter. Stored as a sliding window of the last 20 entries; last 5 injected into the prompt. Reset to `[]` at the start of each trial. |
| `memory_scope` | string | `"none"`, `"scenario_episodic"`, or similar — describes what memory was available |
| `memory_context_available` | bool | Whether any scenario memories were actually injected |
| `planning_context_available` | bool | Whether planning goals were injected |
| `daily_goals` | list | Up to 3 current daily goals injected from the Park et al. planning module (empty when planning disabled) |
| `scenario_reflections` | list | Coordination-level reflection strings injected (empty unless `use_reflection: true` and reflections exist) |
| `condition_capabilities` | dict | `{use_memory, use_planning, use_reflection}` — the active cognitive modules for this agent in this condition |

**Thesis contribution:** This is the primary dataset for all four hypotheses:
- **H1** (memory → coordination): Compare `requested` and `coordination` across conditions using `memory_context_available` and `scenario_reflections` as evidence of what cognitive context was active
- **H2** (sustainability): `resource_level_before` and `granted` track pool depletion over time
- **H3** (planning plausibility): `plan_reference` vs `daily_goals` is the raw input for human rater scoring
- **H4** (believability): `reasoning`, `memory_reference`, and `plan_reference` are the text inputs for human rater believability scoring

---

## 4. `micro_summary.json`

**Location:** `<condition>/trial_N/micro_summary.json`

**What it is:** Per-agent aggregated statistics computed from `micro_log.json`.
One summary for the whole trial, broken down by agent.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `average_request` | dict | Mean credits requested per step, per agent |
| `consistency_score` | dict | How consistently each agent requests the same amount (0–1; 1 = perfectly consistent) |
| `request_consistency` | dict | Alias for `consistency_score` |
| `cooperation_rate` | dict | Fraction of steps where the agent requested ≤ fair share (0 = never cooperated, 1 = always) |
| `profile_alignment` | dict | Cosine similarity between the agent's request vector and a "cooperative" reference vector |
| `behavioural_consistency` | dict | Stability of the agent's request pattern across the trial (TF-IDF based) |
| `behavioural_consistency_band` | dict | Categorical label: `"low"`, `"medium"`, `"high"` |
| `memory_reference_rate` | dict | Fraction of steps where the agent produced a non-empty `memory_reference` |
| `memory_reference_relevance` | dict | Average relevance score of memory references (0–1) |
| `memory_coherence` | dict | Combined score: reference rate × relevance (input to H4 human scoring) |
| `plan_reference_rate` | dict | Fraction of steps where the agent produced a non-empty `plan_reference` |
| `plan_reference_relevance` | dict | Relevance of plan references to the injected `daily_goals` |
| `planning_plausibility` | dict | Combined score: plan reference rate × relevance (input to H3/H4 scoring) |
| `llm_judges_used` | bool | Whether LLM-based relevance scoring was active (requires valid API key) |

**Thesis contribution:**
- `cooperation_rate` feeds H1 and H2 statistical tests (Mann-Whitney U, Kruskal-Wallis)
- `memory_coherence` is the quantitative proxy for H4 memory believability
- `planning_plausibility` is the quantitative proxy for H3 planning plausibility
- `behavioural_consistency` provides evidence for H4 agent coherence claims

---

## 5. `macro_log.json`

**Location:** `<condition>/trial_N/macro_log.json`

**What it is:** Pool-level time series. One entry per step — 100 entries per trial.
Records the collective outcome at each round rather than individual decisions.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `step` | int | Simulation step (0–99) |
| `time` | string | Simulated wall-clock time |
| `resource_level_before` | float | Pool level at the start of this step |
| `resource_level` | float | Pool level after all allocations and replenishment |
| `total_requested` | int | Sum of all 8 agents' requests this step |
| `total_granted` | int | Sum of all 8 agents' granted amounts (may be < total_requested if pool too low) |
| `fair_share` | float | `resource_level_before / n_agents` |
| `oversubscription` | int | `max(0, total_requested - replenishment_rate)` — excess demand above sustainable level |
| `coordinated` | bool | `true` if `total_requested ≤ replenishment_rate (50)` — the coordination threshold |
| `sustainability_score` | float | Per-step pool health: `resource_level / initial_resource`. Each step produces one value; this is the raw value for that step. |
| `gini` | float | Gini coefficient of grant distribution across agents (0 = perfectly equal, 1 = fully unequal) |
| `collapsed` | bool | `true` if `resource_level` dropped to 0 |

**Thesis contribution:**
- `coordinated` is the binary coordination signal for H1 (does memory enable coordination?)
- `sustainability_score` over time is the core H2 metric (does memory improve sustainability?)
- `gini` tracks inequality in resource allocation — relevant for the commons dilemma framing
- `resource_level` time series plotted in the Results chapter to show pool dynamics across conditions

---

## 6. `macro_summary.json`

**Location:** `<condition>/trial_N/macro_summary.json`

**What it is:** Trial-level aggregate of `macro_log.json`. Condenses the 100-step
time series into the key outcome metrics used in hypothesis testing.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `sustainability_score` | float | **Mean** of per-step `(resource_level / initial_resource)` across all 100 steps — average pool health throughout the trial. This is NOT the final pool state; the final pool state is separately available as `final_resource_level`. (Primary H2 metric) |
| `coordination_score` | float | Fraction of steps where `coordinated == true` (0–1; primary H1 metric) |
| `coordination_score_band` | string | `"low"` / `"medium"` / `"high"` categorical label |
| `coordination_success` | bool | `true` if `coordination_score > 0.5` |
| `collapse_step` | int or null | Step at which pool first reached 0; `null` if no collapse |
| `average_gini` | float | Mean Gini coefficient across all 100 steps |
| `demand_pressure` | float | Mean `total_requested / replenishment_rate` — how much agents over-demanded on average |
| `convergence_step` | int or null | First step at which agents began consistently coordinating; `null` if never |
| `convergence_speed` | int | Steps to first convergence (100 = never converged, lower = faster) |
| `convergence_timeout` | bool | `true` if convergence never occurred within 100 steps |
| `emergent_role_differentiation.roles_by_persona` | dict | Each agent labelled `"competitor"`, `"balancer"`, or `"free_rider"` based on cooperation rate |
| `emergent_role_differentiation.role_counts` | dict | Count of each role |
| `emergent_role_differentiation.role_entropy` | float | Shannon entropy of role distribution — high = diverse roles, low = homogeneous |
| `failure_traceability` | dict | See `failure_traceability.json` below — embedded copy |

**Thesis contribution:** This is the primary input to the statistical analysis pipeline:
- `coordination_score` → H1 Mann-Whitney U and Kruskal-Wallis tests across conditions
- `sustainability_score` → H2 OLS regression (condition as predictor)
- `demand_pressure` → descriptive measure of collective behaviour
- `convergence_step` → speed of coordination emergence, relevant to H1 discussion
- `emergent_role_differentiation` → qualitative analysis of agent diversity across conditions

---

## 7. `agent_step_log.jsonl`

**Location:** `<condition>/trial_N/agent_step_log.jsonl`

**What it is:** Deep internal state log from the Park et al. cognitive architecture.
One JSON line per agent per step — 800 entries per trial. Captures the Smallville
simulation internals (memory counts, planning state, movement, action) rather than
the scenario decision itself.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `trial` | int | Trial number |
| `step` | int | Simulation step |
| `sim_time` | string | Simulated time in full datetime format |
| `condition` | string | Experimental condition |
| `persona` | string | Agent name |
| `cognitive_modules_active` | dict | `{memory, planning, reflection}` booleans |
| `perception.new_events_stored` | int | How many new world events entered memory this step |
| `memory.total_events_in_memory` | int | Running count of episodic memories |
| `memory.total_thoughts_in_memory` | int | Running count of reflection thoughts |
| `memory.importance_trigger_curr` | int | Cumulative importance score; reflection triggers at threshold |
| `memory.reflection_triggered` | bool | Whether a reflection was generated this step |
| `planning.daily_goals` | list | Active daily goals at this step |
| `planning.current_scheduled_task` | string | Current task from the hourly schedule |
| `planning.current_scheduled_duration_min` | int | Duration allocated to that task |
| `action.act_address` | string | Full Smallville location string (world:sector:arena:object) |
| `action.act_description` | string | Natural language description of the agent's action |
| `action.act_pronunciatio` | string | Emoji representation of the action |
| `action.chatting_with` | string or null | Name of agent being conversed with, if any |
| `position.curr_tile` | list | `[x, y]` tile coordinates on the Smallville map |

**Thesis contribution:**
- Verifies Park et al. cognitive module activation (confirms memory, planning, reflection
  are actually firing as expected per condition)
- `memory.reflection_triggered` confirms when reflections were generated
- `action.chatting_with` shows spontaneous agent conversations — relevant to
  understanding the higher API call count in memory_planning and full conditions
- Used for process transparency: evidence that the simulation was running correctly
  beyond the scenario-level decisions

---

## 8. `cognitive_process_log.jsonl`

**Location:** `<condition>/trial_N/cognitive_process_log.jsonl`

**Note:** Present from `memory_planning/trial_17` and all `full` condition trials
onwards (added mid-experiment). Earlier trials do not have this file.

**What it is:** A real-time transcript of every LLM call made by the Park et al.
cognitive modules during the trial. One JSON line per call. Captures all internal
reasoning — not just the commons dilemma decisions but every poignancy rating,
schedule generation, navigation choice, and conversation.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `timestamp` | string | Wall-clock time when the LLM call was made (ISO 8601) |
| `call_type` | string | Category of cognitive process (see table below) |
| `prompt` | string | Full prompt sent to the LLM |
| `response` | string | Raw LLM response text |

**Call types:**

| `call_type` | What it represents |
|---|---|
| `commons_decision` | The scenario resource-allocation decision — the research data |
| `event_poignancy` | Park et al. memory importance scoring for world events (1–10) |
| `conversation_poignancy` | Importance scoring for agent-to-agent conversations |
| `task_decomp` | 5-minute subtask breakdown for daily activities |
| `daily_planning` | Hourly schedule generation at agent wake-up |
| `object_state` | Object state description (e.g. "desk is covered with papers") |
| `emoji_conversion` | Action-to-emoji mapping for frontend visualisation |
| `action_sector` | Navigation: which sector the agent moves to |
| `action_arena` | Navigation: which arena within the sector |
| `conversation_generation` | Spontaneous agent-to-agent dialogue |
| `event_triple` | Subject–predicate–object encoding of world events |
| `other` | Any call not matching the above patterns |

**Thesis contribution:**
- Process transparency: enables verification that the cognitive architecture
  behaved as expected (e.g. confirms that `commons_decision` calls were made
  every step, that planning calls fired at wake-up)
- Research reproducibility: full prompt/response pairs are available for
  methodological audit
- Qualitative analysis: prompts and responses for `commons_decision` entries
  can be used to illustrate agent reasoning in the Results/Discussion chapter

**Important filter:** To extract only the research-relevant calls, filter by
`call_type == "commons_decision"`. All other call types are Smallville world
simulation internals.

---

## 9. `failure_traceability.json`

**Location:** `<condition>/trial_N/failure_traceability.json`

**What it is:** A structured diagnostic report generated after each trial
analysing why coordination succeeded or failed. Also embedded inside
`macro_summary.json`.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `failure_detected` | bool | `true` if the trial failed to achieve coordination |
| `critical_step` | int | The step at which failure was first diagnosed |
| `likely_causes` | list | String labels for identified failure causes (see below) |
| `agent_contributions.{name}.requested` | int | Total credits requested by this agent across the trial |
| `agent_contributions.{name}.granted` | int | Total credits granted |
| `agent_contributions.{name}.parse_errors` | int | Steps where the LLM returned unparseable output |
| `agent_contributions.{name}.memory_references` | int | Steps where the agent cited a memory |
| `agent_contributions.{name}.plan_references` | int | Steps where the agent cited a plan |

**Likely cause labels:**

| Label | Meaning |
|---|---|
| `collective_over_demand` | Group total requests consistently exceeded replenishment |
| `allocation_inequality` | High Gini coefficient — a few agents took disproportionate share |
| `weak_memory_use` | Memory-enabled agents rarely cited memories in their reasoning |
| `weak_plan_grounding` | Planning-enabled agents rarely cited goals in their reasoning |
| `parse_errors` | LLM output failures led to agents receiving 0 credits |

**Thesis contribution:**
- Provides qualitative evidence for why coordination failed in specific trials
- `weak_memory_use` and `weak_plan_grounding` flags are quantitative evidence
  for the H3/H4 analysis (when agents have memory/planning but don't use it)
- `agent_contributions` reveals which specific agents drove over-demand —
  relevant to the emergent role differentiation discussion

---

## 10. `human_eval_packets.jsonl`

**Location:** `<condition>/trial_N/human_eval_packets.jsonl`

**What it is:** Blinded decision vignettes prepared for human raters. Each packet
presents one agent's decision at one of three time points (early/middle/late) with
all identifying information replaced by anonymous IDs.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `packet_id` | string | Unique hash identifier for this decision vignette |
| `packet_type` | string | Always `"decision_review"` |
| `scenario` | string | `"commons_dilemma"` |
| `trial` | int | Source trial number |
| `step` | int | Source step (0 = early, 50 = middle, 99 = late) |
| `phase` | string | `"early"`, `"middle"`, or `"late"` |
| `time` | string | Simulated time of this decision |
| `blinded_agent_id` | string | Anonymised agent ID (e.g. `agent_3f962f51`) — real name hidden |
| `persona_background` | string | Agent backstory with name replaced by blinded ID |
| `local_context.resource_level_before` | float | Pool level visible to the agent |
| `local_context.pool_percent_before` | float | Pool health as percentage |
| `local_context.fair_share` | float | Equal-share reference point |
| `local_context.daily_goals` | list | Active goals at decision time (empty in baseline) |
| `local_context.recent_memories` | list | Memories injected (empty in baseline/memory-disabled) |
| `local_context.macro_state` | dict | Group-level pool state visible to all agents |
| `decision.requested` | int | Credits the agent requested |
| `decision.granted` | int | Credits actually received |
| `decision.reasoning` | string | Agent's free-text reasoning |
| `decision.memory_reference` | string | Memory cited (empty if none) |
| `decision.plan_reference` | string | Plan cited (empty if none) |

**Thesis contribution:** These packets are the direct input to human raters for
H3 and H4 scoring. Blinding ensures raters cannot identify the experimental
condition, preventing bias. Each trial produces 24 packets (8 agents × 3 phases).

---

## 11. `human_eval_blind_key.json`

**Location:** `<condition>/trial_N/human_eval_blind_key.json`

**What it is:** The unblinding lookup table — maps each anonymised `packet_id`
and `blinded_agent_id` back to the real agent name, experimental condition,
and trial. **Do not share with raters.**

**Fields:**

| Field | Type | Description |
|---|---|---|
| `{packet_id}.scenario` | string | Scenario name |
| `{packet_id}.trial` | int | Trial number |
| `{packet_id}.persona_name` | string | Real agent name (hidden from raters) |
| `{packet_id}.experimental_condition` | string | The actual condition (hidden from raters) |
| `{packet_id}.sim_code` | string | Full storage folder name for traceability |

**Thesis contribution:** Used after ratings are collected to unblind results and
assign condition labels. Essential for the H3/H4 statistical analysis (you cannot
test whether condition affects believability without knowing which condition each
rated decision came from).

---

## 12. `human_eval_ratings.csv`

**Location:** `<condition>/trial_N/human_eval_ratings.csv`

**What it is:** The rating collection spreadsheet — pre-populated with one row
per decision packet, ready for human raters to fill in scores. Ships empty;
raters add their scores in the numeric columns.

**Columns:**

| Column | Type | Description |
|---|---|---|
| `packet_id` | string | Links back to `human_eval_packets.jsonl` |
| `blinded_agent_id` | string | Anonymised agent ID |
| `scenario` | string | `"commons_dilemma"` |
| `trial` | int | Source trial |
| `step` | int | Source step |
| `phase` | string | `"early"`, `"middle"`, or `"late"` |
| `rater_id` | string | **Filled by rater** — unique identifier for the rater |
| `behavioural_consistency` | int (1–5) | **Filled by rater** — does this agent behave consistently with its persona? |
| `memory_coherence` | int (1–5) | **Filled by rater** — does the memory reference make sense given the agent's history? |
| `planning_plausibility` | int (1–5) | **Filled by rater** — does the plan reference connect plausibly to the stated goals? |
| `response_naturalness` | int (1–5) | **Filled by rater** — does the reasoning read as natural human-like language? |
| `believable_yes_no` | bool | **Filled by rater** — overall: is this agent believable? |
| `notes` | string | **Filled by rater** — optional free-text comments |

**Thesis contribution:** Direct H3 and H4 data. After collection, ratings are
ingested via `rating_ingestion.py`, inter-rater reliability is computed (Krippendorff's
alpha), and blinded scores are merged with condition labels from
`human_eval_blind_key.json` for statistical analysis.

---

## 13. `all_results.json`

**Location:** `<condition>/all_results.json`

**What it is:** A flat list of 20 entries — one per completed trial — each
containing the trial's `macro_summary` and `micro_summary` merged together.
Generated automatically when the last trial of a condition finishes.

**Structure:** Each entry is a dict with:
- All fields from `run_manifest.json` (trial identity)
- `micro_summary` dict embedded in full
- `macro_summary` dict embedded in full (including `failure_traceability`)

**Thesis contribution:** This is the primary input to `experiment_analysis.py`.
Loading this single file gives you the complete 20-trial dataset for one condition,
ready for Mann-Whitney U tests, OLS regression, and Kruskal-Wallis comparisons
across conditions. No need to loop over individual trial folders.

---

## 14. `condition_summary.json`

**Location:** `<condition>/condition_summary.json`

**What it is:** Cross-trial aggregate statistics for one condition. Summarises
all 20 trials into a single object with means, standard deviations, and
categorical outcome rates.

**Key fields:**

| Field | Description |
|---|---|
| `trial_count` | Number of completed trials (should be 20) |
| `coordination_success_rate` | Fraction of trials where `coordination_success == true` |
| `collapse_rate` | Fraction of trials where pool collapsed to 0 |
| `convergence_timeout_rate` | Fraction of trials where agents never converged |
| `metrics.{metric}.mean` | Mean across 20 trials for each key metric |
| `metrics.{metric}.std` | Standard deviation |
| `metrics.{metric}.min` / `.max` | Range |
| `outcome_variance` | Per-metric variance scores |
| `variance_bands` | Categorical variance labels (`"low"`, `"medium"`, `"high"`) |

**Thesis contribution:** Used to generate the condition-level summary table in
the Results chapter. `metrics.coordination_score.mean` and
`metrics.sustainability_score.mean` are the headline numbers reported per
condition. `coordination_success_rate` directly addresses H1.

---

## Summary: Which Files Answer Which Hypotheses

| Hypothesis | Primary files | Key fields |
|---|---|---|
| **H1** Memory → coordination | `macro_summary.json`, `condition_summary.json`, `all_results.json` | `coordination_score`, `coordination_success_rate` |
| **H2** Memory → sustainability | `macro_log.json`, `macro_summary.json`, `condition_summary.json` | `sustainability_score`, `resource_level` time series |
| **H3** Planning plausibility | `micro_log.json`, `micro_summary.json`, `human_eval_packets.jsonl`, `human_eval_ratings.csv` | `plan_reference`, `daily_goals`, `planning_plausibility` |
| **H4** Believability / coherence | `micro_log.json`, `micro_summary.json`, `human_eval_packets.jsonl`, `human_eval_ratings.csv` | `reasoning`, `memory_reference`, `behavioural_consistency`, `memory_coherence` |
| **Process audit** | `cognitive_process_log.jsonl`, `agent_step_log.jsonl` | Full prompt/response pairs, cognitive module activation |
| **Failure diagnosis** | `failure_traceability.json`, `macro_summary.json` | `likely_causes`, `agent_contributions` |
