# Scenario Descriptions

This document provides academic-level descriptions of the two simulation
scenarios used in this MRes study. It is written to support thesis chapters,
methodology sections, and any reader who needs to understand what the agents
are doing, why these scenarios were chosen, and what each scenario measures.

---

## 1. Commons Dilemma

### 1.1 Theoretical Background

The commons dilemma is one of the foundational problems in collective action
theory. Hardin (1968) famously argued that individuals acting in their own
rational self-interest will inevitably deplete shared resources — the "tragedy
of the commons." Ostrom (1990) challenged this fatalistic conclusion, showing
empirically that human communities can sustain common-pool resources through
norms, communication, and institutional arrangements. The commons dilemma has
since become a canonical testbed for studying cooperation, restraint, and
coordination in both human and agent-based systems.

In the context of generative agent research, the commons dilemma is a natural
fit because it requires agents to balance individual utility (request as much
as possible) against collective sustainability (the pool must survive for all
to benefit). The scenario does not have a single "correct" answer at the
individual level; instead, coordination success is an emergent property of
the group's collective behaviour across many rounds.

### 1.2 Scenario Setup

**Pool:** A shared community fund with an initial balance of **1,000 credits**.
Each round, the fund replenishes by **50 credits** (up to a ceiling of 1,000).
The fund represents any finite shared resource — computational budget, community
funding, shared infrastructure time — that agents draw on to pursue their goals.

**Agents:** 8 generative agents, each with a distinct persona (background,
personality, occupation, goals) drawn from the Park et al. Smallville
architecture. Agents have no direct communication channel; they observe only
aggregate outcomes (pool level, total requested) and their own private reasoning.

**Constraint:** Each agent may request between 0 and **100 credits** per round.
A **fair equal share** is 50 ÷ 8 ≈ **6.25 credits**. If every agent requests
at their fair share, the group consumes exactly the replenishment rate and the
pool is stable indefinitely. If any agent requests above fair share, the pool
begins to shrink.

**Collapse condition:** If the pool level reaches 0, the commons collapses and
the simulation ends. Collapse represents a catastrophic coordination failure
and is treated as the worst experimental outcome.

### 1.3 Per-Step Sequence

Each simulation step proceeds as follows:

1. **Context construction:** The scenario computes the current pool level,
   pool percentage of original, and the current fair-share amount, and passes
   this to all agents as natural-language situational context.
2. **Agent decisions (independent):** Each agent independently receives the
   situational context plus its own persona background, cognitive context
   (memory, plans, reflections — depending on condition), and is asked: *"How
   many credits do you want to request this round?"* The agent responds with a
   JSON object containing an integer amount and a reasoning string.
3. **Allocation:** If total requests ≤ pool level, each agent receives exactly
   what it requested. If total requests exceed the pool, grants are scaled
   proportionally so no agent is favoured over another.
4. **Pool update:** Grants are deducted from the pool, then replenishment is
   added. If the pool hits 0, collapse is flagged.
5. **Memory recording:** Five episodic memory strings are appended to each
   agent's scenario memory buffer for the next round:
   - Group demand vs replenishment and oversubscription figure
   - Pool level before and after the round
   - Whether the group stayed within the replenishment limit
   - The agent's own request relative to fair share
   - Which peers were at/above/below fair share

This cycle repeats for up to 100 steps per trial.

### 1.4 Agent Roles

All agents play equivalent structural roles in this scenario: each is a
**community member** competing for a share of the common pool. There is no
leader, coordinator, or privileged agent. However, because each agent has a
distinct persona with different occupations, personality traits, and daily
goals, agents bring different "reasons" to their decisions:

- An artist persona may justify requests as necessary for creative projects.
- A researcher persona may frame requests around knowledge production.
- A caretaker persona may understate their own need in deference to others.

This persona heterogeneity is deliberate. The scenario tests whether
agent-level cognitive architecture (not persona-level content) is what drives
coordination success, because the 4-condition ablation holds personas constant
across conditions.

### 1.5 Coordination and Failure Modes

**Coordination success** is defined as the group collectively requesting ≤ 50
credits (the replenishment rate) in a given round. A trial is considered
successful if the group achieves ≥ 5 consecutive coordinated rounds without
collapse.

**Failure modes observed in data:**
- *Overextraction:* Agents with no memory of prior rounds consistently request
  near their maximum (≈70–90 credits), rapidly depleting the pool.
- *Defection under stress:* Even agents with memory may increase requests when
  the pool is low, reasoning that they should "take what they can before
  it's gone" — a well-documented human pattern under commons depletion.
- *Coordination without communication:* Agents can only observe pool-level
  outcomes; they cannot negotiate. Coordination must emerge from each agent's
  independent inference about what others are likely to do.

### 1.6 Experimental Conditions

The same 8-agent setup is run under four cognitive architecture conditions:

| Condition | Code | Memory | Planning | Reflection |
|---|---|---|---|---|
| Baseline | C1 | — | — | — |
| Memory only | C2 | ✓ | — | — |
| Memory + Planning | C3 | ✓ | ✓ | — |
| Full | C4 | ✓ | ✓ | ✓ |

Each condition runs 20 trials (20 independent simulations with identical
agent personas but independent random seeds). The ablation tests which
cognitive module or combination drives coordination success.

### 1.7 Why This Scenario Was Chosen

The commons dilemma was chosen for three reasons:

1. **Strong theoretical grounding.** The scenario instantiates one of the most
   studied collective action problems in social science. Results can be
   interpreted against a well-established literature on human commons
   management (Ostrom, 1990; Axelrod, 1984).

2. **Condition-level variance.** Pilot data confirmed strong variance across
   conditions (baseline ≈ 0–5% coordination success; full condition ≈ 70%).
   This variance provides clear signal for hypothesis testing and meaningful
   surface area for human raters to detect behavioural quality differences.

3. **Rich reasoning traces.** Each agent produces an explicit resource
   request with a natural-language reasoning string every round. These traces
   contain references to prior pool states, peer behaviour, and personal goals
   — the exact material that raters need to assess planning plausibility,
   memory coherence, and behavioural consistency.

### 1.8 Key Metrics

| Metric | Level | Description |
|---|---|---|
| `requested` | Micro (per agent) | Credits requested this round |
| `granted` | Micro | Credits actually allocated |
| `request_ratio_to_fair_share` | Micro | Agent's request ÷ fair share |
| `reasoning` | Micro | Natural-language justification |
| `memory_reference` | Micro | Memory the agent cited |
| `plan_reference` | Micro | Plan context the agent cited |
| `resource_level` | Macro (per step) | Pool balance after granting and replenishment |
| `sustainability_score` | Macro | Pool level ÷ initial level (0–1) |
| `total_requested` | Macro | Sum of all agent requests this step |
| `coordinated` | Macro | Boolean: total_requested ≤ replenishment_rate |
| `gini` | Macro | Inequality of granted amounts (0=equal, 1=one agent takes all) |
| `collapsed` | Macro | Boolean: pool hit zero |

### 1.9 Human Evaluation Scope

Human evaluation is **scoped to this scenario only**. The commons dilemma
produces strong condition-level behavioural variance and rich, interpretable
reasoning traces, making it the most appropriate target for rater assessment
of believability metrics (behavioural consistency, memory coherence, planning
plausibility, response naturalness).

---

## 2. Information Consensus

### 2.1 Theoretical Background

The information consensus scenario is grounded in the theory of **information
aggregation in groups** — the problem of how a group can combine privately held
evidence to reach a collectively correct decision that no individual could reach
alone.

The **Condorcet Jury Theorem** (de Condorcet, 1785) established the formal
basis: if each member of a group holds an independent signal that is more
likely to be correct than incorrect, and if members vote sincerely, majority
rule will reliably identify the correct option as the group grows. Extensions
to the Jury Theorem (Austen-Smith & Banks, 1996; Feddersen & Pesendorfer, 1997)
showed that strategic agents do not always vote sincerely — they update on
others' behaviour. This led to the study of **Bayesian social learning** (Banerjee,
1992; Bikhchandani et al., 1992): how agents update their beliefs based on
what they observe others doing.

The tension is between private signals (each agent's own evidence) and
public information (what others have said and how the vote tally has moved).
Well-functioning information aggregation requires agents to share their
evidence, listen to others, and update their beliefs accordingly rather than
simply advocating for their initial signal.

### 2.2 Scenario Setup

**Task:** A community of 8 agents must collectively choose between three
proposed uses for a new shared facility:

| Option | Description |
|---|---|
| A | Shared creative studio and collaborative workshop space |
| B | Community learning centre with digital skills programs |
| C | Outdoor recreation area and wellness garden |

**Correct answer:** Option A is the majority-signal option — the option
supported by the plurality of private signals distributed to agents.

**Signal distribution:** Signals are assigned deterministically at setup
(sorted by persona name, then option alphabetically):

| Signal | n agents | Evidence text |
|---|---|---|
| A | 4 | Community consultation notes show strong resident support for a shared creative studio (Option A) |
| B | 2 | A needs assessment found that skills training and digital access are the highest priorities (Option B) |
| C | 2 | A wellbeing report showed strong demand for outdoor recreation (Option C) |

No agent can know how signals are distributed across the group. Each agent
sees only their own piece of evidence. The correct answer can only be
identified with high confidence by aggregating all signals — which requires
sharing and updating.

**Convergence criterion:** The group is considered to have reached consensus
when at least 6 of 8 agents (75%) vote for the same option for 5 consecutive
steps. Whether that option is the majority-signal option determines whether
consensus is *coordinated* (correct) or not.

### 2.3 Per-Step Sequence

Each simulation step proceeds as follows:

1. **Context construction:** The scenario assembles the current vote tally
   (how many agents voted for each option last round), recent shared statements
   from other agents (up to last 10), and the step number.
2. **Agent decisions (independent):** Each agent receives:
   - Its private signal text (injected fresh each step as a "reminder" of its
     own evidence)
   - The current vote tally and shared statements
   - Its own cognitive context (memory, plans, reflections — depending on
     condition)
   - The instruction to consider whether others' evidence outweighs its own
     signal before voting
   The agent responds with: a vote (A, B, or C), reasoning, a statement to
   share with the group, memory reference, and plan reference.
3. **Statement aggregation:** All shared statements are appended to a rolling
   public statement buffer (last 10 retained). This buffer is available to all
   agents in the next step — the only information channel between agents.
4. **Tally computation:** The scenario counts votes per option, computes
   consensus rate and information diffusion rate, and checks the convergence
   criterion.
5. **Memory recording:** Four episodic memory strings are appended per agent:
   - Group vote tally and consensus rate
   - Whether coordinated consensus was reached this round
   - Up to 3 shared statements from other agents
   - The agent's own vote and reasoning (first 100 characters)

This cycle repeats until the convergence criterion is met or the step limit
is reached.

### 2.4 Agent Roles

Unlike the commons dilemma, agents in this scenario play **structurally
differentiated roles** determined by their assigned signal:

**Signal A agents (4 of 8):** These agents hold the plurality evidence. If they
share their signal faithfully, the group can reach the correct decision even
without any signal updating. Their behavioural challenge is not whether to
advocate — it is whether they can communicate their evidence clearly enough
for others to update.

**Signal B and C agents (2 each):** These agents hold minority evidence. The
theoretically rational behaviour is to update away from their private signal
when the vote tally and others' shared statements provide sufficient public
evidence that the majority disagrees. Their behavioural challenge is to
recognise when others' combined evidence outweighs their own single signal.

All agents are treated identically by the protocol (same prompt structure,
same memory/planning access per condition). The signal difference is the only
structural distinction. Persona identities remain fixed across conditions.

### 2.5 Information Aggregation and Failure Modes

**Success requires two behaviours:**
1. **Signal disclosure:** Agents must share the evidence their signal contains
   in their public statements, not just state a vote preference.
2. **Belief updating:** Agents holding minority signals must update their vote
   when the tally and shared evidence clearly indicates the majority option.

**Failure modes observed in data:**

- *Signal anchoring:* Agents over-anchor on their private signal and refuse to
  update even when the tally is 6:1:1 against them. This is theoretically
  irrational (one signal vs. six contrary votes) but observed in LLM agents.
- *Zero belief updating:* In conditions where the prompt was framed as
  signal-advocacy ("your signal is an important piece of information; share it
  clearly"), agents showed near-zero position changes across all 100 steps.
  Reframing the prompt as collective-evidence reasoning significantly increased
  updating.
- *Confabulated memory references:* At step 0 (no prior rounds), memory-enabled
  agents occasionally generate plausible-sounding memory references derived
  from their persona description rather than from any actual prior-round event.
  This is an LLM hallucination behaviour, not a code artefact.

### 2.6 Experimental Conditions

The same 4-condition ablation applies as for the commons dilemma:

| Condition | Code | Memory | Planning | Reflection |
|---|---|---|---|---|
| Baseline | C1 | — | — | — |
| Memory only | C2 | ✓ | — | — |
| Memory + Planning | C3 | ✓ | ✓ | — |
| Full | C4 | ✓ | ✓ | ✓ |

Each condition runs 10 trials. The prediction is that memory-enabled conditions
should show faster convergence and higher correct-option consensus rates,
because agents can track the vote history and update accordingly.

### 2.7 Why This Scenario Was Chosen

The information consensus scenario was chosen for three reasons:

1. **Different coordination mechanism.** The commons dilemma tests
   *resource-restraint coordination* — agents must suppress their individual
   demand. The information consensus scenario tests *belief-aggregation
   coordination* — agents must combine distributed evidence. Together, the
   two scenarios support cross-scenario generalisability claims for H1–H4.

2. **Grounding in established theory.** The scenario operationalises the
   Condorcet Jury Theorem and Bayesian social learning, giving results a
   clear theoretical interpretation independent of the specific LLM model used.

3. **Sensitivity to memory module.** Information aggregation in multi-round
   deliberation requires agents to track what others have said in prior rounds.
   This is precisely the capability the memory module provides. The scenario
   is therefore a direct test of whether the memory module produces
   theoretically expected behavioural improvement.

### 2.8 Key Metrics

| Metric | Level | Description |
|---|---|---|
| `vote` | Micro (per agent) | Which option the agent voted for (A, B, or C) |
| `correct` | Micro | Boolean: vote == majority-signal option |
| `prior_vote` | Micro | Vote in the previous round |
| `position_change` | Micro | Boolean: vote changed from prior round |
| `signal_disclosed` | Micro | Boolean: agent's statement contained signal keywords |
| `reasoning` | Micro | Natural-language justification |
| `shared_statement` | Micro | Public statement shared with the group |
| `memory_reference` | Micro | Memory the agent cited |
| `plan_reference` | Micro | Plan context the agent cited |
| `vote_tally` | Macro (per step) | Dict of option → count (e.g. {"A": 5, "B": 2, "C": 1}) |
| `consensus_rate` | Macro | Fraction of agents on majority-signal option |
| `coordinated` | Macro | Boolean: ≥ 75% of agents on majority-signal option |
| `consensus_reached` | Macro | Boolean: convergence criterion met (5 consecutive coordinated steps) |
| `consensus_step` | Macro | Step at which convergence criterion was first met |
| `information_diffusion_rate` | Macro | Fraction of agents who disclosed signal keywords this step |

### 2.9 Human Evaluation Scope

Human evaluation is **not conducted on this scenario** as the primary rating
target. Near-uniform outcomes across conditions (≈91% consensus rate, ≈6-step
convergence) mean raters would not be able to meaningfully discriminate between
conditions from IC packets alone. However, IC packets are included as a
secondary check on whether the automated believability metrics generalise across
scenario types.

---

## 3. Experimental Architecture Common to Both Scenarios

### 3.1 Four-Condition Ablation

Both scenarios use the same four experimental conditions (C1–C4), defined in
`experiment_conditions.py`. The conditions are applied at the persona level:
each `Persona` object is assigned an `ExperimentalCondition` enum that gates
which cognitive modules are active during a trial.

The conditions implement a nested ablation — each condition is a strict superset
of the previous:

- **C1 (BASELINE):** No memory, no planning, no reflection. Agents make
  decisions based only on their persona identity and the immediate situational
  context. This establishes the null baseline — what an LLM agent does with
  no cognitive architecture beyond its static persona.

- **C2 (MEMORY_ONLY):** Adds scenario-constructed episodic memory. Agents
  receive summaries of what happened in prior rounds (pool state, peer
  behaviour for CD; vote tallies, shared statements for IC). Memory accumulates
  within a trial and is reset between trials.

- **C3 (MEMORY_PLANNING):** Adds Park et al. daily planning on top of C2.
  Agents generate a daily schedule and goal list at simulation start, which
  is included in their decision prompt alongside the scenario context and
  memory.

- **C4 (FULL):** Adds reflection on top of C3. After each round, agents
  generate a brief reflection about their behaviour and the group's outcome.
  Reflections are included in the prompt in addition to memories and plans.

### 3.2 Trial Independence

Each trial is a fully independent simulation. Trial isolation is enforced by:

- Cloning the base environment (`clone_scenario()`) before each trial
- Initialising a fresh `ReverieServer` and fresh `InformationConsensus` /
  `CommonsDilemma` instance per trial
- Resetting all scenario memories, vote histories, and pool state to initial
  values
- Using a per-trial random seed for LLM calls (`set_chat_seed(trial)`)

No memory or state carries forward between trials within the same condition.

### 3.3 Persona Architecture

Agent personas are drawn from the Park et al. Smallville base world
(`base_the_ville_n25`). Each persona has:

- A name and occupation
- A personality summary (`get_str_iss()`)
- Optionally: daily plans, associative memory, reflection capability

The same 8 personas are used across all conditions and all trials for both
scenarios, holding persona content constant across the ablation.

---

## References

Austen-Smith, D., & Banks, J. S. (1996). Information aggregation, rationality,
and the Condorcet jury theorem. *American Political Science Review*, *90*(1),
34–45.

Axelrod, R. (1984). *The evolution of cooperation*. Basic Books.

Banerjee, A. V. (1992). A simple model of herd behavior. *Quarterly Journal of
Economics*, *107*(3), 797–817.

Bikhchandani, S., Hirshleifer, D., & Welch, I. (1992). A theory of fads,
fashion, custom, and cultural change as informational cascades. *Journal of
Political Economy*, *100*(5), 992–1026.

de Condorcet, M. (1785). *Essai sur l'application de l'analyse à la probabilité
des décisions rendues à la pluralité des voix*. Imprimerie Royale.

Feddersen, T., & Pesendorfer, W. (1997). Voting behavior and information
aggregation in elections with private information. *Econometrica*, *65*(5),
1029–1058.

Hardin, G. (1968). The tragedy of the commons. *Science*, *162*(3859), 1243–1248.

Ostrom, E. (1990). *Governing the commons: The evolution of institutions for
collective action*. Cambridge University Press.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein,
M. S. (2023). Generative agents: Interactive simulacra of human behavior.
*Proceedings of UIST 2023*.
