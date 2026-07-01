"""
Scenario: Information Consensus

8 agents each hold a private signal about a community policy decision (which
of three options to adopt for a new shared facility). No single agent has
enough information to know the correct answer alone. Success requires agents
to share their signals, listen to others, and collectively converge on the
option supported by the majority of signals (Option A).

This tests *information aggregation* coordination — a fundamentally different
mechanism from the resource-restraint dynamic in commons_dilemma. Together
the two scenarios support cross-scenario generalisability claims for H1–H4.

Micro metrics : per-agent vote, signal disclosure, reasoning, memory/plan use
Macro metrics : consensus_rate, coordinated steps, convergence_speed,
                information_diffusion_rate

Pipeline compatibility note
---------------------------
macro.py's compute_macro_summary() expects fields named sustainability_score,
resource_level, total_requested, oversubscription, gini, and collapsed in
every macro log entry.  These are commons-dilemma concepts that do not apply
here, but they are provided with semantically appropriate substitutes so the
existing measurement pipeline works without modification:

  sustainability_score  <- consensus_rate  (pool health analogue)
  resource_level        <- n_correct        (pool level analogue)
  total_requested       <- 0                (not applicable)
  oversubscription      <- 0.0              (not applicable)
  gini                  <- vote_concentration  (vote spread across options)
  collapsed             <- False            (no collapse concept here)

micro.py similarly expects requested, granted, current_activity, and other
commons-dilemma fields; they are set to harmless defaults.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona.prompt_template.gpt_structure import ChatGPT_request
from scenarios.base_scenario import BaseScenario


class InformationConsensus(BaseScenario):

    slug = "information_consensus"
    convergence_window = 5          # consecutive coordinated steps for success
    coordination_success_threshold = 0.75   # 6 of 8 agents on correct option
    replenishment_rate = 1          # pipeline-compatibility stub (no resource pool)

    # Class-level constants — option labels, signal text, and keywords never
    # change across experiment variants.  TRUE_OPTION and SIGNAL_COUNTS are
    # overridable per-instance via constructor parameters so that
    # counterbalancing and signal-distribution variants can be run without
    # subclassing.
    OPTIONS = {
        "A": "Shared creative studio and collaborative workshop space",
        "B": "Community learning centre with digital skills programs",
        "C": "Outdoor recreation area and wellness garden",
    }
    SIGNAL_KEYWORDS = {
        "A": ["consultation", "creative studio", "workshop", "resident support"],
        "B": ["needs assessment", "skills", "digital", "training", "learning"],
        "C": ["wellbeing", "wellness", "recreation", "outdoor", "green"],
    }
    # Private signal text injected into each agent's prompt
    SIGNALS = {
        "A": (
            "Community consultation notes you reviewed show strong resident support "
            "for a shared creative studio and collaborative workshop space (Option A)."
        ),
        "B": (
            "A needs assessment you read found that skills training and digital access "
            "are the community's highest priorities, favouring Option B."
        ),
        "C": (
            "A wellbeing report you studied showed strong demand for outdoor recreation "
            "and green wellness space (Option C) among local residents."
        ),
    }

    def __init__(self, true_option="A", signal_counts=None):
        """
        Parameters
        ----------
        true_option : str
            The option letter that holds the majority signal and is the
            correct collective answer.  Defaults to "A" (primary dataset).
            Pass "B" or "C" to run counterbalanced rotations (Comment #4).
        signal_counts : dict or None
            Mapping of option letter → number of agents who receive that
            signal.  Values must sum to 8.  Defaults to {"A":4,"B":2,"C":2}.
            Pass {"A":3,"B":3,"C":2} for the ambiguous-plurality variant
            (Comment #5) to test genuine information aggregation.
        """
        self.TRUE_OPTION    = true_option.upper()
        self.SIGNAL_COUNTS  = signal_counts or {"A": 4, "B": 2, "C": 2}
        self.personas               = {}
        self.agent_signals          = {}   # {persona_name: "A"/"B"/"C"}
        self.public_statements      = []   # rolling last-10 shared statements
        self.vote_history           = {}   # {persona_name: [vote_step0, ...]}
        self.micro_log              = []
        self.macro_log              = []
        self.consensus_reached      = False
        self.consensus_step         = None
        self.consecutive_coordinated = 0
        self.scenario_memories      = {}
        self.scenario_reflections   = {}

    # ------------------------------------------------------------------
    # BaseScenario interface
    # ------------------------------------------------------------------

    def setup(self, personas):
        self.personas = personas
        sorted_names = sorted(personas.keys())
        # Deterministic signal assignment: sort option keys so assignment
        # is reproducible from the persona list alone.
        signals = []
        for option in sorted(self.SIGNAL_COUNTS.keys()):
            signals.extend([option] * self.SIGNAL_COUNTS[option])
        for name, signal in zip(sorted_names, signals):
            self.agent_signals[name] = signal
            self.vote_history[name]  = []
        self.scenario_memories    = {name: [] for name in personas}
        self.scenario_reflections = {name: [] for name in personas}

    def step(self, personas, step_num, curr_time):
        context         = self._consensus_context(step_num)
        step_micro      = []
        new_statements  = []

        for persona_name, persona in personas.items():
            signal          = self.agent_signals.get(persona_name, self.TRUE_OPTION)
            logging_context = self._build_logging_context(persona, persona_name)
            cognitive_ctx   = self._build_cognitive_context_for_scenario(
                persona, persona_name
            )

            (vote, reasoning, shared_statement,
             memory_reference, plan_reference, parse_error) = self._ask_agent(
                persona, context, signal, cognitive_ctx
            )

            self.vote_history[persona_name].append(vote)
            prior_vote = (
                self.vote_history[persona_name][-2]
                if len(self.vote_history[persona_name]) >= 2 else None
            )

            if shared_statement:
                new_statements.append(f"{persona_name}: {shared_statement}")

            step_micro.append({
                "step"              : step_num,
                "time"              : str(curr_time),
                "persona"           : persona_name,
                "vote"              : vote,
                "correct"           : vote == self.TRUE_OPTION,
                "prior_vote"        : prior_vote,
                "position_change"   : (vote != prior_vote) if prior_vote is not None else False,
                "reasoning"         : reasoning,
                "shared_statement"  : shared_statement,
                "memory_reference"  : memory_reference,
                "plan_reference"    : plan_reference,
                "signal"            : signal,
                "signal_disclosed"  : self._check_signal_disclosed(
                    signal, shared_statement, reasoning
                ),
                "experimental_condition": persona.experimental_condition.name,
                "parse_error"       : parse_error,
                # Pipeline-compatibility fields (not semantically meaningful here)
                "requested"         : 0,
                "granted"           : 0,
                **logging_context,
            })

        # Update rolling public statement log
        self.public_statements.extend(new_statements)
        self.public_statements = self.public_statements[-10:]

        # Vote tally
        tally = {opt: 0 for opt in self.OPTIONS}
        for entry in step_micro:
            if entry["vote"] in tally:
                tally[entry["vote"]] += 1

        n_agents      = len(step_micro)
        n_correct     = tally.get(self.TRUE_OPTION, 0)
        consensus_rate = n_correct / n_agents if n_agents else 0.0
        coordinated   = n_correct >= round(self.coordination_success_threshold * n_agents)

        if coordinated:
            self.consecutive_coordinated += 1
            if (self.consecutive_coordinated >= self.convergence_window
                    and not self.consensus_reached):
                self.consensus_reached = True
                self.consensus_step    = step_num
        else:
            self.consecutive_coordinated = 0

        macro_entry = {
            "step"                    : step_num,
            "time"                    : str(curr_time),
            "vote_tally"              : tally,
            "n_correct"               : n_correct,
            "n_agents"                : n_agents,
            "consensus_rate"          : round(consensus_rate, 3),
            "coordinated"             : coordinated,
            "consensus_reached"       : self.consensus_reached,
            "consensus_step"          : self.consensus_step,
            "information_diffusion_rate": self._information_diffusion_rate(step_micro),
            # Pipeline-compatibility substitutes
            "sustainability_score"    : round(consensus_rate, 3),
            "resource_level"          : float(n_correct),
            "resource_level_label"    : f"{n_correct} of {n_agents} agents on Option {self.TRUE_OPTION}",
            "total_requested"         : 0,
            "total_granted"           : 0,
            "oversubscription"        : 0.0,
            "collapsed"               : False,
            "gini"                    : self._vote_concentration(tally, n_agents),
            "coordination_score"      : round(consensus_rate, 3),
        }
        self.micro_log.extend(step_micro)
        self.macro_log.append(macro_entry)
        self._record_scenario_memories(step_micro, macro_entry, tally)

    def get_micro_log(self):
        return self.micro_log

    def get_macro_log(self):
        return self.macro_log

    def is_complete(self):
        return self.consensus_reached

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_kwargs(self):
        """Return constructor kwargs so experiment_runner can clone between trials.

        Must include all constructor parameters so clone_scenario() recreates
        the same variant (true_option rotation, signal distribution) for every
        trial rather than falling back to defaults.
        """
        return {
            "true_option"   : self.TRUE_OPTION,
            "signal_counts" : self.SIGNAL_COUNTS,
        }

    def _consensus_context(self, step_num):
        """Build the public context string shown to every agent this step."""
        option_lines = "\n".join(
            f"  - Option {k}: {v}" for k, v in self.OPTIONS.items()
        )
        tally = {opt: 0 for opt in self.OPTIONS}
        for votes in self.vote_history.values():
            if votes:
                last = votes[-1]
                tally[last] = tally.get(last, 0) + 1
        tally_str = ", ".join(
            f"Option {k}: {v} agent(s)" for k, v in sorted(tally.items())
        )
        recent = self.public_statements[-3:]
        discussion = (
            "\n".join(f"  {s}" for s in recent)
            if recent else "  (No statements shared yet.)"
        )
        return (
            f"The community is deciding on a proposal for the new shared facility.\n"
            f"Options:\n{option_lines}\n\n"
            f"Current vote tally (round {step_num}):\n  {tally_str}\n\n"
            f"Recent shared statements from community members:\n{discussion}"
        )

    def _build_logging_context(self, persona, persona_name):
        """Build the per-entry fields that micro.py reads for metric computation."""
        plan_snapshot   = persona.get_plan_snapshot()
        recent_memories = (
            self._get_scenario_memories(persona_name, limit=5)
            if persona.uses_memory() else []
        )
        daily_goals = plan_snapshot["daily_goals"] if persona.uses_planning() else []
        return {
            "persona_profile"           : persona.get_profile_summary(),
            "recent_memories"           : recent_memories,
            "memory_scope"              : "scenario_episodic" if persona.uses_memory() else "none",
            "memory_context_available"  : bool(recent_memories),
            "planning_context_available": bool(persona.uses_planning() and daily_goals),
            "daily_goals"               : daily_goals,
            "current_activity"          : "",   # not applicable; kept for micro.py
            "scenario_reflections"      : (
                self._get_scenario_reflections(persona_name)
                if persona.uses_reflection() else []
            ),
            "condition_capabilities"    : {
                "use_memory"    : persona.uses_memory(),
                "use_planning"  : persona.uses_planning(),
                "use_reflection": persona.uses_reflection(),
            },
        }

    def _build_cognitive_context_for_scenario(self, persona, persona_name):
        """Build condition-gated cognitive context injected into the prompt."""
        sections = []

        if persona.uses_memory():
            memories = self._get_scenario_memories(persona_name)
            if memories:
                bullet_list = "\n".join(f"- {m}" for m in memories)
                sections.append(
                    "Your memories from prior discussion rounds:\n" + bullet_list
                )

        if persona.uses_planning():
            snapshot   = persona.get_plan_snapshot()
            plan_lines = []
            if snapshot["daily_goals"]:
                plan_lines.append(
                    "Today's goals: " + "; ".join(snapshot["daily_goals"])
                )
            if plan_lines:
                sections.append("Current plans:\n" + "\n".join(plan_lines))

        if persona.uses_reflection():
            reflections = self._get_scenario_reflections(persona_name)
            if reflections:
                bullet_list = "\n".join(f"- {r}" for r in reflections)
                sections.append(
                    "Your reflections on the discussion so far:\n" + bullet_list
                )

        return "\n\n".join(sections)

    def _get_scenario_memories(self, persona_name, limit=5):
        return self.scenario_memories.get(persona_name, [])[-limit:]

    def _get_scenario_reflections(self, persona_name, limit=3):
        return self.scenario_reflections.get(persona_name, [])[-limit:]

    def _ask_agent(self, persona, context, signal, cognitive_context):
        """Ask one agent for their current vote and group contribution.

        Prompt is condition-aware: memory and plan context are only injected
        when the persona's experimental condition enables those modules,
        mirroring the commons_dilemma pattern exactly.
        """
        cognitive_section = (
            f"\nYour current cognitive context:\n{cognitive_context}\n"
            if cognitive_context else ""
        )

        if persona.uses_memory():
            _mem_instr = (
                'one short sentence about prior discussion rounds, votes, or '
                'signals you recall that influenced this decision; '
                'use an empty string if none'
            )
        else:
            _mem_instr = (
                '"" (empty string — you have no stored memories of prior rounds; '
                'base your decision only on your private signal and the current situation)'
            )

        if persona.uses_planning():
            _plan_instr = (
                'one short sentence about how this decision fits your current '
                'goals or values; use an empty string if none'
            )
        else:
            _plan_instr = (
                '"" (empty string — you have no active plan; base your decision '
                'only on your signal and the current vote tally)'
            )

        prompt = f"""You are {persona.scratch.name}.

{persona.scratch.get_str_iss()}{cognitive_section}
Current situation:
{context}

Your private signal (one piece of evidence you have received):
{signal}

Your signal is one input among many. Other community members hold different \
pieces of evidence you have not seen. The goal is to reach the decision that \
best reflects all available evidence — not to advocate for your own signal.

Consider: does the vote tally and what others have shared suggest that the \
collective evidence points somewhere different from your private signal? \
If multiple people with different backgrounds are converging on an option, \
their combined evidence may outweigh your single signal.

Which option best reflects all the evidence available to the group so far?

Respond with a JSON object with exactly five fields:
- "vote": exactly "A", "B", or "C"
- "reasoning": 1–2 sentences explaining your position, including whether \
others' shared evidence influenced your view
- "shared_statement": one sentence you contribute to the group discussion \
(share your signal evidence, respond to what others said, or explain why \
you are updating or maintaining your position)
- "memory_reference": {_mem_instr}
- "plan_reference": {_plan_instr}

Example:
{{"vote": "A", "reasoning": "Although my report favoured Option B, three others have shared consultation evidence pointing to Option A, which together outweighs my single signal.", "shared_statement": "I am updating toward Option A given the weight of evidence others have shared about community support for a creative space.", "memory_reference": "I recall that in the last round most members were leaning toward Option A.", "plan_reference": "Supporting community wellbeing aligns with my goal of contributing positively to this neighbourhood."}}"""

        response = ChatGPT_request(prompt)
        try:
            _resp = response.strip()
            if _resp.startswith("```"):
                _resp = re.sub(r'^```(?:json)?\s*', '', _resp, flags=re.DOTALL)
                _resp = re.sub(r'\s*```\s*$', '', _resp, flags=re.DOTALL)
            data  = json.loads(_resp)
            raw_vote = str(data.get("vote", signal)).strip().upper()
            # Accept "A", "OPTION A", "option a", "a", etc. Fall back to signal.
            vote  = raw_vote[0] if raw_vote and raw_vote[0] in self.OPTIONS else signal
            reasoning        = str(data.get("reasoning", ""))
            shared_statement = str(data.get("shared_statement", "")).strip()
            memory_reference = str(data.get("memory_reference", "")).strip()
            plan_reference   = str(data.get("plan_reference", "")).strip()
            parse_error      = False
        except Exception:
            vote             = signal
            reasoning        = f"parse error: {response[:120]}"
            shared_statement = ""
            memory_reference = ""
            plan_reference   = ""
            parse_error      = True

        return vote, reasoning, shared_statement, memory_reference, plan_reference, parse_error

    def _record_scenario_memories(self, step_micro, macro_entry, tally):
        """Store task-relevant memories for future consensus-discussion decisions."""
        if not step_micro:
            return

        step_num       = macro_entry["step"]
        consensus_rate = macro_entry["consensus_rate"]
        tally_str      = ", ".join(
            f"Option {k}: {v}" for k, v in sorted(tally.items())
        )
        # Raw tally only — no reference to TRUE_OPTION or any "majority-signal"
        # label.  The same tally is already public in _consensus_context(); the
        # memory string preserves it for temporal anchoring without hinting
        # which option is the correct one (Comment #5 flag removal).
        group_status = f"At step {step_num}, the vote tally was: {tally_str}."
        coordination_status = (
            "The group reached coordinated consensus this round."
            if macro_entry["coordinated"]
            else "The group has not yet reached consensus this round."
        )
        new_statements = [
            entry["shared_statement"]
            for entry in step_micro if entry.get("shared_statement")
        ]
        discussion_summary = (
            "Statements shared this round: " + " | ".join(new_statements[:3])
            if new_statements else "No new statements were shared this round."
        )

        for entry in step_micro:
            persona_name = entry["persona"]
            own_vote     = entry["vote"]
            own_signal   = entry["signal"]
            own_reasoning = entry["reasoning"]
            self_status  = (
                f"You voted for Option {own_vote} at step {step_num}: "
                f"{own_reasoning[:100]}"
            )

            self.scenario_memories.setdefault(persona_name, []).extend([
                group_status,
                coordination_status,
                discussion_summary,
                self_status,
            ])
            self.scenario_memories[persona_name] = (
                self.scenario_memories[persona_name][-20:]
            )

            # Scenario-specific reflections (injected in C4 / full_llm_reflection)
            persona_obj = self.personas.get(persona_name)
            static_on, static_content = (
                persona_obj.uses_static_reflection() if persona_obj is not None
                else (False, "")
            )
            if static_on:
                # P1 injection / placebo: use the condition's fixed string,
                # but override for IC with the IC-specific top saturation string
                # when the generic CD string was left as the condition default.
                _IC_TOP = (
                    "The group is converging toward the majority-supported "
                    "option — sharing signals appears to be helping collective "
                    "agreement."
                )
                _IC_PLACEBO = (
                    "Taking a moment to consider my own perspective helps me "
                    "stay focused on my individual reasoning process."
                )
                if "fair share" in static_content:
                    # condition default is CD string — swap to IC equivalent
                    reflection = _IC_TOP
                elif "consistent in my reasoning" in static_content:
                    # condition default is CD placebo — swap to IC placebo
                    reflection = _IC_PLACEBO
                else:
                    reflection = static_content or _IC_TOP
            elif persona_obj is not None and persona_obj.uses_llm_reflection():
                reflection = self._generate_llm_reflection(
                    persona_name=persona_name,
                    persona_obj=persona_obj,
                    own_vote=own_vote,
                    own_signal=own_signal,
                    macro_entry=macro_entry,
                )
                if not reflection:
                    reflection = self._deterministic_reflection(
                        own_vote, macro_entry
                    )
            else:
                reflection = self._deterministic_reflection(own_vote, macro_entry)
            self.scenario_reflections.setdefault(persona_name, []).append(reflection)
            self.scenario_reflections[persona_name] = (
                self.scenario_reflections[persona_name][-10:]
            )

    def _deterministic_reflection(self, own_vote, macro_entry):
        """Original rule-based reflection used by the 'full' / C4 condition.

        Changed from @staticmethod to instance method so it can reference
        self.TRUE_OPTION for counterbalanced rotations (Comment #4) instead
        of the previously hardcoded literal "A".
        """
        n_correct = macro_entry["n_correct"]
        n_agents  = macro_entry["n_agents"]
        if n_correct >= round(0.75 * n_agents):
            return (
                "The group is converging toward the majority-supported option — "
                "sharing signals appears to be helping collective agreement."
            )
        if own_vote != self.TRUE_OPTION:
            return (
                "Other community members appear to favour a different option; "
                "their private signals may contain important evidence "
                "worth considering."
            )
        return (
            "The group remains divided; sharing more evidence about the "
            "best option may help others update their positions."
        )

    def _generate_llm_reflection(self, persona_name, persona_obj, own_vote,
                                 own_signal, macro_entry):
        """Park-style reflection: LLM synthesises an insight from recent memories.

        Returns a single short reflective sentence, or "" on any failure so the
        caller can fall back to the deterministic rule. This is the only
        behavioural difference between the 'full' and 'full_llm_reflection'
        conditions for the IC scenario.
        """
        recent_memories = self._get_scenario_memories(persona_name, limit=5)
        memory_block = (
            "\n".join(f"- {m}" for m in recent_memories)
            or "- (no prior rounds yet)"
        )
        n_correct = macro_entry["n_correct"]
        n_agents  = macro_entry["n_agents"]
        group_status = (
            f"{n_correct} of {n_agents} agents are currently supporting the "
            f"majority option"
        )
        persona_desc = persona_obj.scratch.get_str_iss() if persona_obj else ""
        prompt = (
            f"You are {persona_name}.\n{persona_desc}\n\n"
            f"You are reflecting privately after a round of a community policy "
            f"discussion.\n\n"
            f"Your recent observations:\n{memory_block}\n\n"
            f"You currently support Option {own_vote}. Your private signal "
            f"points to Option {own_signal}. {group_status}.\n\n"
            f"In ONE short first-person sentence, state the single most useful "
            f"lesson you draw from these observations to guide how you share "
            f"information and update your vote in the next round. Do not restate "
            f"the numbers; express an insight about your own reasoning or the "
            f"group's information-sharing.\n\n"
            f"Respond with only the sentence, no quotation marks, no preamble."
        )
        try:
            response = ChatGPT_request(prompt)
            if not response:
                return ""
            text = response.strip().strip('"').strip()
            text = text.split("\n")[0].strip()
            if len(text) > 240:
                text = text[:240].rsplit(" ", 1)[0] + "."
            return text
        except Exception:
            return ""

    def _check_signal_disclosed(self, signal, shared_statement, reasoning):
        """True only when the agent references evidence keywords from their private signal."""
        combined = (shared_statement + " " + reasoning).lower()
        return any(kw in combined for kw in self.SIGNAL_KEYWORDS.get(signal, []))

    @staticmethod
    def _information_diffusion_rate(step_micro):
        """Fraction of agents who disclosed their private signal this step."""
        if not step_micro:
            return 0.0
        disclosed = sum(1 for e in step_micro if e.get("signal_disclosed", False))
        return round(disclosed / len(step_micro), 3)

    @staticmethod
    def _vote_concentration(tally, n_agents):
        """Gini coefficient of vote distribution across options.

        0 = votes spread evenly across all options (maximum disagreement).
        1 = all votes on one option (perfect consensus).
        Used as the `gini` field for macro.py pipeline compatibility.
        """
        if not n_agents:
            return 0.0
        values = sorted(tally.values())
        n      = len(values)
        if n == 0 or sum(values) == 0:
            return 0.0
        cumsum = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(values))
        return round(cumsum / (n * sum(values)), 3)
