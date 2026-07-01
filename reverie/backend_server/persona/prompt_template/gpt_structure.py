"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import openai
import time
import os
from pathlib import Path

from utils import *
from llm_usage import (
  record_chat_completion,
  record_embedding_response,
  record_request_error,
)

client = openai.OpenAI(api_key=openai_api_key)

DEFAULT_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
DEFAULT_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_DEFAULT_CHAT_TEMPERATURE = os.getenv("OPENAI_CHAT_TEMPERATURE")
DEFAULT_CHAT_TEMPERATURE = (
  float(_DEFAULT_CHAT_TEMPERATURE)
  if _DEFAULT_CHAT_TEMPERATURE not in (None, "")
  else None
)
_DEFAULT_CHAT_SEED = os.getenv("OPENAI_CHAT_SEED")
DEFAULT_CHAT_SEED = (
  int(_DEFAULT_CHAT_SEED)
  if _DEFAULT_CHAT_SEED not in (None, "")
  else None
)

def set_chat_seed(seed: int | None):
  """
  Update the seed used for all subsequent chat completion calls in this
  process.  Call before each trial in experiment_runner to improve
  LLM-level reproducibility (research plan §4.7).
  """
  global DEFAULT_CHAT_SEED
  DEFAULT_CHAT_SEED = int(seed) if seed is not None else None


def temp_sleep(seconds=0.1):
  time.sleep(seconds)


def _chat_completion_create(**kwargs):
  """
  Central wrapper so every chat completion records token usage and can opt
  into more reproducible settings via environment variables.
  """
  if DEFAULT_CHAT_SEED is not None and "seed" not in kwargs:
    kwargs["seed"] = DEFAULT_CHAT_SEED

  if DEFAULT_CHAT_TEMPERATURE is not None and "temperature" not in kwargs:
    kwargs["temperature"] = DEFAULT_CHAT_TEMPERATURE

  try:
    completion = client.chat.completions.create(**kwargs)
  except Exception as error:
    if "seed" in kwargs:
      seedless_kwargs = dict(kwargs)
      seedless_kwargs.pop("seed", None)
      try:
        completion = client.chat.completions.create(**seedless_kwargs)
      except Exception as inner_error:
        record_request_error("chat", kwargs.get("model"), inner_error)
        raise
    else:
      record_request_error("chat", kwargs.get("model"), error)
      raise

  record_chat_completion(completion, kwargs.get("model"))
  return completion

def ChatGPT_single_request(prompt):
  temp_sleep()

  completion = _chat_completion_create(
    model=DEFAULT_CHAT_MODEL,
    messages=[{"role": "user", "content": prompt}]
  )
  return completion.choices[0].message.content


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  temp_sleep()

  try:
    completion = _chat_completion_create(
      model=DEFAULT_CHAT_MODEL,
      messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

  except:
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


_INTER_CALL_DELAY = float(os.getenv("OPENAI_INTER_CALL_DELAY", "0.8"))
_MAX_RATE_LIMIT_RETRIES = 6

# ---------------------------------------------------------------------------
# Cognitive process log — captures every internal LLM call per trial
# ---------------------------------------------------------------------------
_PROCESS_LOG_FH = None


def _infer_call_type(prompt: str) -> str:
  p = prompt[:300].lower()
  if "on the scale of 1 to 10" in p and "conversation" in p:
    return "conversation_poignancy"
  if "on the scale of 1 to 10" in p:
    return "event_poignancy"
  if "convert an action description to an emoji" in p:
    return "emoji_conversion"
  if "state of an object" in p:
    return "object_state"
  if "subtasks" in p or "5 min increments" in p or "5-minute" in p:
    return "task_decomp"
  if "hourly schedule" in p or "daily schedule" in p:
    return "daily_planning"
  if "respond with a json object" in p and "amount" in p:
    return "commons_decision"
  if "sector" in p and "area" in p:
    return "action_sector"
  if "address" in p and "arena" in p:
    return "action_arena"
  if "conversation" in p or "currently chatting" in p:
    return "conversation_generation"
  if "triple" in p or "event triple" in p:
    return "event_triple"
  return "other"


def set_process_log(path: str):
  """Open the cognitive process log file for the current trial."""
  global _PROCESS_LOG_FH
  _PROCESS_LOG_FH = open(path, "w", encoding="utf-8")


def close_process_log():
  """Flush and close the cognitive process log file."""
  global _PROCESS_LOG_FH
  if _PROCESS_LOG_FH:
    _PROCESS_LOG_FH.flush()
    _PROCESS_LOG_FH.close()
    _PROCESS_LOG_FH = None


def _write_process_log(prompt: str, response: str):
  if _PROCESS_LOG_FH is None:
    return
  entry = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "call_type": _infer_call_type(prompt),
    "prompt": prompt,
    "response": response,
  }
  _PROCESS_LOG_FH.write(json.dumps(entry) + "\n")
  _PROCESS_LOG_FH.flush()


def ChatGPT_request(prompt):
  """
  Given a prompt, make a chat-completion request and return the response text.

  Includes a proactive inter-call delay and exponential back-off on
  RateLimitError so long-running experiments stay under OpenAI TPM/RPM limits
  without the SDK's internal retries stalling for minutes at a time.
  """
  time.sleep(_INTER_CALL_DELAY)

  for attempt in range(_MAX_RATE_LIMIT_RETRIES):
    try:
      completion = _chat_completion_create(
        model=DEFAULT_CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}]
      )
      response = completion.choices[0].message.content
      _write_process_log(prompt, response)
      return response

    except openai.RateLimitError:
      wait = (2 ** attempt) + random.uniform(0, 1)
      print(f"RateLimitError — waiting {wait:.1f}s (attempt {attempt + 1}/{_MAX_RATE_LIMIT_RETRIES})")
      time.sleep(wait)

    except Exception:
      print("ChatGPT ERROR")
      return "ChatGPT ERROR"

  print("ChatGPT ERROR — rate limit retries exhausted")
  return "ChatGPT ERROR"


def GPT4_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = GPT4_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response_OLD(prompt, 
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass
  print ("FAIL SAFE TRIGGERED") 
  return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt, gpt_parameter): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  temp_sleep()
  try:
    # Route legacy completion-style calls through Chat Completions to avoid
    # deprecated completion models (e.g., text-davinci-002).
    response = _chat_completion_create(
      model=DEFAULT_CHAT_MODEL,
      messages=[{"role": "user", "content": prompt}],
      temperature=gpt_parameter.get("temperature", 0.7),
      max_tokens=gpt_parameter.get("max_tokens", 128),
      top_p=gpt_parameter.get("top_p", 1),
      frequency_penalty=gpt_parameter.get("frequency_penalty", 0),
      presence_penalty=gpt_parameter.get("presence_penalty", 0),
      stop=gpt_parameter.get("stop"),
    )
    return response.choices[0].message.content
  except Exception as e: 
    print (f"GPT REQUEST ERROR: {e}")
    return ""


def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  prompt_path = Path(prompt_lib_file)
  if not prompt_path.is_absolute():
    # Resolve prompt templates relative to backend_server so callers can run
    # reverie.py from any working directory.
    backend_server_dir = Path(__file__).resolve().parents[2]
    prompt_path = backend_server_dir / prompt_path

  f = open(prompt_path, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print (prompt)

  for i in range(repeat): 
    curr_gpt_response = GPT_request(prompt, gpt_parameter)
    if not curr_gpt_response:
      continue
    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  return fail_safe_response


def get_embedding(text, model=None):
  text = text.replace("\n", " ")
  if not text: 
    text = "this is blank"
  model = model or DEFAULT_EMBED_MODEL
  try:
    response = client.embeddings.create(input=[text], model=model)
    record_embedding_response(response, model)
    return response.data[0].embedding
  except Exception as error:
    record_request_error("embedding", model, error)
    raise


if __name__ == '__main__':
  gpt_parameter = {"engine": "text-davinci-003", "max_tokens": 50, 
                   "temperature": 0, "top_p": 1, "stream": False,
                   "frequency_penalty": 0, "presence_penalty": 0, 
                   "stop": ['"']}
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response): 
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(gpt_response):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)
















