"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: persona.py
Description: Defines the Persona class that powers the agents in Reverie. 

Note (May 1, 2023) -- this is effectively GenerativeAgent class. Persona was
the term we used internally back in 2022, taking from our Social Simulacra 
paper.
"""
import math
import sys
import datetime
import random
sys.path.append('../')

from global_methods import *

from persona.memory_structures.spatial_memory import *
from persona.memory_structures.associative_memory import *
from persona.memory_structures.scratch import *

from persona.cognitive_modules.perceive import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.plan import *
from persona.cognitive_modules.reflect import *
from persona.cognitive_modules.execute import *
from persona.cognitive_modules.converse import *
from experiment_conditions import resolve_condition

class Persona: 
  def __init__(self, name, folder_mem_saved=False, experimental_condition=None):
    # PERSONA BASE STATE 
    # <name> is the full name of the persona. This is a unique identifier for
    # the persona within Reverie. 
    self.name = name
    self.experimental_condition = resolve_condition(experimental_condition)

    # PERSONA MEMORY 
    # If there is already memory in folder_mem_saved, we load that. Otherwise,
    # we create new memory instances. 
    # <s_mem> is the persona's spatial memory. 
    f_s_mem_saved = f"{folder_mem_saved}/bootstrap_memory/spatial_memory.json"
    self.s_mem = MemoryTree(f_s_mem_saved)
    # <s_mem> is the persona's associative memory. 
    f_a_mem_saved = f"{folder_mem_saved}/bootstrap_memory/associative_memory"
    self.a_mem = AssociativeMemory(f_a_mem_saved)
    # <scratch> is the persona's scratch (short term memory) space. 
    scratch_saved = f"{folder_mem_saved}/bootstrap_memory/scratch.json"
    self.scratch = Scratch(scratch_saved)


  def uses_memory(self):
    return self.experimental_condition.use_memory


  def uses_planning(self):
    return self.experimental_condition.use_planning


  def uses_reflection(self):
    return self.experimental_condition.use_reflection


  def uses_llm_reflection(self):
    # True only for conditions whose reflection should be LLM-generated
    # (Park-style) rather than produced by the deterministic rule.
    return getattr(self.experimental_condition, "use_llm_reflection", False)


  def uses_static_reflection(self):
    # Returns (True, content_string) for P1 injection/placebo conditions,
    # (False, "") otherwise. Callers: scenarios/_record_scenario_memories().
    flag = getattr(self.experimental_condition, "use_static_reflection", False)
    content = getattr(self.experimental_condition, "static_reflection_content", "")
    return flag, content


  def save(self, save_folder):
    """
    Save persona's current state (i.e., memory). 

    INPUT: 
      save_folder: The folder where we wil be saving our persona's state. 
    OUTPUT: 
      None
    """
    # Spatial memory contains a tree in a json format. 
    # e.g., {"double studio": 
    #         {"double studio": 
    #           {"bedroom 2": 
    #             ["painting", "easel", "closet", "bed"]}}}
    f_s_mem = f"{save_folder}/spatial_memory.json"
    self.s_mem.save(f_s_mem)
    
    # Associative memory contains a csv with the following rows: 
    # [event.type, event.created, event.expiration, s, p, o]
    # e.g., event,2022-10-23 00:00:00,,Isabella Rodriguez,is,idle
    f_a_mem = f"{save_folder}/associative_memory"
    self.a_mem.save(f_a_mem)

    # Scratch contains non-permanent data associated with the persona. When 
    # it is saved, it takes a json form. When we load it, we move the values
    # to Python variables. 
    f_scratch = f"{save_folder}/scratch.json"
    self.scratch.save(f_scratch)


  def perceive(self, maze, store_to_memory=True):
    """
    This function takes the current maze, and returns events that are 
    happening around the persona. Importantly, perceive is guided by 
    two key hyper-parameter for the  persona: 1) att_bandwidth, and 
    2) retention. 

    First, <att_bandwidth> determines the number of nearby events that the 
    persona can perceive. Say there are 10 events that are within the vision
    radius for the persona -- perceiving all 10 might be too much. So, the 
    persona perceives the closest att_bandwidth number of events in case there
    are too many events. 

    Second, the persona does not want to perceive and think about the same 
    event at each time step. That's where <retention> comes in -- there is 
    temporal order to what the persona remembers. So if the persona's memory
    contains the current surrounding events that happened within the most 
    recent retention, there is no need to perceive that again. xx

    INPUT: 
      maze: Current <Maze> instance of the world. 
    OUTPUT: 
      a list of <ConceptNode> that are perceived and new. 
        See associative_memory.py -- but to get you a sense of what it 
        receives as its input: "s, p, o, desc, persona.scratch.curr_time"
    """
    return perceive(self, maze, store_to_memory=store_to_memory)


  def retrieve(self, perceived):
    """
    This function takes the events that are perceived by the persona as input
    and returns a set of related events and thoughts that the persona would 
    need to consider as context when planning. 

    INPUT: 
      perceive: a list of <ConceptNode> that are perceived and new.  
    OUTPUT: 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    """
    return retrieve(self, perceived)


  def plan(self, maze, personas, new_day, retrieved):
    """
    Main cognitive function of the chain. It takes the retrieved memory and 
    perception, as well as the maze and the first day state to conduct both 
    the long term and short term planning for the persona. 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      new_day: This can take one of the three values. 
        1) <Boolean> False -- It is not a "new day" cycle (if it is, we would
           need to call the long term planning sequence for the persona). 
        2) <String> "First day" -- It is literally the start of a simulation,
           so not only is it a new day, but also it is the first day. 
        2) <String> "New day" -- It is a new day. 
      retrieved: dictionary of dictionary. The first layer specifies an event,
                 while the latter layer specifies the "curr_event", "events", 
                 and "thoughts" that are relevant.
    OUTPUT 
      The target action address of the persona (persona.scratch.act_address).
    """
    return plan(self, maze, personas, new_day, retrieved)


  def execute(self, maze, personas, plan):
    """
    This function takes the agent's current plan and outputs a concrete 
    execution (what object to use, and what tile to travel to). 

    INPUT: 
      maze: Current <Maze> instance of the world. 
      personas: A dictionary that contains all persona names as keys, and the 
                Persona instance as values. 
      plan: The target action address of the persona  
            (persona.scratch.act_address).
    OUTPUT: 
      execution: A triple set that contains the following components: 
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g., 
        writing her next novel (editing her novel) 
        @ double studio:double studio:common room:sofa
    """
    return execute(self, maze, personas, plan)


  def reflect(self):
    """
    Reviews the persona's memory and create new thoughts based on it. 

    INPUT: 
      None
    OUTPUT: 
      None
    """
    reflect(self)


  def get_profile_summary(self):
    """
    Return the identity and background string used in agent prompts.
    """
    return self.scratch.get_str_iss()


  def get_recent_memories(self, limit=5):
    """
    Return the most recently accessed event/thought descriptions.
    """
    nodes = sorted(
      self.a_mem.seq_event + self.a_mem.seq_thought,
      key=lambda n: n.last_accessed,
      reverse=True,
    )[:limit]
    return [n.description for n in nodes if getattr(n, "description", None)]


  def get_plan_snapshot(self):
    """
    Return lightweight planning context for logging and scenario prompts.
    """
    return {
      "daily_goals": list(self.scratch.daily_req[:3]) if self.scratch.daily_req else [],
      "current_activity": self.scratch.act_description,
      "action_address": self.scratch.act_address,
      "uses_planning": self.uses_planning(),
    }


  def get_cognitive_context_for_scenario(self):
    """
    Returns a condition-appropriate cognitive context string for injection
    into scenario decision prompts.

    C1 (baseline)        \u2192 empty string; agent has no memory or plan context.
    C2 (memory)          \u2192 recent events and thoughts from associative memory.
    C3 (memory+planning) \u2192 memories plus current daily goals and activity.
    C4 (full)            \u2192 same as C3; reflective thoughts accumulated via
                           reflect() appear automatically in seq_thought and
                           are therefore included in the memory section.
    """
    sections = []

    if self.uses_memory():
      descriptions = self.get_recent_memories(limit=5)
      if descriptions:
        bullet_list = "\n".join(f"- {d}" for d in descriptions)
        sections.append(f"Recent memories:\n{bullet_list}")

    if self.uses_planning():
      snapshot = self.get_plan_snapshot()
      plan_lines = []
      if snapshot["daily_goals"]:
        goals = "; ".join(snapshot["daily_goals"])
        plan_lines.append(f"Today's goals: {goals}")
      if snapshot["current_activity"]:
        plan_lines.append(f"Current activity: {snapshot['current_activity']}")
      if plan_lines:
        sections.append("Current plans:\n" + "\n".join(plan_lines))

    return "\n\n".join(sections)


  def move(self, maze, personas, curr_tile, curr_time):
    """
    This is the main cognitive function where our main sequence is called.

    INPUT:
      maze: The Maze class of the current world.
      personas: A dictionary that contains all persona names as keys, and the
                Persona instance as values.
      curr_tile: A tuple that designates the persona's current tile location
                 in (row, col) form. e.g., (58, 39)
      curr_time: datetime instance that indicates the game's current time.
    OUTPUT:
      execution: A triple set that contains the following components:
        <next_tile> is a x,y coordinate. e.g., (58, 9)
        <pronunciatio> is an emoji.
        <description> is a string description of the movement. e.g.,
        writing her next novel (editing her novel)
        @ double studio:double studio:common room:sofa
    """
    # Updating persona's scratch memory with <curr_tile>.
    self.scratch.curr_tile = curr_tile

    # We figure out whether the persona started a new day, and if it is a new
    # day, whether it is the very first day of the simulation. This is
    # important because we set up the persona's long term plan at the start of
    # a new day.
    new_day = False
    if not self.scratch.curr_time:
      new_day = "First day"
    elif (self.scratch.curr_time.strftime('%A %B %d')
          != curr_time.strftime('%A %B %d')):
      new_day = "New day"
    self.scratch.curr_time = curr_time

    # Condition-gated cognitive sequence.
    #
    # C1 (baseline): perceive only; retrieved = {}, no planning, no reflection.
    # C2 (memory):   perceive + retrieve; no planning module, no reflection.
    # C3 (memory+planning): perceive + retrieve + plan; no reflection.
    # C4 (full):     full Park et al. sequence.
    perceived = self.perceive(maze, store_to_memory=self.uses_memory())

    if self.uses_memory():
      retrieved = self.retrieve(perceived)
    else:
      retrieved = {}

    if self.uses_planning():
      plan = self.plan(maze, personas, new_day, retrieved)
    else:
      # Agents without a planning module keep whatever action address was
      # loaded from bootstrap memory. Initialise a safe idle fallback on the
      # very first step if act_address is not yet set.
      if not self.scratch.act_address:
        area = self.scratch.living_area or "world"
        self.scratch.act_address = f"{area}:idle"
      plan = self.scratch.act_address

    if self.uses_reflection():
      self.reflect()

    # <execution> is a triple set that contains the following components:
    # <next_tile> is a x,y coordinate. e.g., (58, 9)
    # <pronunciatio> is an emoji. e.g., "\ud83d\udca4"
    # <description> is a string description of the movement. e.g.,
    #   writing her next novel (editing her novel)
    #   @ double studio:double studio:common room:sofa
    return self.execute(maze, personas, plan)


  def open_convo_session(self, convo_mode): 
    open_convo_session(self, convo_mode)
    


































