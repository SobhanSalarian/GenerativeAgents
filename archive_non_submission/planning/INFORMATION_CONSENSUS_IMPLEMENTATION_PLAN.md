# Information Consensus — Implementation Plan

## Overview

The `information_consensus` scenario is the second coordination scenario for
the MRes study. It complements `commons_dilemma` by testing a fundamentally
different coordination mechanism: **information aggregation** rather than
resource restraint.

- Commons dilemma: agents *know* what sustainable behaviour looks like
  (request ≤ fair share) but self-interest pulls against it.
- Information consensus: no single agent has enough information to know the
  right answer. Success requires agents to *share* and *integrate* each
  other's private signals.

This distinction matters for the thesis because it tests whether the
believability→coordination relationship (H1–H3) and the predictor ranking
(H4) generalise beyond the restraint-based task.

---

## Scenario Design

### The Decision

The community is voting on how to use a new shared facility. Three options:

| Option | Description |
|---|---|
| **A** (correct) | Community garden and creative workspace |
| **B** | Commercial café and co-working space |
| **C** | Open flexible space with minimal infrastructure |

Option A is the designated correct answer. Agents receive private signals;
the majority of signals point to A, so agents who share information and
aggregate correctly should converge on A.

### Private Signal Distribution

8 agents receive signals distributed deterministically by sorted persona
name order:

| Signal type | Count | Text injected into agent prompt |
|---|---|---|
| Points to A | 4 | "Community consultation notes you reviewed show strong resident support for a shared creative studio and collaborative workshop space (Option A)." |
| Points to B | 2 | "A needs assessment you read found that skills training and digital access are the community's highest priorities, favouring Option B." |
| Points to C | 2 | "A wellbeing report you studied showed strong demand for outdoor recreation and green wellness space (Option C) among local residents." |

Assignment is deterministic: agents are sorted alphabetically; the first 4
receive signal A, the next 2 receive signal B, the last 2 receive signal C.
This is reproducible from the persona list alone (no extra seed needed).

> **Design note (2026-05-10):** The original 5-2-1 distribution was too
> unbalanced — 5 A-signal agents trivially exceeded the 6/8 threshold without
> any information sharing. Changed to 4-2-2 so genuine persuasion of at least
> two non-A agents is required for coordination success.

### Per-Step Flow

Each of the 100 steps:

1. Build `_consensus_context()`: current vote tally + the last 3 shared
   statements that other agents disclosed (a rolling public record).
2. For each agent: call `_ask_agent()` — condition-aware prompt with the
   agent's private signal, the public context, and (for C2–C4) cognitive
   context from prior rounds.
3. Agent returns: `vote` (A/B/C), `reasoning`, `shared_statement`
   (one sentence they contribute to the group), `memory_reference`,
   `plan_reference`.
4. After all agents respond: update vote tally, check convergence,
   append to micro/macro logs, record scenario memories.

### Coordination Success

Step-level `coordinated = True` when ≥ 6 of 8 agents vote for A.

Trial-level `coordination_success = True` when `coordinated` is True for
`convergence_window = 5` consecutive steps at any point in the trial.

> **Design note (2026-05-10):** Originally set to 3; raised to 5 to prevent
> trivially short trials. Matches the commons_dilemma default.

`coordination_score` = fraction of steps where `coordinated` is True
(directly analogous to commons_dilemma).

---

## File Structure

### `scenarios/information_consensus.py` — the scenario class

**Class constants:**

```python
slug = "information_consensus"
convergence_window = 5          # raised from 3 after smoke test (2026-05-10)
coordination_success_threshold = 0.75   # 6/8 agents = 0.75
TRUE_OPTION = "A"
OPTIONS = {
    "A": "Shared creative studio and collaborative workshop space",
    "B": "Community learning centre with digital skills programs",
    "C": "Outdoor recreation area and wellness garden",
}
SIGNAL_KEYWORDS = {
    "A": ["consultation", "creative studio", "workshop", "resident support"],
    "B": ["needs assessment", "skills", "digital", "training", "learning"],
    "C": ["wellbeing", "wellness", "recreation", "outdoor", "green"],
}
SIGNALS = {
    "A": ("Community consultation notes you reviewed show strong resident "
          "support for a shared creative studio and collaborative workshop "
          "space (Option A)."),
    "B": ("A needs assessment you read found that skills training and digital "
          "access are the community's highest priorities, favouring Option B."),
    "C": ("A wellbeing report you studied showed strong demand for outdoor "
          "recreation and green wellness space (Option C) among local residents."),
}
SIGNAL_COUNTS = {"A": 4, "B": 2, "C": 2}   # must sum to 8
```

**`__init__` state:**

```python
self.personas          = {}
self.agent_signals     = {}   # {persona_name: "A"/"B"/"C"} — set in setup()
self.public_statements = []   # rolling list of shared statements (last 10)
self.vote_history      = {}   # {persona_name: [vote_step0, vote_step1, ...]}
self.micro_log         = []
self.macro_log         = []
self.consensus_reached = False
self.consensus_step    = None
self.consecutive_coordinated = 0
self.scenario_memories = {}
self.scenario_reflections = {}
```

**`setup(personas)`:**

```python
def setup(self, personas):
    self.personas = personas
    sorted_names = sorted(personas.keys())
    # Deterministic signal assignment
    signals = []
    for option, count in sorted(self.SIGNAL_COUNTS.items()):
        signals.extend([option] * count)
    for name, signal in zip(sorted_names, signals):
        self.agent_signals[name] = signal
        self.vote_history[name] = []
    self.scenario_memories = {name: [] for name in personas}
    self.scenario_reflections = {name: [] for name in personas}
```

**`step(personas, step_num, curr_time)`:**

```python
def step(self, personas, step_num, curr_time):
    context = self._consensus_context(step_num)
    step_micro = []

    for persona_name, persona in personas.items():
        signal = self.agent_signals[persona_name]
        cognitive_context = self._build_cognitive_context_for_scenario(persona, persona_name)
        vote, reasoning, shared_statement, memory_reference, plan_reference, parse_error = (
            self._ask_agent(persona, context, signal, cognitive_context)
        )
        self.vote_history[persona_name].append(vote)
        prior_vote = (self.vote_history[persona_name][-2]
                      if len(self.vote_history[persona_name]) >= 2 else None)

        step_micro.append({
            "step": step_num, "time": str(curr_time),
            "persona": persona_name,
            "vote": vote,
            "correct": vote == self.TRUE_OPTION,
            "prior_vote": prior_vote,
            "position_change": vote != prior_vote if prior_vote else False,
            "reasoning": reasoning,
            "shared_statement": shared_statement,
            "memory_reference": memory_reference,
            "plan_reference": plan_reference,
            "signal": signal,
            "signal_disclosed": signal.lower() in (shared_statement + reasoning).lower(),
            "experimental_condition": persona.experimental_condition.name,
            "parse_error": parse_error,
        })
        # Add shared statement to public record
        if shared_statement:
            self.public_statements.append(
                f"{persona_name}: {shared_statement}"
            )

    # Trim public statements to last 10
    self.public_statements = self.public_statements[-10:]

    # Vote tally
    tally = {opt: 0 for opt in self.OPTIONS}
    for entry in step_micro:
        tally[entry["vote"]] = tally.get(entry["vote"], 0) + 1

    n_correct = tally.get(self.TRUE_OPTION, 0)
    n_agents  = len(step_micro)
    consensus_rate  = n_correct / n_agents if n_agents else 0
    coordinated     = n_correct >= round(self.coordination_success_threshold * n_agents)

    if coordinated:
        self.consecutive_coordinated += 1
        if (self.consecutive_coordinated >= self.convergence_window
                and not self.consensus_reached):
            self.consensus_reached = True
            self.consensus_step    = step_num
    else:
        self.consecutive_coordinated = 0

    macro_entry = {
        "step": step_num, "time": str(curr_time),
        "vote_tally": tally,
        "n_correct": n_correct,
        "consensus_rate": round(consensus_rate, 3),
        "coordinated": coordinated,
        "consensus_reached": self.consensus_reached,
        "consensus_step": self.consensus_step,
        "coordination_score": round(consensus_rate, 3),
        "information_diffusion": self._information_diffusion_rate(step_micro),
    }
    self.micro_log.extend(step_micro)
    self.macro_log.append(macro_entry)
    self._record_scenario_memories(step_micro, macro_entry, tally)
```

**`_consensus_context(step_num)`:**

```python
def _consensus_context(self, step_num):
    option_lines = "\n".join(
        f"  - Option {k}: {v}" for k, v in self.OPTIONS.items()
    )
    tally = {opt: 0 for opt in self.OPTIONS}
    for votes in self.vote_history.values():
        if votes:
            tally[votes[-1]] = tally.get(votes[-1], 0) + 1
    tally_str = ", ".join(
        f"Option {k}: {v} agent(s)" for k, v in tally.items()
    )
    recent = self.public_statements[-3:]
    discussion = (
        "\n".join(f"  {s}" for s in recent)
        if recent else "  (No statements shared yet.)"
    )
    return (
        f"The community is deciding on a proposal for the new shared facility.\n"
        f"Options:\n{option_lines}\n\n"
        f"Current vote tally (round {step_num}):\n  {tally_str}\n\n"
        f"Recent shared statements:\n{discussion}"
    )
```

**`_ask_agent(persona, context, signal, cognitive_context)`:**

The prompt is condition-aware in exactly the same pattern as commons_dilemma:

```
You are {name}.

{persona ISS}
{cognitive_context — only injected if condition enables it}

Current situation:
{context}

Your private signal:
{signal}

Based on your signal, what you know about the community, and what others have shared:
1. What option do you currently support?
2. What will you share with the group to help everyone make the best decision?

Respond with a JSON object with exactly four fields:
- "vote": exactly "A", "B", or "C"
- "reasoning": 1–2 sentences explaining your position
- "shared_statement": one sentence you contribute to the group discussion
  (share what you know — your signal, reasoning, or response to what others said)
- "memory_reference": {condition-gated instruction}
- "plan_reference": {condition-gated instruction}
```

The `memory_reference` and `plan_reference` condition-gating is identical to
commons_dilemma — baseline agents are explicitly told to leave these empty.

**`_record_scenario_memories(step_micro, macro_entry, tally)`:**

Store three types of memory per agent per step (C2+):

1. **Vote tally memory:** "At step N, the group voted: Option A: 5, Option B: 2, Option C: 1."
2. **Discussion memory:** any shared_statements from this step, attributed by name.
3. **Own-position memory:** "You voted for Option A at step N because [reasoning]."

Cap at last 15 memories per agent.

**Scenario reflections (C4):**

Generate one of three reflection strings based on the current state:
- If ≥ 5 agents are on A: "The group is converging on Option A — information sharing appears to be working."
- If agents are split: "The group remains divided; sharing more evidence about the correct option may help."
- If current agent is on the wrong option: "Other agents appear to favour a different option; their signals may contain important information."

Cap at last 10 reflections per agent.

**`_information_diffusion_rate(step_micro)`:**

Fraction of agents who mentioned their private signal in their
`shared_statement` or `reasoning` this step. Measures how actively agents
are broadcasting information.

---

## Metric Integration

### `measurement/macro.py`

The existing `compute_macro_summary()` reads `coordination_score` and
`coordinated` fields directly from `macro_log`. Those fields are present in
the information_consensus log with the same names and semantics, so the
existing macro pipeline requires **no changes**.

Additional information_consensus-specific summary fields (add to a
`compute_information_consensus_macro_summary()` helper or compute inline):

- `final_consensus_rate` — `consensus_rate` at step 99
- `convergence_step` — first step where 3 consecutive coordinated steps occurred
- `mean_information_diffusion` — mean `information_diffusion_rate` across steps
- `signal_disclosure_rate` — fraction of agent-steps where private signal was disclosed

### `measurement/micro.py`

The existing micro metrics (behavioural_consistency, memory_coherence,
planning_plausibility, response_naturalness, composite_believability) all
read from `micro_log` field names (`reasoning`, `memory_reference`,
`plan_reference`, `persona_profile`, `recent_memories`,
`planning_context_available`, `memory_context_available`).

The information_consensus micro log uses the same field names for those
four fields, so **no changes to micro.py are required** for the core
believability metrics.

One new micro metric worth adding (not required for H1–H4, but useful for
the thesis information-aggregation argument):

- `signal_disclosure_rate_per_agent` — fraction of steps where the agent
  mentioned their private signal; measures whether agents actively
  contribute information.

### `experiment_runner.py`

No changes required. `get_scenario_slug()` already handles any scenario with
a `slug` attribute. Register `InformationConsensus` in `scenarios/__init__.py`
and pass it to `run_experiment()`.

---

## Implementation Steps (ordered)

### Step 1 — Write `information_consensus.py` (~4–5 hours)

Implement the class described above, replacing the existing stub. Work through
the file in this order:
1. `__init__` and class constants
2. `setup()`
3. `_consensus_context()`
4. `_ask_agent()`
5. `step()` — the main loop
6. `_record_scenario_memories()`
7. `_build_cognitive_context_for_scenario()`
8. `get_micro_log()`, `get_macro_log()`, `is_complete()`, `_init_kwargs()`

### Step 2 — Register in `scenarios/__init__.py` (~5 minutes)

Add:
```python
from scenarios.information_consensus import InformationConsensus
```

### Step 3 — Smoke-test with 1 trial, baseline condition (~30 minutes)

```bash
cd reverie/backend_server
python -c "
from scenarios.information_consensus import InformationConsensus
from experiment_runner import run_experiment

run_experiment(
    fork_sim_code='base_the_ville_n25',
    sim_code_prefix='ic_test',
    scenario=InformationConsensus(),
    experimental_condition='baseline',
    n_steps=10,
    n_trials=1,
    output_dir='experiment_results_ic_test',
    persona_sample_size=8,
)
"
```

Verify:
- `micro_log.json` has `vote`, `reasoning`, `shared_statement` fields
- `macro_log.json` has `vote_tally`, `consensus_rate`, `coordinated` fields
- No crashes across the 10 steps

### Step 4 — Smoke-test all 4 conditions (~2 hours)

Run 2-trial pilots for all four conditions. Check:
- C1 (baseline): agents vote randomly or based on persona alone — consensus
  rate should be low
- C2 (memory): agents remember prior votes and statements — should show
  some convergence
- C3 (memory+planning): planning should help agents commit to a strategy
- C4 (full): with reflections, agents should show faster convergence

### Step 5 — Run 10-trial pilot per condition (~API budget: ~10M tokens)

```bash
python experiment_runner.py experiment_results_cd_primary \
  information_consensus --n_trials 10
```

### Step 6 — Run `experiment_analysis.py` on information_consensus results

```bash
python experiment_analysis.py \
  experiment_results_cd_primary \
  --scenario information_consensus
```

Check:
- H1/H2/H3 direction matches commons_dilemma (consistency strengthens the claim)
- H4 predictor ranking — does planning_plausibility remain dominant?

---

## What This Adds to the Thesis

### Generalisability argument (critical)

With two scenarios you can write:

> The believability→coordination relationship (H1, Spearman ρ=0.549 in
> commons_dilemma; ρ=X in information_consensus) replicated across two
> structurally distinct coordination tasks: a resource restraint task and
> an information aggregation task. This suggests the relationship is not
> specific to the commons-dilemma framing.

### New mechanism observable

Information consensus exposes a cognitive mechanism invisible in commons
dilemma: whether agents actively disclose their private signals. The
`signal_disclosure_rate` metric directly measures information-sharing
behaviour, which maps to the research plan's "observable intermediate
behaviours (proposals, counter-proposals, information sharing)" from §4.4.

### H4 replication test

If planning_plausibility remains the dominant OLS predictor in information
consensus as well, that finding is much stronger — it holds across two
different coordination tasks. If the predictor ranking changes, that is
also a contribution: it shows that which micro-level property matters most
depends on the coordination mechanism.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM ignores signal and votes randomly | Medium | Strengthen signal framing in prompt; add "Your private signal is important — it is one piece of evidence others may not have." |
| All agents converge in first 5 steps (ceiling) | Low | If it happens: reduce signal majority (change from 5/2/1 to 4/3/1) |
| Parse errors on vote field | Low | Use robust parsing: accept "option a", "a)", "A." etc. |
| Metric pipeline breaks on new fields | Low | Field names deliberately match commons_dilemma for core metrics |

---

## Estimated Timeline

| Task | Time |
|---|---|
| Implement `information_consensus.py` | 1 day |
| Smoke-test (Step 3–4) | 0.5 day |
| 10-trial pilot per condition (Step 5) | 1 day (API runtime) |
| Analysis and documentation | 0.5 day |
| **Total** | **~3 days** |
