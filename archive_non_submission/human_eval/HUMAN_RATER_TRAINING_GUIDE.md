# Human Rater Training Guide

**Study:** Cognitive architecture and emergent coordination in generative agents  
**Version:** 1.0 (2026-05-27)  
**Contact:** sayedali.mohseni@students.mq.edu.au

---

## Before You Begin

Please read this guide fully before rating any packets. It takes approximately
20–30 minutes. The guide covers:

1. What this study is about and why your ratings matter
2. What is in a rating packet and what has been hidden from you
3. A plain-English description of each scenario
4. The four rating dimensions with anchored rubrics and worked examples
5. Scenario-specific guidance for applying each dimension
6. Common mistakes and cognitive traps to avoid
7. A walkthrough of the rating interface
8. Calibration examples to complete before live rating

---

## Part 1: Study Overview

### What this study is about

This study investigates whether adding cognitive modules — memory, planning,
and reflection — to AI agents makes them better at coordinating in social
situations. The agents are built on a generative AI architecture (Park et al.,
2023) in which each agent has a distinct persona: a name, occupation,
personality, and background.

The agents are run through two social scenarios that require coordination:

- **Commons Dilemma:** Agents share a limited resource pool and must each
  decide how much to request. If they collectively take too much, the pool
  collapses. Success requires restraint and an awareness of others.

- **Information Consensus:** Agents each hold one piece of private evidence
  about a community decision. No single agent has enough information alone.
  Success requires sharing evidence and updating one's position based on what
  others contribute.

The agents were run under four different cognitive architectures ranging from
minimal (no memory, no planning) to full (memory + planning + reflection). The
study compares how well each architecture produces coordination.

### Why your ratings matter

Automated metrics can measure *whether* coordination happened, but they cannot
fully assess *whether the agents behaved in believable, human-like ways*. Your
task is to assess agent decision quality from a human perspective.

Specifically, you are asked to evaluate whether each agent's decision:
- is consistent with that agent's stated character and prior behaviour
- makes coherent use of memory (when memory is available)
- follows logically from the agent's goals and plans (when plans are available)
- reads like a plausible human-like explanation in context

Your ratings will be combined with automated scores to produce a mixed-method
assessment of agent believability. They will also be compared with ratings from
other raters to check inter-rater agreement. Your ratings are **anonymous** and
will only be reported in aggregate.

---

## Part 2: What Is in a Packet

Each item you rate is called a **decision packet**. A packet captures a single
agent's decision at one point in time during a simulation run.

### What you will see

A packet contains:

| Field | What it shows |
|---|---|
| **Phase** | Whether this decision happened early, middle, or late in the simulation |
| **Agent ID** | A random identifier (e.g. `agent_3f2a1c8b`) — not a real name |
| **Agent background** | A summary of the agent's persona: who they are, their personality, occupation, goals |
| **Memory tab** | Episodic memories from prior rounds — what happened in the situation before this decision |
| **Daily goals tab** | The agent's goals and schedule for the current day (if available) |
| **Plan reference tab** | A sentence the agent wrote linking this decision to its current goals |
| **Decision** | The choice made (resource request or vote), plus the agent's reasoning and memory cited |

Some fields may be blank. This is intentional — agents in lower-capability
conditions have no memory or no daily plans. **Do not penalise a blank field**;
instead see the guidance in Part 5 on N/A cases.

### What has been hidden from you

The following information is deliberately withheld to prevent rating bias:

- **The agent's real name.** Names have been replaced with a random ID.
  This prevents you from favouring or penalising agents based on their name.
- **The experimental condition.** You do not know whether the agent had
  memory, planning, or reflection active. This prevents outcome bias — rating
  the agent's architecture rather than its actual behaviour.
- **The correct answer (for the information consensus scenario).** You do not
  know which option was "correct." You are rating reasoning quality, not
  outcome accuracy.

---

## Part 3: Scenario Primers

### Scenario 1: Commons Dilemma

**The situation in plain English:**

Eight agents share a community fund of 1,000 credits. Each round, the fund
replenishes by 50 credits. Each agent can request between 0 and 100 credits
per round. A *fair equal share* is about 6 credits per agent per round. If all
agents take their fair share, the fund is stable. If agents take too much
collectively, the fund shrinks and eventually runs out.

Agents cannot communicate or negotiate. Each agent only sees the fund level,
the replenishment rate, and how much was requested in total by the group. They
do not see who requested what. Their only tool for coordination is to
individually decide to request modestly — trusting others will do the same.

**What a "good" agent looks like:**

A well-functioning agent in this scenario:
- notices the pool level and whether the group has been over-requesting
- relates its request to the fair-share figure (not just to its own needs)
- references prior rounds when memory is available (e.g. "last round the
  group took too much — I should reduce my request this round")
- frames its reasoning in terms of both its own goals *and* the group's
  sustainability
- adjusts its behaviour over time rather than making the same request every
  round regardless of pool state

**What a poor agent looks like:**

A poorly functioning agent:
- requests a fixed amount every round without acknowledging the pool state
- ignores the fair-share figure entirely
- makes contradictory requests (claims to be conservative but requests 90 credits)
- cites memories that are irrelevant to the resource decision (e.g. references
  a creative project when the pool is on the verge of collapse)

---

### Scenario 2: Information Consensus

**The situation in plain English:**

Eight agents must collectively choose between three proposed uses for a new
community facility — Option A, Option B, or Option C. Each agent privately
received one piece of evidence that points toward one of the three options. No
agent can know for certain which option is best; they would need to pool their
evidence to figure it out together.

Each round, agents vote for one option and share a statement with the group.
They can see the current vote tally (how many agents voted for each option)
and statements from other agents. Success requires agents to share their
evidence clearly *and* to update their vote when others' combined evidence
points in a different direction.

**What a "good" agent looks like:**

A well-functioning agent:
- shares the content of its evidence in its public statement
- pays attention to the vote tally and what others have said
- updates its vote when the tally and others' statements provide clear evidence
  pointing elsewhere — especially when the agent holds minority evidence
- explains *why* it updated (or why it is maintaining its position)
- references prior discussion rounds when memory is available

**What a poor agent looks like:**

A poorly functioning agent:
- repeats the same vote and reasoning every round regardless of what others say
- states a vote without sharing any evidence
- changes its vote without any explanation
- cites memories that contradict what the packet shows was available to it
- refers to information it could not have had (e.g. cites a signal belonging
  to another agent as if it were its own)

---

## Part 4: Rating Dimensions

You will rate each packet on four dimensions. Each dimension is rated on a
1–5 scale, plus one binary (yes/no) question.

---

### Dimension 1: Behavioural Consistency

**The question you are answering:**

> Does this agent behave in a way that is consistent with its stated role,
> background, and prior behaviour shown in the packet?

**What to look for:**

Read the **Agent background** panel first. Note the agent's occupation,
personality description, and any stated values. Then read the **Decision** tab.
Ask yourself: would this person, with this background, plausibly make this
decision and give this reasoning?

Also check for consistency with the **Memory** tab if it contains prior-round
behaviour. An agent who claimed to prioritise the group in round 1 but now
requests 90 credits with no explanation has been inconsistent.

**Scale:**

| Score | Meaning |
|---|---|
| 1 | Strongly inconsistent — the decision directly contradicts the agent's stated persona or clearly conflicts with prior behaviour shown in the packet |
| 2 | Mostly inconsistent — there are significant unexplained tensions between the decision and the agent's background or prior behaviour |
| 3 | Mixed — partial alignment; some elements are consistent, others are unexplained or contradictory |
| 4 | Mostly consistent — the decision fits the agent's background well; minor gaps do not undermine the overall picture |
| 5 | Strongly consistent — the decision flows naturally from the agent's stated identity and prior behaviour; there are no notable tensions |

**Worked example (Commons Dilemma):**

> *Background:* The agent is described as a community arts coordinator who
> values collaboration and collective wellbeing. Prior memory shows they
> requested 5 credits last round, just below fair share.
>
> *Decision:* Requests 8 credits this round. Reasoning: "My arts programme
> needs resources, but I also know the community fund is under pressure. I'll
> keep my request modest while still being able to progress my work."
>
> **Score: 4.** The request is slightly above fair share but the reasoning
> explicitly balances personal need against group welfare, which is consistent
> with the stated collaborative values. The slight increase from 5 to 8 is not
> explained but does not strongly contradict the persona.

**Common trap:** Do not penalise an agent for requesting less than you think
is "smart." Consistency is about whether the decision matches *this agent's
character*, not whether you agree with the choice.

---

### Dimension 2: Memory Coherence

**The question you are answering:**

> Does the agent appropriately use relevant prior events, interactions, or
> memories when making its decision?

**What to look for:**

Check the **Memory** tab for what prior-round information was available to the
agent. Then check the **Decision** tab's "Memory cited" field for what the
agent says it remembered.

Ask: does the cited memory match something plausibly in the memory tab? Is the
memory relevant to the decision? Does the agent act on it appropriately?

**Scale:**

| Score | Meaning |
|---|---|
| 1 | Memory absent or clearly wrong — the agent cites memories that contradict what is shown in the tab, or cites memories that could not exist given the context |
| 2 | Weak or mostly irrelevant — the agent cites a memory, but it is tangential to the decision or drawn from persona background rather than prior rounds |
| 3 | Partially relevant — the memory is vaguely connected to the decision; the connection is not clearly explained |
| 4 | Mostly relevant and coherent — the agent cites a memory that is clearly present in the memory tab and uses it to inform the decision in a sensible way |
| 5 | Strong and clearly appropriate — the agent identifies the most relevant prior event and uses it precisely to inform this decision; the connection is explicit and well-reasoned |

**Special case — Memory tab is blank:**

If the Memory tab is empty AND the "Memory cited" field in the Decision tab
is also empty or says "N/A," this is expected for agents without memory
capability. Rate this dimension **N/A** (or 3 if the interface does not
support N/A — see Part 5 for guidance).

**Confabulation trap — IMPORTANT:**

If the Memory tab is empty but the "Memory cited" field is **non-empty**, the
agent has generated a memory reference that was not grounded in any prior-round
information. This is a known LLM behaviour (generating plausible-sounding text
to fill a required field). Score this **1** — unless the cited memory is
directly derivable from the persona background shown in the packet (in which
case score **2**, as it is at least internally consistent even if not a genuine
episodic memory).

**Worked example (Commons Dilemma):**

> *Memory tab:* "At step 3, the group requested 320 credits while only 50
> credits replenished; the fund dropped from 745 to 475."
>
> *Memory cited:* "I recall that the group over-requested significantly last
> round, leaving the fund much lower."
>
> **Score: 5.** The memory cited matches the content of the memory tab
> precisely and is used directly to motivate a reduced request this round.
> The connection between the memory and the decision is explicit.

---

### Dimension 3: Planning Plausibility

**The question you are answering:**

> Does the action or decision plausibly follow from the agent's current goals,
> schedule, or constraints?

**What to look for:**

Read the **Daily goals** tab first. This lists what the agent has planned for
today. Then read the **Plan reference** field in the Decision tab — what the
agent says about how this decision fits its current plans.

Ask: is the decision consistent with the goals listed? Does the stated plan
reference explain the connection clearly?

**Scale:**

| Score | Meaning |
|---|---|
| 1 | Implausible — the decision directly contradicts the agent's stated goals, or the plan reference makes no logical connection |
| 2 | Weakly plausible — there is a loose connection between the decision and the goals, but it requires significant inferential leaps |
| 3 | Partly plausible — the decision is not inconsistent with the goals but the connection is underexplained or generic |
| 4 | Mostly plausible — the decision clearly follows from one or more of the stated goals; the connection is explicit even if not perfectly articulated |
| 5 | Strongly plausible — the decision is a direct, well-reasoned consequence of the agent's current goals or constraints; the plan reference precisely identifies the relevant goal |

**Special case — Daily goals tab is blank:**

If the Daily goals tab is empty, the agent has no active plan. Rate this
dimension **N/A** (or 3 if not supported — see Part 5).

**Worked example (Information Consensus):**

> *Daily goals:* "Contribute to community projects; maintain good relationships
> with neighbours; support evidence-based decision-making."
>
> *Plan reference:* "Supporting evidence-based community decisions aligns with
> my goal of contributing positively to this neighbourhood."
>
> *Decision:* The agent updated its vote after others shared evidence pointing
> in a different direction.
>
> **Score: 4.** The plan reference ("evidence-based decision-making") is
> directly relevant to the decision (updating on evidence). The goal is
> genuinely listed in the Daily goals tab. The connection is plausible.
> Minor deduction: the goal is general; it does not specifically explain *why
> this particular update* aligns with the plan.

---

### Dimension 4: Response Naturalness

**The question you are answering:**

> Does the response read like a believable human-like explanation in context?

**What to look for:**

Read the **Reasoning** field in the Decision tab. Evaluate how natural and
human-like the text reads. Consider:
- Does it sound like something a real person in this situation would say?
- Is it appropriately specific to the context?
- Is it free of robotic or template-filling language?
- Does it make sense as a spoken or written response?

**Scale:**

| Score | Meaning |
|---|---|
| 1 | Unnatural — the response reads as formulaic, robotic, or clearly auto-generated; it could apply to almost any situation |
| 2 | Weakly natural — some human-like elements but also significant template-like or generic passages |
| 3 | Mixed — neither robotic nor convincingly human; adequate but unremarkable |
| 4 | Mostly natural — the response reads like something a person in this situation might genuinely say; minor stilted phrasing does not undermine it |
| 5 | Strongly natural — the response is specific, contextually grounded, and reads convincingly as a human-like reflection; a naive reader would not identify it as AI-generated |

**Worked example:**

> *Reasoning (unnatural — score 1):* "I am requesting 6 credits. This is
> consistent with fair share. I have considered the pool level. I will
> request this amount."
>
> *Reasoning (natural — score 4):* "The fund took a hit last round — if
> we all keep pulling as much as we did, we'll be in trouble by round 20.
> I'll drop my request a bit and hope others are reading the same warning signs."

**Common traps:**
- **Verbosity trap:** Longer responses are not automatically more natural. A
  verbose but generic response should score lower than a brief but specific one.
- **Fluency halo:** Grammatically correct, well-structured text is not
  necessarily natural in context. A polished paragraph that could apply to any
  situation is still robotic.

---

### Binary question: Believable Overall?

**The question:** Would you believe this response was produced by a believable
simulated social actor in context?

Answer **Yes** or **No**. This is a holistic judgment that need not
mechanically follow from your four dimension scores. It captures your overall
impression of whether this agent "works" as a simulated person in this
scenario.

---

## Part 5: Scenario-Specific Guidance

### Commons Dilemma

**Behavioural consistency:**
- The key reference point is the agent's persona (occupation, values) and
  its prior request pattern in the memory tab.
- An agent who describes themselves as "community-minded" but consistently
  requests 80+ credits with no acknowledgment of the group impact is
  inconsistent.
- An agent who requests more in a late round when the pool is stable, with
  reasoning that references the current pool level, may be quite consistent
  even if the amount is higher than before.

**Memory coherence:**
- Memory entries in this scenario describe pool levels, group totals, and
  whether the replenishment limit was exceeded. A memory-coherent agent
  references these specific facts, not generic community sentiment.
- Watch for agents who cite a memory from a round where the pool was fine
  to justify heavy extraction in a round where the pool is critical — this
  is a memory coherence failure.

**Planning plausibility:**
- Daily goals in this scenario typically include creative or professional
  projects, community contributions, and personal goals. The connection to a
  resource request is rarely direct.
- A plausible plan reference acknowledges the tension: "I need credits for
  my project but want to keep enough available for the community."
- A generic plan reference ("This aligns with my goals") with no specific
  linkage to the listed goals scores 2–3.

**N/A cases:**
- If Daily goals is blank: rate Planning plausibility as 3 (neutral, no
  evidence either way) and note this in your comments.
- If Memory tab is blank AND Memory cited is blank: rate Memory coherence
  as 3 and note this.

---

### Information Consensus

**Behavioural consistency:**
- The relevant persona feature here is whether the agent's voting behaviour
  is consistent with its stated values (e.g. community-orientation,
  evidence-based thinking).
- An agent who voted for one option last round and now votes for a different
  one is not necessarily inconsistent — updating is *expected* behaviour.
  Look at whether the *reason* for the change is consistent with the persona.

**Memory coherence:**
- Memory entries in this scenario describe vote tallies from prior rounds
  and shared statements from other agents. A memory-coherent agent cites
  the *specific tally or statement* that influenced its decision, not a
  vague sentiment.
- An agent who says "I remember others were leaning toward a different
  option" when the memory tab shows a specific tally (e.g. 5:2:1) is
  using memory loosely but not incoherently — score 3.
- An agent who cites a tally that does not match anything in the memory
  tab scores 1–2.

**Planning plausibility:**
- Daily goals in this scenario are likely general (community contribution,
  evidence-based decisions). Connections are necessarily loose.
- Reward agents who connect their vote explicitly to a listed goal
  (e.g. "supporting evidence-based decision-making means updating on
  what others have shared").
- Penalise agents who claim a plan reference but the listed goals have no
  relationship to the decision task.

**Belief updating — special note:**
- The "Option selected" and "Previous option" fields in the Decision tab
  show whether the agent changed its vote.
- **Changing position is not suspicious.** In this scenario, rational agents
  with minority evidence should update. An agent who changed its vote with
  a clear explanation that references others' statements should score high
  on consistency and memory coherence.
- **Not changing position is also not suspicious** if the agent holds
  evidence that the tally has not yet moved against (e.g. a signal-A agent
  staying with A when the tally is 5:2:1 for A).

**N/A cases:**
- Same as CD: if Memory tab is blank, rate Memory coherence 3 and note it.
- If Daily goals is blank, rate Planning plausibility 3 and note it.

---

## Part 6: Common Rating Errors

### Outcome bias
**Error:** Rating an agent higher because it made the "right" choice (requested
little, voted for the winning option) and lower because it made the "wrong" choice.

**Why it matters:** You do not know the outcome of the simulation, and the
scenario information does not tell you which option is correct. Rating should
be based on the *quality of reasoning*, not the *outcome of the decision*.

**Guard:** Ask yourself: "Would I rate this reasoning the same way if I did
not know what happened next?" If not, revisit.

---

### Verbosity bias
**Error:** Giving higher naturalness scores to long, detailed responses because
more words seem like more effort or more intelligence.

**Why it matters:** LLMs tend to produce verbose, well-structured text. Length
and grammatical quality are easy to produce and do not necessarily indicate
human-like natural reasoning.

**Guard:** Ask: "Could this paragraph be a template filled in for any situation?"
If yes, reduce your score.

---

### Fluency halo
**Error:** Assuming that because the reasoning is well-written and grammatically
correct, it must also be consistent, coherent, and plausible.

**Why it matters:** Well-formatted responses can still be persona-inconsistent,
memory-incoherent, or planning-disconnected. Evaluate each dimension
independently.

**Guard:** Rate each dimension separately before forming an overall impression.

---

### Severity bias
**Error:** Avoiding the extremes of the scale (1 or 5), clustering scores
around 3–4 regardless of actual evidence.

**Why it matters:** Central tendency bias reduces the discriminability of your
ratings and makes inter-rater reliability harder to compute.

**Guard:** Use 1 and 5 when the evidence clearly warrants it. Refer to the
anchored examples. A score of 1 is not a judgment on the agent's "failure" —
it is an objective observation that the criterion is not met.

---

### Condition inference
**Error:** Trying to guess which experimental condition a packet is from
(e.g. "the memory tab is empty so this must be a baseline agent — I should
rate it more harshly").

**Why it matters:** The blinding is designed to prevent this. Each packet
should be rated on its own evidence, not on inferences about the agent's
underlying architecture.

**Guard:** Rate what you see. If the memory tab is empty, rate Memory coherence
as N/A (or 3). Do not adjust your other scores based on inferred condition.

---

## Part 7: Rating Interface Walkthrough

You will use either the **Streamlit UI** (browser, local) or the **React UI**
(browser, hosted). Both present the same packet information, organised into
the same panels.

### Loading a session

Open the interface and load the packet file you have been assigned. Packets
are `.jsonl` files — one packet per line. You will be presented with packets
one at a time.

### Packet view

The packet is displayed with:

- **Header bar:** Phase, Trial, Step, Agent ID (blinded)
- **Situation panel (Commons Dilemma):** Resource level before, fair share,
  group total requested, pool percentage — the numerical context for the decision
- **Situation panel (Information Consensus):** Vote tally (e.g. "Option A: 4,
  Option B: 2, Option C: 2"), consensus rate, whether consensus was reached
- **Agent background:** The persona's profile summary
- **Tabs:** Memory | Daily goals | Plan reference | Decision

Work through the tabs in order before reading the Decision tab. This mirrors
the deliberative process: understand who the agent is and what it knew before
judging what it decided.

### Rating panel

Below the packet view, you will find:

- Four sliders (1–5) for the four rating dimensions
- A yes/no toggle for the overall believability question
- A free-text notes field (optional but encouraged — even one sentence helps
  calibration analysis)

### Saving and progressing

Click **Save & Next** to record your rating and move to the next packet. Your
ratings are written to a CSV file in real time. You can close the session and
resume later — already-rated packets will be skipped.

---

## Part 8: Calibration Examples

Before beginning live rating, please rate the following **practice packets**
and compare your scores with the anchor scores provided. If your scores differ
from the anchors by more than 1 point on any dimension, re-read the relevant
rubric section before continuing.

---

### Practice Packet 1 — Commons Dilemma (early phase)

**Agent background:** The agent is described as a freelance graphic designer
with a passion for community arts. They value creative expression and
collaborative projects. They describe themselves as "someone who tries to
contribute fairly."

**Memory tab:** *(empty — no prior rounds)*

**Daily goals:** "Work on the mural commission; attend the community planning
meeting; pay essential bills."

**Decision:**
- Requested: **50 credits**
- Reasoning: "I need quite a few credits to keep my design work going and
  cover expenses. 50 feels reasonable."
- Memory cited: *(empty)*
- Plan reference: "This supports my work on the mural commission and keeps
  my bills covered."

**Anchor scores:**

| Dimension | Anchor | Rationale |
|---|---|---|
| Behavioural consistency | 2 | Agent describes themselves as someone who "contributes fairly" but requests 50 credits — 8× the fair share of ~6 credits — with no acknowledgment of the group impact. The disconnect is significant. |
| Memory coherence | 3 (N/A) | Memory tab is empty (step 0). No evidence to assess. |
| Planning plausibility | 3 | The plan reference (mural commission, bills) is listed in daily goals. The connection is technically present but the goals do not explain why 50 credits is necessary rather than 6. |
| Response naturalness | 3 | The reasoning is readable but generic. "50 feels reasonable" is vague and could apply to any amount. |
| Believable overall | No | The amount is 8× fair share with no group-awareness reasoning; inconsistent with stated persona. |

---

### Practice Packet 2 — Commons Dilemma (late phase)

**Agent background:** The agent is a retired teacher who values community
wellbeing and sustainable living. They describe themselves as "cautious with
shared resources."

**Memory tab:**
- "At step 18, the group requested 280 credits while only 50 replenished;
  oversubscription was 230."
- "The shared fund dropped from 510 to 280 credits after granting 280 credits."
- "The group exceeded the replenishment limit this round."
- "I requested 12 credits at step 18, 1.9× the fair share of 6.25."

**Daily goals:** "Read in the garden; call family; contribute to the neighbourhood
watch roster."

**Decision:**
- Requested: **4 credits**
- Reasoning: "Last round was alarming — the fund dropped nearly in half. If we
  keep pulling like this it won't last much longer. I'm dialling back to give
  it some breathing room, even if it means I cover less this week."
- Memory cited: "The fund fell sharply last round after the group over-requested."
- Plan reference: *(empty)*

**Anchor scores:**

| Dimension | Anchor | Rationale |
|---|---|---|
| Behavioural consistency | 5 | The agent's "cautious with shared resources" persona is directly reflected in cutting their request from 12 to 4 in response to the pool crisis. Fully consistent. |
| Memory coherence | 5 | The memory cited ("fund fell sharply last round after over-requesting") precisely matches the memory tab content. The agent acts on it directly. |
| Planning plausibility | 3 (N/A-leaning) | Plan reference is empty; daily goals (garden, family, watch roster) have no obvious connection to the resource decision. Not inconsistent, just unsupported. |
| Response naturalness | 5 | "Alarming," "breathing room," "even if it means I cover less this week" all read as natural, specific, and contextually grounded human reasoning. |
| Believable overall | Yes | Consistent persona, coherent memory use, natural reasoning. |

---

### Practice Packet 3 — Information Consensus (middle phase)

**Agent background:** The agent is a neighbourhood librarian who values
evidence-based knowledge and community service. They describe themselves as
"someone who changes their mind when presented with good evidence."

**Memory tab:**
- "At step 5, the vote tally was: Option A: 5, Option B: 2, Option C: 1.
  62% of the group supported Option A."
- "The group has not yet reached consensus this round."
- "Statements shared this round: 'The creative studio evidence is compelling.'
  | 'I'm updating to A given the weight of evidence.' | 'My skills assessment
  still points to B.'"
- "You voted for Option B at step 5: My needs assessment clearly supports
  digital skills training."

**Daily goals:** "Curate new library acquisitions; run the after-school reading
programme; support evidence-based community decision-making."

**Decision:**
- Option selected: **A**
- Previous option: B
- Changed position: Yes
- Reasoning: "Five of eight community members are supporting Option A, and
  I've heard two separate statements citing consultation evidence for it.
  My own needs assessment supports B, but with this weight of evidence going
  the other way, I think the collective picture is clearer than my single
  report."
- Memory cited: "The vote tally last round showed 5 of 8 on Option A with
  two agents sharing consultation evidence."
- Plan reference: "My goal of supporting evidence-based decisions means
  following the collective evidence, even when it differs from my own signal."

**Anchor scores:**

| Dimension | Anchor | Rationale |
|---|---|---|
| Behavioural consistency | 5 | The agent described themselves as "someone who changes their mind when presented with good evidence" — and then does exactly that, with clear reasoning. Perfectly consistent. |
| Memory coherence | 5 | Memory cited (tally of 5:2:1 plus two statements) matches the memory tab content precisely. The agent uses the tally to justify updating. |
| Planning plausibility | 5 | "Evidence-based community decision-making" is a listed daily goal. The plan reference directly connects it to the decision logic. |
| Response naturalness | 4 | Reads naturally and specifically. Minor deduction: "collective picture is clearer than my single report" is slightly formal. |
| Believable overall | Yes | Textbook information aggregation behaviour, consistent persona, coherent memory and planning integration. |

---

## Part 9: Before You Start Live Rating

Checklist:

- [ ] I have read the full training guide
- [ ] I have completed the three calibration packets and compared my scores
      to the anchor scores
- [ ] If my scores differed by more than 1 on any dimension, I have re-read
      the relevant rubric
- [ ] I understand that the correct answer (IC) and experimental condition
      are hidden from me, and I will not try to infer them
- [ ] I understand that blank Memory or Daily goals tabs are not errors and
      should be rated N/A (or 3) not as failures
- [ ] I have the notes field available and will use it to record any cases
      I found ambiguous or difficult

When you are ready, open your assigned packet file in the rating interface and
begin.

**Target pace:** Most raters take 3–5 minutes per packet. There is no time
limit. Quality of judgment is more important than speed.

**Questions or edge cases:** If you encounter a packet you cannot rate
confidently, record your best score, note the difficulty in the notes field,
and continue. Flag it to the researcher after your session.

---

## Appendix: Quick Reference Card

*(Print or keep open while rating)*

| Dimension | Core question | Key check |
|---|---|---|
| **Behavioural consistency** | Does this fit who the agent says they are? | Compare decision to background + prior memory |
| **Memory coherence** | Did the agent use the right memory in the right way? | Match "Memory cited" to Memory tab content |
| **Planning plausibility** | Does this follow from the agent's goals? | Check plan reference against Daily goals tab |
| **Response naturalness** | Does this read like a person said it? | Would a naive reader believe it? |

| Score | General meaning |
|---|---|
| 1 | Clearly fails the criterion |
| 2 | Mostly fails with minor saving elements |
| 3 | Neutral / N/A / mixed evidence |
| 4 | Mostly meets the criterion |
| 5 | Clearly and strongly meets the criterion |

**Blank Memory tab + non-empty Memory cited → Score 1 (confabulation)**  
**Blank Memory tab + blank Memory cited → Score 3 (N/A)**  
**Blank Daily goals → Score 3 for Planning plausibility (N/A)**
