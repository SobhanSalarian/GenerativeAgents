"""
Micro-level (individual agent) metrics for generative agent validation.

Aligned with the MRes research plan Table 1:
- Behavioural consistency : cosine similarity of action embeddings vs. profile
- Memory coherence        : prior-context refs ÷ opportunities (embedding relevance)
- Planning plausibility   : LLM-assisted 1–5 rubric + embedding alignment fallback
- Response naturalness    : LLM-as-judge distinction test + heuristic fallback
- Composite believability : weighted average of the four sub-dimensions

Embedding calls use the shared get_embedding() client and an in-process cache
to deduplicate API requests across a run. LLM judge calls are sampled (3–4
entries per persona) to keep API costs proportional to the human-eval budget.
"""
import json
import math
import os
import sys
from collections import defaultdict
import re

# ---------------------------------------------------------------------------
# Optional LLM / embedding back-end
# Importing here keeps measurement/ self-contained; graceful fallback when
# the API client is not wired up (e.g. unit tests).
# ---------------------------------------------------------------------------
try:
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend_dir not in sys.path:
        sys.path.insert(0, _backend_dir)
    from persona.prompt_template.gpt_structure import (
        get_embedding,
        ChatGPT_request,
    )
    _LLM_AVAILABLE = True
except Exception:
    _LLM_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIGH_LOW_DEFAULTS = {
    "behavioural_consistency": (0.7, 0.4),
    "memory_coherence": (0.6, 0.3),
    "planning_plausibility": (0.7, 0.4),
    "response_naturalness": (0.7, 0.4),
    "composite_believability": (0.7, 0.4),
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "i", "in", "is", "it", "its", "my", "of", "on", "or",
    "our", "that", "the", "their", "them", "they", "this", "to", "was",
    "we", "with", "would", "you", "your",
}

# Sampling: number of entries per persona fed to the LLM judges
_LLM_JUDGE_SAMPLES_PER_PERSONA = 4


# ---------------------------------------------------------------------------
# Embedding cache and cosine similarity
# ---------------------------------------------------------------------------

_EMBEDDING_CACHE: dict = {}


def clear_embedding_cache():
    """Free cached embeddings between runs."""
    _EMBEDDING_CACHE.clear()


def _embed_text(text: str):
    """Return embedding vector (list of floats) with cache; None on failure."""
    text = str(text or "").strip()
    if not text:
        return None
    if text not in _EMBEDDING_CACHE:
        if not _LLM_AVAILABLE:
            return None
        try:
            _EMBEDDING_CACHE[text] = get_embedding(text)
        except Exception:
            return None
    return _EMBEDDING_CACHE[text]


def _cosine_similarity(vec_a, vec_b) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embedding_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity between two texts; Jaccard fallback if unavailable."""
    vec_a = _embed_text(text_a)
    vec_b = _embed_text(text_b)
    if vec_a is None or vec_b is None:
        return _jaccard_similarity(text_a, text_b)
    return max(0.0, _cosine_similarity(vec_a, vec_b))


def _best_embedding_match(text: str, candidates) -> float:
    """Max cosine similarity of text against each candidate; Jaccard fallback."""
    if not text:
        return 0.0
    valid = [c for c in (candidates or []) if c]
    if not valid:
        return 0.0
    text_vec = _embed_text(text)
    if text_vec is None:
        return _best_text_match(text, valid)
    best = 0.0
    for candidate in valid:
        cand_vec = _embed_text(candidate)
        if cand_vec is None:
            best = max(best, _jaccard_similarity(text, candidate))
        else:
            best = max(best, _cosine_similarity(text_vec, cand_vec))
    return max(0.0, best)


def pre_embed_micro_log(micro_log):
    """
    Pre-populate the embedding cache for every unique text field in micro_log.
    Call once before computing metrics so API calls are batched up front.
    """
    if not _LLM_AVAILABLE:
        return
    texts = set()
    for entry in micro_log:
        for field in ("reasoning", "memory_reference", "plan_reference",
                      "persona_profile", "current_activity"):
            val = str(entry.get(field, "") or "").strip()
            if val:
                texts.add(val)
        for mem in (entry.get("recent_memories") or []):
            val = str(mem or "").strip()
            if val:
                texts.add(val)
        for goal in (entry.get("daily_goals") or []):
            val = str(goal or "").strip()
            if val:
                texts.add(val)
    for text in texts:
        _embed_text(text)


# ---------------------------------------------------------------------------
# Jaccard fallback (kept for when embeddings are unavailable)
# ---------------------------------------------------------------------------

def _tokenize(text):
    tokens = re.findall(r"[a-zA-Z0-9']+", str(text or "").lower())
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def _jaccard_similarity(text_a, text_b) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union else 0.0


def _best_text_match(text, candidates) -> float:
    if not text:
        return 0.0
    valid = [c for c in candidates if c]
    if not valid:
        return 0.0
    return max(_jaccard_similarity(text, c) for c in valid)


# ---------------------------------------------------------------------------
# LLM judges (sampled per persona)
# ---------------------------------------------------------------------------

def _sample_entries_for_judge(entries, n=_LLM_JUDGE_SAMPLES_PER_PERSONA,
                               critical_step=None):
    """
    Return up to n representative entries (first, evenly-spaced, last,
    + closest to critical_step).
    """
    if not entries:
        return []
    indices = {0, len(entries) // 2, len(entries) - 1}
    if len(entries) >= 4:
        indices.add(len(entries) // 4)
        indices.add(3 * len(entries) // 4)
    chosen = [entries[i] for i in sorted(indices)]
    if critical_step is not None:
        nearest = min(entries, key=lambda e: abs(e["step"] - critical_step))
        if nearest not in chosen:
            chosen.append(nearest)
    # Deduplicate by step
    seen, deduped = set(), []
    for e in sorted(chosen, key=lambda e: e["step"]):
        if e["step"] not in seen:
            deduped.append(e)
            seen.add(e["step"])
    return deduped[:n]


def _llm_planning_plausibility_score(plan_reference: str,
                                     daily_goals,
                                     current_activity: str) -> float | None:
    """
    LLM-assisted 1–5 rubric for planning plausibility (research plan §4.5).
    Returns normalised 0–1 value (score-1)/4, or None on failure.
    """
    if not _LLM_AVAILABLE:
        return None
    text = str(plan_reference or "").strip()
    if not text:
        return None

    goals_str = "; ".join(daily_goals) if daily_goals else "none stated"
    activity_str = str(current_activity or "none stated").strip()

    prompt = (
        "Rate the planning plausibility of the following agent decision "
        "on a 1–5 integer scale.\n\n"
        f"Agent's current goals    : {goals_str}\n"
        f"Agent's current activity : {activity_str}\n"
        f"Agent's plan reference   : {text}\n\n"
        "Scoring rubric:\n"
        "5 = Directly and logically follows from stated goals/activity\n"
        "4 = Mostly aligned, minor inconsistency\n"
        "3 = Weakly related to goals/activity\n"
        "2 = Little logical connection\n"
        "1 = Contradicts or ignores stated goals/activity\n\n"
        'Respond with exactly: {"score": <1–5>, "reason": "<one sentence>"}'
    )
    try:
        response = ChatGPT_request(prompt)
        data = json.loads(response)
        score = int(data.get("score", 3))
        score = max(1, min(5, score))
        return round((score - 1) / 4, 3)    # map 1–5 → 0–1
    except Exception:
        return None


def _llm_response_naturalness_score(reasoning_text: str) -> float | None:
    """
    LLM-as-judge distinction test (research plan §4.5):
    'Would a naive reader be fooled into thinking this is human-written?'
    Returns a 0–1 naturalness score, or None on failure.
    """
    if not _LLM_AVAILABLE:
        return None
    text = str(reasoning_text or "").strip()
    if not text or text.lower().startswith("parse error"):
        return None

    prompt = (
        "Evaluate whether the following text sounds like it was written by "
        "a human or an AI agent.\n\n"
        f'Text: "{text}"\n\n'
        "Rate on a 0–1 scale:\n"
        "1.0 = Indistinguishable from natural human writing\n"
        "0.5 = Ambiguous — could be human or AI\n"
        "0.0 = Clearly formulaic or AI-generated\n\n"
        "Also give a binary verdict: would a naive reader be fooled?\n\n"
        'Respond with exactly: {"naturalness_score": <0.0–1.0>, '
        '"fooled": <true|false>, "reason": "<one sentence>"}'
    )
    try:
        response = ChatGPT_request(prompt)
        data = json.loads(response)
        score = float(data.get("naturalness_score", 0.5))
        return round(max(0.0, min(1.0, score)), 3)
    except Exception:
        return None


def planning_plausibility_llm_per_agent(micro_log,
                                         critical_step=None) -> dict:
    """
    Per-persona LLM planning-plausibility scores (0–1).
    Samples up to _LLM_JUDGE_SAMPLES_PER_PERSONA entries per persona.
    Falls back to empty dict if LLM unavailable.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(entry)

    scores = {}
    for persona, entries in buckets.items():
        sampled = _sample_entries_for_judge(entries, critical_step=critical_step)
        persona_scores = []
        for entry in sampled:
            s = _llm_planning_plausibility_score(
                entry.get("plan_reference", ""),
                entry.get("daily_goals") or [],
                entry.get("current_activity", ""),
            )
            if s is not None:
                persona_scores.append(s)
        if persona_scores:
            scores[persona] = round(sum(persona_scores) / len(persona_scores), 3)
    return scores


def response_naturalness_llm_per_agent(micro_log,
                                        critical_step=None) -> dict:
    """
    Per-persona LLM response-naturalness scores (0–1).
    Samples up to _LLM_JUDGE_SAMPLES_PER_PERSONA entries per persona.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(entry)

    scores = {}
    for persona, entries in buckets.items():
        sampled = _sample_entries_for_judge(entries, critical_step=critical_step)
        persona_scores = []
        for entry in sampled:
            s = _llm_response_naturalness_score(entry.get("reasoning", ""))
            if s is not None:
                persona_scores.append(s)
        if persona_scores:
            scores[persona] = round(sum(persona_scores) / len(persona_scores), 3)
    return scores


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _bucket_by_persona(micro_log):
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(entry)
    return buckets


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _safe_round_dict(d, digits=3):
    return {k: round(v, digits) if isinstance(v, (int, float)) else v
            for k, v in d.items()}


def _label_score(value, high, low):
    if value is None:
        return "not_applicable"
    if value >= high:
        return "high"
    if value < low:
        return "low"
    return "medium"


# ---------------------------------------------------------------------------
# Request-level helpers (unchanged from original)
# ---------------------------------------------------------------------------

def average_request_per_agent(micro_log):
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(entry["requested"])
    return {name: round(sum(v) / len(v), 2) for name, v in buckets.items()}


def request_consistency_per_agent(micro_log):
    """1 - coefficient_of_variation of requests (higher = more consistent)."""
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(entry["requested"])
    scores = {}
    for name, reqs in buckets.items():
        mean = _mean(reqs)
        if mean == 0:
            scores[name] = 1.0
            continue
        variance = sum((r - mean) ** 2 for r in reqs) / len(reqs)
        cv = (variance ** 0.5) / mean
        scores[name] = round(max(0.0, 1.0 - cv), 3)
    return scores


def cooperation_rate_per_agent(micro_log, replenishment_rate, n_agents):
    fair_share = replenishment_rate / n_agents if n_agents else 0
    buckets = defaultdict(list)
    for entry in micro_log:
        buckets[entry["persona"]].append(
            1 if entry["requested"] <= fair_share else 0
        )
    return {name: round(sum(v) / len(v), 3) for name, v in buckets.items()}


# ---------------------------------------------------------------------------
# Profile alignment — embedding-based (was Jaccard)
# ---------------------------------------------------------------------------

def profile_alignment_per_agent(micro_log):
    """
    Cosine similarity between the agent's action text and its persona profile.
    Uses Jaccard if embeddings are unavailable.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        action_text = " ".join(
            part for part in [
                entry.get("reasoning", ""),
                entry.get("memory_reference", ""),
                entry.get("plan_reference", ""),
            ] if part
        )
        profile = entry.get("persona_profile", "")
        buckets[entry["persona"]].append(
            _embedding_similarity(action_text, profile)
        )
    return _safe_round_dict(
        {name: _mean(values) for name, values in buckets.items()}
    )


# ---------------------------------------------------------------------------
# Memory metrics — embedding-based relevance
# ---------------------------------------------------------------------------

def memory_reference_rate(micro_log):
    buckets = defaultdict(list)
    for entry in micro_log:
        reference = str(entry.get("memory_reference", "")).strip()
        buckets[entry["persona"]].append(1 if reference else 0)
    return _safe_round_dict({name: _mean(v) for name, v in buckets.items()})


def memory_relevance_per_agent(micro_log):
    """
    Cosine similarity between cited memory reference and available memories.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        reference = str(entry.get("memory_reference", "")).strip()
        memories = entry.get("recent_memories") or []
        buckets[entry["persona"]].append(
            _best_embedding_match(reference, memories)
        )
    return _safe_round_dict({name: _mean(v) for name, v in buckets.items()})


def memory_coherence_per_agent(micro_log):
    """
    MRes-aligned: opportunity flag × (0.4 × mention + 0.6 × embedding relevance).
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        has_opportunity = bool(entry.get("memory_context_available"))
        reference = str(entry.get("memory_reference", "")).strip()
        memories = entry.get("recent_memories") or []
        if not has_opportunity:
            score = 0.0
        else:
            mention = 1.0 if reference else 0.0
            relevance = _best_embedding_match(reference, memories)
            score = (0.4 * mention) + (0.6 * relevance)
        buckets[entry["persona"]].append(score)
    return _safe_round_dict({name: _mean(v) for name, v in buckets.items()})


# ---------------------------------------------------------------------------
# Planning metrics — embedding-based alignment + LLM judge
# ---------------------------------------------------------------------------

def planning_reference_rate(micro_log):
    buckets = defaultdict(list)
    for entry in micro_log:
        reference = str(entry.get("plan_reference", "")).strip()
        buckets[entry["persona"]].append(1 if reference else 0)
    return _safe_round_dict({name: _mean(v) for name, v in buckets.items()})


def planning_alignment_per_agent(micro_log):
    """Cosine similarity between plan reference text and daily goals/activity."""
    buckets = defaultdict(list)
    for entry in micro_log:
        plan_targets = list(entry.get("daily_goals") or [])
        current_activity = entry.get("current_activity")
        if current_activity:
            plan_targets.append(current_activity)
        reference = str(entry.get("plan_reference", "")).strip()
        fallback = str(entry.get("reasoning", "")).strip()
        text = reference or fallback
        buckets[entry["persona"]].append(
            _best_embedding_match(text, plan_targets)
        )
    return _safe_round_dict({name: _mean(v) for name, v in buckets.items()})


def planning_plausibility_per_agent(micro_log,
                                     llm_scores: dict | None = None):
    """
    Embedding-based planning plausibility proxy (automated fallback).
    If llm_scores are provided (from planning_plausibility_llm_per_agent),
    they are blended in: 0.5 × llm_score + 0.5 × embedding_score.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        has_opportunity = bool(entry.get("planning_context_available"))
        reference = str(entry.get("plan_reference", "")).strip()
        plan_targets = list(entry.get("daily_goals") or [])
        current_activity = entry.get("current_activity")
        if current_activity:
            plan_targets.append(current_activity)
        fallback = str(entry.get("reasoning", "")).strip()

        if not has_opportunity:
            score = 0.0
        else:
            alignment = _best_embedding_match(reference or fallback, plan_targets)
            explicit_reference = 1.0 if reference else 0.5 if alignment > 0 else 0.0
            score = (0.4 * explicit_reference) + (0.6 * alignment)
        buckets[entry["persona"]].append(score)

    embedding_scores = _safe_round_dict(
        {name: _mean(v) for name, v in buckets.items()}
    )

    if not llm_scores:
        return embedding_scores

    # Blend LLM judge with embedding proxy
    blended = {}
    for persona, emb in embedding_scores.items():
        llm = llm_scores.get(persona)
        if llm is not None:
            blended[persona] = round(0.5 * llm + 0.5 * emb, 3)
        else:
            blended[persona] = emb
    return blended


def planning_plausibility_rubric(micro_log, llm_scores: dict | None = None):
    """Convert the 0–1 planning proxy to a 1–5 rubric-like score."""
    raw = planning_plausibility_per_agent(micro_log, llm_scores=llm_scores)
    return _safe_round_dict({name: 1 + (4 * value) for name, value in raw.items()})


# ---------------------------------------------------------------------------
# Response naturalness — LLM judge + heuristic fallback
# ---------------------------------------------------------------------------

def _heuristic_naturalness(reasoning: str) -> float:
    """Original word-count / sentence heuristic; used as fallback."""
    if not reasoning:
        return 0.0
    text = reasoning.strip()
    if text.lower().startswith("parse error:"):
        return 0.0
    word_count = len(text.split())
    sentence_count = len(
        [p for p in re.split(r"[.!?]+", text) if p.strip()]
    )
    unique_ratio = (
        len(set(text.lower().split())) / word_count if word_count else 0.0
    )
    score = 1.0
    if word_count < 5:
        score -= 0.35
    if word_count > 45:
        score -= 0.15
    if sentence_count == 0:
        score -= 0.3
    if sentence_count > 3:
        score -= 0.15
    if unique_ratio < 0.45:
        score -= 0.15
    return round(max(0.0, min(1.0, score)), 3)


def response_naturalness_per_agent(micro_log,
                                    llm_scores: dict | None = None):
    """
    Per-persona response naturalness (0–1).
    If llm_scores are provided, blends 0.6 × llm + 0.4 × heuristic.
    Falls back to pure heuristic when LLM scores are absent.
    """
    buckets = defaultdict(list)
    for entry in micro_log:
        score = _heuristic_naturalness(entry.get("reasoning", ""))
        if entry.get("parse_error"):
            score = 0.0
        buckets[entry["persona"]].append(score)

    heuristic_scores = _safe_round_dict(
        {name: _mean(v) for name, v in buckets.items()}
    )

    if not llm_scores:
        return heuristic_scores

    blended = {}
    for persona, heur in heuristic_scores.items():
        llm = llm_scores.get(persona)
        if llm is not None:
            blended[persona] = round(0.6 * llm + 0.4 * heur, 3)
        else:
            blended[persona] = heur
    return blended


# ---------------------------------------------------------------------------
# Behavioural consistency — embedding-based profile alignment
# ---------------------------------------------------------------------------

def behavioural_consistency_per_agent(micro_log,
                                       replenishment_rate=50,
                                       n_agents=None):
    """
    Composite: request_consistency (0.45) + profile_alignment (0.35)
               + cooperation_rate (0.20).
    Profile alignment now uses cosine embedding similarity.
    """
    if n_agents is None:
        n_agents = len({e["persona"] for e in micro_log})

    request_consistency = request_consistency_per_agent(micro_log)
    cooperation = cooperation_rate_per_agent(micro_log, replenishment_rate, n_agents)
    profile_alignment = profile_alignment_per_agent(micro_log)

    personas = {entry["persona"] for entry in micro_log}
    scores = {}
    for persona in personas:
        score = (
            request_consistency.get(persona, 0.0) * 0.45
            + profile_alignment.get(persona, 0.0) * 0.35
            + cooperation.get(persona, 0.0) * 0.20
        )
        scores[persona] = round(score, 3)
    return scores


# ---------------------------------------------------------------------------
# Composite believability
# ---------------------------------------------------------------------------

def composite_believability_per_agent(micro_log,
                                       replenishment_rate=50,
                                       n_agents=None,
                                       llm_planning_scores: dict | None = None,
                                       llm_naturalness_scores: dict | None = None):
    if n_agents is None:
        n_agents = len({e["persona"] for e in micro_log})

    behaviour = behavioural_consistency_per_agent(
        micro_log, replenishment_rate=replenishment_rate, n_agents=n_agents
    )
    memory = memory_coherence_per_agent(micro_log)
    planning = planning_plausibility_per_agent(
        micro_log, llm_scores=llm_planning_scores
    )
    naturalness = response_naturalness_per_agent(
        micro_log, llm_scores=llm_naturalness_scores
    )

    personas = {entry["persona"] for entry in micro_log}
    scores = {}
    for persona in personas:
        score = (
            behaviour.get(persona, 0.0) * 0.30
            + memory.get(persona, 0.0) * 0.25
            + planning.get(persona, 0.0) * 0.25
            + naturalness.get(persona, 0.0) * 0.20
        )
        scores[persona] = round(score, 3)
    return scores


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------

def _label_dict(values, metric_name):
    high, low = HIGH_LOW_DEFAULTS[metric_name]
    return {
        persona: _label_score(score, high, low)
        for persona, score in values.items()
    }


# ---------------------------------------------------------------------------
# Human-rating blend helpers
# ---------------------------------------------------------------------------

_BLEND_WEIGHTS_DEFAULT = {
    "behavioural_consistency": {"auto": 0.50, "human": 0.50},
    "memory_coherence":        {"auto": 0.50, "human": 0.50},
    "planning_plausibility":   {"auto": 0.50, "human": 0.50},
    "response_naturalness":    {"auto": 0.60, "human": 0.40},
}

_COMPOSITE_WEIGHTS = {
    "behavioural_consistency": 0.30,
    "memory_coherence":        0.25,
    "planning_plausibility":   0.25,
    "response_naturalness":    0.20,
}

_BLEND_DIMENSIONS = list(_BLEND_WEIGHTS_DEFAULT.keys())


def _build_agent_deblind_map(trial_dir):
    """
    Build {blinded_agent_id: persona_name} from the human-eval artefacts in
    trial_dir.  Returns an empty dict if the files are not present.
    """
    packets_path = os.path.join(trial_dir, "human_eval_packets.jsonl")
    key_path = os.path.join(trial_dir, "human_eval_blind_key.json")
    if not os.path.exists(packets_path) or not os.path.exists(key_path):
        return {}
    with open(key_path) as fh:
        blind_key = json.load(fh)
    mapping = {}
    with open(packets_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                pkt = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = pkt.get("packet_id")
            bid = pkt.get("blinded_agent_id")
            if pid and bid and pid in blind_key:
                mapping[bid] = blind_key[pid]["persona_name"]
    return mapping


def blend_human_ratings_into_summary(
    micro_summary,
    merged_ratings,
    agent_deblind_map,
    reliability=None,
    weights=None,
):
    """
    Extend micro_summary with final mixed-method per-agent scores.

    Parameters
    ----------
    micro_summary     : dict returned by compute_micro_summary
    merged_ratings    : list[dict] from rating_ingestion.merge_ratings();
                        each row has blinded_agent_id and {dim}_mean fields
    agent_deblind_map : {blinded_agent_id: persona_name}; produced by
                        _build_agent_deblind_map(trial_dir)
    reliability       : reliability dict from rating_ingestion (optional);
                        dimensions with alpha < 0.67 fall back to auto-only
    weights           : optional {dim: {auto: float, human: float}} override

    Returns the input dict with these extra keys for each dimension d:
        {d}_final            {persona: float(0–1)}
        {d}_final_band       {persona: str}
    Plus:
        composite_believability_final      {persona: float(0–1)}
        composite_believability_final_band {persona: str}
        human_ratings_blended              bool
        human_blend_weights                {dim: {auto, human}}
        reliability_gated_dimensions       list[str]
        personas_with_human_ratings        list[str]
    """
    w = weights or _BLEND_WEIGHTS_DEFAULT

    # Determine which dimensions are reliability-gated (alpha < threshold)
    gated = []
    if reliability and "dimensions" in reliability:
        for dim in _BLEND_DIMENSIONS:
            dim_info = reliability["dimensions"].get(dim, {})
            if dim_info.get("acceptable") is False:
                gated.append(dim)

    # Build per-persona human rating averages from merged_ratings rows.
    # merged_ratings rows are already averaged across raters; here we average
    # across time-points (packets) for the same agent.
    persona_scores: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for row in merged_ratings:
        bid = row.get("blinded_agent_id", "")
        persona = agent_deblind_map.get(bid, bid)  # fall back to bid if no map
        for dim in _BLEND_DIMENSIONS:
            val = row.get(f"{dim}_mean")
            if val is not None:
                persona_scores[persona][dim].append(float(val))

    # Average across time-points and normalise 1–5 → 0–1
    human_avg: dict[str, dict[str, float]] = {}
    for persona, dim_lists in persona_scores.items():
        human_avg[persona] = {}
        for dim, vals in dim_lists.items():
            if vals:
                mean_likert = sum(vals) / len(vals)
                human_avg[persona][dim] = (mean_likert - 1.0) / 4.0

    personas_with_ratings = sorted(human_avg.keys())

    # Blend per dimension
    result = dict(micro_summary)
    for dim in _BLEND_DIMENSIONS:
        auto_scores: dict = micro_summary.get(dim, {})
        final_scores: dict = {}
        for persona, auto_val in auto_scores.items():
            if dim in gated or persona not in human_avg or dim not in human_avg[persona]:
                final_scores[persona] = auto_val
            else:
                aw = w[dim]["auto"]
                hw = w[dim]["human"]
                final_scores[persona] = aw * auto_val + hw * human_avg[persona][dim]
        result[f"{dim}_final"] = final_scores
        result[f"{dim}_final_band"] = _label_dict(final_scores, dim)

    # Recompute composite believability from blended sub-scores
    all_personas = set()
    for dim in _BLEND_DIMENSIONS:
        all_personas.update(result.get(f"{dim}_final", {}).keys())

    composite_final: dict = {}
    for persona in all_personas:
        score = sum(
            _COMPOSITE_WEIGHTS[dim] * result[f"{dim}_final"].get(persona, 0.0)
            for dim in _BLEND_DIMENSIONS
        )
        composite_final[persona] = round(score, 4)

    result["composite_believability_final"] = composite_final
    result["composite_believability_final_band"] = _label_dict(
        composite_final, "composite_believability"
    )

    # Metadata
    result["human_ratings_blended"] = True
    result["human_blend_weights"] = {dim: dict(w[dim]) for dim in _BLEND_DIMENSIONS}
    result["reliability_gated_dimensions"] = gated
    result["personas_with_human_ratings"] = personas_with_ratings
    return result


# ---------------------------------------------------------------------------
# Main summary entry point
# ---------------------------------------------------------------------------

def compute_micro_summary(micro_log,
                           replenishment_rate=50,
                           n_agents=None,
                           use_llm_judges=True,
                           critical_step=None,
                           human_ratings=None,
                           agent_deblind_map=None,
                           reliability=None):
    """
    Return the micro-level metrics used by the MRes experiment pipeline.

    Parameters
    ----------
    micro_log          : list of per-agent per-step dicts
    replenishment_rate : resource replenishment rate (for cooperation proxy)
    n_agents           : number of agents (inferred if None)
    use_llm_judges     : when True, run LLM-assisted planning and naturalness
                         judges (sampled; 3-4 calls per persona)
    critical_step      : step index used to anchor the LLM-judge sample
    human_ratings      : list[dict] from rating_ingestion.merge_ratings(); when
                         provided the summary is extended with *_final blended keys
    agent_deblind_map  : {blinded_agent_id: persona_name}; build with
                         _build_agent_deblind_map(trial_dir) or pass None to
                         skip de-blinding (ratings keyed by persona_name directly)
    reliability        : reliability dict from rating_ingestion; used to gate
                         dimensions with Krippendorff's alpha < 0.67
    """
    if n_agents is None:
        n_agents = len({e["persona"] for e in micro_log})

    # Pre-populate embedding cache for all unique texts in one pass
    pre_embed_micro_log(micro_log)

    # LLM judges (sampled per persona)
    llm_planning_scores = {}
    llm_naturalness_scores = {}
    if use_llm_judges and _LLM_AVAILABLE:
        llm_planning_scores = planning_plausibility_llm_per_agent(
            micro_log, critical_step=critical_step
        )
        llm_naturalness_scores = response_naturalness_llm_per_agent(
            micro_log, critical_step=critical_step
        )

    # Core metrics
    average_request = average_request_per_agent(micro_log)
    request_consistency = request_consistency_per_agent(micro_log)
    cooperation_rate = cooperation_rate_per_agent(
        micro_log, replenishment_rate, n_agents
    )
    profile_alignment = profile_alignment_per_agent(micro_log)
    behavioural_consistency = behavioural_consistency_per_agent(
        micro_log, replenishment_rate=replenishment_rate, n_agents=n_agents
    )
    memory_reference = memory_reference_rate(micro_log)
    memory_relevance = memory_relevance_per_agent(micro_log)
    memory_coherence = memory_coherence_per_agent(micro_log)
    planning_reference = planning_reference_rate(micro_log)
    planning_alignment = planning_alignment_per_agent(micro_log)
    planning_plausibility = planning_plausibility_per_agent(
        micro_log, llm_scores=llm_planning_scores
    )
    planning_rubric = planning_plausibility_rubric(
        micro_log, llm_scores=llm_planning_scores
    )
    response_naturalness = response_naturalness_per_agent(
        micro_log, llm_scores=llm_naturalness_scores
    )
    composite_believability = composite_believability_per_agent(
        micro_log,
        replenishment_rate=replenishment_rate,
        n_agents=n_agents,
        llm_planning_scores=llm_planning_scores,
        llm_naturalness_scores=llm_naturalness_scores,
    )

    summary = {
        "average_request": average_request,
        "consistency_score": request_consistency,
        "request_consistency": request_consistency,
        "cooperation_rate": cooperation_rate,
        "profile_alignment": profile_alignment,
        "behavioural_consistency": behavioural_consistency,
        "behavioural_consistency_band": _label_dict(
            behavioural_consistency, "behavioural_consistency"
        ),
        "memory_reference_rate": memory_reference,
        "memory_reference_relevance": memory_relevance,
        "memory_coherence": memory_coherence,
        "memory_coherence_band": _label_dict(memory_coherence, "memory_coherence"),
        "planning_reference_rate": planning_reference,
        "planning_alignment": planning_alignment,
        "planning_plausibility": planning_plausibility,
        "planning_plausibility_llm": llm_planning_scores,
        "planning_plausibility_rubric": planning_rubric,
        "planning_plausibility_band": _label_dict(
            planning_plausibility, "planning_plausibility"
        ),
        "response_naturalness": response_naturalness,
        "response_naturalness_proxy": response_naturalness,
        "response_naturalness_llm": llm_naturalness_scores,
        "response_naturalness_band": _label_dict(
            response_naturalness, "response_naturalness"
        ),
        "composite_believability": composite_believability,
        "composite_believability_band": _label_dict(
            composite_believability, "composite_believability"
        ),
        # Backward-compatible alias
        "believability_proxy": composite_believability,
        # Metadata
        "llm_judges_used": use_llm_judges and _LLM_AVAILABLE,
        "embedding_method": "cosine" if _LLM_AVAILABLE else "jaccard_fallback",
    }

    if human_ratings is not None:
        summary = blend_human_ratings_into_summary(
            summary,
            human_ratings,
            agent_deblind_map or {},
            reliability=reliability,
        )
    return summary
