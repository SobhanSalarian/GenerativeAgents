"""
preflight.py — Pre-experiment validation suite.

Run before any experiment matrix to catch environment problems, broken
cognitive modules, and API connectivity issues before they waste compute or
API budget mid-run.

Can be run standalone:
    python preflight.py

Or called from experiment_runner:
    from preflight import run_preflight
    run_preflight(fork_sim_code, persona_names, output_dir)

Raises PreflightError with a descriptive message on first failure.
"""
import json
import os
import shutil
import sys
import tempfile
import datetime

# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class PreflightError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_WIDTH = 50  # label column width for aligned output


def _report(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    padding = "." * (_WIDTH - len(label))
    suffix = f"  ({detail})" if detail else ""
    print(f"[PREFLIGHT] {label} {padding} {status}{suffix}", flush=True)


def _fail(label, reason):
    _report(label, False, reason)
    raise PreflightError(f"{label}: {reason}")


# ---------------------------------------------------------------------------
# Check 1 — Environment (no LLM)
# ---------------------------------------------------------------------------

def _check_environment(fork_sim_code, persona_names):
    label = "Environment checks"
    from utils import fs_storage

    base = os.path.join(fs_storage, fork_sim_code)
    if not os.path.isdir(base):
        _fail(label, f"base simulation folder not found: {base}")

    meta_path = os.path.join(base, "reverie", "meta.json")
    if not os.path.isfile(meta_path):
        _fail(label, f"meta.json missing at {meta_path}")
    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except Exception as exc:
        _fail(label, f"meta.json is invalid JSON: {exc}")
    if "persona_names" not in meta:
        _fail(label, "meta.json has no 'persona_names' key")

    if not os.getenv("OPENAI_API_KEY"):
        _fail(label, "OPENAI_API_KEY environment variable is not set")

    for name in persona_names:
        persona_dir = os.path.join(base, "personas", name, "bootstrap_memory")
        if not os.path.isdir(persona_dir):
            _fail(label, f"bootstrap_memory folder missing for persona: {name}")
        for fname in ("scratch.json", "associative_memory/nodes.json",
                      "associative_memory/kw_strength.json"):
            fpath = os.path.join(persona_dir, fname)
            if not os.path.isfile(fpath):
                _fail(label, f"missing file: {fpath}")
            try:
                with open(fpath) as f:
                    data = json.load(f)
            except Exception as exc:
                _fail(label, f"invalid JSON in {fpath}: {exc}")
        # scratch identity fields
        scratch_path = os.path.join(persona_dir, "scratch.json")
        with open(scratch_path) as f:
            scratch = json.load(f)
        for field in ("name", "innate", "learned", "currently",
                      "lifestyle", "living_area"):
            if not scratch.get(field):
                _fail(label, f"scratch.json for {name} missing field: {field}")

    _report(label, True, f"{len(persona_names)} persona(s) validated")


# ---------------------------------------------------------------------------
# Check 2 — LLM connectivity (1 cheap API call)
# ---------------------------------------------------------------------------

def _check_llm_connectivity():
    label = "LLM connectivity"
    try:
        from persona.prompt_template.gpt_structure import (
            ChatGPT_request,
            DEFAULT_CHAT_MODEL,
        )
    except Exception as exc:
        _fail(label, f"cannot import gpt_structure: {exc}")

    try:
        response = ChatGPT_request("Reply with the single word: ready")
    except Exception as exc:
        _fail(label, f"API call failed: {exc}")

    if not response or not isinstance(response, str):
        _fail(label, "API returned empty or non-string response")

    _report(label, True, f"model={DEFAULT_CHAT_MODEL}")


# ---------------------------------------------------------------------------
# Check 3 — Cognitive module smoke tests (1 temp ReverieServer, 1 step)
# ---------------------------------------------------------------------------

def _check_cognitive_modules(fork_sim_code, test_persona="Abigail Chen"):
    """
    Spins up a one-persona ReverieServer in a temp sim folder, runs 1 step,
    then directly calls reflect() to verify the full cognitive pipeline.
    Cleans up the temp folder on success or failure.
    """
    tmp_sim_code = f"preflight_smoke_{os.getpid()}"

    try:
        from reverie import ReverieServer
        from experiment_conditions import resolve_condition

        rs = ReverieServer(
            fork_sim_code,
            tmp_sim_code,
            experimental_condition=resolve_condition("full"),
            persona_names=[test_persona],
        )
        rs.scenario = None

        # ---- Memory check -------------------------------------------------
        label_mem = "Memory module"
        persona = rs.personas[test_persona]
        events_before = len(persona.a_mem.seq_event)
        rs.start_server(1)
        events_after = len(persona.a_mem.seq_event)
        if events_after <= events_before:
            _fail(label_mem, "perceive() did not store any new events in memory")
        _report(label_mem, True,
                f"{events_after - events_before} new event(s) stored")

        # ---- Planning check -----------------------------------------------
        label_plan = "Planning module"
        if not persona.scratch.act_address:
            _fail(label_plan, "act_address is None after first step")
        _report(label_plan, True, f"act_address={persona.scratch.act_address!r}")

        # ---- Scratch save/load round-trip ---------------------------------
        label_save = "Scratch save/load roundtrip"
        with tempfile.TemporaryDirectory() as td:
            scratch_out = os.path.join(td, "scratch.json")
            try:
                persona.scratch.save(scratch_out)
            except AttributeError as exc:
                _fail(label_save, f"scratch.save() crashed: {exc}")
            if not os.path.isfile(scratch_out):
                _fail(label_save, "scratch.json was not written")
        _report(label_save, True)

        # ---- Reflection check (force trigger) ----------------------------
        label_ref = "Reflection module"
        thoughts_before = len(persona.a_mem.seq_thought)
        persona.scratch.importance_trigger_curr = 0   # force trigger
        try:
            persona.reflect()
        except Exception as exc:
            _fail(label_ref, f"reflect() raised: {exc}")
        thoughts_after = len(persona.a_mem.seq_thought)
        if thoughts_after <= thoughts_before:
            _fail(label_ref,
                  "reflect() did not add any thoughts (check bootstrap memory)")
        _report(label_ref, True,
                f"{thoughts_after - thoughts_before} thought(s) generated")

    finally:
        # Always clean up the temp sim folder
        from utils import fs_storage
        tmp_folder = os.path.join(fs_storage, tmp_sim_code)
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)


# ---------------------------------------------------------------------------
# Check 4 — Scenario unit tests (no LLM)
# ---------------------------------------------------------------------------

def _check_scenario(test_personas):
    label = "Scenario unit tests"
    try:
        from scenarios.commons_dilemma import CommonsDilemma
    except Exception as exc:
        _fail(label, f"cannot import CommonsDilemma: {exc}")

    sc = CommonsDilemma(initial_resource=100, replenishment_rate=10,
                        max_request=20, capacity=100)

    # Minimal stub persona — covers all methods that CommonsDilemma calls
    class _Scratch:
        name = "Test Agent"
        innate = "helpful"
        learned = "researcher"
        currently = "sitting"
        lifestyle = "normal"
        living_area = "room"
        daily_req = ["work"]
        f_daily_schedule = [["working", 60]]
        act_description = "sitting"
        act_address = "room:idle"
        chatting_with = None

    class _AMem:
        seq_event = []
        seq_thought = []

    class _Stub:
        def __init__(self, name):
            self.name = name
            self.scratch = _Scratch()
            self.a_mem = _AMem()

        def uses_memory(self): return True
        def uses_planning(self): return True
        def uses_reflection(self): return True
        def get_cognitive_context_for_scenario(self): return ""
        def get_plan_snapshot(self):
            return {
                "daily_goals": self.scratch.daily_req,
                "current_activity": self.scratch.act_description,
                "action_address": self.scratch.act_address,
                "uses_planning": True,
            }
        def get_recent_memories(self, limit=5):
            return []
        def get_profile_summary(self):
            return f"{self.name}: {self.scratch.innate}"

    stub_personas = {name: _Stub(name) for name in test_personas[:2]}
    sc.setup(stub_personas)

    ctx = sc._resource_context()
    if not ctx or not isinstance(ctx, str):
        _fail(label, "_resource_context() returned empty or non-string")

    for name, persona in stub_personas.items():
        log_ctx = sc._build_logging_context(persona)
        for key in ("persona_profile", "recent_memories",
                    "condition_capabilities", "daily_goals"):
            if key not in log_ctx:
                _fail(label, f"_build_logging_context() missing key: {key}")

    # Gini correctness
    assert sc._gini([]) == 0.0, "gini([]) should be 0"
    vals = sc._gini([1, 1, 1])
    if abs(vals) > 1e-9:
        _fail(label, f"gini([1,1,1]) should be 0, got {vals}")
    vals = sc._gini([0, 0, 100])
    if vals < 0.5:
        _fail(label, f"gini([0,0,100]) should be > 0.5, got {vals}")

    _report(label, True)


# ---------------------------------------------------------------------------
# Check 5 — Measurement unit tests (no LLM)
# ---------------------------------------------------------------------------

def _check_measurement(test_personas):
    label = "Measurement unit tests"
    try:
        from measurement.micro import compute_micro_summary
        from measurement.macro import compute_macro_summary
    except Exception as exc:
        _fail(label, f"cannot import measurement modules: {exc}")

    agents = list(test_personas[:3])
    now = datetime.datetime(2022, 10, 31, 8, 0, 0)

    # Synthetic micro_log: 3 agents × 5 steps
    micro_log = []
    for step in range(5):
        t = now + datetime.timedelta(minutes=step * 10)
        for name in agents:
            micro_log.append({
                "persona": name,
                "step": step,
                "time": t.strftime("%B %d, %Y, %H:%M:%S"),
                "requested": 8.0,
                "granted": 8.0,
                "parse_error": False,
                "reasoning": "I will request a fair share of the resource.",
                "memory_reference": "I remember we agreed to share equally.",
                "plan_reference": "My plan is to cooperate.",
                "persona_profile": "A cooperative person",
                "current_activity": "sitting and thinking",
                "daily_goals": ["cooperate", "be fair"],
                "recent_memories": ["We agreed to share"],
                "resource_level_before": 100.0,
                "pool_percent_before": 1.0,
                "fair_share": 10.0,
                "memory_context_available": True,
                "planning_context_available": True,
                "experimental_condition": "full",
                "condition_capabilities": {
                    "use_memory": True,
                    "use_planning": True,
                    "use_reflection": True,
                },
            })

    try:
        micro_summary = compute_micro_summary(
            micro_log,
            replenishment_rate=30,
            n_agents=3,
            use_llm_judges=False,
        )
    except Exception as exc:
        _fail(label, f"compute_micro_summary raised: {exc}")

    for key in ("composite_believability", "behavioural_consistency",
                "memory_coherence", "planning_plausibility",
                "response_naturalness"):
        if key not in micro_summary:
            _fail(label, f"micro_summary missing key: {key}")
        for name, score in micro_summary[key].items():
            if not (0.0 <= score <= 1.0):
                _fail(label, f"{key}[{name}]={score} is outside [0, 1]")

    # Synthetic macro_log: 5 steps
    macro_log = []
    for step in range(5):
        macro_log.append({
            "step": step,
            "time": (now + datetime.timedelta(minutes=step * 10))
                    .strftime("%B %d, %Y, %H:%M:%S"),
            "resource_level_before": 100.0 - step * 2,
            "resource_level": 98.0 - step * 2,
            "total_requested": 24.0,
            "total_granted": 24.0,
            "fair_share": 10.0,
            "oversubscription": 0.8,
            "coordinated": True,
            "sustainability_score": 0.98 - step * 0.02,
            "gini": 0.0,
            "collapsed": False,
        })

    try:
        macro_summary = compute_macro_summary(
            macro_log,
            replenishment_rate=30,
            n_agents=3,
            micro_log=micro_log,
        )
    except Exception as exc:
        _fail(label, f"compute_macro_summary raised: {exc}")

    for key in ("coordination_score", "sustainability_score"):
        val = macro_summary.get(key)
        if val is None or not (0.0 <= val <= 1.0):
            _fail(label, f"macro_summary[{key}]={val} is outside [0, 1]")

    _report(label, True)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_preflight(fork_sim_code, persona_names, output_dir="experiment_results"):
    """
    Run all pre-flight checks. Raises PreflightError on first failure.
    Prints a PASS/FAIL line for each check.
    """
    print("\n" + "=" * 60, flush=True)
    print("PREFLIGHT CHECKS", flush=True)
    print("=" * 60, flush=True)

    _check_environment(fork_sim_code, persona_names)
    _check_llm_connectivity()
    _check_cognitive_modules(fork_sim_code, test_persona=persona_names[0])
    _check_scenario(persona_names)
    _check_measurement(persona_names)

    print("=" * 60, flush=True)
    print("All preflight checks passed. Proceeding to experiment.", flush=True)
    print("=" * 60 + "\n", flush=True)


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run pre-flight checks")
    parser.add_argument(
        "--fork-sim-code",
        default="base_the_ville_n25",
        help="Base simulation to validate against",
    )
    parser.add_argument(
        "--personas",
        nargs="+",
        default=[
            "Abigail Chen", "Ayesha Khan", "Carlos Gomez",
            "Francisco Lopez", "Giorgio Rossi", "Sam Moore",
            "Wolfgang Schulz", "Yuriko Yamamoto",
        ],
        help="Persona names to validate",
    )
    args = parser.parse_args()

    try:
        run_preflight(args.fork_sim_code, args.personas)
        sys.exit(0)
    except PreflightError as exc:
        print(f"\n[PREFLIGHT] FAILED: {exc}", flush=True)
        sys.exit(1)
