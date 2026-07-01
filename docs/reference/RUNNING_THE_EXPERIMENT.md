# Running the Experiment: Step-by-Step Guide

This guide covers everything from a fresh clone to a completed multi-condition
experiment run, including output inspection, human-rating ingestion, and the
hypothesis analysis pipeline.

---

## Prerequisites

- Python 3.10
- An OpenAI API key with access to `gpt-4o-mini` and `text-embedding-3-small`
- The `base_the_ville_n25` fork world present under
  `environment/frontend_server/storage/` (already included in the repo)

---

## Part 1 — One-time Setup

### Step 1. Navigate to the repository

```bash
cd /mnt/shared/Sayedali/Mres_demo
```

### Step 2. Create and activate a virtual environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

### Step 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4. Create `utils.py`

The backend server requires a `utils.py` file in
`reverie/backend_server/` that holds your API key and path constants.
This file is git-ignored and must be created manually.

Create the file at `reverie/backend_server/utils.py` with this content:

```python
# Copy and paste your OpenAI API key
openai_api_key = "<Your OpenAI API Key>"
# Your name (used for cost tracking)
key_owner = "<Your Name>"

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix    = f"{maze_assets_loc}/the_ville/matrix"
env_visuals   = f"{maze_assets_loc}/the_ville/visuals"

fs_storage      = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

collision_block_id = "32125"

debug = True
```

Replace `<Your OpenAI API Key>` and `<Your Name>` with real values.

### Step 5. (Optional) Override model and temperature via environment variables

The defaults are `gpt-4o-mini` for chat and `text-embedding-3-small` for
embeddings. To override:

```bash
export OPENAI_CHAT_MODEL="gpt-4o-mini"       # or gpt-4o, gpt-4-turbo, etc.
export OPENAI_EMBED_MODEL="text-embedding-3-small"
export OPENAI_CHAT_TEMPERATURE="0.7"         # omit to use model default
export OPENAI_CHAT_SEED="42"                 # global default seed (overridden per trial)
```

---

## Part 2 — Running the Headless Experiment

The experiment runner is fully headless — no browser or frontend server
required. All output is written to disk.

### Step 6. Navigate to the backend server directory

The runner must be executed from `reverie/backend_server/` so that relative
imports resolve correctly.

```bash
cd reverie/backend_server
```

### Step 7. Run the full experiment matrix

```bash
python experiment_runner.py
```

This executes the `__main__` block, which runs:
- **4 conditions**: `baseline`, `memory`, `memory_planning`, `full`
- **20 trials** per condition (80 trials total)
- **8 personas** sampled deterministically from `base_the_ville_n25`
- **100 steps** per trial (or fewer if the resource pool collapses early)
- Hypothesis analysis (H1–H4) automatically after all conditions complete

Expected runtime: several hours depending on OpenAI API latency and whether
you use `gpt-4o-mini` (faster) or `gpt-4o` (more capable but slower).

The current default run writes to:

```text
experiment_results_cd_primary/
```

and uses simulation names beginning with:

```text
commons_experiment_scenario_memory
```

This separates corrected scenario-memory data from older pilot outputs under
`experiment_results/`.

### Simulation timing note

The base world (`base_the_ville_n25`) starts at `09:00:00` on February 13,
2023. With `sec_per_step = 10`, all 100 commons-dilemma rounds complete within
17 simulated minutes (09:00–09:17). This places all decisions during morning
waking hours — all 8 personas wake between 05:00–08:00 — so the planning
context (daily goals generated at wake-up) is coherent with the timing of
resource decisions.

Do not change `sec_per_step` to 86400 without first refactoring the new-day
detection in `persona.py`: doing so causes daily re-planning to fire every
step, breaking the Park et al. planning module.

### Prompt design note

The commons-dilemma prompt uses the following design choices, each with an
academic rationale:

- **"community fund / credits"** rather than abstract "resource pool / units"
  — grounds the resource in the community context
- **Fair-share anchor** — the prompt tells agents what an equal share would be
  (`replenishment_rate / n_agents ≈ 6.3 credits`), matching standard
  Ostrom-inspired ABM practice
- **Personal stakes sentence** — one sentence links the resource to the agent's
  work and goals before the decision question
- **Example amount = 6** (≈ fair share) — prevents the LLM from anchoring on
  an unrealistically high example

### Scenario-memory validity note

The commons-dilemma memory condition uses task-relevant episodic memories from
prior resource-allocation rounds. It does not use generic Smallville world
memories such as `bed is idle` or `desk is idle` as the scenario memory
context.

This was changed after pilot inspection showed that generic recent memories
were dominated by low-level room/object states. For this research plan,
memory coherence is intended to measure appropriate use of prior
coordination-task interactions, so the current implementation records and
injects memories such as:

- how much the group requested relative to the replenishment rate
- how the pool changed after a round
- whether demand exceeded replenishment
- each agent's request relative to fair share
- which agents requested above or below fair share

### Step 7a. Run a quick smoke test first (recommended)

Before committing to 80 full trials, verify the pipeline works end to end
with a single short trial:

```python
# run_smoke_test.py  (create this in reverie/backend_server/)
from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment

scenario = CommonsDilemma(
    initial_resource=1000,
    replenishment_rate=50,
    max_request=100,
    capacity=1000,
)

run_experiment(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="smoke_test",
    scenario=scenario,
    experimental_condition="full",
    n_steps=5,
    n_trials=1,
    output_dir="smoke_test_results",
    persona_sample_size=3,
    export_human_eval=True,
)
```

```bash
python run_smoke_test.py
```

If `smoke_test_results/commons_dilemma/full/trial_0/micro_summary.json`
exists and contains believability scores, the pipeline is working.

---

## Part 3 — Understanding the Output

After the run, `experiment_results_cd_primary/` has this structure:

```
experiment_results_cd_primary/
  commons_dilemma/
    experiment_config.json          ← full run configuration
    matrix_results.json             ← all condition summaries combined
    analysis/
      hypothesis_report.json        ← H1–H4 test results
      hypothesis_report.txt         ← human-readable report
      feature_table.csv             ← flat table for downstream modelling

    baseline/
      condition_summary.json        ← aggregated across 20 trials
      all_results.json              ← all 20 trial results combined
      trial_0/
        micro_summary.json          ← per-agent believability scores
        macro_summary.json          ← pool-level coordination metrics
        failure_traceability.json   ← breakdown analysis if collapsed
        run_manifest.json           ← reproducibility metadata
        human_eval_packets.jsonl    ← blinded decision excerpts for raters
        human_eval_ratings.csv      ← empty rating template for raters
        human_eval_blind_key.json   ← de-blinding map (keep confidential)
      trial_1/ ...
      trial_19/

    memory/          ← same structure
    memory_planning/ ← same structure
    full/            ← same structure
```

### Key files to check after a run

| File | What to look at |
|---|---|
| `micro_summary.json` | `composite_believability` per agent (0–1); `llm_judges_used` flag |
| `macro_summary.json` | `coordination_success`, `convergence_step`, `collapse_step` |
| `condition_summary.json` | `coordination_success_rate` across 20 trials; `outcome_variance` |
| `hypothesis_report.txt` | plain-English H1–H4 results with p-values |
| `feature_table.csv` | one row per trial; all micro + macro metrics in one flat table |
| `cognitive_process_log.jsonl` | every internal LLM call tagged by type — filter by `call_type == "commons_decision"` for research data only |

For a complete field-by-field reference of every output file and its thesis
contribution, see **[EXPERIMENT_RESULTS_DATA_DICTIONARY.md](EXPERIMENT_RESULTS_DATA_DICTIONARY.md)**.

---

## Part 4 — Human Rating Collection

### Step 8. Distribute rating packets to raters

After at least one condition has run, collect the rating templates:

```bash
find experiment_results_cd_primary/ -name "human_eval_ratings.csv" | head -20
```

Send the `human_eval_ratings.csv` and matching `human_eval_packets.jsonl`
from each trial to your 3–5 raters. Raters fill in:

| Column | Scale | What to rate |
|---|---|---|
| `behavioural_consistency` | 1–5 | Does the agent act consistently with its persona? |
| `memory_coherence` | 1–5 | Are cited memories genuinely relevant to the decision? |
| `planning_plausibility` | 1–5 | Does the reasoning connect logically to stated goals? |
| `response_naturalness` | 1–5 | Does the response read as natural human decision-making? |
| `believable_yes_no` | yes/no | Would a naive reader mistake this for a real person? |

Each rater fills in their `rater_id` and their ratings. Return the filled
CSVs to a shared directory, e.g. `human_ratings/`.

### Step 9. Ingest ratings and compute inter-rater reliability

```bash
python rating_ingestion.py experiment_results_cd_primary/ --output human_ratings/report.json
```

Check the output for Krippendorff's α per dimension:

```json
"dimensions": {
  "behavioural_consistency": {"alpha": 0.72, "status": "acceptable"},
  "memory_coherence":        {"alpha": 0.68, "status": "acceptable"},
  "planning_plausibility":   {"alpha": 0.81, "status": "acceptable"},
  "response_naturalness":    {"alpha": 0.59, "status": "marginal"}
}
```

Any dimension with α < 0.67 will be automatically gated (auto-only) in the
final blend. Marginal dimensions should be discussed in the thesis
limitations section.

### Step 10. Blend human ratings into final scores

Set `human_ratings_path` on the scenario and re-run the summary step, or
call the blend function directly:

```python
from measurement.micro import blend_human_ratings_into_summary, _build_agent_deblind_map
from rating_ingestion import load_and_analyse_ratings
import json, os

trial_dir = "experiment_results_cd_primary/commons_dilemma/full/trial_0"

# Load automated summary
with open(f"{trial_dir}/micro_summary.json") as f:
    micro_summary = json.load(f)

# Load and analyse ratings
ratings_result = load_and_analyse_ratings("human_ratings/")

# De-blind and blend
deblind_map = _build_agent_deblind_map(trial_dir)
final_summary = blend_human_ratings_into_summary(
    micro_summary,
    ratings_result["merged_ratings"],
    deblind_map,
    reliability=ratings_result.get("reliability"),
)

# Save
with open(f"{trial_dir}/micro_summary_final.json", "w") as f:
    json.dump(final_summary, f, indent=2)
```

The output will contain `composite_believability_final` — this is the
thesis metric.

---

## Part 5 — Re-running Analysis After Blending

### Step 11. Re-run hypothesis analysis on blended scores

```bash
python -c "
from experiment_analysis import run_analysis
run_analysis('experiment_results_cd_primary', 'commons_dilemma')
"
```

This regenerates `hypothesis_report.json` and `hypothesis_report.txt` using
the updated feature table. The H4 regression will now use the blended
`*_final` scores if they are present in the feature table.

---

## Part 6 — How Agents Interact During a Run

### Agents do not talk to each other during resource decisions

Each agent makes its request independently, seeing only the current pool
level. No agent knows what any other agent is requesting in the same step.
The decision loop inside `scenario.step()` is:

```
for each agent (in alphabetical order by name):
    ask agent → get (amount, reasoning, memory_ref, plan_ref)
sum all amounts → update pool → log macro state
```

Because every agent sees the **same pre-step pool level**, the order of
asking does not affect any agent's decision or outcome.

### The only coordination channel is the pool level between steps

Agents learn about collective behaviour through scenario memory between
steps:

- If agents over-request at step 5, the pool drops noticeably
- At step 6 every agent sees a lower pool percentage
- A memory-enabled agent (C2+) receives task-relevant episodic memories of
  prior requests, pool changes, oversubscription, and fair-share deviations
- A full agent (C4) also receives scenario-level coordination reflections,
  such as the need for restraint when requests exceed fair share

### The Park et al. conversation system is present but separate

The underlying architecture can generate spontaneous agent-to-agent
conversations when two agents are co-located during `persona.move()`. These
are logged in `movement/<step>.json` under each persona's `chat` field.

These conversations complete **before** `scenario.step()` is called. They
remain part of the underlying Smallville world simulation, but the current
commons-dilemma memory manipulation uses controlled scenario episodic memory
for the resource decision so the memory-coherence metric stays task-relevant.

### What to look for in the output

- `movement/<step>.json` — `chat` field per persona shows any spontaneous
  conversations that occurred during that step's `persona.move()` call
- `micro_summary.json` — `memory_reference` fields show whether agents
  cited past commons-round events in their reasoning
- `micro_log.json` — `memory_scope` should be `scenario_episodic` for
  memory-enabled conditions, and `recent_memories` should contain pool/request
  memories rather than object-state memories
- `macro_summary.json` — `coordinated` field tracks whether collective
  restraint emerged over time

## Part 7 — API Rate Limiting and Cost

### Rate limiting

Each trial makes ~832 API calls (800 scenario decisions + ~32 persona planning
calls). Without pacing, early trials complete in ~20 minutes but after 6–7
trials the OpenAI TPM/RPM bucket exhausts and the SDK's internal retries stall
each call for minutes, pushing trial duration to ~2 hours.

`gpt_structure.py` now includes two protections:

- **Inter-call delay** (default 0.8 s) — spreads calls evenly across the
  trial, preventing burst exhaustion. The default was raised from 0.3 s to
  0.8 s after observing that `memory_planning` and `full` conditions make
  ~1,000+ calls per trial (more than baseline's ~832) due to agent
  conversations and richer planning module activity, causing rate limiting
  from trial 3 onwards even with the 0.3 s delay. Override via environment
  variable:

```bash
export OPENAI_INTER_CALL_DELAY=1.0   # increase if still hitting limits
export OPENAI_INTER_CALL_DELAY=0.3   # decrease on a high-tier account
```

- **Exponential backoff on `RateLimitError`** — retries up to 6 times with
  delays of 1 s, 3 s, 5 s, 9 s, 17 s, 33 s, logging each attempt. Previously
  rate limit errors were silently swallowed and returned `"ChatGPT ERROR"`.

Expected trial duration with the fix: **~25–30 minutes** consistently across
all 80 trials.

### Cost tracking

The `run_manifest.json` `llm_usage.estimated_cost_usd` field is only populated
when cost-per-token environment variables are set. Add these before running:

```bash
export OPENAI_CHAT_INPUT_COST_PER_1K_USD=0.00015    # gpt-4o-mini input
export OPENAI_CHAT_OUTPUT_COST_PER_1K_USD=0.00060    # gpt-4o-mini output
```

**Estimated total cost for the full 80-trial experiment on gpt-4o-mini: ~$7 USD**
(~$0.08/trial for baseline; memory/full conditions add 10–20% due to richer
prompt context). Using gpt-4o instead would cost ~$104.

---

## Part 8 — Recomputing Metrics Without Re-running

All summary files (`macro_summary.json`, `condition_summary.json`,
`matrix_results.json`, `hypothesis_report.*`) are derived from the raw logs and
can be regenerated at any time without new API calls.

**Raw files (permanent, never change after a trial completes):**

| File | Contents |
|---|---|
| `micro_log.json` | Per-agent per-step: requested, granted, reasoning, memory_reference, pool state, fair_share ratio |
| `macro_log.json` | Per-step: resource_level, total_requested, total_granted, gini, oversubscription, coordinated flag |
| `agent_step_log.jsonl` | Same as micro_log in JSONL format |

**To recompute all derived metrics after changing logic in `measurement/macro.py`:**

```bash
cd reverie/backend_server
python -c "
from experiment_analysis import run_analysis
run_analysis('experiment_results_cd_primary', 'commons_dilemma')
"
```

### Coordination threshold

The `coordinated` flag in `macro_log` is baked in at run time as
`total_requested <= replenishment_rate` (i.e. ≤ 50 credits). If you change
this threshold, the stored flag is stale — recompute from `total_requested`
directly:

```python
new_threshold = 75  # 1.5× replenishment, for example
for entry in macro_log:
    entry["coordinated"] = entry["total_requested"] <= new_threshold
```

Then pass the updated `macro_log` to `compute_macro_summary()`. All downstream
metrics (coordination_score, coordination_success, convergence_step) update
automatically.

**Important:** decide on any threshold change before analysing results from all
4 conditions. Changing it after seeing all results would constitute
post-hoc adjustment of the primary outcome measure (p-hacking). The safe
window is while only the baseline condition has completed.

---

## Part 9 — Troubleshooting

| Symptom | Likely cause | Fix |

|---|---|---|
| `ImportError: cannot import name 'openai_api_key'` | `utils.py` not created or in wrong directory | Create `reverie/backend_server/utils.py` per Step 4 |
| `AuthenticationError` from OpenAI | Wrong or expired API key | Check `openai_api_key` in `utils.py` |
| `ValueError: Requested sample size N exceeds M available personas` | `persona_sample_size` larger than personas in fork | Reduce `persona_sample_size` or use `base_the_ville_n25` (25 personas) |
| All agents request 0 with `parse_error: True` | LLM returning malformed JSON | Usually transient; check if model is rate-limited or prompt is too long |
| `micro_summary.json` has `llm_judges_used: false` | `_LLM_AVAILABLE` is False | LLM import failed silently; check that `utils.py` key is valid |
| Very small C3→C4 difference in believability | Short run length limits reflection accumulation | See methodological caveat in `MRES_IMPLEMENTATION_PLAN.md`; consider pre-warming the fork |
| `alpha: null` in reliability report | Fewer than 2 raters returned ratings for a dimension | Collect more rater responses before blending |
| `TypeError: 'NoneType' object is not subscriptable` in `plan.py` | A `run_gpt_prompt_*` helper returns `None` (parse failure or rate-limit retry) and the original code subscripts `[0]` without a null check | **Fully fixed** — all 9 affected functions in `plan.py` now have null guards with safe fallbacks (`"idle"`, `"<random>"`, `"conversing"`, `False`, `"wait"`, `[]`). If crash recurs, delete incomplete trial folder + matching storage folder, delete `plan.cpython-310.pyc` from `__pycache__/`, and restart |
| `ValueError: too many values to unpack (expected 2)` in `run_gpt_prompt.py` | LLM returns task schedule in markdown format instead of expected `(duration in minutes: N)` format; parser falls back to `get_fail_safe()` which returned a bare string `["asleep"]` instead of a proper 2-tuple list | Fixed `get_fail_safe()` in `run_gpt_prompt_task_decomp` to return `[["asleep", duration]]`; also delete `.pyc` cache files before restarting |

---

## Quick Reference: Key Commands

```bash
# Full experiment (from reverie/backend_server/)
python experiment_runner.py

# Smoke test (1 trial, 5 steps, 3 agents)
python run_smoke_test.py

# Ingest human ratings
python rating_ingestion.py experiment_results_cd_primary/ --output report.json

# Re-run hypothesis analysis (also recomputes all summary files from raw logs)
python -c "from experiment_analysis import run_analysis; run_analysis('experiment_results_cd_primary', 'commons_dilemma')"

# Check LLM usage / cost summary
python llm_usage.py

# Tune inter-call delay to avoid rate limiting (default 0.8 s)
OPENAI_INTER_CALL_DELAY=1.0 python experiment_runner.py
```
