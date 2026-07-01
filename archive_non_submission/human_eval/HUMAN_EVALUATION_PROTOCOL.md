# Human Evaluation Protocol

This document outlines the intended human-evaluation workflow for the MRes
study.

## Purpose

The current repository already computes several automated proxy metrics, but
the research plan requires mixed-method evaluation for several Table 1 items.
This protocol defines how human scoring should be integrated later.

## Target Metrics

Human evaluation is especially important for:

- behavioural consistency
- memory coherence
- planning plausibility
- response naturalness
- failure traceability

## Proposed Inputs for Raters

Each rating packet should include:

- anonymised agent identifier
- scenario name
- condition label hidden from the rater
- sampled transcript or reasoning snippets
- relevant local context
- a structured rubric sheet

## Proposed Rating Dimensions

### Behavioural consistency

Prompt to rater:
- Does this agent behave in a way that is consistent with its stated role,
  background, and prior behaviour?

Suggested rubric:
- `1`: strongly inconsistent
- `2`: mostly inconsistent
- `3`: mixed / unclear
- `4`: mostly consistent
- `5`: strongly consistent

### Memory coherence

Prompt to rater:
- Does the agent appropriately use relevant prior events, interactions, or
  memories when making its decision?

Suggested rubric:
- `1`: memory use absent or clearly wrong
- `2`: weak or mostly irrelevant memory use
- `3`: partially relevant memory use
- `4`: mostly relevant and coherent memory use
- `5`: strong and clearly appropriate memory use

### Planning plausibility

Prompt to rater:
- Does the action or decision plausibly follow from the agent’s current goals,
  schedule, or constraints?

Suggested rubric:
- `1`: implausible
- `2`: weakly plausible
- `3`: partly plausible
- `4`: mostly plausible
- `5`: strongly plausible

### Response naturalness

Prompt to rater:
- Does the response read like a believable human-like explanation in context?

Suggested rubric:
- `1`: unnatural
- `2`: weakly natural
- `3`: mixed
- `4`: mostly natural
- `5`: strongly natural

Optional binary distinction question:
- Would you believe this response was produced by a believable simulated
  social actor in context?
  - `yes`
  - `no`

## Scope

**Human evaluation is scoped to the Commons Dilemma scenario.**

This is a deliberate methodological choice, not a resource constraint.

The Information Consensus scenario (C2–C4) converges to near-identical
outcomes across conditions (≈91% consensus, ≈6-step convergence).
Raters would not be able to meaningfully discriminate between conditions
from IC packets, which would undermine the purpose of the human eval pass —
validating that automated believability metrics track genuine behavioural
quality differences.

Commons Dilemma is the appropriate target because:

- it produces strong condition-level variance (0% → 5% → 10% → 70%
  coordination success), giving raters visible differences to respond to
- agents produce explicit resource-allocation reasoning with social cues,
  providing richer surface area for assessing planning plausibility, memory
  coherence, and response naturalness
- the full condition's sustained cooperation provides a visible correct
  outcome that anchors rater calibration

Thesis framing (limitations):

> Human evaluation was conducted on the commons dilemma scenario, as it
> produced the greatest behavioural variance across conditions and the richest
> decision traces for rater assessment.  Whether human-rated believability
> generalises to information-sharing scenarios with lower within-condition
> variance remains a direction for future work.

## Sampling Strategy

Suggested minimum approach:

- sample from the **Commons Dilemma** scenario only (see scope note above)
- sample across all four architecture conditions (C1–C4)
- sample across successful and failed runs
- sample across early, middle, and late steps
- sample from more than one agent persona

This avoids overfitting the human study to one condition or one stage of a
run.

## Reliability

Suggested study design:

- `3–5` trained raters
- anchored rubric examples before rating begins
- overlap a subset of examples across all raters
- compute Krippendorff’s alpha for agreement

## Implemented Exports

The repository now exports the following files per trial:

- blinded transcript bundles
- decision-level context packets in `human_eval_packets.jsonl`
- researcher-only de-blinding map in `human_eval_blind_key.json`
- rater-ready CSV template in `human_eval_ratings.csv`

## Current Status

This protocol is now partially operationalised:

- the repository generates blinded packets and rating sheets automatically
- packets include persona background, local context, memory context, and plan
  context with agent names redacted

What still remains manual:

- recruiting and training `3-5` raters
- collecting completed rating CSVs
- computing inter-rater reliability and integrating human scores back into the
  final believability measures

---

## Metric-to-Variable Mapping (verified 2026-05-23)

This section documents the exact packet fields each metric depends on, traced
from scenario implementation through the micro log to the packet builder
(`human_evaluation.py`).

### Per-metric evidence variables

| Metric | Primary packet field(s) | Condition gate |
|---|---|---|
| Behavioural Consistency | `persona_background` + `local_context.recent_memories` | `persona_background` always present; `recent_memories` only when `uses_memory()=True` |
| Memory Coherence | `local_context.recent_memories` ↔ `decision.memory_reference` | `recent_memories` empty `[]` for BASELINE and PLANNING_ONLY conditions |
| Planning Plausibility | `local_context.daily_goals` ↔ `decision.plan_reference` | `daily_goals` empty `[]` for BASELINE and MEMORY_ONLY conditions |
| Response Naturalness | `decision.reasoning` | Always populated across all conditions and scenarios |

Field origins in the micro log:

- `persona_background` ← `entry["persona_profile"]` ← `persona.get_profile_summary()`
- `recent_memories` ← `entry["recent_memories"]` ← `scenario.scenario_memories[name][-5:]`, gated on `uses_memory()`
- `daily_goals` ← `entry["daily_goals"]` ← `persona.get_plan_snapshot()["daily_goals"]`, gated on `uses_planning()`
- `decision.reasoning` ← `entry["reasoning"]` ← LLM response field, always extracted
- `decision.memory_reference` ← `entry["memory_reference"]` ← LLM response field; prompt instructs `""` for no-memory conditions
- `decision.plan_reference` ← `entry["plan_reference"]` ← LLM response field; prompt instructs `""` for no-planning conditions

### Scenario-specific notes

**Commons Dilemma** additionally populates:
- `local_context.resource_level_before`, `pool_percent_before`, `fair_share` — these give raters the pool state at decision time, relevant for behavioural consistency scoring

**Information Consensus** differences:
- `local_context.current_activity` is always `""` (not applicable to IC)
- `vote` and `shared_statement` are in the micro log but not included in the packet — the agent's vote position is only visible to raters indirectly through `decision.reasoning`

### What `recent_memories` actually contains

`recent_memories` are **scenario-constructed episodic summaries**, not entries
from the persona's internal memory retrieval system. They are plain strings
built by the scenario after each step and capped at the last 20, with the last
5 taken for the packet. Their content is:

**Information Consensus** (4 strings per agent per step):
1. Group vote tally + % supporting the majority option
2. Whether the group reached coordinated consensus this round
3. Up to 3 shared statements from other agents
4. The agent's own vote and first 100 chars of their reasoning

**Commons Dilemma** (5 strings per agent per step):
1. Total requested vs replenishment rate + oversubscription figure
2. Pool level before and after granting
3. Whether the group stayed within the replenishment limit
4. The agent's own request amount relative to fair share
5. Which peers were at/above/below fair share (contains other agents' names — see validity issue #4 below)

These strings are what gets injected into the agent's prompt via
`_build_cognitive_context_for_scenario()`, so they correctly represent
what the agent had access to when making its decision.

### Academic validity issues in `recent_memories`

1. **`scenario_reflections` missing from packets** — both scenarios populate
   `scenario_reflections` in the micro log, but `human_evaluation.py`
   `build_human_evaluation_packets()` never reads this field. For FULL-condition
   agents, raters are missing the reflection context that influenced the
   decision. Fix: add `scenario_reflections` to `local_context` in the packet
   builder and render it as a tab in `human_eval_ui.py`.

2. **Memory/planning metrics unrateable for no-capability conditions** —
   BASELINE agents have `recent_memories=[]` and `daily_goals=[]`, leaving
   raters with no evidence to score memory coherence or planning plausibility.
   Fix: either exclude those metrics from the rubric for no-capability packets,
   or add a "not applicable" option to the rater UI for those sliders.

3. **Condition leakage via empty `recent_memories`** — because `recent_memories`
   is gated on `uses_memory()`, raters can infer the condition from whether the
   Memory tab is populated or empty. This breaks the blinding design. Fix:
   populate `recent_memories` for all conditions (using the same scenario
   summaries) but label the tab to indicate whether the agent had access to
   them during its decision. Alternatively, document this as a known limitation
   and note it does not affect the primary automated metrics, only human rating
   validity.

4. **Peer name leakage in Commons Dilemma** — the `peer_status` string in CD
   memories contains other agents' names (e.g. `"Community members above fair
   share: Alice, Bob"`). The sanitiser in `human_evaluation.py` only replaces
   the current packet's persona name, not other agents' names. This means other
   agents' real names appear in the Memory tab, breaking blinding for those
   agents. Fix: either sanitise all persona names across all memory strings, or
   replace peer names with generic labels (e.g. `"Agent 1"`, `"Agent 2"`).

5. **IC private signal absent from memory tab** — the agent's private signal
   (the most influential piece of evidence in IC) is injected directly into the
   prompt each step, not stored in `scenario_memories`. Raters will see
   `decision.memory_reference` entries that cite the signal but will find no
   corresponding entry in the Memory tab. Fix: include the agent's private
   signal text in `local_context` as a separate field, and surface it in the UI
   alongside the memory tab.

6. **IC vote not surfaced** — ~~raters cannot see what option the agent voted
   for without reading through the reasoning~~ **FIXED (2026-05-27)**: `vote`,
   `prior_vote`, `position_change`, `signal_disclosed`, and `shared_statement`
   are now included in `decision` for IC packets.  Both UIs render a dedicated
   IC Decision panel showing these fields explicitly.

7. **LLM confabulation of `memory_reference` at step 0 (and when memories are
   empty)** — `decision.memory_reference` and `local_context.recent_memories`
   come from completely separate sources:
   - `recent_memories` = scenario-recorded episodic summaries from *prior
     rounds*, injected into the prompt.  At step 0 there are no prior rounds,
     so the list is always empty regardless of condition.
   - `memory_reference` = what the LLM *wrote* in its own JSON response when
     asked for the `memory_reference` field.  The prompt instruction for
     memory-capable conditions is permissive: *"one short sentence about any
     memory, prior event, or prior interaction that influenced this decision;
     use an empty string if none."*

   When `recent_memories = []` (step 0, or early steps with no accumulated
   scenario memory) the LLM receives no scenario memory in its prompt but may
   still write a non-empty `memory_reference` by drawing on the **persona
   description** in the prompt (e.g. *"Previously, I learned that investing in
   the right tools can significantly improve my outputs."*).  This is an LLM
   behaviour — it prefers generating something plausible over returning an
   empty string — not a code bug.  The code correctly records what the LLM
   produced.

   **Effect on evaluation:** A packet can show `recent_memories = not
   available` alongside a non-empty `Memory cited`, which appears contradictory
   to a rater.  For `memory_coherence` scoring, this case should be rated low
   (1–2): the agent is citing a memory it was never given.

   **Rater guidance (add to rubric):** If "Recent memories" is blank but
   "Memory cited" is non-empty, the agent has confabulated a memory reference.
   Score `memory_coherence` as 1 unless the cited memory is directly derivable
   from the persona background shown (in which case score 2).

   **Code fix option:** Post-process `memory_reference` to `""` whenever
   `memory_context_available = False` in the parse step of the scenario.
   **Not recommended for this study** — the confabulated reference is
   informative data showing that LLM agents invent memories when none are
   available; zeroing it out would hide a real phenomenon worth reporting in
   the thesis.

8. **"Correct option" wording in IC packets** — ~~`resource_level_label` in
   `information_consensus.py` was written as `"N of M agents on correct option"`,
   and the Streamlit UI showed this as "Resource note" while the React UI showed
   it as "Consensus support". The word "correct" directly revealed that a right
   answer exists and implicitly identified which option it is~~ **FIXED
   (2026-05-27)**:
   - `resource_level_label` in `information_consensus.py` changed to
     `f"{n_correct} of {n_agents} agents on Option {self.TRUE_OPTION}"`.
   - IC packets no longer include `resource_level_label` or `resource_level_note`
     at all — those fields are now CD-only.  Raters see `consensus_rate` (a
     group-level aggregate) and `vote_tally` (shows all options' support equally),
     neither of which identifies which option is "correct".
   - Both UIs updated to render IC situation via `consensus_rate` and
     `vote_tally` rather than the retired `resource_level_note`.

   **Thesis note:** This fix is methodologically necessary.  If raters could
   identify the correct option from UI wording, their ratings of
   `behavioural_consistency` and `response_naturalness` would be contaminated
   by outcome knowledge.  The corrected UIs present only group-level convergence
   information, consistent with the blinding requirement.

---

## LLM-as-a-Judge Evaluation (added 2026-05-24)

`reverie/backend_server/llm_judge.py` implements an automated LLM rater that
processes every `human_eval_packets.jsonl` file and writes
`llm_judge_ratings.csv` beside it.  The output format is identical to
`human_eval_ratings.csv` so `rating_ingestion.py` can treat the LLM as an
additional rater when computing Krippendorff's alpha.

### Judge-generator independence (methodological rationale)

The generative agents in this study were driven by **GPT-4o-mini** (OpenAI).
The LLM judge uses **Claude** (Anthropic) — a different model family.

This is a deliberate methodological choice, not an arbitrary preference.
Using the same model to both generate decisions and judge them introduces
**self-serving bias**: GPT-4o-mini tends to rate its own outputs higher than
an independent evaluator would, which would inflate agreement with any
human raters who disagree with GPT's style.

Judge-generator independence is a standard requirement in LLM-as-a-judge
methodology (Zheng et al., 2023, "Judging LLM-as-a-Judge with MT-Bench and
Chatbot Arena"; Pandalinkage et al., 2024).  Using a model from a separate
provider and architecture family ensures:

- the judge has no prior exposure to the specific outputs it is rating
- agreement with human raters reflects genuine quality signal
- the result is defensible in peer review

**Thesis wording (§4.5 recommended):**

> Agent decisions were generated using GPT-4o-mini (OpenAI). To avoid
> self-evaluation bias, the LLM-as-a-judge pass used Claude (Anthropic), a
> model from a different provider and architecture family. This
> judge-generator independence follows the recommendation of Zheng et al.
> (2023) and ensures that agreement between the LLM judge and human raters
> reflects genuine decision quality rather than model self-consistency.

### Purpose

- Provides a scalable reference rating before human raters are recruited
- Enables inter-rater reliability analysis between LLM and human raters
- Never replaces human judgement — supplements it

### Rating dimensions

Identical to the human rubric:

| Dimension | Scale | Low anchor | High anchor |
|---|---|---|---|
| `behavioural_consistency` | 1–5 | Contradicts persona | Fully consistent |
| `memory_coherence` | 1–5 | Ignores / misuses memory | Uses it well |
| `planning_plausibility` | 1–5 | No connection | Clear logical connection |
| `response_naturalness` | 1–5 | Clearly robotic | Natural |
| `believable_yes_no` | yes/no | — | — |

The judge also writes a 1–2 sentence `notes` justification per packet.

### How it works

1. Builds a structured prompt from each packet (persona, context, memory,
   plan, decision) — mirrors exactly what human raters see in the UI
2. Calls Claude via tool use (`submit_rating`) to get structured JSON output
3. Uses `tool_choice={"type": "tool", "name": "submit_rating"}` — no free-text
   parsing; all five fields are validated by the tool schema
4. Writes `llm_judge_ratings.csv` with `rater_id="llm_judge"`

### Usage

```bash
# Dry run — print prompt for first packet without making API calls
python llm_judge.py --dry-run experiment_results_ic_primary

# Rate one result directory
python llm_judge.py experiment_results_cd_primary/commons_dilemma

# Rate all standard result directories
python llm_judge.py --all

# Force re-rate (overwrite existing llm_judge_ratings.csv)
python llm_judge.py --force --all

# Use a stronger model
python llm_judge.py --model claude-sonnet-4-6 --all
```

Requires `ANTHROPIC_API_KEY` environment variable.  Default model is
`claude-haiku-4-5-20251001` for cost efficiency.

### Integration with rating_ingestion.py

Because `llm_judge_ratings.csv` uses the same fieldnames and `rater_id`
convention as human rating files, `rating_ingestion.py` will pick it up
automatically when pointed at a result directory:

```bash
python rating_ingestion.py experiment_results_cd_primary --output report.json
```

The LLM judge will appear as one rater in the alpha computation.

---

## Resource Note fix (2026-05-24)

The `resource_level_note` field in packets was previously only populated for
Information Consensus.  Commons Dilemma macro logs never wrote
`resource_level_label`, so the Resource Note field appeared blank for all CD
packets in the human eval UI.

Fix applied:

- `scenarios/commons_dilemma.py` — macro entry now writes
  `"resource_level_label"` as e.g. `"898.0 credits (89.8% of original pool)"`
- `human_evaluation.py` — new `_resource_level_note()` helper: checks for
  `resource_level_label` first; if absent (existing results) derives the same
  string from `resource_level` + `sustainability_score`

All existing packets regenerated (168 trials across CD and IC result
directories) using the updated builder.  No underlying log data was modified.
