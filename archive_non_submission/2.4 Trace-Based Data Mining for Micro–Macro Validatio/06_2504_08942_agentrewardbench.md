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

