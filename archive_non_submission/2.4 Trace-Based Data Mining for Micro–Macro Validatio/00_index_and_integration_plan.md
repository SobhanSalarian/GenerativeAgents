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
