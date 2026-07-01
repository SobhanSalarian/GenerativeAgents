# Discussion Summary: Consensus Search, Literature Review Updates, Paper-by-Paper Notes, and Title Framing

**Date:** 24 May 2026  
**Scope covered:** From the request *“now, using the GPT Explore Consensus tool, see how should update the literature if needed”* through the discussion about whether “framework” should remain in the ICDM paper title.

---

## 1. Consensus Tool Attempt

You asked to use the GPT Explore / Consensus tool to assess whether the literature review or related work section needed updating.

The Consensus connector was attempted, but it failed to connect in the session. Because of that, the literature-review assessment was completed using:

- the uploaded thesis/project documents,
- the uploaded research papers,
- scholarly/public web checking where needed,
- and the project’s existing framework and ICDM positioning.

The conclusion was that the related work **does need targeted updating**, especially if the target is **ICDM**.

---

## 2. Main Literature Review Judgement

The existing literature review is already strong for the thesis because it covers:

1. Agent-based modelling validation
2. Microface and macroface validation
3. Generative agents
4. GABM validation
5. LLM-agent evaluation
6. Multi-agent coordination

However, for an ICDM paper, it needs an additional **data-mining layer**.

The key recommendation was to add a new subsection:

## **Trace-Based Data Mining for Micro–Macro Validation**

This section should reframe generative-agent simulation outputs as **behavioural traces** that can be mined to predict and explain macro-level outcomes.

---

## 3. Why the New Section Is Needed

The current thesis framing is:

> A dual-level validation framework for generative agent-based models.

That is appropriate for a thesis and for ABM/simulation venues.

For ICDM, the framing needs to become more computational and data-mining oriented:

> A trace-based data-mining approach for predicting and explaining emergent coordination in generative multi-agent simulations.

The added section should explain that generative-agent simulations produce rich trace data, including:

- numeric requests,
- granted amounts,
- natural-language reasoning,
- memory references,
- plan references,
- fair-share ratios,
- resource states,
- demand pressure,
- collapse status,
- coordination score,
- sustainability score,
- failure categories.

This strengthens the ICDM fit because it connects the project to behavioural trace mining, predictive analytics, explainability, and failure diagnosis.

---

## 4. Updated Related Work Structure

The recommended ICDM-related-work structure is:

### **2.1 Agent-Based Modelling and Micro–Macro Validation**

Keep the current theoretical foundation. Include microface validation, macroface validation, and generative sufficiency.

### **2.2 Generative Agents in Agent-Based Simulation**

Keep Park et al. and add Gao et al. Use this section to show that LLM-empowered ABM is emerging and that evaluation remains an open challenge.

### **2.3 LLM-Agent Evaluation and Multi-Agent Coordination**

Use AgentBench and related agent-evaluation work here. The key distinction is that existing benchmarks evaluate agent capability, while your work evaluates simulation validity.

### **2.4 Trace-Based Data Mining for Micro–Macro Validation**

Add this as the main new section for ICDM. Include predictive process monitoring, explainable process monitoring, agent trajectory evaluation, and multi-agent failure taxonomy.

---

## 5. Suggested ICDM Gap Statement

The recommended ICDM-style gap statement was:

> Existing GABM validation research has recognised the need to assess both individual agent behaviour and aggregate simulation outcomes. However, prior work has not sufficiently treated generative-agent simulations as behavioural trace-mining problems. As a result, there is limited empirical evidence on whether micro-level features extracted from agent decision traces can predict, explain, or diagnose macro-level coordination success and failure. This study addresses that gap by combining dual-level GABM validation with trace-based predictive and explanatory analysis.

This gap statement is stronger for ICDM than only saying that the field lacks a validation framework.

---

## 6. Papers Reviewed One by One

You then uploaded six papers and asked to read them one by one, prepare Markdown notes against your work, and proceed to the next.

The six papers were:

1. `2012.04218v1.pdf`
2. `2008.01807v2.pdf`
3. `2312.11970v1.pdf`
4. `2308.03688v3.pdf`
5. `2503.13657v3.pdf`
6. `2504.08942v2.pdf`

A ZIP file and a master Markdown file were created containing one note file per paper and an integration plan.

Created files:

- `all_papers_against_my_work.md`
- `paper_alignment_notes_against_my_work.zip`

---

## 7. Paper-by-Paper Findings

### 7.1 Velmurugan et al. — Functionally-Grounded XAI Evaluation

**Use in your work:** Explanation quality.

This paper supports the idea that if you use SHAP, LIME, or feature-importance methods to explain coordination success/failure, those explanations should be evaluated for:

- stability,
- fidelity,
- robustness.

**How it helps your framework:**

It strengthens the **Explain** function of your framework by showing that explanations should not be accepted uncritically. If failure traceability uses model explanations, those explanations should be checked for stability and faithfulness.

**Recommended use:**

Add it to the new trace-mining / explainable-predictive-analytics subsection.

---

### 7.2 Galanti et al. — Explainable Predictive Process Monitoring

**Use in your work:** Trace-based prediction and explanation.

This was judged as one of the strongest papers for ICDM framing.

The paper treats process executions as event logs and predicts future KPIs from traces. This maps well to your work:

| Predictive process monitoring | Your project |
|---|---|
| Event | Agent decision or system state at one round |
| Trace | One simulation trial |
| Event log | All trials across conditions |
| KPI | Coordination success, collapse, sustainability, convergence |
| Explanation | Which micro-level features influenced macro-level outcome |

**Recommended use:**

Use it to justify treating simulation logs as event traces and coordination success/failure as a trace-level prediction and explanation problem.

---

### 7.3 Gao et al. — LLM-Empowered Agent-Based Modelling and Simulation Survey

**Use in your work:** Background and motivation.

This paper supports the claim that LLMs are increasingly used in ABM and simulation. It identifies evaluation, robustness, environment perception, action generation, and human alignment as important challenges.

**How it helps:**

It supports the need for your study, but it does not directly solve your research problem.

**Recommended use:**

Use it in the background section on generative agents in ABM, not as the main novelty anchor.

---

### 7.4 AgentBench

**Use in your work:** Distinguishing your contribution from LLM-agent benchmarks.

AgentBench evaluates LLMs as agents across multiple interactive environments. Its focus is agent capability, including reasoning, decision-making, and instruction following.

**Key distinction:**

AgentBench asks:

> Can an LLM act as an agent and complete tasks?

Your work asks:

> Does believable individual generative-agent behaviour produce valid and explainable macro-level coordination in an ABM simulation?

**Recommended use:**

Use AgentBench to position your work against existing agent benchmarks and explain why they are not sufficient for GABM validation.

---

### 7.5 Cemri et al. — Why Do Multi-Agent LLM Systems Fail?

**Use in your work:** Failure traceability.

This was judged as one of the most important papers for your framework.

The paper introduces:

- MAST-Data,
- a multi-agent system failure taxonomy,
- annotated traces,
- human agreement,
- LLM-as-judge annotation.

It identifies failure categories such as:

- system-design issues,
- inter-agent misalignment,
- task-verification failures.

**How it helps your work:**

It strengthens your failure-traceability coding scheme. However, the recommendation was **not** to replace your own failure categories. Instead, MAST should be used as a supporting taxonomy.

Your contribution remains different:

> Your work links micro-level believability failures to macro-level coordination breakdowns in generative agent-based simulations.

**Recommended update:**

Use a two-layer failure coding scheme:

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
- failure to converge,
- fund collapse,
- unstable role differentiation,
- high demand pressure.

---

### 7.6 AgentRewardBench

**Use in your work:** Human evaluation and LLM-as-judge calibration.

This paper evaluates automatic evaluation of web-agent trajectories and compares LLM judges against expert annotations.

It supports your decision to use human evaluators and not rely only on automated or rule-based metrics.

**How it helps:**

It strengthens your human-evaluation webpage, paid annotator setup, and human-validation logic.

**Recommended use:**

Use it to justify:

- human-validated agent evaluation,
- caution against relying only on rule-based scores,
- calibrating LLM-assisted ratings against human judgement,
- trajectory-level evaluation rather than only final success/failure.

---

## 8. Recommended Priority of Papers

The papers were ranked for use in the ICDM paper as follows:

| Priority | Paper | Main use |
|---|---|---|
| Very high | Galanti et al. | Trace-based prediction/explanation from event logs |
| Very high | Cemri et al. | Multi-agent failure taxonomy and trace-level failure diagnosis |
| High | Velmurugan et al. | Explanation stability and fidelity |
| High | AgentRewardBench | Human/expert evaluation of trajectories and LLM judge calibration |
| High | AgentBench | Positioning against LLM-agent capability benchmarks |
| Medium-high | Gao et al. | Background on LLM-empowered ABM and evaluation challenges |

---

## 9. Final Recommendation on Related Work

The recommendation was:

> Do not rewrite the whole literature review. Add one new ICDM-oriented section on trace-based data mining and adjust the gap statement.

The section to add is:

## **Trace-Based Data Mining for Micro–Macro Validation**

This section should connect four literatures:

1. Explainable predictive process monitoring
2. Functionally-grounded XAI evaluation
3. Agent trajectory evaluation
4. Multi-agent failure taxonomy

The section should then position your work as the bridge between:

- ABM validation,
- LLM-agent evaluation,
- behavioural trace mining,
- explainable coordination-failure diagnosis.

---

## 10. Suggested Paragraph for the New Related Work Section

A suggested paragraph was:

> Recent work in predictive process monitoring provides a useful methodological bridge for analysing generative-agent simulations as trace data. In explainable predictive process monitoring, event logs are represented as sequences of events, and future process outcomes or KPIs are predicted and explained from those traces. This perspective is relevant to GABMs because each simulation trial can be represented as a behavioural trace containing agent actions, reasoning, memory references, planning references, and system states. Similarly, recent work on agent trajectory evaluation shows that automatic or rule-based evaluation may not fully align with expert judgement, motivating the use of human-validated evaluation protocols. Recent multi-agent failure-taxonomy work further demonstrates the value of analysing execution traces to identify failure modes rather than relying only on aggregate success scores. Building on these strands, the present study treats generative-agent simulation logs as behavioural traces and examines whether micro-level features predict and explain macro-level coordination outcomes.

---

## 11. Discussion About “Framework” in the Title

You asked why “framework” had been removed from the suggested title.

The clarification was:

> “Framework” should not be removed completely. The issue is that for ICDM, the title should not sound like a purely conceptual framework paper.

ICDM reviewers usually expect empirical, computational, or data-mining contributions. Therefore, the recommendation was to keep **framework**, but pair it with language such as:

- trace mining,
- behavioural traces,
- prediction,
- explanation,
- micro–macro validation,
- coordination failure diagnosis.

---

## 12. Recommended Title Options

The strongest recommended title was:

## **A Dual-Level Trace-Mining Framework for Micro–Macro Validation of Generative Agent-Based Models**

Other options included:

1. **A Trace-Based Data Mining Framework for Validating Emergent Coordination in Generative Agent-Based Simulations**

2. **From Believability to Coordination: A Trace-Based Validation Framework for Generative Agent-Based Models**

3. **Mining Micro-Level Agent Traces: A Dual-Level Framework for Validating Emergent Coordination in Generative Simulations**

4. **Predicting and Explaining Coordination Failures in Generative Multi-Agent Simulations: A Trace-Based Validation Framework**

The final clarification was:

> The word “framework” should stay, because it is your core contribution. But for ICDM, it should be combined with “trace-mining” or “data mining” so the title signals both the methodological contribution and the data-mining relevance.

---

## 13. Final Position at the End of This Discussion

The final position was:

- Your **framework remains central**.
- The title should still include **framework**.
- The related work should be updated with a new trace-mining subsection.
- The ICDM version should frame the paper as a **dual-level trace-mining framework**.
- Your originality is not only the metrics, but the integration of:
  - micro-level believability,
  - macro-level coordination,
  - trace-based predictive analysis,
  - failure traceability,
  - human-validated evaluation.

The best short framing is:

> This study proposes a dual-level trace-mining framework for validating generative agent-based models by testing whether micro-level believability features extracted from agent decision traces can generate, sustain, and explain macro-level coordination outcomes.

---

## 14. Immediate Next Step

The next useful task would be to draft the actual **updated Related Work section** using the new structure:

1. Agent-Based Modelling and Micro–Macro Validation
2. Generative Agents in Agent-Based Simulation
3. LLM-Agent Evaluation and Multi-Agent Coordination
4. Trace-Based Data Mining for Micro–Macro Validation

The most important new subsection is the fourth one.
