# Updated Related Work Section — 2026-06-10

**What changed vs. the version in `writing/research_methods_report_final.tex`:**

| Section | Change |
|---------|--------|
| §2.1 | +1 sentence: Zhao et al. FAccT 2026 mechanism plausibility vocabulary |
| §2.2 | Expanded Larooij paragraph (from 1 sentence to full use); new paragraph on Zeng et al. 2026 and the believability–validity gap as a named problem; +Wu et al. 2026 boundary paper |
| §2.3 | New paragraph on information cascades (Bikhchandani, Cho, Jain, Zhong); new paragraph on tacit focal-point coordination (Aharon, Schelling); updated gap statement |
| §2.4 | **NEW** subsection: Trace-Based Data Mining for Micro–Macro Validation |
| References | 13 new entries listed at the bottom of this file |

The text below is a full drop-in replacement for the `\section{Background and Related Work}` block in `writing/research_methods_report_final.tex` (lines 57–79). The new bibliography entries should be appended to the `\thebibliography` block.

---

## LaTeX text — full §2 replacement

```latex
\section{Background and Related Work}

\subsection{Agent-Based Modelling and Validation}
Agent-based modelling is a computational approach for studying systems composed of
interacting autonomous agents. Each agent follows behavioural rules or decision processes,
and macro-level patterns emerge from local interactions among agents \cite{epstein1996growing}.
ABM is particularly useful when a system cannot be explained only by top-down aggregate
equations, because outcomes depend on heterogeneity, adaptation, feedback, and interaction
structure.

A central challenge in ABM is validation: showing that a model is an adequate representation
of the target phenomenon for a given research purpose. Windrum et al.\ distinguish between
microface validation and macroface validation \cite{windrum2007empirical}. Microface validation
asks whether individual agents behave in ways that are plausible or empirically grounded.
Macroface validation asks whether the aggregate model outputs resemble observed or expected
system-level patterns. Moss and Edmonds also emphasise the idea of generative sufficiency:
the model should demonstrate that the proposed individual-level mechanisms are sufficient to
generate the relevant macro-level phenomena \cite{moss2005towards}. Recent work has refined
this vocabulary further: Zhao et al.\ introduce the concept of \emph{mechanism plausibility},
proposing a four-level scale that separates generative sufficiency from mechanistic
plausibility, and calls for evaluating whether a GABM explains \emph{how} and \emph{why}
a phenomenon arises, not only whether it can reproduce surface-level patterns
\cite{zhao2026mechanism}. This micro-macro relationship is especially important in social
simulation because the explanatory value of an ABM depends on whether plausible local
mechanisms produce credible collective outcomes.

Traditional ABM validation is already difficult because social systems are open,
multi-causal, and often hard to measure directly. GABMs add a further challenge: the
agent's decision process may be partly hidden inside an LLM, while its outputs are
open-ended natural-language responses rather than fixed rule outputs. This means that
validation must attend not only to numerical outputs, but also to the quality of agent
reasoning, memory use, planning, and communication.

\subsection{Generative Agents in Simulation}
Generative agents are LLM-based agents designed to simulate believable human-like behaviour
in interactive environments. Park et al.\ introduced a generative-agent architecture with
memory, reflection, and planning modules, showing that LLM-based agents could produce
coherent daily routines and social interactions in a simulated town
\cite{park2023generative}. Subsequent work has explored the use of LLM agents in ABM and
computational social simulation, including applications in social dynamics, epidemiology,
economics, information diffusion, and organisational behaviour
\cite{gao2024survey, ma2024computational, ghaffarzadegan2024tutorial}.

The appeal of generative agents is that they can reduce the need for oversimplified
hand-coded behavioural rules. Instead, agent behaviour can be conditioned on persona
descriptions, memories, goals, situational context, and natural-language interaction
histories. However, a systematic critical review of the generative ABM literature by
Larooij and T\"{o}rnberg found that LLM-driven ABMs may ``exacerbate rather than alleviate
the challenge of validating ABMs'': they introduce new validation obstacles including
black-box opacity, hallucination tendencies, cultural selection biases, and a widespread
reliance on face validity rather than rigorous empirical grounding \cite{larooij2025critical}.
Analysing 35 published generative ABM studies, Larooij and T\"{o}rnberg found that most
employed only weak-form outcome measures and that operational validity---where simulated
outputs have the accuracy required for the model's intended purpose---remained largely unmet
across the literature.

A particularly sharp formulation of this challenge is offered by Zeng et al., who argue that
LLM agents may produce an ``uncanny valley'' effect in social simulation: surface-level
behavioural plausibility can actively obscure systemic invalidity \cite{zeng2026uncanny}.
In their account, agents that appear appropriately human-like on individual metrics may
produce collective dynamics that diverge from real social phenomena because individual
realism masks mode collapse, temporal mismatch, and the substitution of verbal fluency for
genuine emergence. We frame this as the \emph{believability--validity gap}: a condition in
which individual believability and group-level validity are not merely uncorrelated but may
be systematically decoupled. Demonstrating this gap empirically, rather than arguing for it
theoretically, is the central contribution of the present study.

Further evidence for boundary conditions on GABM validity comes from Wu et al., who show
that LLM-based social simulations systematically under-report variance and tend toward
homogeneous ``average persona'' outputs \cite{wu2026boundary}. Their finding implies that
even well-designed multi-trial experiments may have a lower effective sample size than the
nominal trial count, since per-condition outputs may cluster around a single implicit LLM
response tendency rather than covering the diversity of behaviours that real human
populations exhibit.

Recent work has begun to address validation in generative-agent systems more directly.
Adornetto et al.\ propose a validation workflow for generative agents in ABM and distinguish
methods for assessing agent behaviour, interaction coherence, and aggregate dynamics
\cite{adornetto2025overview}. Sen et al.\ propose a quality framework for validating GABMs,
organised around representation, measurement, and reliability across input, process, and
output stages \cite{sen2025validating}. These studies demonstrate that validation is now
recognised as a central issue. However, much of the literature remains conceptual or
workflow-oriented; fewer studies empirically test how individual-level believability relates
to macro-level simulation validity, and none---prior to this work---quantify the gap between
them as a measurable, trial-level outcome.

\subsection{LLM-Agent Evaluation and Multi-Agent Coordination}
LLM-agent evaluation has developed rapidly, but much of it focuses on agent capability in
task environments rather than ABM validity. AgentBench evaluates LLMs as agents across
multiple environments \cite{li2024agentbench}. Other surveys and frameworks classify
evaluation objectives such as behaviour, capability, reliability, and safety
\cite{mohammadi2025evaluation}. Metrics such as consistency, believability, task success,
effort, and failure interpretation have also been proposed
\cite{chen2024evaluating, barkur2024magenta, sung2025verila}.

Multi-agent LLM systems reveal additional issues that may not appear when evaluating agents
individually. Zhang et al.\ identify a communication-reasoning gap in distributed
multi-agent coordination, where agents may form reasonable communication structures but
still fail to integrate distributed information effectively \cite{zhang2026silo}.
Kulshreshtha et al.\ show that a single uncooperative agent can destabilise group behaviour
in multi-agent systems \cite{kulshreshtha2026defection}. Hishiki et al.\ demonstrate that
memory design can substantially affect collective cooperation outcomes
\cite{hishiki2026memory}. These findings suggest that individual agent properties can shape
group-level outcomes, but the relationship is not guaranteed or simple.

A recurring pattern in multi-agent LLM systems is informational herding: when agents share
their outputs publicly, other agents tend to discount their private signals and align with
the apparent majority. This dynamic parallels the information cascades formalised by
Bikhchandani et al.\ in human decision-making, where agents rationally discard private
information once a sufficiently large public prior has formed \cite{bikhchandani1992theory}.
Recent empirical work confirms that LLM agents exhibit cascade behaviour with comparable
structural properties. Cho et al.\ demonstrate herding driven by a confidence gap, showing
that agents adopt public majority positions even when their own signals are more accurate
\cite{cho2025herd}. Jain and Krishnamurthy formally prove cascade conditions for LLM agents
under public belief pressure and show that cascade depth and irrationality increase with
signal variance \cite{jain2025social}. Zhong et al.\ disentangle informational from
normative conformity as a function of agent uncertainty, finding that LLM agents switch
from evidence-based updating to social conformity as public-belief confidence rises
\cite{zhong2025conformity}. These studies establish that cascade dynamics are not a
simulation artefact but a structural feature of language-model agents in social settings,
with direct implications for whether LLM-based information-aggregation tasks can yield valid
group outcomes.

A related but distinct coordination mechanism is tacit focal-point coordination, in which
agents converge on a common strategy through shared schema or cultural salience rather than
explicit communication. This mechanism was theorised by Schelling and extended to the
concept of focal points as equilibria that become salient through common knowledge. Aharon
et al.\ provide the first large-scale empirical test of LLMs in Schelling-point games,
finding that LLM agents achieve tacit coordination significantly above chance but that the
coordination mechanism is dominated by cultural salience encoded in pre-training rather than
dynamic strategic reasoning \cite{aharon2026tacit}. This is directly relevant to the
reflection saturation finding in this study: the deterministic reflection condition creates
a shared lexical anchor --- a pre-committed norm injected identically to all agents --- that
functions as a focal point in exactly the sense Aharon et al.\ describe. The observed
coordination gains in this condition are therefore attributable to the \emph{content} of
the focal norm rather than to the richness of the reasoning process that produced it.

The gap addressed by this project lies at the intersection of these fields. ABM validation
emphasises micro-macro linkage, while LLM-agent evaluation provides tools for assessing
individual agents, and the emerging literature on cascades and focal-point coordination
reveals the mechanisms through which individual agent properties can either produce or
subvert group-level validity. What remains underdeveloped is an integrated empirical
framework that connects these perspectives: one that uses both levels of evaluation to
measure not only whether believable agents coordinate, but whether high believability can
coexist with and mask collectively invalid outcomes. This project addresses that gap.

\subsection{Trace-Based Data Mining for Micro--Macro Validation}
The validation framework in this study relies on mining the behavioural traces produced by
generative agents during simulation. Each trial generates a structured event log containing,
for each agent at each step: the requested and granted resource amounts, the natural-language
reasoning, memory references, plan references, fair-share deviation, and resource state. At
the system level, the log captures group coordination, sustainability, inequality, and
collapse status at each step. Treating generative-agent simulation logs as event traces ---
rather than only as outcome records --- connects this work to a broader literature on
trace-based data mining and process analysis.

In explainable predictive process monitoring, event logs are treated as sequences of events,
and future process outcomes or KPIs are predicted and explained from partial traces
\cite{galanti2020explainable}. This perspective maps naturally to GABM validation: a
simulation trial is a process instance, a step is an event, and coordination success or
failure is the outcome to predict. Galanti et al.\ demonstrate that trace-based predictors
can provide interpretable explanations alongside accurate forecasts --- a dual requirement
that this study inherits: the early-warning classifier (H7) should not only predict failures
but identify which micro-level features drove each prediction.

The multi-agent failure literature provides a complementary taxonomy. Cemri et al.\ identify
recurring failure modes in multi-agent LLM systems from annotated execution traces ---
including inter-agent misalignment, task-verification failures, and reasoning-action
mismatches --- and demonstrate that final success/failure scores are insufficient for
understanding why failures occur \cite{cemri2025fails}. This motivates the failure
traceability dimension in the macro-level framework: rather than reporting only whether a
trial failed, the framework codes failure type and traces it back to agent-level causes.
This study introduces two simulation-specific failure types: Type~D (persistent
oversubscription, in which agents systematically exceed the replenishment limit despite
available memory) and Type~E (sub-threshold failure, in which agents exhibit high
believability but still fail coordination --- the C2 gap cases).

Automatic and rule-based evaluation of agent trajectories requires calibration against
expert judgement. AgentRewardBench demonstrates that LLM-as-judge ratings of agent
trajectories diverge from expert annotations in systematic ways, particularly for borderline
cases \cite{pan2025agentrewardbench}. This motivates both the human evaluation protocol in
this study and the use of an independent LLM judge model (Claude rather than GPT-4o-mini)
to avoid generator-judge circularity \cite{zheng2023judging}. The evaluation design follows
the principle of Velmurugan et al., who argue that explanation quality should be assessed
for stability and fidelity rather than accepted at face value: automated scores are treated
as proxies throughout this study, and blending with human ratings is the intended final
evaluation step \cite{velmurugan2021functionally}.

Recent work has begun to systematise multi-level agent evaluation. Yehudai et al.\ propose
Agentic CLEAR, a framework for automated multi-level evaluation of LLM agents at the
system, trace, and node granularity \cite{yehudai2026clear}. This three-granularity
structure maps closely to the macro/micro distinction in this study and provides methodological
precedent for treating the trace level as a first-class evaluation target rather than an
afterthought. The contribution of this study extends that paradigm specifically to
generative ABM validation: rather than benchmarking agent capability in isolated task
environments, the trace-mining layer is used to test whether micro-level believability
features predict, explain, and diagnose macro-level coordination outcomes in a
multi-trial social simulation.
```

---

## New bibliography entries (append to `\thebibliography`)

```latex
\bibitem{zhao2026mechanism}
W. Zhao et al., ``Mechanism plausibility in generative agent-based modeling,''
in \emph{Proc. ACM Conference on Fairness, Accountability, and Transparency (FAccT)},
arXiv:2605.12824, 2026.

\bibitem{zeng2026uncanny}
Y. Zeng et al., ``Too human to model: The uncanny valley of LLMs in social simulation,''
\emph{npj Complexity}, vol.\ 3, article 13, 2026 (arXiv:2507.06310).

\bibitem{wu2026boundary}
J. Wu et al., ``LLM-based social simulations require a boundary,''
arXiv:2506.19806, 2026.

\bibitem{bikhchandani1992theory}
S. Bikhchandani, D. Hirshleifer, and I. Welch, ``A theory of fads, fashion, custom,
and cultural change as informational cascades,'' \emph{Journal of Political Economy},
vol.\ 100, no.\ 5, pp.\ 992--1026, 1992.

\bibitem{cho2025herd}
S. Cho et al., ``Herd behavior: Investigating peer influence in LLM-based multi-agent
systems,'' arXiv:2505.21588, 2025.

\bibitem{jain2025social}
A. Jain and R. Krishnamurthy, ``Interacting large language model agents: Interpretable
models and social learning,'' arXiv:2411.01271, 2025.

\bibitem{zhong2025conformity}
Y. Zhong et al., ``Disentangling the drivers of LLM social conformity,''
arXiv:2508.14918, 2025.

\bibitem{aharon2026tacit}
D. Aharon et al., ``Tacit coordination of large language models,''
arXiv:2601.22184, 2026.

\bibitem{galanti2020explainable}
R. Galanti, B. Coma-Puig, M. de Leoni, J. Carmona, and N. Navarin, ``Explainable
predictive process monitoring,'' in \emph{Proc. 2nd International Conference on
Process Mining}, arXiv:2008.01807, 2020.

\bibitem{cemri2025fails}
M. Cemri, M. Liu, S. Yang, J. E. Gonzalez, and A. Stoica, ``Why do multi-agent LLM
systems fail?,'' arXiv:2503.13657, 2025.

\bibitem{velmurugan2021functionally}
M. Velmurugan, C. Ouyang, C. Moreira, and P. Sindhgatta, ``Evaluating fidelity of
explainable methods for predictive process analytics,'' arXiv:2012.04218, 2021.

\bibitem{pan2025agentrewardbench}
Z. Pan et al., ``AgentRewardBench: Evaluating automatic evaluations of web agent
trajectories,'' arXiv:2504.08942, 2025.

\bibitem{yehudai2026clear}
M. Yehudai et al., ``Agentic CLEAR: Automating multi-level evaluation of LLM agents,''
arXiv:2605.22608, 2026.
```

---

## Fix to existing `larooij2025critical` entry

The existing entry has `vol. 58, 2025`. The published details are:
*Artificial Intelligence Review*, **Volume 59**, Article 15, **2026** (published online 18 November 2025).

Replace the existing entry with:

```latex
\bibitem{larooij2025critical}
M. Larooij and P. T\"{o}rnberg, ``Validation is the central challenge for generative
social simulation: A critical review of LLMs in agent-based modeling,''
\emph{Artificial Intelligence Review}, vol.\ 59, article 15, 2026.
```

---

## Summary of structural changes

The updated §2 has four subsections instead of three:

| Section | Status | Primary new citations |
|---------|--------|----------------------|
| §2.1 ABM and Validation | Updated | Zhao et al. FAccT 2026 |
| §2.2 Generative Agents | Updated | Zeng et al. 2026, Wu et al. 2026; Larooij expanded |
| §2.3 LLM-Agent Evaluation | Updated | Bikhchandani 1992, Cho 2025, Jain 2025, Zhong 2025, Aharon 2026 |
| §2.4 Trace-Based Data Mining | **NEW** | Galanti 2020, Cemri 2025, Velmurugan 2021, AgentRewardBench 2025, Yehudai 2026 |

The gap statement at the end of §2.3 is updated to include the believability–validity gap framing, which now ties §2.2 (where the gap is named using Zeng) to §2.3 (where the mechanisms that produce the gap — cascade dynamics and focal-point saturation — are introduced). §2.4 then explains how the trace-mining methodology allows the gap to be measured and diagnosed at the trial level.
