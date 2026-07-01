# Literature Review / Related Work Update Plan

This Markdown file was prepared from the attached text. It summarises the recommended updates to the literature review or related work section for the ICDM-oriented version of the project.

---

## 1. Main Recommendation

Add **one new subsection**, rather than rewriting the whole literature review:

## 2.X Trace-Based Data Mining for Micro–Macro Validation

This should be the new **ICDM-oriented** section.

The core argument should be:

> Generative-agent simulations produce rich behavioural traces, including actions, natural-language reasoning, memory references, plans, temporal interaction patterns, and system-level outcomes. Existing GABM validation work recognises the need for micro–macro validation, but has not sufficiently treated these simulation outputs as trace data that can be mined to predict and explain coordination success or failure.

This connects the work directly to ICDM by framing the project as a **trace-based data-mining contribution**, not only a GABM validation framework.

---

## 2. Papers to Add and How to Use Them

| Paper | Add? | Where to use it | Why |
|---|---|---|---|
| **Galanti et al., _Explainable Predictive Process Monitoring_** | Yes — high priority | New trace-mining subsection | Supports treating logs as traces and predicting/explaining future KPIs. Their event-log framing maps well to simulation trials and coordination outcomes. |
| **Velmurugan et al., _Functionally-Grounded XAI Evaluation_** | Yes — high priority | Explanation / SHAP / evaluation subsection | Supports checking explanation quality through stability and fidelity, useful if SHAP or feature importance is used for coordination-failure explanation. |
| **Cemri et al., _Why Do Multi-Agent LLM Systems Fail?_** | Yes — very high priority | Failure traceability subsection | Supports the failure-traceability layer with a recent MAS failure taxonomy, annotated traces, human agreement, and LLM-as-judge calibration. |
| **AgentRewardBench** | Yes — high priority | Human evaluation / trajectory evaluation | Supports expert/human evaluation of trajectories and warns that rule-based or LLM judges may not align with expert judgement. |
| **AgentBench** | Yes, but concise | LLM-agent benchmark subsection | Use it to show that existing benchmarks evaluate agent task capability, not ABM-style micro–macro simulation validity. |
| **Gao et al. LLM-ABM survey** | Yes, but mostly background | Generative agents in ABM | Use it to show LLM-empowered ABM is growing and that evaluation remains an open challenge. |

---

## 3. Recommended Related Work Structure

Use the following structure:

### 2.1 Agent-Based Modelling and Micro–Macro Validation

Keep the current content. Do not expand it too much. This is the theoretical foundation.

### 2.2 Generative Agents in Agent-Based Simulation

Keep Park et al. and add Gao et al. here.

Use Gao et al. mainly to show that:

- LLM-empowered ABM is emerging;
- evaluation remains an open challenge;
- robustness, action generation, and human alignment are unresolved issues.

### 2.3 LLM-Agent Evaluation and Multi-Agent Coordination

Keep AgentBench and similar benchmark papers here.

Make the contrast clear:

> These benchmarks evaluate whether LLMs can act as agents in interactive environments, but they do not test whether believable agents generate valid collective simulation outcomes.

### 2.4 Trace-Based Data Mining for Micro–Macro Validation

Add this as the main new section.

Include:

- Galanti et al.;
- Velmurugan et al.;
- AgentRewardBench;
- Cemri et al.

This section should say that the project treats simulation logs as **heterogeneous behavioural traces**.

The traces include:

- request amount;
- granted amount;
- reasoning text;
- memory reference;
- plan reference;
- fair-share ratio;
- resource state;
- demand pressure;
- collapse status;
- coordination score;
- sustainability;
- failure category.

The methods report already describes this kind of per-step logging and the use of automated plus human-validated micro/macro metrics.

---

## 4. Exact Gap Statement to Add

Replace or extend the current gap with the following:

> Existing GABM validation research has recognised the need to assess both individual agent behaviour and aggregate simulation outcomes. However, prior work has not sufficiently treated generative-agent simulations as behavioural trace-mining problems. As a result, there is limited empirical evidence on whether micro-level features extracted from agent decision traces can predict, explain, or diagnose macro-level coordination success and failure. This study addresses that gap by combining dual-level GABM validation with trace-based predictive and explanatory analysis.

This is the strongest ICDM-oriented framing.

---

## 5. Paragraph to Add to the Related Work Section

Add the following paragraph after the current LLM-agent evaluation section:

> Recent work in predictive process monitoring provides a useful methodological bridge for analysing generative-agent simulations as trace data. In explainable predictive process monitoring, event logs are represented as sequences of events, and future process outcomes or KPIs are predicted and explained from those traces. This perspective is relevant to GABMs because each simulation trial can be represented as a behavioural trace containing agent actions, reasoning, memory references, planning references, and system states. Similarly, recent work on agent trajectory evaluation shows that automatic or rule-based evaluation may not fully align with expert judgement, motivating the use of human-validated evaluation protocols. Recent multi-agent failure-taxonomy work further demonstrates the value of analysing execution traces to identify failure modes rather than relying only on aggregate success scores. Building on these strands, the present study treats generative-agent simulation logs as behavioural traces and examines whether micro-level features predict and explain macro-level coordination outcomes.

---

## 6. Sentence to Distinguish the Work from AgentBench

Add the following sentence where AgentBench is discussed:

> Unlike LLM-agent benchmarks such as AgentBench, which evaluate whether individual LLMs can complete tasks across interactive environments, this study evaluates whether individual-level believability in generative agents is sufficient to generate, sustain, and explain valid emergent coordination in an agent-based simulation.

This is important because reviewers may ask:

> How is this different from agent benchmarks?

---

## 7. Sentence for Failure Traceability

Add the following sentence to strengthen the failure-traceability argument:

> Recent multi-agent failure-taxonomy work shows that aggregate task success is insufficient for understanding multi-agent systems; trace-level diagnosis is needed to identify whether failures arise from system-design issues, inter-agent misalignment, or verification failures. This study adapts that trace-level diagnostic logic to GABM validation by linking coordination breakdowns to micro-level believability deficiencies.

---

## 8. Final Recommendation

For the thesis, add a **short version** of the new trace-based data-mining section.

For the ICDM paper, make this section **central**.

The paper should not look only like:

> A validation framework for generative agent-based models.

It should look like:

> A trace-based data-mining approach for predicting and explaining emergent coordination in generative multi-agent simulations.

The main addition is therefore:

## Trace-Based Data Mining for Micro–Macro Validation

This is the missing literature-review piece.
