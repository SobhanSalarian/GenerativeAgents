"""
Experiment runner for headless generative-agent simulations.

This version aligns the code more closely with the MRes research plan:
- supports 5-10 agent studies through deterministic persona sub-sampling
- records reproducibility metadata and LLM usage
- exports human-evaluation packets automatically
- saves richer macro outputs including failure-traceability artifacts
- can run the post-hoc H1-H4 analysis automatically
- pre-flight validation before experiment starts (preflight.py)
- real-time logging via Python logging module (tail -f experiment_results/run_*.log)
- per-step academic agent action dataset (agent_step_log.jsonl per trial)
"""
import json
import logging
import os
import random
import re
import datetime

import numpy as np


# ---------------------------------------------------------------------------
# Logging setup — two handlers so output is always live:
#   1. StreamHandler  → console (unbuffered, always visible)
#   2. FileHandler    → experiment_results/run_<timestamp>.log
# Call _setup_logging(output_dir) once before the first trial.
# ---------------------------------------------------------------------------

logger = logging.getLogger("experiment_runner")
logger.setLevel(logging.DEBUG)
_logging_configured = False


def _setup_logging(output_dir):
    global _logging_configured
    if _logging_configured:
        return
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(output_dir, f"run_{ts}.log")

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    _logging_configured = True
    logger.info("Logging initialised — live log: %s", log_path)

from measurement.micro import (
    compute_micro_summary,
    clear_embedding_cache,
    blend_human_ratings_into_summary,
    _build_agent_deblind_map,
)
from measurement.macro import compute_macro_summary, aggregate_macro_summaries
from experiment_conditions import resolve_condition
from human_evaluation import write_human_evaluation_exports

try:
    from persona.prompt_template.gpt_structure import set_chat_seed as _set_chat_seed
    _SEED_SETTER_AVAILABLE = True
except Exception:
    _SEED_SETTER_AVAILABLE = False

    def _set_chat_seed(seed):
        pass

try:
    from persona.prompt_template.gpt_structure import (
        set_process_log as _set_process_log,
        close_process_log as _close_process_log,
    )
    _PROCESS_LOG_AVAILABLE = True
except Exception:
    _PROCESS_LOG_AVAILABLE = False

    def _set_process_log(path): pass
    def _close_process_log(): pass


def get_scenario_slug(scenario):
    if hasattr(scenario, "slug"):
        return scenario.slug

    name = scenario.__class__.__name__
    slug = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return slug


def clone_scenario(scenario):
    if hasattr(scenario, "_init_kwargs"):
        return scenario.__class__(**scenario._init_kwargs())
    return scenario.__class__()


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)


def load_available_personas(fork_sim_code):
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    meta_path = os.path.join(
        backend_dir,
        "../../environment/frontend_server/storage",
        fork_sim_code,
        "reverie",
        "meta.json",
    )
    with open(meta_path) as infile:
        meta = json.load(infile)
    return list(meta.get("persona_names", []))


def resolve_persona_selection(
    fork_sim_code,
    persona_names=None,
    persona_sample_size=None,
    selection_seed=42,
):
    available_personas = sorted(load_available_personas(fork_sim_code))

    if persona_names:
        selected = list(persona_names)
        strategy = "explicit_list"
    elif persona_sample_size:
        if persona_sample_size > len(available_personas):
            raise ValueError(
                f"Requested sample size {persona_sample_size} exceeds "
                f"{len(available_personas)} available personas."
            )
        chooser = random.Random(selection_seed)
        selected = sorted(chooser.sample(available_personas, persona_sample_size))
        strategy = "deterministic_sample"
    else:
        selected = available_personas
        strategy = "all_personas"

    return {
        "available_persona_count": len(available_personas),
        "selected_personas": selected,
        "selected_persona_count": len(selected),
        "selection_strategy": strategy,
        "selection_seed": selection_seed,
    }


def write_experiment_config(output_dir, scenario_slug, config):
    config_path = os.path.join(output_dir, scenario_slug, "experiment_config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as outfile:
        json.dump(config, outfile, indent=2)
    return config_path


def run_experiment(
    fork_sim_code,
    sim_code_prefix,
    scenario,
    experimental_condition="full",
    n_steps=100,
    n_trials=1,
    output_dir="experiment_results",
    persona_names=None,
    persona_sample_size=None,
    selection_seed=42,
    base_seed=1234,
    export_human_eval=True,
):
    """
    Run one scenario across one experimental condition for multiple trials.
    """
    condition = resolve_condition(experimental_condition)
    scenario_slug = get_scenario_slug(scenario)
    condition_output_dir = os.path.join(output_dir, scenario_slug, condition.name)
    os.makedirs(condition_output_dir, exist_ok=True)
    all_results = []

    selection = resolve_persona_selection(
        fork_sim_code,
        persona_names=persona_names,
        persona_sample_size=persona_sample_size,
        selection_seed=selection_seed,
    )

    for trial in range(n_trials):
        trial_seed = base_seed + trial
        trial_dir = os.path.join(condition_output_dir, f"trial_{trial}")
        manifest_path = os.path.join(trial_dir, "run_manifest.json")

        # Resume support: if the manifest exists the trial fully completed.
        # Load the saved result and skip re-running it.
        if os.path.exists(manifest_path):
            try:
                micro_summary = json.load(
                    open(os.path.join(trial_dir, "micro_summary.json"))
                )
                macro_summary = json.load(
                    open(os.path.join(trial_dir, "macro_summary.json"))
                )
                sim_code = f"{sim_code_prefix}_{condition.name}_trial_{trial}"
                all_results.append({
                    "trial": trial,
                    "scenario": scenario_slug,
                    "sim_code": sim_code,
                    "experimental_condition": condition.name,
                    "steps_run": macro_summary.get("total_steps", n_steps),
                    "selected_personas": selection["selected_personas"],
                    "trial_seed": trial_seed,
                    "micro_summary": micro_summary,
                    "macro_summary": macro_summary,
                })
                logger.info("=" * 60)
                logger.info("Trial %d/%d  SKIPPED (already complete) — %s",
                            trial + 1, n_trials, trial_dir)
                continue
            except Exception as _resume_err:
                logger.warning(
                    "Trial %d/%d: resume failed (%s) — re-running.",
                    trial + 1, n_trials, _resume_err,
                )

        seed_everything(trial_seed)
        _set_chat_seed(trial_seed)   # LLM-level seed for reproducibility (plan §4.7)
        clear_embedding_cache()      # free prior-trial embeddings

        trial_scenario = clone_scenario(scenario)
        sim_code = f"{sim_code_prefix}_{condition.name}_trial_{trial}"
        logger.info("=" * 60)
        logger.info("Trial %d/%d  |  sim: %s", trial + 1, n_trials, sim_code)
        logger.info("Scenario: %s", scenario_slug)
        logger.info("Condition: %s", condition.name)
        logger.info("Selected personas (%d): %s",
                    selection['selected_persona_count'],
                    selection['selected_personas'])
        logger.info("Trial seed: %d", trial_seed)
        logger.info("=" * 60)

        from reverie import ReverieServer
        rs = ReverieServer(
            fork_sim_code,
            sim_code,
            experimental_condition=condition,
            persona_names=selection["selected_personas"],
            run_seed=trial_seed,
            run_notes=(
                "MRes experiment run with deterministic persona selection and "
                "seeded local RNGs."
            ),
        )
        rs.scenario = trial_scenario
        trial_scenario.setup(rs.personas)

        logger.info("Personas loaded: %s", list(rs.personas.keys()))
        logger.info("Running %d steps ...", n_steps)

        os.makedirs(trial_dir, exist_ok=True)
        step_log_path = os.path.join(trial_dir, "agent_step_log.jsonl")
        process_log_path = os.path.join(trial_dir, "cognitive_process_log.jsonl")
        _set_process_log(process_log_path)
        completed_steps = 0

        with open(step_log_path, "w", encoding="utf-8") as _step_fh:
            # Capture pre-step memory counts to detect reflection and
            # new events during each step.
            _pre = {
                name: {
                    "events": len(p.a_mem.seq_event),
                    "thoughts": len(p.a_mem.seq_thought),
                    "importance_trigger": p.scratch.importance_trigger_curr,
                }
                for name, p in rs.personas.items()
            }

            for _ in range(n_steps):
                rs.start_server(1)
                completed_steps += 1

                # --- write one record per agent per step -------------------
                _post = {}
                for name, p in rs.personas.items():
                    _post[name] = {
                        "events": len(p.a_mem.seq_event),
                        "thoughts": len(p.a_mem.seq_thought),
                    }
                    sc = p.scratch
                    cond = rs.experimental_condition

                    # Determine scheduled task from daily plan
                    _sched_task = None
                    _sched_dur = None
                    if sc.f_daily_schedule:
                        _idx = min(
                            rs.step - 2,   # rs.step already incremented
                            len(sc.f_daily_schedule) - 1,
                        )
                        _sched_task = sc.f_daily_schedule[max(0, _idx)][0]
                        _sched_dur = sc.f_daily_schedule[max(0, _idx)][1]

                    # rs.step was incremented inside start_server(1), so
                    # rs.step - 1 is the 0-indexed step number that matches
                    # macro_log and micro_log.
                    record = {
                        "trial": trial,
                        "step": rs.step - 1,
                        "sim_time": (sc.curr_time.strftime(
                                         "%B %d, %Y, %H:%M:%S")
                                     if sc.curr_time else None),
                        "condition": condition.name,
                        "persona": name,
                        "cognitive_modules_active": {
                            "memory": cond.use_memory,
                            "planning": cond.use_planning,
                            "reflection": cond.use_reflection,
                        },
                        "perception": {
                            "new_events_stored": (
                                _post[name]["events"]
                                - _pre[name]["events"]
                            ),
                        },
                        "memory": {
                            "total_events_in_memory": _post[name]["events"],
                            "total_thoughts_in_memory": (
                                _post[name]["thoughts"]
                            ),
                            "importance_trigger_curr": (
                                sc.importance_trigger_curr
                            ),
                            "reflection_triggered": (
                                _post[name]["thoughts"]
                                > _pre[name]["thoughts"]
                            ),
                        },
                        "planning": {
                            "daily_goals": list(sc.daily_req or []),
                            "current_scheduled_task": _sched_task,
                            "current_scheduled_duration_min": _sched_dur,
                        },
                        "action": {
                            "act_address": sc.act_address,
                            "act_description": sc.act_description,
                            "act_pronunciatio": sc.act_pronunciatio,
                            "act_event": list(sc.act_event)
                                         if sc.act_event else None,
                            "act_start_time": (
                                sc.act_start_time.strftime(
                                    "%B %d, %Y, %H:%M:%S")
                                if sc.act_start_time else None
                            ),
                            "act_duration_min": sc.act_duration,
                            "chatting_with": sc.chatting_with,
                        },
                        "position": {
                            "curr_tile": list(sc.curr_tile)
                                         if sc.curr_tile else None,
                        },
                    }
                    _step_fh.write(json.dumps(record) + "\n")
                _step_fh.flush()

                # Update pre-step snapshot for the next iteration
                _pre = {
                    name: {
                        "events": _post[name]["events"],
                        "thoughts": _post[name]["thoughts"],
                        "importance_trigger": (
                            rs.personas[name].scratch.importance_trigger_curr
                        ),
                    }
                    for name in rs.personas
                }

                if trial_scenario.is_complete():
                    logger.info(
                        "  -> Scenario terminated at step %d "
                        "(terminal state reached).",
                        completed_steps,
                    )
                    break

        logger.info("Agent step log saved: %s (%d steps × %d agents = %d records)",
                    step_log_path, completed_steps,
                    len(rs.personas),
                    completed_steps * len(rs.personas))

        trial_scenario.save_results(trial_dir)
        rs.save()
        _close_process_log()

        micro_log = trial_scenario.get_micro_log()
        macro_log = trial_scenario.get_macro_log()

        # Derive critical step for LLM judge sampling anchor
        _collapse = next(
            (e["step"] for e in macro_log if e.get("collapsed")), None
        )
        _critical_step = _collapse or (
            max(macro_log, key=lambda e: e.get("oversubscription", 0.0))["step"]
            if macro_log else None
        )

        micro_summary = compute_micro_summary(
            micro_log,
            replenishment_rate=trial_scenario.replenishment_rate,
            n_agents=len(rs.personas),
            use_llm_judges=True,
            critical_step=_critical_step,
        )
        macro_summary = compute_macro_summary(
            macro_log,
            replenishment_rate=trial_scenario.replenishment_rate,
            n_agents=len(rs.personas),
            micro_log=micro_log,
            success_threshold=getattr(
                trial_scenario,
                "coordination_success_threshold",
                0.7,
            ),
            convergence_window=getattr(trial_scenario, "convergence_window", 5),
        )

        # Optional: blend human ratings if collected ratings are available
        _human_ratings_path = getattr(trial_scenario, "human_ratings_path", None)
        if _human_ratings_path:
            try:
                from rating_ingestion import load_and_analyse_ratings
                _ratings_result = load_and_analyse_ratings(_human_ratings_path)
                if "merged_ratings" in _ratings_result:
                    _deblind = _build_agent_deblind_map(trial_dir)
                    micro_summary = blend_human_ratings_into_summary(
                        micro_summary,
                        _ratings_result["merged_ratings"],
                        _deblind,
                        reliability=_ratings_result.get("reliability"),
                    )
                    logger.info(
                        "  Human ratings blended: %d persona(s); gated dims: %s",
                        len(micro_summary.get("personas_with_human_ratings", [])),
                        micro_summary.get("reliability_gated_dimensions", []),
                    )
            except Exception as _blend_err:
                logger.warning("Human-rating blend skipped: %s", _blend_err)

        with open(f"{trial_dir}/micro_summary.json", "w") as outfile:
            json.dump(micro_summary, outfile, indent=2)
        with open(f"{trial_dir}/macro_summary.json", "w") as outfile:
            json.dump(macro_summary, outfile, indent=2)
        with open(f"{trial_dir}/failure_traceability.json", "w") as outfile:
            json.dump(macro_summary["failure_traceability"], outfile, indent=2)

        run_manifest = rs.get_run_manifest()
        run_manifest.update({
            "scenario": scenario_slug,
            "trial": trial,
            "output_dir": trial_dir,
            "selection_strategy": selection["selection_strategy"],
            "selection_seed": selection["selection_seed"],
            "selected_personas": selection["selected_personas"],
            "base_seed": base_seed,
            "trial_seed": trial_seed,
            "python_random_seed_applied": True,
            "numpy_random_seed_applied": True,
        })

        human_eval_exports = None
        if export_human_eval:
            human_eval_exports = write_human_evaluation_exports(
                trial_dir,
                micro_log,
                macro_log,
                run_manifest,
                failure_traceability=macro_summary["failure_traceability"],
            )
            run_manifest["human_evaluation_exports"] = human_eval_exports

        with open(f"{trial_dir}/run_manifest.json", "w") as outfile:
            json.dump(run_manifest, outfile, indent=2)

        trial_result = {
            "trial": trial,
            "scenario": scenario_slug,
            "sim_code": sim_code,
            "experimental_condition": condition.name,
            "steps_run": completed_steps,
            "selected_personas": selection["selected_personas"],
            "trial_seed": trial_seed,
            "micro_summary": micro_summary,
            "macro_summary": macro_summary,
        }
        all_results.append(trial_result)

        logger.info("--- Trial %d summary ---", trial + 1)
        logger.info("  Steps run               : %d", completed_steps)
        logger.info("  Sustainability          : %s",
                    macro_summary['sustainability_score'])
        logger.info("  Coordination score      : %s",
                    macro_summary['coordination_score'])
        logger.info("  Coordination success    : %s",
                    macro_summary['coordination_success'])
        logger.info("  Convergence step        : %s",
                    macro_summary['convergence_step'])
        logger.info("  Demand pressure         : %s",
                    macro_summary['demand_pressure'])
        logger.info("  Average Gini            : %s",
                    macro_summary['average_gini'])
        logger.info("  Collapse at step        : %s",
                    macro_summary['collapse_step'])
        if human_eval_exports:
            logger.info("  Human-eval packets      : %d",
                        human_eval_exports['packet_count'])
        logger.info("  Results saved to        : %s/", trial_dir)

    combined_path = os.path.join(condition_output_dir, "all_results.json")
    with open(combined_path, "w") as outfile:
        json.dump(all_results, outfile, indent=2)

    condition_summary = aggregate_macro_summaries(
        [result["macro_summary"] for result in all_results]
    )
    condition_summary["scenario"] = scenario_slug
    condition_summary["experimental_condition"] = condition.name
    condition_summary["selected_personas"] = selection["selected_personas"]
    condition_summary_path = os.path.join(
        condition_output_dir,
        "condition_summary.json",
    )
    with open(condition_summary_path, "w") as outfile:
        json.dump(condition_summary, outfile, indent=2)

    logger.info("All %d trial(s) complete. Combined results -> %s",
                n_trials, combined_path)
    logger.info("Condition summary         -> %s", condition_summary_path)
    return {
        "results": all_results,
        "selection": selection,
        "condition_summary_path": condition_summary_path,
    }


def run_experiment_matrix(
    fork_sim_code,
    sim_code_prefix,
    scenario,
    experimental_conditions=None,
    n_steps=100,
    n_trials=1,
    output_dir="experiment_results",
    persona_names=None,
    persona_sample_size=None,
    selection_seed=42,
    base_seed=1234,
    export_human_eval=True,
    run_hypothesis_analysis=True,
):
    experimental_conditions = experimental_conditions or ["full"]
    scenario_slug = get_scenario_slug(scenario)
    matrix_results = {}

    # Set up real-time logging to file + console before anything else
    _setup_logging(output_dir)

    # Resolve the persona list that preflight will validate against
    _preflight_personas = list(persona_names) if persona_names else None
    if _preflight_personas is None:
        _preflight_personas = resolve_persona_selection(
            fork_sim_code,
            persona_sample_size=persona_sample_size,
            selection_seed=selection_seed,
        )["selected_personas"]

    from preflight import run_preflight
    run_preflight(fork_sim_code, _preflight_personas, output_dir)

    config = {
        "fork_sim_code": fork_sim_code,
        "sim_code_prefix": sim_code_prefix,
        "scenario": scenario_slug,
        "scenario_parameters": getattr(scenario, "_init_kwargs", lambda: {})(),
        "experimental_conditions": experimental_conditions,
        "n_steps": n_steps,
        "n_trials": n_trials,
        "persona_names": persona_names,
        "persona_sample_size": persona_sample_size,
        "selection_seed": selection_seed,
        "base_seed": base_seed,
        "export_human_eval": export_human_eval,
    }
    config_path = write_experiment_config(output_dir, scenario_slug, config)

    for condition_name in experimental_conditions:
        condition = resolve_condition(condition_name)
        matrix_results[condition.name] = run_experiment(
            fork_sim_code=fork_sim_code,
            sim_code_prefix=sim_code_prefix,
            scenario=scenario,
            experimental_condition=condition,
            n_steps=n_steps,
            n_trials=n_trials,
            output_dir=output_dir,
            persona_names=persona_names,
            persona_sample_size=persona_sample_size,
            selection_seed=selection_seed,
            base_seed=base_seed,
            export_human_eval=export_human_eval,
        )

    matrix_path = os.path.join(output_dir, scenario_slug, "matrix_results.json")
    os.makedirs(os.path.dirname(matrix_path), exist_ok=True)
    with open(matrix_path, "w") as outfile:
        json.dump(matrix_results, outfile, indent=2)

    analysis_paths = None
    if run_hypothesis_analysis:
        from experiment_analysis import run_analysis
        analysis_results = run_analysis(output_dir, scenario_slug)
        if analysis_results:
            analysis_paths = {
                "json": os.path.join(
                    output_dir,
                    scenario_slug,
                    "analysis",
                    "hypothesis_report.json",
                ),
                "text": os.path.join(
                    output_dir,
                    scenario_slug,
                    "analysis",
                    "hypothesis_report.txt",
                ),
            }

    logger.info("Condition matrix complete. Combined results -> %s", matrix_path)
    logger.info("Experiment config saved    -> %s", config_path)
    if analysis_paths:
        logger.info("Hypothesis analysis        -> %s", analysis_paths['json'])
    return matrix_results


if __name__ == "__main__":
    from scenarios.information_consensus import InformationConsensus

    scenario = InformationConsensus()

    run_experiment_matrix(
        fork_sim_code="base_the_ville_n25",
        sim_code_prefix="ic_experiment_llm_reflection",
        scenario=scenario,
        experimental_conditions=[
            "full_llm_reflection",
        ],
        n_steps=30,
        n_trials=10,
        output_dir="experiment_results_ic_llm_reflection",
        persona_sample_size=8,
        selection_seed=42,
        base_seed=20260524,
        export_human_eval=True,
        run_hypothesis_analysis=False,
    )
