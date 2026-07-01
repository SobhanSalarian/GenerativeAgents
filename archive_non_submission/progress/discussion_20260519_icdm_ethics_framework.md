# Summary of Today’s Discussion: Framework, ICDM Paper Potential, Ethics, and Related Work

**Date:** 24 May 2026  
**Project:** Validation of Generative Agents in Agent-Based Models: Linking Individual Believability to Emergent Group Coordination

---

## 1. Framework: Main Understanding

The project’s framework is a **dual-level validation framework** for generative agent-based models (GABMs). It is designed to connect:

- **Micro-level validation:** whether individual generative agents behave believably.
- **Macro-level validation:** whether groups of agents produce valid emergent coordination.

The framework is not just a diagram or a list of metrics. It is the methodological logic of the thesis: individual believability should be tested in relation to group-level coordination outcomes.

### Micro-level dimensions

The individual-agent level includes four believability dimensions:

1. **Behavioural consistency**  
   Whether the agent behaves consistently with its persona and previous behaviour.

2. **Memory coherence**  
   Whether the agent retrieves and uses relevant prior coordination-task information.

3. **Planning plausibility**  
   Whether the agent’s stated plan logically connects to its decision.

4. **Response naturalness**  
   Whether the agent’s explanation sounds human-like and contextually plausible.

### Macro-level criteria

The system-level validation includes:

1. **Coordination effectiveness**
2. **Stability and robustness**
3. **Emergent structure**
4. **Failure traceability**

### Key framework functions

The framework can be summarised through three functions:

| Function | Meaning |
|---|---|
| **Generate** | Can micro-level mechanisms produce macro-level coordination? |
| **Sustain** | Does coordination remain stable over time and across trials? |
| **Explain** | Can coordination failures be traced back to micro-level deficiencies? |

The strongest and most original part of the framework is **failure traceability**, because it links macro-level coordination failures back to specific micro-level agent problems such as weak memory use, inconsistent behaviour, poor planning, or self-interested over-requesting.

---

## 2. ICDM Suitability: Honest Assessment

The project can potentially be developed into an **ICDM paper**, but it should not be framed mainly as an ABM methodology paper.

The current thesis framing is:

> A dual-level validation framework for generative agent-based models.

For ICDM, the stronger framing is:

> Mining generative multi-agent behavioural traces to predict and explain emergent coordination outcomes.

### Honest suitability judgement

| Target | Suitability |
|---|---|
| **ICDM 2026 main track** | Possible but challenging unless final results are ready very soon. |
| **ICDM 2026 workshop** | Stronger and more realistic. |
| **ICDM 2026 PhD Forum** | Very suitable. |
| **ICDM 2027 main track** | Realistic if the full experiment, human evaluation, and analysis are completed properly. |

The work becomes ICDM-suitable if the paper emphasises:

- behavioural trace mining,
- feature extraction from agent logs,
- prediction of coordination success/failure,
- failure diagnosis,
- explainable modelling,
- human-validated automated metrics,
- ablation across agent architectures.

### Suggested ICDM-style titles

Possible titles:

1. **Mining Micro-Level Behavioural Traces to Validate Emergent Coordination in Generative Agent-Based Simulations**

2. **From Believability to Coordination: Trace-Based Data Mining for Validating Generative Multi-Agent Simulations**

3. **Predicting and Explaining Coordination Failures in Generative Multi-Agent Simulations Using Behavioural Trace Mining**

Avoid a title that sounds only methodological, such as:

> A Dual-Level Validation Framework for Generative Agent-Based Models

That title is more suitable for ABM, simulation, or multi-agent-system venues than ICDM.

---

## 3. What Is Needed for an ICDM Paper

To make the project strong enough for ICDM, the manuscript should include the following components.

### Required empirical components

1. **Completed experiment matrix**
   - Four conditions
   - 20 trials per condition
   - Eight agents per trial
   - Up to 100 rounds per trial

2. **Structured dataset**
   - Agent-step logs
   - System-level logs
   - Trial summaries
   - Condition summaries
   - Failure labels or categories

3. **Micro-level feature extraction**
   - Behavioural consistency
   - Memory coherence
   - Planning plausibility
   - Response naturalness

4. **Macro-level outcomes**
   - Coordination success
   - Coordination score
   - Sustainability
   - Demand pressure
   - Gini coefficient
   - Convergence speed
   - Outcome variance
   - Failure traceability

5. **Predictive modelling**
   - Logistic regression
   - Random forest or gradient boosting
   - Possibly ordinal or survival-style models for convergence/collapse

6. **Explainability**
   - Feature importance
   - SHAP values or similar explanation methods
   - Failure-category analysis

7. **Baselines**
   - Architecture-only baseline
   - Request-only baseline
   - Macro-only baseline
   - No-traceability baseline

8. **Human validation**
   - Human rating results
   - Inter-rater reliability
   - Comparison between human ratings and automated proxies

---

## 4. Ethics Discussion

The project uses human evaluators to rate anonymised AI-agent decision packets. Because these ratings are used as research evidence, this may count as human-participant research, even though the task is low risk.

The evaluation being online through a webpage is helpful because it reduces burden and standardises the process, but it does not automatically remove the ethics question.

### Why ethics may still matter

Ethics is relevant because:

- human evaluators provide judgement data,
- their ratings are used in thesis/paper analysis,
- the ratings validate or blend with automated metrics,
- evaluators are being paid,
- the research is conducted under a university project.

The likely pathway is not necessarily full HREC review. It may be:

- negligible-risk confirmation,
- low-risk review,
- exemption confirmation,
- or another internal pathway advised by the supervisor or ethics office.

### Important action

Ask **Professor Amin Beheshti** urgently:

> Because the human evaluation is conducted online using paid evaluators who rate anonymised AI-agent decision packets, can we confirm whether this requires low-risk ethics review, exemption confirmation, or another Macquarie ethics pathway before the results are used in the thesis or paper?

---

## 5. Web-Based Human Evaluation

Preparing a webpage for the human evaluation is a strong design choice. It makes the evaluation more professional and scalable.

### Benefits of the webpage

The webpage helps because it provides:

- standardised instructions,
- consistent presentation of decision packets,
- condition blinding,
- easier remote participation,
- structured Likert rating collection,
- better reproducibility,
- easier export of human-evaluation data.

### Recommended webpage elements

The webpage should include:

1. Participant/evaluator information section
2. Consent checkbox
3. Description of the rating task
4. Estimated time
5. Payment information
6. Withdrawal statement
7. Data-use statement
8. Contact information
9. Rubric definitions
10. Condition-blinded decision packets
11. Final submission confirmation

---

## 6. Paying Human Evaluators

Paying evaluators is acceptable and may strengthen the project, but it must be documented carefully.

### Key principles

Payment should be:

- fixed,
- fair,
- not tied to specific answers,
- not tied to agreement with expected results,
- clearly stated before the task,
- documented.

The evaluators should be described as **paid human evaluators** or **paid annotators** who rate anonymised AI-agent decision packets.

### Suggested manuscript wording

> Human evaluation was conducted through a web-based annotation interface. Paid evaluators reviewed anonymised AI-agent decision packets and scored behavioural consistency, memory coherence, planning plausibility, and response naturalness using structured rubrics. Evaluators were compensated at a fixed rate independent of rating outcomes. Condition labels were concealed, and ratings were analysed only in aggregated form.

---

## 7. Consent Statement

A consent statement from evaluators is necessary, but consent alone is not the same as ethics approval or exemption confirmation.

### Suggested consent wording

> I understand that I am participating as a paid evaluator in a research project on generative agent-based simulations. I will review anonymised AI-agent decision packets and provide rubric-based ratings. I understand that my ratings may be used in aggregated form in a thesis, academic paper, or presentation. I understand that I will be compensated at a fixed rate independent of my answers, and that my identity will not be reported in publications. I confirm that I have had the opportunity to ask questions and that I voluntarily agree to participate.

### Recommended additions

The consent form or webpage should also state:

- participation is voluntary,
- evaluators can stop before submission,
- payment is not based on rating outcomes,
- data will be stored securely,
- names will not appear in publications,
- ratings will be reported in aggregate form.

---

## 8. Should Ethics Be Mentioned in the Paper?

If human-evaluation results are included in the ICDM manuscript, ethics and consent should be mentioned briefly.

Do not hide the human-evaluation component. Reviewers may ask how human ratings were collected, whether consent was obtained, and whether the evaluation was reviewed or confirmed through an institutional process.

### Safe short wording if confirmed

> The human evaluation protocol was reviewed/confirmed through Macquarie University’s human research ethics process as [low-risk / exempt / approved], reference [ID]. Paid evaluators provided informed consent before rating anonymised AI-agent decision packets through a web-based interface.

### If ethics confirmation is not ready

Do not overclaim. Use cautious wording internally and avoid submitting human-evaluation results until the pathway is clarified.

### Alternative option

If ethics confirmation becomes a problem, the ICDM paper could exclude human ratings and focus only on:

- automated metrics,
- simulation logs,
- architecture ablation,
- predictive modelling,
- failure-trace mining.

However, this would make the paper weaker because human validation supports construct validity.

---

## 9. Related Work / Literature Review Update

For the thesis, the current literature review is mostly solid. For ICDM, the related work section should be updated and reframed.

The current literature review is strong on:

- ABM validation,
- microface and macroface validation,
- generative agents,
- GABM validation,
- LLM-agent evaluation,
- multi-agent coordination.

However, for ICDM, one important data-mining pillar should be added.

### Add a new related work subsection

Recommended new section:

> **Trace-Based Data Mining for Micro–Macro Validation**

This section should frame generative-agent logs as heterogeneous behavioural traces containing:

- numeric requests,
- natural-language reasoning,
- memory references,
- plan references,
- temporal decisions,
- group-level outcomes,
- failure patterns.

### Revised ICDM-related work structure

Suggested structure:

1. **Generative Agents and Agent-Based Simulation**
2. **Validation of Generative Agent-Based Models**
3. **Evaluation of LLM Agents and Multi-Agent Coordination**
4. **Trace-Based Data Mining for Micro–Macro Validation**

### ICDM-style gap statement

Use a gap statement like:

> Existing GABM validation work has not treated generative-agent simulations as a behavioural trace-mining problem. As a result, there is limited empirical evidence on whether micro-level features extracted from agent decision logs can predict, explain, or diagnose macro-level coordination success and failure.

This is stronger for ICDM than only saying that there is no validation framework.

---

## 10. Main Action Plan

### Immediate actions

1. Ask Amin about the ethics pathway.
2. Save screenshots and documentation of the evaluation webpage.
3. Add a consent checkbox to the webpage if not already included.
4. Record payment terms clearly.
5. Complete human evaluation.
6. Compute inter-rater reliability.
7. Finalise automated metrics.
8. Run statistical tests.
9. Add predictive modelling and explainability analysis.
10. Update the related work section for ICDM framing.

### For the ICDM manuscript

The paper should be structured around:

1. Problem: validating GABMs requires linking micro-level believability to macro-level coordination.
2. Data: generative-agent behavioural traces from controlled simulations.
3. Method: dual-level trace-mining validation framework.
4. Experiment: four cognitive architectures in a commons-dilemma scenario.
5. Results: predictive relationship between micro features and macro outcomes.
6. Explanation: failure traceability and feature importance.
7. Validation: human ratings and reliability.
8. Implications: design recommendations for generative agent architectures.

---

## 11. Final Position

The project is promising and can be developed into an ICDM paper if final results are available soon.

The key is to shift the framing from:

> A methodology for validating generative agent-based models

to:

> A data-mining approach for extracting, predicting, and explaining micro–macro relationships in generative multi-agent simulation logs.

The most realistic publication strategy is:

- **ICDM 2026 workshop or PhD Forum** if results are ready soon.
- **ICDM 2027 main track** if the full dataset, human validation, predictive modelling, and explainability analysis are completed and polished.
