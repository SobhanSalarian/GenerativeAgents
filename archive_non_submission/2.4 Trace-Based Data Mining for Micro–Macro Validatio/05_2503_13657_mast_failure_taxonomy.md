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

