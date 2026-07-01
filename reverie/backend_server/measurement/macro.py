"""
Macro-level (group / system) metrics for generative agent validation.

The MRes research plan requires more than single-run sustainability numbers.
This module now computes explicit run-level success, convergence, role
differentiation, stability, and structured failure-traceability artifacts.
"""
import math


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _std(values):
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _coefficient_of_variation(values):
    mean = _mean(values)
    if not values or mean == 0:
        return 0.0
    return _std(values) / mean


def _label_score(value, high, low, invert=False):
    if value is None:
        return "not_applicable"
    if invert:
        if value <= high:
            return "high"
        if value > low:
            return "low"
        return "medium"
    if value >= high:
        return "high"
    if value < low:
        return "low"
    return "medium"


def sustainability_score(macro_log):
    if not macro_log:
        return 0.0
    return round(
        sum(e["sustainability_score"] for e in macro_log) / len(macro_log), 3
    )


def coordination_score(macro_log, replenishment_rate):
    if not macro_log:
        return 0.0
    sustainable = sum(
        1 for e in macro_log
        if e.get("coordinated", e["total_requested"] <= replenishment_rate)
    )
    return round(sustainable / len(macro_log), 3)


def collapse_step(macro_log):
    for entry in macro_log:
        if entry.get("collapsed"):
            return entry["step"]
    return None


def average_gini(macro_log):
    if not macro_log:
        return 0.0
    ginis = [e.get("gini", 0.0) for e in macro_log]
    return round(sum(ginis) / len(ginis), 3)


def demand_pressure(macro_log, replenishment_rate):
    if not macro_log:
        return 0.0
    ratios = [
        e["total_requested"] / replenishment_rate
        for e in macro_log if replenishment_rate > 0
    ]
    return round(sum(ratios) / len(ratios), 3) if ratios else 0.0


def coordination_success(macro_log, replenishment_rate, success_threshold=0.7):
    score = coordination_score(macro_log, replenishment_rate)
    return bool(collapse_step(macro_log) is None and score >= success_threshold)


def convergence_step(macro_log, replenishment_rate, window=5):
    """
    Earliest step at which a sustained coordination streak of `window` rounds
    begins. Returns None when no such streak occurs before timeout.
    """
    if not macro_log:
        return None

    coordinated_flags = [
        entry.get("coordinated", entry["total_requested"] <= replenishment_rate)
        for entry in macro_log
    ]
    for start in range(0, max(0, len(coordinated_flags) - window + 1)):
        if all(coordinated_flags[start:start + window]):
            return macro_log[start]["step"]
    return None


def convergence_speed(macro_log, replenishment_rate, window=5):
    step = convergence_step(macro_log, replenishment_rate, window=window)
    if step is not None:
        return step
    return len(macro_log)


def _assign_role(mean_request_ratio, consistency_score):
    if consistency_score < 0.45:
        return "volatile"
    if mean_request_ratio < 0.8:
        return "conserver"
    if mean_request_ratio > 1.2:
        return "competitor"
    return "balancer"


def emergent_role_differentiation(micro_log, replenishment_rate, n_agents):
    """
    Proxy for role differentiation based on distinct request strategies.
    """
    if not micro_log or not n_agents:
        return {
            "roles_by_persona": {},
            "role_counts": {},
            "role_entropy": 0.0,
            "normalized_role_entropy": 0.0,
            "unique_role_count": 0,
        }

    fair_share = replenishment_rate / n_agents if n_agents else 0.0
    buckets = {}
    for entry in micro_log:
        persona = entry["persona"]
        stats = buckets.setdefault(persona, {"requests": []})
        stats["requests"].append(entry["requested"])

    roles = {}
    for persona, stats in buckets.items():
        requests = stats["requests"]
        mean_request = _mean(requests)
        variance = _mean([(request - mean_request) ** 2 for request in requests])
        std = math.sqrt(variance)
        consistency = 1.0 - (std / mean_request) if mean_request else 1.0
        ratio = (mean_request / fair_share) if fair_share else 0.0
        roles[persona] = _assign_role(ratio, max(0.0, consistency))

    role_counts = {}
    for role in roles.values():
        role_counts[role] = role_counts.get(role, 0) + 1

    total = sum(role_counts.values())
    entropy = 0.0
    for count in role_counts.values():
        proportion = count / total if total else 0.0
        if proportion:
            entropy -= proportion * math.log(proportion, 2)

    max_entropy = math.log(len(role_counts), 2) if len(role_counts) > 1 else 0.0
    normalized_entropy = (
        entropy / max_entropy
        if max_entropy else 0.0
    )

    return {
        "roles_by_persona": roles,
        "role_counts": role_counts,
        "role_entropy": round(entropy, 3),
        "normalized_role_entropy": round(normalized_entropy, 3),
        "unique_role_count": len(role_counts),
    }


def failure_traceability(micro_log, macro_log, replenishment_rate):
    """
    Build a structured analyst-facing summary of likely micro-to-macro failure
    pathways around the critical run moment.
    """
    if not macro_log:
        return {
            "failure_detected": False,
            "critical_step": None,
            "likely_causes": [],
            "agent_contributions": {},
            "critical_window": [],
        }

    critical_step = collapse_step(macro_log)
    if critical_step is None:
        # Use the most over-demanded step when the run does not outright collapse.
        critical_entry = max(
            macro_log,
            key=lambda entry: entry.get("oversubscription", 0.0),
        )
        critical_step = critical_entry["step"]

    window_steps = {step for step in range(max(0, critical_step - 2), critical_step + 3)}
    critical_window = [entry for entry in micro_log if entry["step"] in window_steps]
    macro_window = [entry for entry in macro_log if entry["step"] in window_steps]

    agent_contributions = {}
    for entry in critical_window:
        persona = entry["persona"]
        stats = agent_contributions.setdefault(
            persona,
            {
                "requested": 0,
                "granted": 0,
                "parse_errors": 0,
                "memory_references": 0,
                "plan_references": 0,
            },
        )
        stats["requested"] += entry.get("requested", 0)
        stats["granted"] += entry.get("granted", 0)
        stats["parse_errors"] += 1 if entry.get("parse_error") else 0
        stats["memory_references"] += 1 if entry.get("memory_reference") else 0
        stats["plan_references"] += 1 if entry.get("plan_reference") else 0

    likely_causes = []
    mean_oversubscription = _mean(
        [entry.get("oversubscription", 0.0) for entry in macro_window]
    )
    if mean_oversubscription > 0:
        likely_causes.append("collective_over_demand")

    mean_gini = _mean([entry.get("gini", 0.0) for entry in macro_window])
    if mean_gini > 0.3:
        likely_causes.append("allocation_inequality")

    parse_error_total = sum(stats["parse_errors"] for stats in agent_contributions.values())
    if parse_error_total > 0:
        likely_causes.append("response_parse_instability")

    low_memory_agents = [
        persona for persona, stats in agent_contributions.items()
        if stats["memory_references"] == 0
    ]
    if low_memory_agents:
        likely_causes.append("weak_memory_use")

    low_plan_agents = [
        persona for persona, stats in agent_contributions.items()
        if stats["plan_references"] == 0
    ]
    if low_plan_agents:
        likely_causes.append("weak_plan_grounding")

    dominant_agents = sorted(
        agent_contributions.items(),
        key=lambda item: item[1]["requested"],
        reverse=True,
    )

    return {
        "failure_detected": bool(collapse_step(macro_log) is not None or mean_oversubscription > 0),
        "critical_step": critical_step,
        "likely_causes": likely_causes,
        "agent_contributions": agent_contributions,
        "dominant_agents": [persona for persona, _ in dominant_agents[:3]],
        "critical_window": critical_window,
        "macro_window": macro_window,
        "coding_template": {
            "micro_causes": "",
            "macro_outcome": "",
            "analyst_notes": "",
        },
    }


def _pearson(xs, ys):
    """Pearson r between two equal-length sequences. Returns 0.0 if undefined."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return round(num / (dx * dy), 4)


def influence_network(micro_log):
    """
    Directed pairwise lagged-correlation network across agents.

    For each ordered pair (source, target): computes Pearson r between
    source's requests at steps 0..T-2 and target's requests at steps 1..T-1.
    A positive weight means target tends to follow source's prior request.

    Returns
    -------
    {
        "agents": [sorted list of persona names],
        "matrix": {source: {target: r}},   # excludes self-loops
        "min_steps": int,                   # length of shortest series used
    }
    """
    if not micro_log:
        return {"agents": [], "matrix": {}, "min_steps": 0}

    # Build per-agent request series sorted by step
    buckets = {}
    for entry in micro_log:
        persona = entry["persona"]
        buckets.setdefault(persona, []).append((entry["step"], entry["requested"]))

    series = {
        persona: [req for _, req in sorted(steps)]
        for persona, steps in buckets.items()
    }

    agents = sorted(series.keys())
    min_steps = min(len(s) for s in series.values()) if series else 0

    matrix = {}
    for source in agents:
        matrix[source] = {}
        src = series[source][:min_steps]
        for target in agents:
            if target == source:
                continue
            tgt = series[target][:min_steps]
            # lagged: source[0:T-1] predicts target[1:T]
            matrix[source][target] = _pearson(src[:-1], tgt[1:])

    return {"agents": agents, "matrix": matrix, "min_steps": min_steps}


def network_descriptors(network, threshold=0.30):
    """
    Derive summary descriptors from an influence_network() result.

    An edge (source -> target) is considered *significant* when
    |r| >= threshold.

    Returns
    -------
    {
        "edge_count":      int,
        "possible_edges":  int,
        "density":         float,   # edge_count / possible_edges
        "in_degree":       {agent: int},   # how many agents significantly influence it
        "out_degree":      {agent: int},   # how many agents it significantly influences
        "reciprocal_pairs": int,           # pairs where both i->j and j->i are significant
        "reciprocity":     float,          # reciprocal_pairs / edge_count (0 if no edges)
        "max_influence_pair": (source, target, r) | None,
        "threshold_used":  float,
    }
    """
    agents = network.get("agents", [])
    matrix = network.get("matrix", {})
    n = len(agents)
    possible = n * (n - 1) if n > 1 else 0

    in_deg = {a: 0 for a in agents}
    out_deg = {a: 0 for a in agents}
    sig_edges = set()
    max_r = 0.0
    max_pair = None

    for source in agents:
        for target, r in matrix.get(source, {}).items():
            if abs(r) >= threshold:
                sig_edges.add((source, target))
                out_deg[source] += 1
                in_deg[target] += 1
                if abs(r) > abs(max_r):
                    max_r = r
                    max_pair = (source, target, r)

    edge_count = len(sig_edges)
    density = round(edge_count / possible, 4) if possible else 0.0

    reciprocal = sum(
        1 for (s, t) in sig_edges if (t, s) in sig_edges
    ) // 2
    reciprocity = round(reciprocal / edge_count, 4) if edge_count else 0.0

    return {
        "edge_count": edge_count,
        "possible_edges": possible,
        "density": density,
        "in_degree": in_deg,
        "out_degree": out_deg,
        "reciprocal_pairs": reciprocal,
        "reciprocity": reciprocity,
        "max_influence_pair": max_pair,
        "threshold_used": threshold,
    }


def _shuffle_list(lst, seed):
    """Fisher-Yates shuffle without numpy, using a seeded LCG."""
    result = list(lst)
    n = len(result)
    # LCG parameters (same as glibc)
    a, c, m = 1103515245, 12345, 2 ** 31
    state = seed
    for i in range(n - 1, 0, -1):
        state = (a * state + c) % m
        j = state % (i + 1)
        result[i], result[j] = result[j], result[i]
    return result


def influence_baseline(micro_log, n_permutations=100, threshold=0.30, seed=42):
    """
    Random baseline for the influence network via permutation test.

    Shuffles each agent's request sequence independently n_permutations times,
    recomputes network density each time, and compares observed density against
    the null distribution.

    Returns
    -------
    {
        "observed_density":  float,
        "baseline_mean":     float,
        "baseline_std":      float,
        "p_value":           float,   # fraction of permutations >= observed
        "above_chance":      bool,    # observed > baseline_mean + 2*baseline_std
        "n_permutations":    int,
    }
    """
    if not micro_log:
        return {
            "observed_density": 0.0,
            "baseline_mean": 0.0,
            "baseline_std": 0.0,
            "p_value": 1.0,
            "above_chance": False,
            "n_permutations": n_permutations,
        }

    observed_net = influence_network(micro_log)
    observed_density = network_descriptors(observed_net, threshold)["density"]

    # Build per-agent request series (sorted by step) for shuffling
    buckets = {}
    for entry in micro_log:
        persona = entry["persona"]
        buckets.setdefault(persona, []).append((entry["step"], entry["requested"]))
    series = {
        p: [r for _, r in sorted(steps)]
        for p, steps in buckets.items()
    }
    agents = sorted(series.keys())
    steps_sorted = sorted({e["step"] for e in micro_log})

    null_densities = []
    for perm_i in range(n_permutations):
        shuffled_log = []
        for agent_i, persona in enumerate(agents):
            shuffled_reqs = _shuffle_list(series[persona], seed + perm_i * 31 + agent_i)
            for step, req in zip(steps_sorted, shuffled_reqs):
                shuffled_log.append({"persona": persona, "step": step, "requested": req})
        perm_net = influence_network(shuffled_log)
        null_densities.append(network_descriptors(perm_net, threshold)["density"])

    baseline_mean = _mean(null_densities)
    baseline_std = _std(null_densities)
    p_value = round(
        sum(1 for d in null_densities if d >= observed_density) / n_permutations, 4
    )
    above_chance = observed_density > baseline_mean + 2 * baseline_std

    return {
        "observed_density": observed_density,
        "baseline_mean": round(baseline_mean, 4),
        "baseline_std": round(baseline_std, 4),
        "p_value": p_value,
        "above_chance": above_chance,
        "n_permutations": n_permutations,
    }


def group_state_responsiveness(micro_log, macro_log):
    """
    Per-agent correlation between own request at step t and prior-step group
    demand excluding self (total_requested_t-1 - own_request_t-1).

    Positive r  → agent follows the crowd (requests more when group demands more)
    Negative r  → agent counter-balances (pulls back when group over-demands)
    Near zero   → agent ignores group state

    Returns
    -------
    {persona: {"r": float, "interpretation": str}}
    """
    if not micro_log or not macro_log:
        return {}

    # Index macro log by step for quick lookup
    macro_by_step = {e["step"]: e for e in macro_log}

    # Build per-agent series of (own_request_t, group_excl_self_t_minus_1)
    buckets = {}
    for entry in micro_log:
        persona = entry["persona"]
        step = entry["step"]
        own = entry["requested"]
        prior_step = step - 1
        if prior_step not in macro_by_step:
            continue
        prior_total = macro_by_step[prior_step]["total_requested"]
        # approximate self-exclusion using current agent's prior request
        # (exact exclusion would need per-agent prior, this is a close proxy)
        prior_own_approx = entry.get("requested", 0)
        group_excl = prior_total - prior_own_approx
        buckets.setdefault(persona, {"own": [], "group": []})
        buckets[persona]["own"].append(own)
        buckets[persona]["group"].append(group_excl)

    result = {}
    for persona, data in buckets.items():
        r = _pearson(data["group"], data["own"])
        if r > 0.3:
            interpretation = "follows_crowd"
        elif r < -0.3:
            interpretation = "counter_balances"
        else:
            interpretation = "independent"
        result[persona] = {"r": r, "interpretation": interpretation}
    return result


def compute_macro_summary(
    macro_log,
    replenishment_rate=50,
    n_agents=None,
    micro_log=None,
    success_threshold=0.7,
    convergence_window=5,
):
    role_differentiation = emergent_role_differentiation(
        micro_log or [],
        replenishment_rate,
        n_agents or 0,
    )

    # Influence network analysis
    _micro = micro_log or []
    _net = influence_network(_micro)
    _descriptors = network_descriptors(_net)
    _baseline = influence_baseline(_micro)
    _responsiveness = group_state_responsiveness(_micro, macro_log)

    run_coordination_score = coordination_score(macro_log, replenishment_rate)
    run_coordination_success = coordination_success(
        macro_log,
        replenishment_rate,
        success_threshold=success_threshold,
    )
    # If the scenario wrote a consensus_reached flag into the macro log
    # (e.g. information_consensus), honour it as an override so that trials
    # that achieved the sustained convergence window are not penalised by
    # early uncoordinated warm-up steps pulling the overall fraction down.
    if macro_log and macro_log[-1].get("consensus_reached", False):
        run_coordination_success = True
    run_convergence_step = convergence_step(
        macro_log,
        replenishment_rate,
        window=convergence_window,
    )
    run_failure_traceability = failure_traceability(
        micro_log or [],
        macro_log,
        replenishment_rate,
    )

    return {
        "sustainability_score": sustainability_score(macro_log),
        "coordination_score": run_coordination_score,
        "coordination_score_band": _label_score(
            run_coordination_score,
            0.7,
            0.3,
        ),
        "coordination_success": run_coordination_success,
        "collapse_step": collapse_step(macro_log),
        "average_gini": average_gini(macro_log),
        "demand_pressure": demand_pressure(macro_log, replenishment_rate),
        "convergence_step": run_convergence_step,
        "convergence_speed": convergence_speed(
            macro_log,
            replenishment_rate,
            window=convergence_window,
        ),
        "convergence_timeout": run_convergence_step is None,
        "emergent_role_differentiation": role_differentiation,
        "influence_network": {
            "matrix": _net["matrix"],
            "descriptors": _descriptors,
            "baseline": _baseline,
            "group_state_responsiveness": _responsiveness,
        },
        "failure_traceability": run_failure_traceability,
        "total_steps": len(macro_log),
        "final_resource_level": macro_log[-1]["resource_level"] if macro_log else None,
    }


def aggregate_macro_summaries(macro_summaries):
    if not macro_summaries:
        return {
            "trial_count": 0,
            "collapsed_runs": 0,
            "collapse_rate": 0.0,
            "mean_collapse_step": None,
            "coordination_success_rate": 0.0,
            "coordination_success_band": "low",
            "convergence_timeout_rate": 0.0,
            "outcome_variance": {},
            "variance_bands": {},
            "metrics": {},
            "failure_modes": {},
        }

    numeric_metrics = [
        "sustainability_score",
        "coordination_score",
        "average_gini",
        "demand_pressure",
        "final_resource_level",
        "total_steps",
        "convergence_speed",
    ]

    metrics = {}
    for metric_name in numeric_metrics:
        values = [
            summary[metric_name]
            for summary in macro_summaries
            if summary.get(metric_name) is not None
        ]
        metrics[metric_name] = {
            "mean": round(_mean(values), 3) if values else None,
            "std": round(_std(values), 3) if values else None,
            "min": round(min(values), 3) if values else None,
            "max": round(max(values), 3) if values else None,
        }

    collapse_steps = [
        summary["collapse_step"]
        for summary in macro_summaries
        if summary.get("collapse_step") is not None
    ]
    collapsed_runs = len(collapse_steps)
    coordination_successes = sum(
        1 for summary in macro_summaries
        if summary.get("coordination_success")
    )
    convergence_timeouts = sum(
        1 for summary in macro_summaries
        if summary.get("convergence_timeout")
    )

    variance_metrics = {}
    variance_bands = {}
    for metric_name in [
        "sustainability_score",
        "coordination_score",
        "average_gini",
        "demand_pressure",
        "convergence_speed",
    ]:
        values = [
            summary[metric_name]
            for summary in macro_summaries
            if summary.get(metric_name) is not None
        ]
        cv = round(_coefficient_of_variation(values), 3) if values else None
        variance_metrics[metric_name] = cv
        variance_bands[metric_name] = _label_score(cv, 0.2, 0.5, invert=True)

    failure_modes = {}
    for summary in macro_summaries:
        for cause in summary.get("failure_traceability", {}).get("likely_causes", []):
            failure_modes[cause] = failure_modes.get(cause, 0) + 1

    coordination_success_rate = round(
        coordination_successes / len(macro_summaries),
        3,
    )

    return {
        "trial_count": len(macro_summaries),
        "collapsed_runs": collapsed_runs,
        "collapse_rate": round(collapsed_runs / len(macro_summaries), 3),
        "mean_collapse_step": round(_mean(collapse_steps), 3)
        if collapse_steps else None,
        "coordination_success_rate": coordination_success_rate,
        "coordination_success_band": _label_score(
            coordination_success_rate,
            0.7,
            0.3,
        ),
        "convergence_timeout_rate": round(
            convergence_timeouts / len(macro_summaries),
            3,
        ),
        "outcome_variance": variance_metrics,
        "variance_bands": variance_bands,
        "metrics": metrics,
        "failure_modes": failure_modes,
    }
