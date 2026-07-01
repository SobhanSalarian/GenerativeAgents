# Paper-by-Paper Literature Alignment Notes

These notes were prepared one paper at a time against your project.

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


## Recommended order of use in your ICDM paper

| Priority | Paper | Where to use it |
|---|---|---|
| Very high | Galanti et al. (2008.01807) | Trace-based prediction/explanation of outcomes from event logs |
| Very high | Cemri et al. (2503.13657) | Multi-agent failure taxonomy and trace-level failure diagnosis |
| High | Velmurugan et al. (2012.04218) | Explanation stability/fidelity and functionally-grounded evaluation |
| High | AgentBench (2308.03688) | Positioning against LLM-agent capability benchmarks |
| High | AgentRewardBench (2504.08942) | Human/expert evaluation of agent trajectories and LLM judge calibration |
| Medium-high | Gao et al. (2312.11970) | Background/motivation for LLM-empowered ABM and evaluation challenge |

## One-paragraph synthesis for your related work

Existing work can be organised into four streams. First, LLM-empowered ABM surveys establish that LLMs can enrich simulation through more flexible reasoning, communication, and adaptation, but also identify evaluation as an unresolved challenge. Second, LLM-agent benchmarks such as AgentBench evaluate individual agent capability across interactive environments, but they do not test whether individually believable agents generate valid emergent group behaviour. Third, recent trajectory-evaluation work such as AgentRewardBench shows that automatic evaluation of agent trajectories should be calibrated against expert judgement. Fourth, explainable predictive process monitoring and functionally-grounded XAI provide methods for treating event logs as predictive traces and evaluating the stability/fidelity of explanations. Your project sits at the intersection of these streams by mining generative multi-agent simulation traces to test whether micro-level believability features predict and explain macro-level coordination success or failure.

## Main update to your literature review

Add this subsection:

### Trace-Based Data Mining for Micro-Macro Validation

Suggested content:
- Generative-agent simulations produce rich behavioural traces.
- These traces include numeric actions, natural-language reasoning, memory references, plan references, temporal interactions, and system-level outcomes.
- Event-log and predictive-process-monitoring literature shows how sequential traces can be mined to predict and explain outcomes.
- Agent trajectory evaluation literature shows that rule-based and LLM-based evaluators need human/expert calibration.
- Multi-agent failure-taxonomy work shows that final success/failure scores are insufficient; trace-level failure diagnosis is needed.
- Your contribution is to connect these ideas to ABM validation by linking micro-level believability to macro-level coordination.

## Final recommendation

For your thesis, the current literature review is broadly acceptable. For ICDM, update it with a new trace-mining layer and cite these six papers strategically.


---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 1 — Velmurugan et al. (2020): Functionally-Grounded Evaluation of Explainable Methods

**File:** `2012.04218v1.pdf`  
**Paper title:** *Evaluating Explainable Methods for Predictive Process Analytics: A Functionally-Grounded Approach*

## 1. What the paper is about

This paper is about **evaluating explanation methods** in predictive process analytics. The authors focus on predictive models that operate over event logs and then ask whether explanation methods such as **LIME** and **SHAP** are fit for purpose.

The key contribution is not a new predictive model. The contribution is an **evaluation method for explanations**. The paper uses a **functionally-grounded** approach, meaning that explanation quality is assessed using computational criteria rather than direct human-user evaluation.

The two main explanation-quality criteria are:

| Criterion | Meaning |
|---|---|
| **Stability** | Whether similar or repeated explanation runs produce consistent feature attributions. |
| **Fidelity** | Whether the explanation faithfully reflects the behaviour of the underlying black-box predictive model. |

A useful result from the paper is that **SHAP is generally more stable than LIME** in their predictive-process setting, while LIME can become unstable depending on feature-vector size and encoding strategy.

## 2. How this paper relates to your work

This paper is directly useful for the **ICDM framing** of your work, especially if you use predictive models and explainability methods to explain coordination success/failure.

Your current framework already has an **Explain** function through failure traceability. However, if you add predictive modelling — for example, predicting coordination success from micro-level features — you will probably also add explanations through feature importance or SHAP.

This paper gives you the methodological language to say:

> If we use post-hoc explanation methods to explain predicted coordination outcomes, those explanations should themselves be evaluated for stability and fidelity.

That is important because your failure-traceability claim should not rely only on a single unstable feature-attribution output.

## 3. What it adds to your literature review

Add this paper under a new ICDM-oriented subsection such as:

> **Trace-Based Data Mining and Explainable Predictive Analytics**

Use it to support the following argument:

> Predictive process analytics has already treated event logs as sequential behavioural data and has developed functionally-grounded ways to evaluate explanation methods. This is relevant to generative-agent simulations because agent-step logs can similarly be treated as behavioural traces, and explanation methods used to diagnose coordination outcomes should be evaluated for stability and fidelity.

## 4. How to update your method because of this paper

Add a small subsection in your ICDM paper or thesis methods:

### Explanation-quality checks

When using SHAP, LIME, or any feature-attribution method to explain coordination success/failure:

1. Generate explanations multiple times where applicable.
2. Check **stability by feature subset**: do the same top features appear across repeated explanations?
3. Check **stability by feature weight**: are the feature importance values consistent?
4. Where possible, check **fidelity**: perturb or remove highly attributed features and test whether the prediction changes in the expected direction.
5. Report explanation-quality limitations if the attributions are unstable.

This would strengthen your **failure traceability** section.

## 5. Specific mapping to your framework

| Paper concept | Your framework equivalent |
|---|---|
| Event log | Agent-step and system-step logs |
| Process instance | One simulation trial |
| Prefix length | Early/middle/late trial phases |
| Prediction outcome | Coordination success, collapse, sustainability, convergence |
| Explanation method | SHAP/feature importance for micro-to-macro prediction |
| Stability/fidelity | Robustness of failure-trace explanations |

## 6. Suggested text to add to related work

> Explainable predictive process analytics provides a useful bridge between event-log mining and explanation-oriented validation. Velmurugan et al. propose a functionally-grounded evaluation approach for explanation methods in predictive process analytics, focusing on stability and fidelity of explanations. This is relevant to generative-agent simulation because agent interaction logs can also be treated as sequential behavioural traces. If micro-level features extracted from such traces are used to predict macro-level coordination outcomes, explanation methods should be assessed not only for interpretability but also for stability and faithfulness to the predictive model.

## 7. Verdict for your work

**Priority:** High for ICDM framing.  
**Use this paper to justify:** explanation stability, explanation fidelity, and functionally-grounded evaluation of the “Explain” part of your framework.



---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 2 — Galanti et al. (2020): Explainable Predictive Process Monitoring

**File:** `2008.01807v2.pdf`  
**Paper title:** *Explainable Predictive Process Monitoring*

## 1. What the paper is about

This paper is about adding **explanation capabilities** to predictive process monitoring. In predictive process monitoring, the system predicts future process outcomes or KPIs from an event log. The paper argues that accurate predictions alone are not enough: users also need to know **why** a prediction was made.

The paper defines process data in terms of:

| Concept | Meaning |
|---|---|
| **Event** | A set of process attributes at a given moment. |
| **Trace** | A sequence of events for one process instance. |
| **Event log** | A collection of traces. |
| **KPI** | The future process outcome to be predicted, such as remaining time, cost, or activity occurrence. |
| **Prediction-explanation problem** | Identifying which attributes at which timestep influenced the predicted KPI. |

The paper uses **Shapley values** to explain predictions. It supports both:

- **Offline explanations**: global patterns across the test set.
- **Online explanations**: explanation of a specific running case.

## 2. How this paper relates to your work

This paper is one of the strongest bridges between your current ABM/GABM framing and an ICDM/data-mining framing.

Your simulation produces logs that can be treated like event logs:

| Process monitoring | Your project |
|---|---|
| Event | One agent decision at one round, or one system state at one round |
| Trace | One full simulation trial |
| Event log | All trials across conditions |
| KPI | Coordination success, collapse, sustainability, convergence speed |
| Explanation | Which micro-level features caused/predicted macro-level coordination outcome |

This paper helps you say:

> We treat generative-agent simulation outputs as behavioural event logs and formulate coordination success/failure as a trace-level prediction and explanation problem.

That sentence is very ICDM-compatible.

## 3. What it adds to your literature review

Add this paper to the proposed subsection:

> **Trace-Based Data Mining for Micro–Macro Validation**

It supports the claim that sequential traces can be mined for outcome prediction and explanation.

Your work differs because Galanti et al. focus on business-process logs, while you focus on **generative multi-agent simulation logs**. Their objective is to explain process KPIs; your objective is to explain whether micro-level generative-agent behaviour can generate, sustain, and explain macro-level coordination.

## 4. How to update your method because of this paper

Add a formal trace notation to your ICDM paper:

### Suggested notation

Let:

- `e_t^i` = event generated by agent `i` at round `t`.
- `x_t^i` = micro-level feature vector for that event, including request amount, reasoning features, memory-reference score, planning score, and response-naturalness score.
- `σ_j` = one trial trace, containing all agent events and system states across rounds.
- `Y_j` = macro-level outcome for trial `j`, such as coordination success, collapse, sustainability, or convergence speed.

Then define the predictive problem:

> Given a partial or complete simulation trace `σ_j`, predict macro-level outcome `Y_j`, and explain which micro-level attributes contributed most to that outcome.

This would make your paper much more data-mining-oriented.

## 5. Specific mapping to your framework

| Galanti et al. concept | Your framework equivalent |
|---|---|
| Process KPI | Coordination success / sustainability / collapse |
| Running case | Ongoing simulation trial |
| Event-log prediction | Predicting macro-level coordination from micro-level traces |
| Shapley explanation | Feature-level failure traceability |
| Offline explanation | Condition-level analysis across all trials |
| Online explanation | Trial-specific failure trajectory explanation |

## 6. Suggested text to add to related work

> Explainable predictive process monitoring treats process executions as event-log traces and seeks to predict and explain future KPIs such as remaining time, cost, or activity occurrence. Galanti et al. formulate the prediction-explanation problem over event traces and use Shapley values to identify which event attributes influence predicted outcomes. This perspective is useful for generative-agent simulations because a simulation trial can similarly be represented as a trace of agent decisions and system states, with macro-level coordination success or failure treated as the outcome to be predicted and explained.

## 7. Verdict for your work

**Priority:** Very high for ICDM framing.  
**Use this paper to justify:** treating simulation logs as event traces, predicting macro-level outcomes from trace features, and using SHAP/Shapley-style explanations for failure traceability.



---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 3 — Gao et al. (2023/2024): LLM-Empowered Agent-Based Modelling and Simulation Survey

**File:** `2312.11970v1.pdf`  
**Paper title:** *Large Language Models Empowered Agent-based Modeling and Simulation: A Survey and Perspectives*

## 1. What the paper is about

This survey reviews the use of large language models in agent-based modelling and simulation. It argues that LLMs can enrich ABM by giving agents stronger abilities in language, reasoning, communication, adaptation, and action generation.

The paper structures the field around several major themes:

| Theme | Meaning |
|---|---|
| **Agent capability** | Autonomy, social ability, reactivity, pro-activeness |
| **Simulation domains** | Cyber, physical, social, hybrid |
| **LLM-agent advantages** | Natural-language reasoning, flexible action generation, interaction with humans/agents |
| **Challenges** | Environment perception, human alignment, action generation, evaluation, scaling, robustness, ethics |

## 2. How this paper relates to your work

This paper is important for your **background and motivation**.

It supports your claim that LLMs are increasingly used as agents in simulations and that this creates a new methodological problem. The survey explicitly identifies **evaluation** as a key challenge, which aligns with your thesis contribution.

However, the survey does not solve your specific problem. It surveys the field and challenges, but it does not provide a controlled empirical framework that links:

> individual believability → emergent group coordination → failure traceability.

That is where your contribution should be positioned.

## 3. What it adds to your literature review

Keep this paper in the related work, but use it more strategically.

It should appear in:

### 2.1 Generative Agents in Agent-Based Simulation

Use it to establish that:

- LLM-empowered ABM is now an active research area.
- LLMs are attractive because they support richer agent cognition and social interaction.
- Evaluation remains unresolved.
- Existing work spans multiple domains, but systematic validation remains immature.

## 4. How to update your gap statement

Your current gap is already good, but after this paper you can sharpen it:

> Surveys of LLM-empowered ABM identify evaluation, robustness, and human alignment as open challenges. However, existing survey-level work does not operationalise a micro–macro validation framework or empirically test whether individual-level believability predicts emergent group coordination. This study addresses that gap by treating GABM outputs as behavioural traces and analysing how micro-level agent features relate to macro-level coordination outcomes.

## 5. How this paper supports your framework

| Survey concept | Your framework |
|---|---|
| Autonomy | Agents make repeated independent resource requests |
| Social ability | Agents must coordinate in the commons dilemma |
| Reactivity | Agents respond to resource-pool state and prior rounds |
| Pro-activeness | Planning and reflection modules support future-oriented decisions |
| Evaluation challenge | Your dual-level validation framework |
| Robustness challenge | Repeated trials, outcome variance, stochasticity management |
| Human alignment challenge | Human evaluation of believability dimensions |

## 6. What not to overclaim

Do not say this survey supports your specific hypotheses directly. It supports the **need** for evaluation, but not the specific claim that memory coherence and behavioural consistency predict coordination success. That claim must come from your experiment.

## 7. Suggested text to add to related work

> Recent surveys of LLM-empowered agent-based modelling argue that LLMs can enrich simulation by improving agent autonomy, social interaction, reactivity, and pro-activeness. At the same time, they identify evaluation, robustness, human alignment, and action generation as unresolved challenges. This motivates the present study, which focuses specifically on the evaluation problem: whether micro-level believability in generative agents is sufficient to generate, sustain, and explain macro-level coordination in agent-based simulations.

## 8. Verdict for your work

**Priority:** High for thesis background; medium for ICDM novelty.  
**Use this paper to justify:** the existence and importance of LLM-empowered ABM, and the fact that evaluation is an open challenge.



---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 4 — Liu et al. (2024): AgentBench

**File:** `2308.03688v3.pdf`  
**Paper title:** *AgentBench: Evaluating LLMs as Agents*

## 1. What the paper is about

AgentBench is a benchmark for evaluating LLMs as agents in interactive environments. It evaluates 29 LLMs across eight environments grouped into:

| Category | Environments |
|---|---|
| Code-grounded | Operating system, database, knowledge graph |
| Game-grounded | Digital card game, lateral thinking puzzle, house-holding |
| Web-grounded | Web shopping, web browsing |

The paper frames LLM-as-agent evaluation as an interactive decision-making problem and identifies common failure reasons, including:

- context limit exceeded,
- invalid format,
- invalid action,
- task limit exceeded,
- task completion.

The main focus is **agent capability**: whether the LLM can reason, decide, follow instructions, and complete tasks in interactive environments.

## 2. How this paper relates to your work

AgentBench is already useful in your related work, but you should be clearer about how your work differs from it.

AgentBench answers:

> How capable is an LLM when acting as an agent across interactive tasks?

Your work answers:

> Does believable individual generative-agent behaviour produce valid and explainable macro-level coordination in an agent-based simulation?

These are related but not the same.

AgentBench is a **benchmark of agent capability**. Your work is a **validation framework for simulation validity**.

This distinction is important for defending your novelty.

## 3. What it adds to your literature review

Use AgentBench in:

### 2.3 LLM-Agent Evaluation and Multi-Agent Coordination

It supports the claim that LLM-agent evaluation is mature in some ways, but still mostly focused on task performance rather than ABM-style micro–macro validation.

## 4. How to update your paper because of AgentBench

Add a short paragraph distinguishing **capability evaluation** from **simulation validation**.

### Suggested argument

- AgentBench evaluates whether an agent can complete tasks in different environments.
- Its metrics are mostly success/failure or environment-specific performance.
- It does not test whether individually believable agents generate valid emergent collective behaviour.
- Your framework fills this gap by linking micro-level believability dimensions to macro-level coordination outcomes and failure explanations.

## 5. Useful concepts to borrow carefully

| AgentBench concept | Possible use in your work |
|---|---|
| Interactive evaluation | Describe your commons dilemma as an interactive evaluation environment |
| Failure reasons | Use invalid output/action and task-limit/repetition as technical diagnostics |
| Multiple environments | Use as a benchmark standard; acknowledge that your current scenario has narrower ecological breadth |
| Server-client toolkit | Supports reproducibility and modular evaluation discussion |
| POMDP framing | Optional: not necessary unless you want a formal ML-style setup |

## 6. Potential threat to your work

An ICDM reviewer may ask:

> How is this different from agent benchmarks like AgentBench?

Your answer should be:

> AgentBench benchmarks LLM-agent task capability. Our work validates GABM simulations by linking micro-level believability features to macro-level emergent coordination outcomes. We are not ranking LLMs; we are testing whether agent-level believability is sufficient evidence for simulation validity.

## 7. Suggested text to add to related work

> AgentBench evaluates LLMs as agents across multiple interactive environments and shows that long-term reasoning, decision-making, and instruction following remain major obstacles for usable LLM agents. However, such benchmarks primarily assess task-level agent capability. They do not address the ABM validation question of whether individually believable agents generate valid and explainable collective dynamics. The present work complements benchmark-based agent evaluation by focusing on micro–macro validation in a controlled generative-agent simulation.

## 8. Verdict for your work

**Priority:** High for positioning against LLM-agent benchmarks.  
**Use this paper to justify:** why existing agent benchmarks are not enough for GABM validation.



---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 5 — Cemri et al. (2025): Why Do Multi-Agent LLM Systems Fail?

**File:** `2503.13657v3.pdf`  
**Paper title:** *Why Do Multi-Agent LLM Systems Fail?*

## 1. What the paper is about

This paper develops a systematic failure analysis for multi-agent LLM systems. It introduces:

- **MAST-Data:** a dataset of more than 1600 annotated multi-agent execution traces.
- **MAST:** a Multi-Agent System Failure Taxonomy.
- A human-annotation process with strong inter-annotator agreement.
- An LLM-as-judge pipeline calibrated against human annotations.

The taxonomy contains 14 failure modes grouped into three broad categories:

| Category | Examples |
|---|---|
| **System design issues** | disobey task specification, disobey role specification, step repetition, loss of conversation history, unaware of termination conditions |
| **Inter-agent misalignment** | conversation reset, failure to ask for clarification, task derailment, information withholding, ignoring other agents’ input, reasoning-action mismatch |
| **Task verification** | premature termination, incomplete verification, incorrect verification |

## 2. How this paper relates to your work

This is probably the **most important paper** among the six for strengthening your **failure traceability** section.

Your framework already includes failure traceability, but your current categories are more specific to your commons-dilemma setup:

- memory failures,
- consistency failures,
- planning failures,
- self-interest dominance,
- information-integration failures.

MAST gives you a broader multi-agent failure taxonomy that can support or refine your coding scheme.

## 3. How to use it without losing your originality

Do not replace your failure taxonomy completely with MAST.

Instead, use MAST as a **supporting taxonomy** and adapt it to GABM validation.

Your contribution is not simply “classifying MAS failures”. MAST already does that. Your contribution is:

> linking micro-level believability failures to macro-level coordination breakdowns in generative agent-based simulation.

So your failure traceability should remain micro–macro oriented.

## 4. Suggested mapping to your failure categories

| Your category | Related MAST concept |
|---|---|
| Behavioural consistency failure | Disobey role specification; reasoning-action mismatch |
| Memory coherence failure | Loss of conversation history; ignored input |
| Planning plausibility failure | Reasoning-action mismatch; task derailment |
| Information-integration failure | Ignored other agent’s input; information withholding |
| Self-interest dominance | Role/specification misalignment in coordination context |
| Repetition / volatile behaviour | Step repetition; task derailment |
| Premature collapse explanation | Incomplete verification; unaware of termination/fair-share conditions |

## 5. How to update your methodology

Add a short paragraph to your failure-traceability subsection:

> The failure-coding scheme is informed by recent multi-agent LLM failure-taxonomy work but adapted to the ABM validation objective. Rather than classifying all possible MAS failures, the coding focuses on failures that can be linked to macro-level coordination breakdowns.

Then mention that your coding scheme has two layers:

### Layer 1 — General MAS failure mode

Examples:
- role inconsistency,
- ignored information,
- reasoning-action mismatch,
- repetition,
- task derailment.

### Layer 2 — Micro–macro validation consequence

Examples:
- over-requesting,
- inability to converge,
- collapse of fund,
- unstable role differentiation,
- high demand pressure.

This two-layer coding would make your failure traceability much stronger.

## 6. How to update human evaluation

MAST uses expert annotation and inter-annotator agreement. Your work also uses trained human evaluators. This supports your plan to report reliability.

You can strengthen your protocol by adding:

- a calibration round,
- overlap items,
- disagreement adjudication,
- inter-rater reliability for failure categories as well as believability ratings.

## 7. Suggested text to add to related work

> Recent work on multi-agent LLM systems has moved beyond aggregate task scores toward systematic failure diagnosis. Cemri et al. introduce MAST, a taxonomy of multi-agent LLM failure modes derived from annotated execution traces, including system-design issues, inter-agent misalignment, and task-verification failures. This line of work is relevant because it shows that multi-agent evaluation requires trace-level failure analysis rather than final success scores alone. The present study builds on this direction but adapts failure analysis to the ABM validation problem: tracing how micro-level believability deficiencies produce macro-level coordination breakdowns.

## 8. Verdict for your work

**Priority:** Very high.  
**Use this paper to strengthen:** failure traceability, human annotation, failure taxonomy, inter-rater reliability, and ICDM trace-mining framing.



---

# Project context used for all notes

Your project: **Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination**.

Core contribution:
- A **dual-level validation framework** for generative agent-based models (GABMs).
- Micro level: behavioural consistency, memory coherence, planning plausibility, response naturalness.
- Macro level: coordination effectiveness, stability/robustness, emergent structure, failure traceability.
- Experimental design: four architecture conditions — baseline, memory, memory + planning, full memory + planning + reflection — evaluated in a commons-dilemma coordination task.
- ICDM framing under consideration: **trace-based mining of generative multi-agent simulation logs to predict and explain emergent coordination success/failure**.


# Paper 6 — Lù et al. (2025): AgentRewardBench

**File:** `2504.08942v2.pdf`  
**Paper title:** *AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories*

## 1. What the paper is about

AgentRewardBench evaluates whether LLM judges can accurately assess web-agent trajectories. It contains more than 1300 trajectories across several web-agent benchmarks. Each trajectory is reviewed by expert annotators across three dimensions:

| Dimension | Meaning |
|---|---|
| **Success** | Whether the agent completed the task. |
| **Side effects** | Whether the agent caused unintended consequences. |
| **Repetition** | Whether the agent repeated unnecessary actions. |

The paper compares LLM judges with expert annotations and finds that rule-based evaluation can underreport success because it may reject valid trajectories. It also shows that LLM judges are useful but not uniformly reliable across tasks and benchmarks.

## 2. How this paper relates to your work

This paper is highly relevant to your **human-evaluation webpage** and your use of automated or LLM-assisted scores.

Your project includes human evaluators who rate agent decision packets. You also plan to use automated proxies and possibly LLM-assisted rubric judges. AgentRewardBench gives you a strong reason to say:

> Automatic evaluation of agent trajectories should be calibrated against human/expert judgement, because rule-based and LLM-based evaluators may not fully reflect human assessment.

This directly supports your blended human + automated evaluation design.

## 3. What it adds to your literature review

Add this paper under:

### 2.3 LLM-Agent Evaluation and Multi-Agent Coordination

or under the new section:

### 2.4 Trace-Based Data Mining for Micro–Macro Validation

It helps position your human evaluation as part of a broader movement toward **trajectory-level agent evaluation**.

## 4. What you should borrow conceptually

The paper’s three expert-evaluation dimensions suggest useful additions to your diagnostics:

| AgentRewardBench dimension | Your possible equivalent |
|---|---|
| Success | Coordination success / sustained coordination |
| Side effects | Unintended macro-level instability, inequity, resource collapse |
| Repetition | Repeated over-requesting, repeated generic reasoning, unstable loops |
| Expert annotation | Human evaluation of decision packets |
| LLM judge calibration | Human-validation of LLM-assisted planning/naturalness scores |

## 5. How to update your method because of this paper

Add a paragraph explaining why you use human evaluation despite having automated proxies:

> Automated metrics are scalable but may fail to capture legitimate variation in agent reasoning or trajectory success. Following recent work on agent trajectory evaluation, human ratings are used to validate automated and LLM-assisted evaluators rather than assuming that rule-based or model-based scores are sufficient.

Also add a diagnostic for **repetition**:

- repeated reasoning templates,
- repeated failure to adjust demand,
- repeated irrelevant memory references,
- repeated plan statements without behavioural change.

You already partially include repetition under response naturalness, but this paper supports making it more explicit as a trajectory-level diagnostic.

## 6. How it strengthens your ICDM paper

This paper supports a strong ICDM-style evaluation pipeline:

1. Generate agent trajectories.
2. Extract automated features.
3. Use human evaluators to annotate selected packets or trajectories.
4. Calibrate automated/LLM-assisted metrics against human ratings.
5. Use the validated features to predict macro-level coordination outcomes.

This is exactly the kind of pipeline ICDM reviewers will understand.

## 7. Suggested text to add to related work

> Agent trajectory evaluation has increasingly focused on whether automatic evaluators align with expert judgement. AgentRewardBench evaluates LLM judges for web-agent trajectories using expert annotations of success, side effects, and repetition, showing that rule-based evaluation may reject valid trajectories and that LLM judges vary across settings. This supports the need for human-validated evaluation in generative-agent simulations: automated proxies can scale across logs, but human ratings remain important for assessing whether agent reasoning and behaviour are genuinely believable in context.

## 8. Verdict for your work

**Priority:** High.  
**Use this paper to justify:** human-evaluation webpage, paid annotators, LLM-as-judge calibration, and caution against relying only on rule-based or automated evaluation.

