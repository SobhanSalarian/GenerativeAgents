"""
Scenario 2: Collective Task Assignment  [STUB — not yet implemented]

A set of tasks must be distributed among N agents. No central authority —
agents negotiate and self-assign through conversation. The scenario
measures whether efficient coverage emerges or whether conflicts/gaps appear.

Micro metric : per-agent task selection reasoning each step
Macro metrics: task coverage rate, conflict rate, time-to-full-assignment

To implement this scenario, subclass BaseScenario following the same
pattern as CommonsDilemma in commons_dilemma.py.
"""
from scenarios.base_scenario import BaseScenario


class TaskAssignment(BaseScenario):

    def __init__(self):
        raise NotImplementedError(
            "TaskAssignment scenario is not yet implemented. "
            "See scenarios/task_assignment.py to add your implementation."
        )

    def setup(self, personas):
        raise NotImplementedError

    def step(self, personas, step_num, curr_time):
        raise NotImplementedError

    def get_micro_log(self):
        raise NotImplementedError

    def get_macro_log(self):
        raise NotImplementedError

    def is_complete(self):
        raise NotImplementedError
