# Running the LLM-Reflection Condition (`full_llm_reflection`)

**Added:** 2026-05-29
**Purpose:** Rerun the full cognitive condition with **genuine LLM-generated (Park-style) reflection** instead of the original deterministic rule-based reflection, so the "reflection drives coordination" finding rests on a faithful mechanism.

---

## What changed (summary)

| File | Change |
|---|---|
| `experiment_conditions.py` | New condition `full_llm_reflection`; new field `use_llm_reflection` (default `False`). All existing conditions are unchanged. |
| `persona/persona.py` | New accessor `uses_llm_reflection()`. |
| `scenarios/commons_dilemma.py` | Reflection now branches: `full` → deterministic rule (unchanged); `full_llm_reflection` → `_generate_llm_reflection()` (LLM synthesis over the agent's last 5 episodic memories), with automatic fallback to the deterministic rule on any failure. |

The **only** behavioural difference between `full` and `full_llm_reflection` is how the per-round reflection string is produced. Everything else (memory injection, planning, prompts, allocation logic, scoring) is identical.

---

## Critical: keep the comparison clean

To compare new `full_llm_reflection` against the **existing** `full` / C3 / C2 / C1 data, the rest of the pipeline must be frozen:

- **Same generator model** — set `OPENAI_CHAT_MODEL` to the exact model used for the original run (`gpt-4o-mini` is the default).
- **Same seeds** — keep `selection_seed=42` and `base_seed=20260430` (these match the original CD run in `experiment_runner.py`). For per-call reproducibility also set `OPENAI_CHAT_SEED` to whatever the original run used (or leave unset if it was unset originally).
- **Same scoring code** — do not edit `measurement/` between runs.
- **Same persona sample** — `persona_sample_size=8`, same world `base_the_ville_n25`.

If any of these differ from the original run, you must also rerun the conditions you intend to compare against, not just the new one.

---

## 1. Environment

```bash
cd "reverie/backend_server"

# API key: the codebase reads openai_api_key from utils.py.
# Make sure utils.py has your key, or export it as the project expects.
export OPENAI_CHAT_MODEL="gpt-4o-mini"          # must match the original run
export OPENAI_EMBED_MODEL="text-embedding-3-small"
# Optional, for tighter reproducibility (only if the original run used it):
# export OPENAI_CHAT_SEED="20260430"
```

Activate the project venv first if you use one (`.venv`).

---

## 2. Quick smoke test (no full run)

Confirms the new condition resolves and routes to the LLM path:

```bash
cd "reverie/backend_server"
python -c "from experiment_conditions import resolve_condition as r; \
c=r('full_llm_reflection'); \
print(c.name, 'use_reflection=', c.use_reflection, 'use_llm_reflection=', c.use_llm_reflection); \
print('full.use_llm_reflection (must be False) =', r('full').use_llm_reflection)"
```

Expected:
```
full_llm_reflection use_reflection= True use_llm_reflection= True
full.use_llm_reflection (must be False) = False
```

---

## 3. Run ONLY the new condition (targeted rerun, recommended)

Edit the `__main__` block of `experiment_runner.py` so `experimental_conditions` contains **only** the new condition, and point the output at a fresh directory so the original data is not overwritten:

```python
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="commons_experiment_llm_reflection",
    scenario=scenario,
    experimental_conditions=[
        "full_llm_reflection",          # <-- only the new condition
    ],
    n_steps=100,
    n_trials=20,
    output_dir="experiment_results_cd_llm_reflection",   # <-- fresh dir
    persona_sample_size=8,
    selection_seed=42,                  # same as original
    base_seed=20260430,                 # same as original
    export_human_eval=True,
    run_hypothesis_analysis=False,      # analysis needs all conditions; run separately
)
```

Then:

```bash
cd "reverie/backend_server"
python experiment_runner.py
```

This produces `experiment_results_cd_llm_reflection/commons_dilemma/full_llm_reflection/trial_0..19/` with the same output schema as the original conditions.

**Cost/time estimate:** 8 agents × 100 steps × 20 trials = 16,000 extra reflection LLM calls (one per agent per step), on top of the existing decision calls. Budget for rate-limiting and ~1–2 days wall-clock at the default 0.8s inter-call delay.

---

## 4. Run all five conditions together (full clean rerun, optional)

If seeds/model/scoring are **not** guaranteed identical to the May run, rerun the whole matrix so every condition is generated under the same settings:

```python
experimental_conditions=[
    "baseline",
    "memory",
    "memory_planning",
    "full",                 # deterministic reflection (original C4)
    "full_llm_reflection",  # LLM reflection (new)
],
run_hypothesis_analysis=True,
```

This gives a clean `full` vs `full_llm_reflection` contrast within one run.

---

## 5. Analysis

To regenerate H1–H4 over the new results, point `run_analysis` at the output dir:

```bash
cd "reverie/backend_server"
python -c "from experiment_analysis import run_analysis; \
run_analysis('experiment_results_cd_llm_reflection', 'commons_dilemma')"
```

Reports land in `experiment_results_cd_llm_reflection/commons_dilemma/analysis/` (`hypothesis_report.json` and `.txt`).

For the headline comparison you care about — **deterministic vs generative reflection** — compare coordination success and sustainability between the original `full` directory and the new `full_llm_reflection` directory (same metrics, `condition_summary.json` in each).

---

## 6. What to report afterward

- `full` (deterministic reflection) vs `full_llm_reflection` (generative): coordination success rate, mean sustainability, and the C3→Cfull jump under each.
- Whether genuine reflection **strengthens, weakens, or matches** the deterministic version. All three are publishable; commit to reporting whichever occurs.
- Number of **unique** reflection strings generated under `full_llm_reflection` (should be far more than the 2–3 the deterministic rule produced) — this is direct evidence the reflection is now generative.

---

## 7. Safety / reversibility

- `full` is untouched — the original C4 dataset and its reproduction path are intact.
- The new condition fails safe: if a reflection LLM call errors or returns empty, it falls back to the deterministic string, so a single bad generation never aborts a trial.
- To disable the new condition entirely, simply omit `"full_llm_reflection"` from `experimental_conditions`.
