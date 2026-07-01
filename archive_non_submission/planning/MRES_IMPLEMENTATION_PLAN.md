# MRes Implementation Plan

This document turns the MRes research plan into an implementation roadmap for
the `research-scenarios` branch in this repository.

## Goal

Use the existing Park et al.-style generative agent architecture as the base
simulation engine, then extend it into a controlled experimental platform for:

- micro-level validation of individual agent believability
- macro-level validation of emergent coordination
- comparison across architecture conditions
- repeatable headless experiment runs

## Existing Repository Capabilities

The repository already provides:

- the core Park et al. persona architecture under
  `reverie/backend_server/persona/`
- the simulation server in `reverie/backend_server/reverie.py`
- a headless experiment entrypoint in
  `reverie/backend_server/experiment_runner.py`
- an experiment condition layer in
  `reverie/backend_server/experiment_conditions.py`
- a multi-condition experiment matrix runner in
  `reverie/backend_server/experiment_runner.py`
- one implemented research scenario in
  `reverie/backend_server/scenarios/commons_dilemma.py`
- micro and macro summary modules in
  `reverie/backend_server/measurement/`

## Gap Between Repo and Research Plan

As of 2026-04-30 (post mixed-method blend pass), the main remaining gaps are:

- **Human ratings not yet collected** — export, ingestion, reliability, and
  blend infrastructure is fully complete; ratings have not yet been gathered
  from 3–5 raters; this is the single remaining gap on the measurement side
- **Additional scenarios still stubs** — task_assignment, information_consensus,
  emergency_coordination are not yet implemented; `information_consensus` is
  the recommended next scenario to implement
- **Network analysis for role differentiation** — the entropy component is
  implemented; the interaction-graph topology component is not

Previously resolved gaps (completed 2026-04-30):
- ~~Jaccard similarity~~ → cosine embedding similarity throughout micro.py
- ~~Planning plausibility missing LLM judge~~ → `_llm_planning_plausibility_score`
- ~~Response naturalness heuristic only~~ → `_llm_response_naturalness_score`
- ~~No regression for H4~~ → OLS implemented in `experiment_analysis.py`
- ~~No Krippendorff's alpha~~ → `rating_ingestion.py` created
- ~~LLM seed not enforced per trial~~ → `set_chat_seed` + per-trial call
- ~~n_trials=3~~ → n_trials=20
- ~~Human ratings not blended into final scores~~ → `blend_human_ratings_into_summary`
  + `_build_agent_deblind_map` in `micro.py`; `compute_micro_summary` extended
  with `human_ratings`, `agent_deblind_map`, `reliability` optional params;
  `experiment_runner.py` auto-triggers blend when `scenario.human_ratings_path`
  is set

## Architecture Mapping

The existing codebase already contains the cognitive modules needed for the
condition design:

- memory structures:
  - `persona/memory_structures/associative_memory.py`
  - `persona/memory_structures/spatial_memory.py`
  - `persona/memory_structures/scratch.py`
- perception and retrieval:
  - `persona/cognitive_modules/perceive.py`
  - `persona/cognitive_modules/retrieve.py`
- planning:
  - `persona/cognitive_modules/plan.py`
- reflection:
  - `persona/cognitive_modules/reflect.py`
- action execution:
  - `persona/cognitive_modules/execute.py`
- main agent loop:
  - `persona/persona.py`

## Experimental Conditions

These conditions are now defined as configuration objects in
`reverie/backend_server/experiment_conditions.py`, rather than as four
separate codebases.

Implementation status:

- the condition definitions, runtime metadata, and behavioural gating are all
  implemented (as of 2026-04-30)
- `persona.move()` gates retrieve, plan, and reflect based on condition flags
- `_ask_agent()` in commons_dilemma injects condition-appropriate task context
  into LLM prompts so C1-C4 differ in actual LLM input, not only metadata
- for commons_dilemma, memory is operationalised as scenario-specific
  episodic memory from prior resource-allocation rounds, not generic
  Smallville object-state memories

### `baseline`

- no episodic memory retrieval in the experimental sense
- no explicit planning module
- no reflection
- intended as the weakest architecture condition

### `memory`

- memory retrieval enabled
- planning disabled
- reflection disabled

### `memory_planning`

- memory retrieval enabled
- planning enabled
- reflection disabled

### `full`

- memory retrieval enabled
- planning enabled
- reflection enabled

## Scenario: Commons Dilemma

### What the scenario is

The Commons Dilemma is a classic social-science coordination problem: a group
of agents shares a finite renewable resource. Each agent must independently
decide how much to take each round. If the group is collectively greedy, the
resource degrades and eventually collapses. If agents restrain themselves and
stay within the resource's replenishment capacity, the pool is sustainable
indefinitely.

The scenario is chosen because it has a clean, measurable group-level outcome
(pool survival vs. collapse), no single-agent optimal strategy (taking more
is always individually rational in the short term, but collectively
destructive), and a natural role for memory, planning, and reflection to
influence decisions.

### Setup

At the start of each trial the scenario is initialised with:

| Parameter | Value | Meaning |
|---|---|---|
| `initial_resource` | 1000 | starting credits in the community fund |
| `replenishment_rate` | 50 | credits added to the fund each round |
| `max_request` | 100 | maximum any one agent can request |
| `capacity` | 1000 | hard ceiling on the fund |
| `n_agents` | 8 | sampled from the 25-agent base world |
| `fair_share` per agent | 50 / 8 ≈ 6.25 | sustainable per-agent quota |

The fund starts full. Collectively sustainable behaviour requires each agent
to request at or below their fair share (~6 credits). At `max_request=100` an
agent can single-handedly consume double the entire replenishment in one round.

### What happens each step

**1. Resource context is constructed**

A plain-English string is built describing the current fund state:

> "The shared community fund currently holds 823.0 credits (82.3% of the
> original 1000). It is replenished by 50 credits each round. 8 community
> members are sharing this fund. A fair equal share would be 6.3 credits each."

**2. Each agent is asked how much they want**

`_ask_agent()` sends a prompt to the LLM containing:
- the agent's persona (name, identity, traits via `scratch.get_str_iss()`)
- the current resource context
- a condition-appropriate cognitive section (see below)
- a JSON response schema requiring `amount`, `reasoning`,
  `memory_reference`, and `plan_reference`

The agent responds with an integer request (0–100) and three text fields
explaining its decision.

**3. Allocation**

If total requests ≤ current pool: every agent receives exactly what they
asked for.

If total requests > current pool: each agent receives a proportional
fraction (`requested × pool / total_requested`). No agent is singled out;
the shortfall is shared equally in proportion to requests.

**4. Pool update**

```
new_pool = min(capacity, old_pool − total_granted + replenishment_rate)
```

If `new_pool ≤ 0` the pool collapses: `collapsed = True` and the trial ends
immediately, regardless of how many steps remain.

**5. Logging**

Per-agent micro entry logged each step:

| Field | What it captures |
|---|---|
| `requested` | integer credits the agent asked for |
| `granted` | integer credits actually received |
| `reasoning` | agent's explanation of its decision |
| `memory_reference` | any memory/prior event the agent cited |
| `plan_reference` | how the decision fits the agent's goals |
| `resource_level_before` | pool level at the start of this step |
| `fair_share` | sustainable per-agent quota this step |
| `request_ratio_to_fair_share` | >1.0 means agent is over-consuming |
| `memory_scope` | `scenario_episodic` when commons task memory is enabled |
| `recent_memories` | prior commons-round memory available to the agent |
| `memory_context_available` | whether the agent had memories to draw on |
| `planning_context_available` | whether the agent had a plan to draw on |
| `scenario_reflections` | coordination reflections available in C4/full |
| `condition_capabilities` | which modules were enabled for this agent |

Pool-level macro entry logged each step:

| Field | What it captures |
|---|---|
| `resource_level` | pool size after this step |
| `total_requested` | sum of all requests this step |
| `oversubscription` | `max(0, total_requested − replenishment_rate)` |
| `coordinated` | True if `total_requested ≤ replenishment_rate` |
| `sustainability_score` | Mean of per-step `(resource_level / initial_resource)` across all 100 steps (0–1). Measures average pool health throughout the trial, not the final state. Final pool state is `final_resource_level`. |
| `gini` | Gini coefficient of granted amounts (0=equal, 1=maximally unequal) |
| `collapsed` | True if pool hit zero this step |

### Success and failure

**Coordination success** is defined as a sustained streak of `convergence_window=5`
consecutive coordinated steps (total requests ≤ replenishment rate) at a pool
level ≥ `coordination_success_threshold × initial_resource` (≥ 700 units).

**Collapse** is the hard failure: pool reaches zero, all agents get nothing,
trial ends early.

A trial can also end without either: agents may keep the pool marginally
above zero indefinitely without truly coordinating, or step out at 100 steps
with moderate but not catastrophic resource depletion.

### How the four conditions differ in what agents see

The cognitive section injected into each agent's prompt changes with the
condition. This is what makes C1–C4 produce genuinely different LLM inputs:

| Condition | What is added to the prompt |
|---|---|
| **C1 baseline** | nothing extra; agent decides from persona + pool state alone |
| **C2 memory** | scenario-specific episodic memories from prior commons rounds (up to 5); agent can cite past resource-allocation outcomes |
| **C3 memory+planning** | memories + daily goals + current activity; agent has a plan to honour |
| **C4 full** | memories + planning context + scenario-level coordination reflections |

The research hypothesis is that richer cognitive context (C4 > C3 > C2 > C1)
should produce more believable reasoning (micro) and better collective
restraint (macro), because agents with memory and planning can recognise the
tragedy-of-the-commons dynamic and act strategically rather than greedily.

#### Scenario memory construct-validity fix

Pilot inspection showed that the earlier memory-context implementation used
the generic Park et al. associative memory stream via
`persona.get_recent_memories(limit=5)`. In headless mode the backend still
runs the Smallville world simulation, so the latest memories were often
environmental perceptions such as `bed is idle`, `desk is idle`, and
`<persona> is sleeping`.

Those memories are valid world-state memories, but they do not measure the
research-plan construct of memory coherence in a commons-dilemma task. The
current implementation therefore keeps world memory in the underlying agent
architecture but separates the experimental memory manipulation:

- world memory remains available to the core generative-agent architecture
- scenario memory is a controlled record of prior commons-round interactions
  used for the resource-allocation decision prompt and logged in
  `micro_log.json`

Scenario memories record group demand, pool change, oversubscription,
fair-share deviation, and which agents requested above or below fair share.
This makes the memory condition test whether agents can appropriately use
prior task interactions, as specified in the research plan.

#### Within-trial memory accumulation

Scenario memories accumulate step by step within a single trial:

- **Step 0**: no memories available — `recent_memories = []`
- **Step 1**: memories from step 0 are available
- **Step N**: memories from all prior steps, subject to the sliding window

The sliding window keeps the last **20 entries** in storage and injects the
last **5** into the agent's prompt. For CD this means roughly the last 4 steps
of context (5 entries per step); for IC roughly the last 1–2 steps (4 entries
per step). This window prevents the prompt from growing unboundedly while
ensuring the agent always has recent task history.

Memory accumulation is **gated by condition**: BASELINE and PLANNING_ONLY
agents always receive `recent_memories = []` at every step, regardless of
how many steps have elapsed.

#### Cross-trial isolation

Each trial receives a completely fresh scenario instance via `clone_scenario()`
and a fresh `ReverieServer` loaded from the original `fork_sim_code`. This
means:

- `scenario_memories` and `scenario_reflections` reset to `{}` at the start
  of every trial
- The Park et al. associative memory (`a_mem`) reloads from the original fork
  state, not from any prior trial's saved state
- `rs.save()` writes each trial to disk but the next trial always forks from
  `fork_sim_code`, never from the previous trial's output

Trials are therefore statistically independent observations, as required for
the repeated-measures analysis across H1–H4.

### Agent communication and decision order

**Agents do not communicate directly with each other during the scenario.**
Each agent makes its resource request in complete isolation from other agents'
current decisions. Understanding this is important for interpreting the results.

#### What each agent can see each step

Before any agent is asked, a single resource context string is built from
the fund level at the **end of the previous step**:

> "The shared community fund currently holds 823.0 credits (82.3% of the
> original 1000). It is replenished by 50 credits each round. 8 community
> members are sharing this fund. A fair equal share would be 6.3 credits each."

Every agent receives **the same string**. No agent knows what any other
agent is requesting during the current step.

#### The decision loop

```
step N begins
  → resource context built from fund level at end of step N−1
  → agent 1 asked  →  decides X credits  (cannot see other agents' decisions)
  → agent 2 asked  →  decides Y credits  (cannot see other agents' decisions)
  → ...
  → agent 8 asked  →  decides Z credits  (cannot see other agents' decisions)
  → all requests summed → fund updated → logged
step N ends
```

#### Order of agents within a step

Agents are iterated in the Python dict insertion order of `personas`, which
follows the sorted alphabetical list produced by `resolve_persona_selection`.
So agents are asked in **alphabetical order by persona name**. Because every
agent sees the same pre-step context, the order has no effect on what any
agent decides or what any agent receives.

#### What about the Park et al. conversation system?

The Park et al. architecture supports agent-to-agent conversations: during
`persona.move()`, the `execute()` module can trigger a spontaneous
conversation if two agents are spatially co-located and one decides to
initiate. These conversations are logged in `persona.scratch.chat`.

However, this is **separate from the scenario resource decision**.
`scenario.step()` is called **after** all `persona.move()` calls complete
for that step. Any conversation from `move()` could enter an agent's
associative memory (in C2–C4 conditions), and that memory might be retrieved
and cited in a later step's `_ask_agent()` — but only as a recalled past
event, not as real-time knowledge of the current step's requests.

#### Coordination is entirely implicit

The only real-time coordination channel is **pool depletion across steps**:

- If agents collectively over-request at step 5 the pool drops visibly
- At step 6 all agents see the lower pool level
- A C2–C4 agent with memory can notice the pattern: *"the pool dropped
  again — others must be over-requesting"*
- A C4 agent may have a reflection synthesised from several such steps:
  *"I've noticed the shared resource is declining; I should restrain myself"*

This is **emergent implicit coordination** — agents adjust behaviour based
on an aggregate signal without any explicit negotiation. This is
intentional: it is a harder and more ecologically valid test of the
cognitive architecture than a scenario where agents can directly tell each
other what they plan to request.

#### Implication for interpreting results

- Cooperation differences between conditions (C1 vs C4) reflect whether
  memory and reflection enable agents to *read the aggregate signal* and
  *adjust accordingly*, not whether they can negotiate
- Small coordination improvements in C2 vs C1 reflect memory enabling
  recognition of past depletion events
- Larger improvements in C3–C4 reflect planning and reflection enabling
  forward-looking restraint based on inferred group behaviour

### What the measurements capture

**Micro (believability):**
- Does the agent's request pattern stay consistent with its persona over time?
  → `behavioural_consistency` (cosine embedding similarity of actions vs. profile)
- Does the agent actually use its cited memories relevantly?
  → `memory_coherence` (cosine embedding: cited memory vs. available memories)
- Does the agent's reasoning align with its stated plan/goals?
  → `planning_plausibility` (LLM 1–5 rubric + embedding alignment)
- Does the agent's reasoning read as natural human decision-making?
  → `response_naturalness` (LLM distinction test + heuristic)

**Macro (coordination):**
- Does the group avoid collapse and sustain the pool?
  → `coordination_success`, `sustainability_score`, `convergence_step`
- How stable is the outcome across 20 replications?
  → `outcome_variance` (CV across trials)
- Do agents spontaneously specialise into different request roles?
  → `emergent_role_differentiation` (entropy of request strategies)
- When things go wrong, which agent(s) caused the breakdown?
  → `failure_traceability` (structured bundle linking collapse steps to
  per-agent over-requests)

## Planned Phases

### Phase 1: Experimental Condition Scaffolding

Purpose:
- create a single source of truth for the architecture conditions
- inject condition metadata into the runtime cleanly
- keep current default behaviour stable

Primary files:
- `reverie/backend_server/experiment_conditions.py`
- `reverie/backend_server/reverie.py`
- `reverie/backend_server/persona/persona.py`
- `reverie/backend_server/experiment_runner.py`

Target outputs:
- condition definitions
- condition resolution helpers
- runtime metadata for the chosen condition

### Phase 2: Condition-Aware Experiment Runner

Purpose:
- run a matrix of conditions x trials x scenarios
- standardise output directory layout
- capture run manifests for analysis

Primary files:
- `reverie/backend_server/experiment_runner.py`

Target outputs:
- structured trial orchestration
- condition-aware output folders
- run-level manifests and summaries
- matrix-level summary output for condition comparisons

### Phase 3: Micro-Level Believability Metrics

Purpose:
- align implementation with the thesis validation framework

Primary files:
- `reverie/backend_server/measurement/micro.py`
- new export helpers for transcript-based rating

Target outputs:
- behavioural consistency metric
- memory coherence proxy
- planning plausibility proxy
- response naturalness export path
- first-pass automated believability proxy at the per-agent level
- richer context-aware logging so later human evaluation has decision inputs

### Phase 4: Macro-Level Validation and Stability

Purpose:
- strengthen the system-level analysis for coordination validity

Primary files:
- `reverie/backend_server/measurement/macro.py`

Target outputs:
- coordination success
- convergence behaviour
- stability across replications
- collapse and inequality reporting
- failure traceability hooks
- condition-level aggregate summaries across trials
- feature-table exports for downstream hypothesis testing

### Phase 5: Human Evaluation Support

Purpose:
- export clean artefacts for rubric-based scoring by human raters

Primary files:
- new helper module under `reverie/backend_server/`

Target outputs:
- blinded transcript samples
- rater-ready CSV/JSON exports
- condition labels and scenario metadata
- de-blinding support for researchers

### Phase 6: Additional Scenarios

Purpose:
- move beyond a single commons dilemma scenario when the core pipeline is
  stable

Primary files:
- `reverie/backend_server/scenarios/task_assignment.py`
- `reverie/backend_server/scenarios/information_consensus.py`
- `reverie/backend_server/scenarios/emergency_coordination.py`

Target outputs:
- at least one more fully implemented coordination scenario

## First Files To Change

The implementation sequence should begin with:

1. `reverie/backend_server/experiment_conditions.py`
2. `reverie/backend_server/persona/persona.py`
3. `reverie/backend_server/reverie.py`
4. `reverie/backend_server/experiment_runner.py`
5. `reverie/backend_server/scenarios/commons_dilemma.py`
6. `reverie/backend_server/measurement/micro.py`
7. `reverie/backend_server/measurement/macro.py`

## Documentation Policy

This project will keep a living progress log in:

- `docs/MRES_PROGRESS_LOG.md`

It also keeps a dedicated Table 1 coverage map in:

- `docs/TABLE1_IMPLEMENTATION_CHECKLIST.md`

And a broader research-plan fidelity check in:

- `docs/RESEARCH_PLAN_FIDELITY_CHECKLIST.md`

That log should be updated after each completed phase with:

- what changed
- which files changed
- why the change matters for the thesis
- what remains next

## Status

- Phase 1: completed
- Phase 2: completed
- Phase 3: completed (2026-04-30, upgraded to embedding similarity + LLM judges)
- Phase 4: completed (stability + convergence + traceability summary layer)
- Condition behavioural gating: completed (2026-04-30)
- Phase 5: completed (export pipeline + Krippendorff's alpha ingestion module)
- Mixed-method blend: completed (2026-04-30)
- Phase 6: pending

### Phase 3 addendum (2026-04-30 gap-fix pass)

The following were added on top of the Phase 3 proxy-only implementation:

- `pre_embed_micro_log()` + `_EMBEDDING_CACHE` for cosine embedding similarity
- `planning_plausibility_llm_per_agent()` — LLM-assisted 1–5 rubric judge
- `response_naturalness_llm_per_agent()` — LLM-as-judge distinction test
- `compute_micro_summary()` extended with `use_llm_judges` and `critical_step`

### Phase 5 addendum (2026-04-30 gap-fix pass)

- `rating_ingestion.py` created: ingests completed `human_eval_ratings.csv`
  files, computes Krippendorff's alpha per dimension, merges ratings, and
  flags low-reliability packets

### Phase 5 addendum (2026-04-30 mixed-method blend pass)

- `_build_agent_deblind_map(trial_dir)` added to `micro.py`: builds
  `{blinded_agent_id: persona_name}` from exported human-eval artefacts
- `blend_human_ratings_into_summary(...)` added to `micro.py`: non-destructive
  blend of automated scores + ingested human ratings; reliability gating
  (α < 0.67 → auto-only); adds `*_final` and `composite_believability_final`
  keys; emits audit metadata
- `compute_micro_summary()` extended with `human_ratings`, `agent_deblind_map`,
  `reliability` optional params
- `experiment_runner.py` auto-triggers blend when
  `scenario.human_ratings_path` is set; fully backwards-compatible

### Analysis addendum (2026-04-30 gap-fix pass)

- `experiment_analysis.py` extended with `_ols_regression()` and
  regression-based H4 ranking (research plan §4.6)

### Reproducibility addendum (2026-04-30 gap-fix pass)

- `gpt_structure.set_chat_seed()` added
- `experiment_runner.py` now enforces LLM seed and clears embedding cache
  between trials
- `n_trials` updated to 20 in `__main__`

## Current Reality Check

As of 2026-04-30 (post mixed-method blend pass):

- all four experimental conditions are implemented with full behavioural gating
- the runner supports multi-condition, multi-trial, 5–10 agent experiments with
  deterministic persona sub-sampling and per-trial seed control
- micro metrics use cosine embedding similarity and LLM judges matching Table 1
- **the full mixed-method blend pipeline is implemented end to end**: export →
  ingestion → Krippendorff's α reliability gating → per-agent blended
  `*_final` scores → `composite_believability_final`
- macro metrics cover all five Table 1 macro dimensions
- the H1–H4 analysis pipeline includes Spearman, Mann-Whitney U, Kruskal-Wallis,
  and OLS regression
- the commons-dilemma memory condition now uses scenario-specific episodic
  memory, improving construct validity for memory coherence and H4
- **the remaining gaps are study execution and scenario breadth, not infrastructure**
- additional scenarios beyond commons_dilemma remain as stubs

## Methodological Caveats

These are known boundary conditions on the study design. They do not
invalidate the ablation comparison but bound the claims that can be made
and should appear explicitly in the thesis limitations section.

### Reflection history depth and C3→C4 effect size

The Park et al. reflection module synthesises higher-level insights from
accumulated episodic memories. Its contribution grows over extended
simulation time. In this study each trial starts from the
`base_the_ville_n25` fork point and runs for 100 steps, so C4 (full) has
limited accumulated reflection content at the start of each trial.

**What this means:**
- The ablation comparison remains internally valid: C4 vs C3 tests whether
  enabling the reflection module during a run improves coordination outcomes
- The effect size for C3→C4 should be treated as a **conservative lower-bound
  estimate** of reflection's full contribution, not a definitive measure
- Very small C3→C4 gaps should not be interpreted as "reflection has no
  effect" without first considering run-length as a confound

**Recommended thesis framing:**

> The reflection condition (C4) tests the contribution of the reflection
> module when active during a 100-step experimental run, not the contribution
> of deeply accumulated reflective insight from extended simulation time.
> Effect sizes for C3→C4 comparisons may therefore underestimate the
> reflection module's full potential contribution.

**Optional mitigation:** Pre-warm the fork simulation by running it for
additional steps with reflection enabled before branching to experiment
trials. This enriches agents' reflection content at trial start at the cost
of additional API calls. Evaluate after pilot runs.

**Empirical finding (2026-05-07):** Inspection of `full/trial_0/micro_log.json`
confirmed that reflection content converges to exactly **2 unique strings** by
step 1 and remains fixed for all 100 steps (2,049 and 303 injections
respectively). The commons dilemma outcome space is binary enough that the
reflection generator produces the same two lessons on every step after the
first round. This reinforces the conservative-lower-bound framing above: the
C3→C4 comparison measures the effect of a weak, rapidly-saturating reflection
signal, not rich accumulated insight. Acknowledge explicitly in the thesis
limitations section.

### Baseline condition approximation

C1 (baseline) disables associative-memory retrieval, planning, and
reflection. Agents retain persona identity, scratch state, and spatial/world
grounding. This matches the intent of "stateless" in the research plan but
not the strongest possible architectural reading. State this as a boundary
condition, not a flaw: the four conditions represent increasing architectural
sophistication within the same agent framework, which is what the ablation
requires.

### LLM temperature

Park et al. (2023) used task-specific temperatures across different cognitive
calls (0 for deterministic tasks such as poignancy scoring and object states;
0.7 for conversational tasks; 1.0 for daily planning). This study routes all
calls through the OpenAI Chat Completions API (`gpt-4o-mini`) with no
temperature parameter set, defaulting to the model's global default of **1.0**
for every call type.

**What this means:**
- The `commons_decision` call (the research-critical prompt) has no Park et al.
  temperature baseline — it is a new call type not present in the original
  architecture. Temperature 1.0 is appropriate here as it produces variability
  across trials, which is desirable for a behavioural experiment.
- The only calls where the departure from Park et al. is material are
  `emoji_conversion` and `object_state` (Park et al. temperature: 0). Both are
  pure Smallville visual overhead — they do not feed into any decision prompt,
  memory retrieval, planning context, or research output file.
- No `daily_planning`, `task_decomp`, or `conversation_generation` calls
  appeared in the `cognitive_process_log.jsonl` during experiment steps,
  confirming these tasks fire outside the logged window and do not interact
  with the commons dilemma decision loop.

**Impact on results:** None. Temperature affects only cosmetic world-simulation
calls that do not enter any hypothesis test.

**Recommended thesis framing:**

> All LLM calls used `gpt-4o-mini` via the Chat Completions API at the model
> default temperature (1.0). Per-task temperature variation from the original
> Park et al. implementation (which used `text-davinci-003` with temperatures
> ranging from 0 to 1.0 by task type) was not replicated. This difference
> affects only Smallville world-simulation calls (emoji conversion, object
> state description) and has no bearing on agent resource-allocation decisions
> or any reported metric.

### Scenario memory operationalisation

The commons-dilemma memory manipulation is explicitly scoped to
task-relevant episodic memory. It does not claim to test open-ended retrieval
from the full autobiographical Smallville memory stream. This is an internal
validity choice: it aligns memory coherence with "appropriate retrieval and
use of prior interactions" in the resource-allocation task.

Recommended thesis framing:

> For the commons-dilemma task, memory was operationalised as scenario-
> specific episodic memory: records of prior resource requests, fair-share
> deviations, group demand relative to replenishment, and pool outcomes.
> General environmental memories from the Smallville world were retained as
> part of the underlying generative-agent architecture but separated from the
> scenario-level memory context used for evaluating memory coherence.

Effect on believability scoring:

- The scoring formula is unchanged.
- The direct effect is on the memory-coherence component, which contributes
  0.25 of the composite believability score.
- The memory-enabled conditions are not given credit simply because relevant
  memory is available. They score well only when the agent accurately cites,
  interprets, and behaviourally responds to prior commons-round context.
- The fix makes the memory-coherence component more valid for H4 because it
  now measures use of prior task interactions instead of overlap with generic
  room/object memories.
- Any pre-fix and post-fix believability scores should not be pooled, because
  they use different memory-context operationalisations.

## Next Steps

### Critical path (thesis data collection)

1. **Distribute rating packets** — send `human_eval_ratings.csv` and
   `human_eval_packets.jsonl` artefacts from a completed trial run to 3–5
   raters; ask them to fill in the four Likert columns plus `believable_yes_no`
2. **Ingest and verify reliability** — run
   `python rating_ingestion.py <experiment_results_dir> --output report.json`
   and confirm Krippendorff's α ≥ 0.67 for each dimension
3. **Blend ratings into final scores** — set `scenario.human_ratings_path`
   to the directory containing returned rating files and re-run the experiment
   summary step; `composite_believability_final` in each trial's
   `micro_summary.json` is then the thesis metric
4. **Run full experiment matrix** — execute `experiment_runner.py __main__`
   for 4 conditions × 20 trials with `persona_sample_size=8`; corrected
   outputs are written to `experiment_results_cd_primary/`

### Code improvements (can start immediately)

5. **Implement `information_consensus` scenario** —
   `reverie/backend_server/scenarios/information_consensus.py`; consensus-
   building framing from §4.4; required for cross-scenario generalisability
6. **Network analysis for role differentiation** — add adjacency-matrix
   construction and centrality/clustering metrics to `macro.py` alongside the
   existing entropy component; this closes the last Table 1 code gap
7. **Qualitative failure coding template** — add a structured analyst
   worksheet alongside the exported `failure_traceability.json` bundles
8. **Implement `task_assignment` scenario** — second stub to fill after
   information_consensus is stable
