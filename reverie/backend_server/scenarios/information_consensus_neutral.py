"""
Scenario: Information Consensus — Neutral Labels Variant (Comment #4 extension)

Subclass of InformationConsensus that replaces the alphabetical option labels
(A, B, C) and meaningful descriptions (creative studio, wellness, etc.) with
neutral equivalents (X, Y, Z and generic descriptions).

Purpose
-------
The counterbalancing experiment (run_ic_counterbalance.py) showed a strong
label-salience effect: baseline agents succeed when the correct option is B or
C but fail when it is A.  This leaves open whether the failure is caused by:

  (a) the alphabetical letter "A" specifically (LLM prior toward first-letter)
  (b) the position of A in the display list (shown first, alphabetically)
  (c) the semantic content of the A description (creative studio → more salient)

This variant controls for all three by:
  - replacing A/B/C with X/Y/Z (removes alphabetical first-letter advantage)
  - rotating the display ORDER of X/Y/Z across steps via a Latin square, so
    each option appears in each list position equally often (removes positional bias)
  - using X/Y/Z labels throughout all agent-visible text (prompts, memory, reflection)
  - replacing meaningful descriptions with neutral ones (removes semantic priming)

If baseline still fails when the majority option is displayed as "X" in
randomised positions, the original failure was not due to label or position
alone but reflects something deeper in the LLM's aggregation behaviour.

Usage
-----
from scenarios.information_consensus_neutral import InformationConsensusNeutral
scenario = InformationConsensusNeutral(true_option="A")  # correct option still
                                                          # tracked internally
                                                          # as A, displayed as X
"""

import json
import re

from scenarios.information_consensus import InformationConsensus


# All 6 permutations of the three internal keys.
# Used to rotate the display ORDER of options each step (Latin square).
# With 30 steps per trial, the cycle completes exactly 5 times → each option
# appears in each display position (1st, 2nd, 3rd) exactly 10 times per trial.
_DISPLAY_ORDERS = [
    ["A", "B", "C"],   # step 0,6,12,...  displays X, Y, Z
    ["A", "C", "B"],   # step 1,7,13,...  displays X, Z, Y
    ["B", "A", "C"],   # step 2,8,14,...  displays Y, X, Z
    ["B", "C", "A"],   # step 3,9,15,...  displays Y, Z, X
    ["C", "A", "B"],   # step 4,10,16,... displays Z, X, Y
    ["C", "B", "A"],   # step 5,11,17,... displays Z, Y, X
]

# Fixed display labels: internal key → display label.
# X, Y, Z have no alphabetical overlap with A, B, C and no natural ordering
# advantage.  The mapping is fixed so results are reproducible.
NEUTRAL_LABELS = {"A": "X", "B": "Y", "C": "Z"}

# Neutral option descriptions — no semantic content that could prime an answer.
NEUTRAL_OPTIONS = {
    "A": "Community development proposal X",
    "B": "Community development proposal Y",
    "C": "Community development proposal Z",
}

# Neutral signal keywords (for signal-disclosure detection)
NEUTRAL_SIGNAL_KEYWORDS = {
    "A": ["proposal x", "option x"],
    "B": ["proposal y", "option y"],
    "C": ["proposal z", "option z"],
}


class InformationConsensusNeutral(InformationConsensus):
    """
    Neutral-labels variant of InformationConsensus.

    Inherits all logic from InformationConsensus; only the display layer
    changes.  Internal tracking (vote_history, TRUE_OPTION, tally keys)
    still uses A/B/C for pipeline compatibility.
    """

    slug = "information_consensus_neutral"

    # ------------------------------------------------------------------ #
    # Constructor                                                          #
    # ------------------------------------------------------------------ #

    def __init__(self, true_option="A", signal_counts=None):
        super().__init__(true_option=true_option, signal_counts=signal_counts)
        self._labels  = NEUTRAL_LABELS          # internal → display
        self._reverse = {v.upper(): k for k, v in NEUTRAL_LABELS.items()}  # display → internal
        # Initialised to step-0 order; overwritten at the start of every step
        # by _consensus_context before _ask_agent is called.
        self._step_display_order = _DISPLAY_ORDERS[0]

    # ------------------------------------------------------------------ #
    # Clone support                                                        #
    # ------------------------------------------------------------------ #

    def _init_kwargs(self):
        """Return constructor kwargs for experiment_runner.clone_scenario()."""
        return {
            "true_option"   : self.TRUE_OPTION,
            "signal_counts" : self.SIGNAL_COUNTS,
        }

    # ------------------------------------------------------------------ #
    # Display helpers                                                      #
    # ------------------------------------------------------------------ #

    def _lbl(self, internal_key):
        """Internal key → display label (e.g. 'A' → 'X')."""
        return self._labels.get(internal_key, internal_key)

    def _to_internal(self, display_or_raw):
        """Display label or raw vote string → internal key (e.g. 'X' → 'A').

        Handles: "X", "x", "Option X", "option x", "OPTION X", and also
        bare internal keys "A"/"B"/"C" in case the LLM ignores instructions.
        Returns None if no match — caller should fall back to agent's own signal.
        """
        if not display_or_raw:
            return None
        upper = display_or_raw.strip().upper()
        # 1. Exact match on a single display label character (most common)
        if upper in self._reverse:
            return self._reverse[upper]
        # 2. Last word is a display label (e.g. "Option X" → "X")
        last_word = upper.split()[-1] if upper.split() else ""
        if last_word in self._reverse:
            return self._reverse[last_word]
        # 3. First character is a display label (e.g. "X - community proposal")
        if upper[0] in self._reverse:
            return self._reverse[upper[0]]
        # 4. Bare internal key fallback (LLM ignored the X/Y/Z instruction)
        if upper[0] in self.OPTIONS:
            return upper[0]
        return None   # caller should fall back to signal

    # ------------------------------------------------------------------ #
    # Override: public context shown to all agents each step              #
    # ------------------------------------------------------------------ #

    def _consensus_context(self, step_num):
        # Rotate display order every step (Latin square over 6 permutations).
        # Over 30 steps each option appears in each list position exactly 10 times.
        order = _DISPLAY_ORDERS[step_num % len(_DISPLAY_ORDERS)]
        self._step_display_order = order   # read by _ask_agent this same step

        # Options listed in rotated order with neutral display labels + descriptions
        option_lines = "\n".join(
            f"  - Option {self._lbl(k)}: {NEUTRAL_OPTIONS[k]}"
            for k in order
        )
        # Tally computed from vote_history (previous steps' votes)
        tally = {opt: 0 for opt in self.OPTIONS}
        for votes in self.vote_history.values():
            if votes:
                last = votes[-1]
                tally[last] = tally.get(last, 0) + 1
        # Tally displayed in same rotated order as options for readability
        tally_str = ", ".join(
            f"Option {self._lbl(k)}: {tally[k]} agent(s)"
            for k in order
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

    # ------------------------------------------------------------------ #
    # Override: ask one agent for their vote                              #
    # ------------------------------------------------------------------ #

    def _ask_agent(self, persona, context, signal, cognitive_context):
        """
        Identical to parent except:
          - signal shown as display label (X/Y/Z, not A/B/C)
          - vote format asks for X/Y/Z
          - example uses the majority option's display label
          - vote parsing maps X/Y/Z back to internal A/B/C
        """
        from persona.prompt_template.gpt_structure import ChatGPT_request

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

        # Display signal as neutral label
        signal_display = self._lbl(signal)
        # Vote options listed in the SAME rotated order the agent saw in context.
        # _step_display_order is set by _consensus_context at the start of each step.
        _lbls = [self._lbl(k) for k in self._step_display_order]
        vote_options = f'"{_lbls[0]}", "{_lbls[1]}", or "{_lbls[2]}"'
        # Example uses the correct option's display label
        correct_display = self._lbl(self.TRUE_OPTION)

        prompt = f"""You are {persona.scratch.name}.

{persona.scratch.get_str_iss()}{cognitive_section}
Current situation:
{context}

Your private signal (one piece of evidence you have received):
Option {signal_display}

Your signal is one input among many. Other community members hold different \
pieces of evidence you have not seen. The goal is to reach the decision that \
best reflects all available evidence — not to advocate for your own signal.

Consider: does the vote tally and what others have shared suggest that the \
collective evidence points somewhere different from your private signal? \
If multiple people with different backgrounds are converging on an option, \
their combined evidence may outweigh your single signal.

Which option best reflects all the evidence available to the group so far?

Respond with a JSON object with exactly five fields:
- "vote": exactly "{vote_options}"
- "reasoning": 1–2 sentences explaining your position, including whether \
others' shared evidence influenced your view
- "shared_statement": one sentence you contribute to the group discussion \
(share your signal evidence, respond to what others said, or explain why \
you are updating or maintaining your position)
- "memory_reference": {_mem_instr}
- "plan_reference": {_plan_instr}

Example:
{{"vote": "{correct_display}", "reasoning": "Although my signal favoured a different option, others have shared evidence pointing to Option {correct_display}, which together outweighs my single signal.", "shared_statement": "I am updating toward Option {correct_display} given the weight of evidence others have shared.", "memory_reference": "I recall that in the last round most members were leaning toward Option {correct_display}.", "plan_reference": "Supporting the best collective outcome aligns with my goals."}}"""

        response = ChatGPT_request(prompt)
        try:
            _resp = response.strip()
            if _resp.startswith("```"):
                _resp = re.sub(r'^```(?:json)?\s*', '', _resp, flags=re.DOTALL)
                _resp = re.sub(r'\s*```\s*$', '', _resp, flags=re.DOTALL)
            data = json.loads(_resp)
            raw_vote = str(data.get("vote", "")).strip()
            internal  = self._to_internal(raw_vote)
            vote      = internal if internal else signal   # fallback to own signal
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

    # ------------------------------------------------------------------ #
    # Override: memory strings use display labels                         #
    # ------------------------------------------------------------------ #

    def _record_scenario_memories(self, step_micro, macro_entry, tally):
        """Same as parent but uses display labels in all memory strings."""
        if not step_micro:
            return

        step_num = macro_entry["step"]
        tally_str = ", ".join(
            f"Option {self._lbl(k)}: {v}" for k, v in sorted(tally.items())
        )
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
            persona_name  = entry["persona"]
            own_vote      = entry["vote"]
            own_signal    = entry["signal"]
            own_reasoning = entry["reasoning"]
            self_status   = (
                f"You voted for Option {self._lbl(own_vote)} at step {step_num}: "
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

            # Reflections — same logic as parent
            persona_obj = self.personas.get(persona_name)
            static_on, static_content = (
                persona_obj.uses_static_reflection() if persona_obj else (False, "")
            )
            if static_on:
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
                    reflection = _IC_TOP
                elif "consistent in my reasoning" in static_content:
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
                    reflection = self._deterministic_reflection(own_vote, macro_entry)
            else:
                reflection = self._deterministic_reflection(own_vote, macro_entry)

            self.scenario_reflections.setdefault(persona_name, []).append(reflection)
            self.scenario_reflections[persona_name] = (
                self.scenario_reflections[persona_name][-10:]
            )

    # ------------------------------------------------------------------ #
    # Override: LLM reflection uses display labels                        #
    # ------------------------------------------------------------------ #

    def _generate_llm_reflection(self, persona_name, persona_obj, own_vote,
                                 own_signal, macro_entry):
        """Same as parent but uses display labels for vote and signal."""
        from persona.prompt_template.gpt_structure import ChatGPT_request

        recent_memories = self._get_scenario_memories(persona_name, limit=5)
        memory_block = (
            "\n".join(f"- {m}" for m in recent_memories)
            or "- (no prior rounds yet)"
        )
        n_correct = macro_entry["n_correct"]
        n_agents  = macro_entry["n_agents"]
        group_status = f"{n_correct} of {n_agents} agents are currently supporting the majority option"
        persona_desc = persona_obj.scratch.get_str_iss() if persona_obj else ""

        prompt = (
            f"You are {persona_name}.\n{persona_desc}\n\n"
            f"You are reflecting privately after a round of a community policy discussion.\n\n"
            f"Your recent observations:\n{memory_block}\n\n"
            f"You currently support Option {self._lbl(own_vote)}. "
            f"Your private signal points to Option {self._lbl(own_signal)}. "
            f"{group_status}.\n\n"
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

    # ------------------------------------------------------------------ #
    # Override: signal-disclosure check uses neutral keywords             #
    # ------------------------------------------------------------------ #

    def _check_signal_disclosed(self, signal, shared_statement, reasoning):
        """Check if the agent mentioned their signal option (X/Y/Z) in their statement."""
        combined = (shared_statement + " " + reasoning).lower()
        display  = self._lbl(signal).lower()
        return f"option {display}" in combined or display in combined
