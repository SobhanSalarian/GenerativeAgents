# Experiment Archive

This folder contains superseded or pilot experiment result directories that are **excluded from all analysis**.
They are kept for provenance — so the full history of data collection decisions is traceable — but nothing in
this folder is referenced by `experiment_analysis.py`, `early_warning.py`, or any hypothesis test.

The four active datasets used in the thesis are one level up, in `reverie/backend_server/`:

| Active directory | Role |
|-----------------|------|
| `experiment_results_scenario_memory/` | Primary CD dataset — 4 conditions × 20 trials |
| `experiment_results_ic_v3/` | Primary IC dataset — 4 conditions × 10 trials |
| `experiment_results_ic_v3_reflection/` | IC full_llm_reflection — 10 trials, both bug fixes applied |
| `experiment_results_cd_llm_reflection_v2/` | CD full_llm_reflection — 10 trials, both bug fixes applied |

---

## Archived directories

### `experiment_results_ic_test/`

- **When:** 2026-05-09
- **What:** 3 trials per condition (baseline, memory, memory_planning, full) — Information Consensus
- **Why archived:** Exploratory test run to verify the IC scenario was wired up correctly.
  Never intended as analysis data. Superseded by `experiment_results_ic_v3/`.

---

### `experiment_results_ic/`

- **When:** 2026-05-10
- **What:** 12 trials per condition (4 conditions) — Information Consensus v1
- **Why archived:** First full IC run. Superseded by `experiment_results_ic_v3/` which uses the
  corrected persona description fix (Fix 2: `get_str_iss()` added to `_generate_llm_reflection()`)
  and a standardised 10-trial-per-condition protocol.

---

### `experiment_results_ic_v2/`

- **When:** 2026-05-11 to 2026-05-23
- **What:** 12 trials per condition (4 conditions) — Information Consensus v2
- **Why archived:** Second full IC run. Also superseded by v3. At the time of this run, the
  scenario and measurement code were still being refined. The 12-trial protocol was replaced
  with 10 trials per condition for consistency with the CD primary dataset.

---

### `experiment_results_ic_v3_pilot/`

- **When:** 2026-05-24
- **What:** 4 trials per condition (4 conditions) — Information Consensus v3 pilot
- **Why archived:** Short pilot run to validate the v3 IC scenario and measurement pipeline
  before committing to the full 10-trial run. Results are structurally correct but N=4 is
  too small for any hypothesis test. Superseded by `experiment_results_ic_v3/`.

---

### `experiment_results_llm_reflection/`

- **When:** 2026-05-29
- **What:** 10 trials — Commons Dilemma `full_llm_reflection` condition (v1)
- **Why archived:** **Faulty data — do not use.** This run was completed before Fix 2 was
  applied: the `_generate_llm_reflection()` call did not include the agent's persona
  description (`get_str_iss()`), so all LLM reflections were persona-blind. The agents
  reflected on group events without any grounding in their individual identity.
  Replaced by `experiment_results_cd_llm_reflection_v2/` which has both fixes applied.
  Kept here for reference so the v1 vs v2 divergence is inspectable if needed.

---

## Bug fixes referenced above

| Fix | Description | Files changed |
|-----|-------------|---------------|
| Fix 1 | `NameError` in IC `_record_scenario_memories()` — `personas` → `self.personas` | `scenarios/information_consensus.py` |
| Fix 2 | Persona description (`get_str_iss()`) added to `_generate_llm_reflection()` in both scenarios — without it, reflections were persona-blind | `scenarios/commons_dilemma.py`, `scenarios/information_consensus.py` |

Both fixes were applied before `experiment_results_ic_v3_reflection/` and
`experiment_results_cd_llm_reflection_v2/` were collected (2026-06-06 onwards).
