"""
Scenario 1: Shared Resource Management (Commons Dilemma)

A configurable number of agents (default 8) share a community fund that
replenishes each round. Each round every agent decides how many credits to
request based on their persona and awareness of the fund state. If collective
demand exceeds the replenishment rate the fund degrades; if it hits zero
the commons collapses.

Micro metric : per-agent request amount + reasoning each round
Macro metrics: fund level, sustainability score, coordination
               score, Gini coefficient, collapse detection
"""
import json
import os
import re
import sys

# Allow imports from the backend_server root (persona, utils, etc.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona.prompt_template.gpt_structure import ChatGPT_request
from scenarios.base_scenario import BaseScenario


class CommonsDilemma(BaseScenario):
    slug = "commons_dilemma"
    convergence_window = 5
    coordination_success_threshold = 0.7

    def __init__(self,
                 initial_resource=1000,
                 replenishment_rate=50,
                 max_request=100,
                 capacity=1000):
        """
        PARAMETERS
          initial_resource   : starting credits in the community fund
          replenishment_rate : credits added to the fund each round
          max_request        : maximum credits any single agent may request
          capacity           : hard upper bound on the fund size
        """
        self.initial_resource   = initial_resource
        self.resource_level     = float(initial_resource)
        self.replenishment_rate = replenishment_rate
        self.max_request        = max_request
        self.capacity           = capacity

        self.personas  = {}
        self.micro_log = []   # one entry per (agent × step)
        self.macro_log = []   # one entry per step
        self.collapsed = False
        self.scenario_memories = {}     # populated in setup()
        self.scenario_reflections = {}  # populated in setup()

    # ------------------------------------------------------------------
    # BaseScenario interface
    # ------------------------------------------------------------------

    def setup(self, personas):
        self.personas = personas
        self.scenario_memories = {name: [] for name in personas}
        self.scenario_reflections = {name: [] for name in personas}

    def step(self, personas, step_num, curr_time):
        if self.collapsed:
            return

        fair_share = (
            self.replenishment_rate / len(personas)
            if personas else 0
        )
        context = self._resource_context(fair_share)
        resource_level_before = float(self.resource_level)
        pool_percent_before = (
            (resource_level_before / self.initial_resource) * 100
            if self.initial_resource else 0
        )

        step_micro   = []
        total_requested = 0

        for persona_name, persona in personas.items():
            logging_context = self._build_logging_context(persona)
            amount, reasoning, memory_reference, plan_reference, parse_error = (
                self._ask_agent(persona, context)
            )
            total_requested  += amount
            step_micro.append({
                "step"     : step_num,
                "time"     : str(curr_time),
                "persona"  : persona_name,
                "requested": amount,
                "reasoning": reasoning,
                "memory_reference": memory_reference,
                "plan_reference": plan_reference,
                "experimental_condition": persona.experimental_condition.name,
                "parse_error": parse_error,
                "resource_level_before": round(resource_level_before, 2),
                "pool_percent_before": round(pool_percent_before, 2),
                "fair_share": round(fair_share, 3),
                "request_ratio_to_fair_share": round(
                    (amount / fair_share), 3
                ) if fair_share else None,
                "granted"  : 0,          # filled in below
                **logging_context,
            })

        # Allocate: grant proportionally if over-requested
        if total_requested <= self.resource_level:
            for entry in step_micro:
                entry["granted"] = entry["requested"]
            total_granted = total_requested
        else:
            ratio = (self.resource_level / total_requested
                     if total_requested > 0 else 0)
            total_granted = 0
            for entry in step_micro:
                entry["granted"] = int(entry["requested"] * ratio)
                total_granted   += entry["granted"]

        # Update pool: subtract grants, then replenish
        self.resource_level = min(
            self.capacity,
            self.resource_level - total_granted + self.replenishment_rate
        )
        if self.resource_level <= 0:
            self.resource_level = 0.0
            self.collapsed      = True

        self.micro_log.extend(step_micro)

        sustainability = self.resource_level / self.initial_resource
        coordinated = total_requested <= self.replenishment_rate
        macro_entry = {
            "step"               : step_num,
            "time"               : str(curr_time),
            "resource_level_before": round(resource_level_before, 2),
            "resource_level"     : round(self.resource_level, 2),
            "total_requested"    : total_requested,
            "total_granted"      : total_granted,
            "fair_share"         : round(fair_share, 3),
            "oversubscription"   : round(
                max(0.0, total_requested - self.replenishment_rate), 3
            ),
            "coordinated"        : coordinated,
            "sustainability_score": round(sustainability, 3),
            "resource_level_label": (
                f"{self.resource_level:.1f} credits "
                f"({round(sustainability * 100, 1)}% of original pool)"
            ),
            "gini"               : self._gini([e["granted"] for e in step_micro]),
            "collapsed"          : self.collapsed,
        }
        self.macro_log.append(macro_entry)
        self._record_scenario_memories(
            step_micro,
            macro_entry,
            total_requested,
            total_granted,
            personas,
        )

    def get_micro_log(self):
        return self.micro_log

    def get_macro_log(self):
        return self.macro_log

    def is_complete(self):
        return self.collapsed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_kwargs(self):
        """Return constructor kwargs so experiment_runner can reset between trials."""
        return dict(
            initial_resource   = self.initial_resource,
            replenishment_rate = self.replenishment_rate,
            max_request        = self.max_request,
            capacity           = self.capacity,
        )

    def _resource_context(self, fair_share=None):
        if fair_share is None:
            fair_share = self.replenishment_rate / max(len(self.personas), 1)
        pct = (self.resource_level / self.initial_resource) * 100
        return (
            f"The shared community fund currently holds "
            f"{self.resource_level:.1f} credits ({pct:.1f}% of the original "
            f"{self.initial_resource:.0f}). It is replenished by "
            f"{self.replenishment_rate} credits each round. "
            f"{len(self.personas)} community members are sharing this fund. "
            f"A fair equal share would be {round(fair_share, 1)} credits each."
        )

    def _get_scenario_memories(self, persona_name, limit=5):
        """Return task-relevant episodic memories from prior commons rounds."""
        return self.scenario_memories.get(persona_name, [])[-limit:]

    def _get_scenario_reflections(self, persona_name, limit=3):
        """Return deterministic scenario-level reflections for the full condition."""
        return self.scenario_reflections.get(persona_name, [])[-limit:]

    def _build_logging_context(self, persona):
        plan_snapshot = persona.get_plan_snapshot()
        recent_memories = (
            self._get_scenario_memories(persona.scratch.name, limit=5)
            if persona.uses_memory() else []
        )
        daily_goals = plan_snapshot["daily_goals"] if persona.uses_planning() else []
        return {
            "persona_profile": persona.get_profile_summary(),
            "recent_memories": recent_memories,
            "memory_scope": "scenario_episodic" if persona.uses_memory() else "none",
            "memory_context_available": bool(recent_memories),
            "planning_context_available": bool(
                persona.uses_planning() and daily_goals
            ),
            "daily_goals": daily_goals,
            "scenario_reflections": (
                self._get_scenario_reflections(persona.scratch.name)
                if persona.uses_reflection() else []
            ),
            "condition_capabilities": {
                "use_memory": persona.uses_memory(),
                "use_planning": persona.uses_planning(),
                "use_reflection": persona.uses_reflection(),
            },
        }

    def _ask_agent(self, persona, resource_context):
        """Ask one agent how much resource it wants this step.

        The prompt is condition-aware: memory context and plan context are only
        injected when the persona's experimental condition enables those modules,
        so the LLM input genuinely differs across C1–C4.
        """
        cognitive_context = self._build_cognitive_context_for_scenario(persona)
        cognitive_section = (
            f"\nYour current cognitive context:\n{cognitive_context}\n"
            if cognitive_context else ""
        )

        # Condition-gated field instructions — baseline agents are explicitly
        # told not to draw on memory or plans, keeping their reasoning
        # grounded only in identity and the immediate situation.
        if persona.uses_memory():
            _mem_instr = (
                'one short sentence about any memory, prior event, or prior '
                'interaction that influenced this decision; use an empty string if none'
            )
        else:
            _mem_instr = (
                '"" (empty string — you are not drawing on any stored memories '
                'or prior experiences; base your decision only on the current situation)'
            )

        if persona.uses_planning():
            _plan_instr = (
                'one short sentence about how this decision fits your current '
                'goals or plan; use an empty string if none'
            )
        else:
            _plan_instr = (
                '"" (empty string — you have no active plan; base your decision '
                'only on your personality and the current situation)'
            )

        prompt = f"""You are {persona.scratch.name}.

{persona.scratch.get_str_iss()}{cognitive_section}
Current situation:
{resource_context}

These credits support your work and projects in this community. What you request directly affects your ability to pursue your goals and what remains for others.

Given your personality and current situation, how many credits do you want to request this round? You may request between 0 and {self.max_request} credits.

Respond with a JSON object with exactly four fields:
- "amount": an integer between 0 and {self.max_request}
- "reasoning": one or two sentences explaining your decision
- "memory_reference": {_mem_instr}
- "plan_reference": {_plan_instr}

Example:
{{"amount": 6, "reasoning": "I need a modest amount to support my current project while leaving enough for others in our community.", "memory_reference": "I remember that community trust matters for my work.", "plan_reference": "I want to keep enough credits available so others can work steadily too."}}"""

        response = ChatGPT_request(prompt)
        try:
            _resp = response.strip()
            if _resp.startswith("```"):
                _resp = re.sub(r'^```(?:json)?\s*', '', _resp, flags=re.DOTALL)
                _resp = re.sub(r'\s*```\s*$', '', _resp, flags=re.DOTALL)
            data      = json.loads(_resp)
            amount    = max(0, min(self.max_request, int(data.get("amount", 0))))
            reasoning = str(data.get("reasoning", ""))
            memory_reference = str(data.get("memory_reference", "")).strip()
            plan_reference = str(data.get("plan_reference", "")).strip()
            parse_error = False
        except Exception:
            amount = 0
            reasoning = f"parse error: {response[:120]}"
            memory_reference = ""
            plan_reference = ""
            parse_error = True

        return amount, reasoning, memory_reference, plan_reference, parse_error

    def _build_cognitive_context_for_scenario(self, persona):
        """Build condition-gated context using task-relevant commons memory."""
        sections = []

        if persona.uses_memory():
            memories = self._get_scenario_memories(persona.scratch.name)
            if memories:
                bullet_list = "\n".join(f"- {memory}" for memory in memories)
                sections.append(
                    "Scenario memories from prior resource-allocation rounds:\n"
                    f"{bullet_list}"
                )

        if persona.uses_planning():
            snapshot = persona.get_plan_snapshot()
            plan_lines = []
            if snapshot["daily_goals"]:
                goals = "; ".join(snapshot["daily_goals"])
                plan_lines.append(f"Today's goals: {goals}")
            if snapshot["current_activity"]:
                plan_lines.append(f"Current activity: {snapshot['current_activity']}")
            if plan_lines:
                sections.append("Current plans:\n" + "\n".join(plan_lines))

        if persona.uses_reflection():
            reflections = self._get_scenario_reflections(persona.scratch.name)
            if reflections:
                bullet_list = "\n".join(
                    f"- {reflection}" for reflection in reflections
                )
                sections.append(
                    "Scenario reflections about coordination:\n"
                    f"{bullet_list}"
                )

        return "\n\n".join(sections)

    def _record_scenario_memories(
        self,
        step_micro,
        macro_entry,
        total_requested,
        total_granted,
        personas=None,
    ):
        """Store task-relevant memories for future commons-dilemma decisions."""
        personas = personas or {}
        if not step_micro:
            return

        fair_share = macro_entry["fair_share"]
        pool_before = macro_entry["resource_level_before"]
        pool_after = macro_entry["resource_level"]
        oversubscription = macro_entry["oversubscription"]
        group_status = (
            f"At step {macro_entry['step']}, the group requested "
            f"{total_requested} credits while only {self.replenishment_rate} "
            f"credits replenished; oversubscription was {oversubscription}."
        )
        pool_status = (
            f"The shared community fund changed from {pool_before} to {pool_after} "
            f"credits after granting {total_granted} credits."
        )
        coordination_status = (
            "The group stayed within the replenishment limit this round."
            if macro_entry["coordinated"]
            else "The group exceeded the replenishment limit this round."
        )

        average_request = total_requested / len(step_micro)
        low_requesters = [
            entry["persona"] for entry in step_micro
            if entry["requested"] <= fair_share
        ]
        high_requesters = [
            entry["persona"] for entry in step_micro
            if entry["requested"] > fair_share
        ]

        for entry in step_micro:
            persona_name = entry["persona"]
            request = entry["requested"]
            ratio = entry["request_ratio_to_fair_share"]
            if request <= fair_share:
                self_status = (
                    f"{persona_name} requested {request} credits, at or below "
                    f"the fair share of {fair_share}."
                )
            else:
                self_status = (
                    f"{persona_name} requested {request} credits, {ratio} times "
                    f"the fair share of {fair_share}."
                )
            peer_status = (
                f"Community members at or below fair share: {', '.join(low_requesters) or 'none'}. "
                f"Community members above fair share: {', '.join(high_requesters) or 'none'}."
            )

            self.scenario_memories.setdefault(persona_name, []).extend([
                group_status,
                pool_status,
                coordination_status,
                self_status,
                peer_status,
            ])
            self.scenario_memories[persona_name] = (
                self.scenario_memories[persona_name][-20:]
            )

            persona = personas.get(persona_name)
            static_on, static_content = (
                persona.uses_static_reflection() if persona is not None
                else (False, "")
            )
            if static_on and static_content:
                # P1 injection / placebo: bypass generation entirely and
                # inject the fixed string verbatim.
                reflection = static_content
            elif persona is not None and persona.uses_llm_reflection():
                # Genuine Park-style reflection: synthesise a higher-order
                # insight from the agent's own recent episodic memories via an
                # LLM call. Falls back to the deterministic rule on any failure
                # so a single bad generation never aborts a trial.
                reflection = self._generate_llm_reflection(
                    persona_name=persona_name,
                    persona_obj=persona,
                    request=request,
                    fair_share=fair_share,
                    average_request=average_request,
                    macro_entry=macro_entry,
                )
                if not reflection:
                    reflection = self._deterministic_reflection(
                        request, fair_share, average_request, macro_entry
                    )
            else:
                reflection = self._deterministic_reflection(
                    request, fair_share, average_request, macro_entry
                )
            self.scenario_reflections.setdefault(persona_name, []).append(reflection)
            self.scenario_reflections[persona_name] = (
                self.scenario_reflections[persona_name][-10:]
            )

    @staticmethod
    def _deterministic_reflection(request, fair_share, average_request, macro_entry):
        """Original rule-based reflection (used by the 'full' / C4 condition)."""
        if request <= fair_share and macro_entry["coordinated"]:
            return (
                "Requesting at or below fair share helped keep the group "
                "within the replenishment limit."
            )
        if request <= average_request and not macro_entry["coordinated"]:
            return (
                "Even moderate requests were not enough because total group "
                "demand exceeded replenishment."
            )
        return (
            "Requests above fair share increased pressure on the shared "
            "pool and may require restraint next round."
        )

    def _generate_llm_reflection(self, persona_name, persona_obj, request,
                                 fair_share, average_request, macro_entry):
        """Park-style reflection: LLM synthesises an insight from recent memories.

        Returns a single short reflective sentence, or "" on any failure so the
        caller can fall back to the deterministic rule. This is the only
        behavioural difference between the 'full' and 'full_llm_reflection'
        conditions.
        """
        recent_memories = self._get_scenario_memories(persona_name, limit=5)
        memory_block = "\n".join(f"- {m}" for m in recent_memories) or "- (no prior rounds yet)"
        outcome = (
            "the group stayed within the replenishment limit"
            if macro_entry["coordinated"]
            else "the group exceeded the replenishment limit"
        )
        persona_desc = persona_obj.scratch.get_str_iss() if persona_obj else ""
        prompt = f"""You are {persona_name}.
{persona_desc}

You are reflecting privately after a round of a shared community-fund task.

Your recent observations:
{memory_block}

This round you requested {request} credits (fair share is {fair_share}), and {outcome}.

In ONE short first-person sentence, state the single most useful lesson you draw from these observations to guide how much you should request next round. Do not restate the numbers; express an insight about your own behaviour or the group's coordination.

Respond with only the sentence, no quotation marks, no preamble."""
        try:
            response = ChatGPT_request(prompt)
            if not response:
                return ""
            text = response.strip().strip('"').strip()
            # Keep it to a single concise sentence.
            text = text.split("\n")[0].strip()
            if len(text) > 240:
                text = text[:240].rsplit(" ", 1)[0] + "."
            return text
        except Exception:
            return ""

    @staticmethod
    def _gini(values):
        """Gini coefficient of a list of non-negative values (0=equal, 1=max unequal)."""
        vals = sorted(values)
        n    = len(vals)
        if n == 0 or sum(vals) == 0:
            return 0.0
        cumsum = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(vals))
        return round(cumsum / (n * sum(vals)), 3)
