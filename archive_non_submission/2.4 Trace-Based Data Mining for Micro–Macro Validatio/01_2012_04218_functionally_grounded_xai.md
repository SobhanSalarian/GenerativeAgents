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

