"""
Scenario 4: Emergency Coordination  [STUB — not yet implemented]

Agents face an unexpected event and must coordinate a response without
a designated leader. The scenario measures whether an organised collective
response emerges and how individual believability relates to group resilience.

Micro metric : per-agent response decisions and reasoning each step
Macro metrics: response coverage, time-to-coordination, leaderless emergence rate

To implement this scenario, subclass BaseScenario following the same
pattern as CommonsDilemma in commons_dilemma.py.
"""
from scenarios.base_scenario import BaseScenario


class EmergencyCoordination(BaseScenario):

    def __init__(self):
        raise NotImplementedError(
            "EmergencyCoordination scenario is not yet implemented. "
            "See scenarios/emergency_coordination.py to add your implementation."
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
