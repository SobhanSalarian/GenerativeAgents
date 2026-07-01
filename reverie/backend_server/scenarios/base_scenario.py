"""
Base scenario interface for all simulation scenarios.

Every scenario must inherit from BaseScenario and implement all
abstract methods. This ensures that experiment_runner.py and
ReverieServer can work with any scenario interchangeably.
"""
from abc import ABC, abstractmethod


class BaseScenario(ABC):

    @abstractmethod
    def setup(self, personas):
        """
        Called once before the simulation starts.
        Use this to initialise scenario state and store the persona dict.

        INPUT
          personas: dict  {persona_name: Persona instance}
        """
        pass

    @abstractmethod
    def step(self, personas, step_num, curr_time):
        """
        Called once per simulation step, after all persona.move() calls.

        INPUT
          personas : dict       {persona_name: Persona instance}
          step_num : int        current simulation step index
          curr_time: datetime   current simulation time
        """
        pass

    @abstractmethod
    def get_micro_log(self):
        """
        Return the per-agent, per-step decision log.

        OUTPUT
          list of dicts, one entry per (agent, step).
        """
        pass

    @abstractmethod
    def get_macro_log(self):
        """
        Return the group-level outcome log.

        OUTPUT
          list of dicts, one entry per step.
        """
        pass

    @abstractmethod
    def is_complete(self):
        """
        Return True if the scenario has reached a terminal state
        (e.g. resource collapsed, task fully assigned, consensus reached).
        """
        pass

    def save_results(self, output_path):
        """
        Save micro and macro logs to JSON files under output_path.
        Concrete subclasses may override to add extra files.
        """
        import json, os
        os.makedirs(output_path, exist_ok=True)

        with open(f"{output_path}/micro_log.json", "w") as f:
            json.dump(self.get_micro_log(), f, indent=2)

        with open(f"{output_path}/macro_log.json", "w") as f:
            json.dump(self.get_macro_log(), f, indent=2)
