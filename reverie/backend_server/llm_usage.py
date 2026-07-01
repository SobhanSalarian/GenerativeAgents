"""
Run-level LLM and embedding usage tracking for experiments.

The research plan calls out API-cost management and reproducibility controls.
This module keeps lightweight aggregate usage stats in-process so experiment
runs can persist token counts and estimated cost in their manifests.
"""
from __future__ import annotations

from copy import deepcopy
from threading import Lock
import os


_LOCK = Lock()


def _new_usage_state():
    return {
        "chat_requests": 0,
        "embedding_requests": 0,
        "chat_prompt_tokens": 0,
        "chat_completion_tokens": 0,
        "chat_total_tokens": 0,
        "embedding_prompt_tokens": 0,
        "embedding_total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "models": {},
        "errors": [],
    }


_USAGE = _new_usage_state()


def _float_env(name, default="0"):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


CHAT_INPUT_COST_PER_1K_USD = _float_env("OPENAI_CHAT_INPUT_COST_PER_1K_USD")
CHAT_OUTPUT_COST_PER_1K_USD = _float_env("OPENAI_CHAT_OUTPUT_COST_PER_1K_USD")
EMBED_INPUT_COST_PER_1K_USD = _float_env("OPENAI_EMBED_INPUT_COST_PER_1K_USD")


def reset_usage_stats():
    with _LOCK:
        _USAGE.clear()
        _USAGE.update(_new_usage_state())


def _ensure_model_bucket(model_name):
    return _USAGE["models"].setdefault(
        model_name or "unknown",
        {
            "chat_requests": 0,
            "embedding_requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    )


def record_chat_completion(completion, model_name=None):
    usage = getattr(completion, "usage", None)
    model_name = model_name or getattr(completion, "model", None) or "unknown"
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or 0)

    with _LOCK:
        _USAGE["chat_requests"] += 1
        _USAGE["chat_prompt_tokens"] += prompt_tokens
        _USAGE["chat_completion_tokens"] += completion_tokens
        _USAGE["chat_total_tokens"] += total_tokens
        _USAGE["estimated_cost_usd"] += (
            (prompt_tokens / 1000.0) * CHAT_INPUT_COST_PER_1K_USD
            + (completion_tokens / 1000.0) * CHAT_OUTPUT_COST_PER_1K_USD
        )
        bucket = _ensure_model_bucket(model_name)
        bucket["chat_requests"] += 1
        bucket["prompt_tokens"] += prompt_tokens
        bucket["completion_tokens"] += completion_tokens
        bucket["total_tokens"] += total_tokens


def record_embedding_response(response, model_name=None):
    usage = getattr(response, "usage", None)
    model_name = model_name or getattr(response, "model", None) or "unknown"
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", prompt_tokens) or 0)

    with _LOCK:
        _USAGE["embedding_requests"] += 1
        _USAGE["embedding_prompt_tokens"] += prompt_tokens
        _USAGE["embedding_total_tokens"] += total_tokens
        _USAGE["estimated_cost_usd"] += (
            (prompt_tokens / 1000.0) * EMBED_INPUT_COST_PER_1K_USD
        )
        bucket = _ensure_model_bucket(model_name)
        bucket["embedding_requests"] += 1
        bucket["prompt_tokens"] += prompt_tokens
        bucket["total_tokens"] += total_tokens


def record_request_error(kind, model_name=None, error_message=None):
    with _LOCK:
        _USAGE["errors"].append(
            {
                "kind": kind,
                "model": model_name or "unknown",
                "error": str(error_message or "")[:300],
            }
        )


def get_usage_stats():
    with _LOCK:
        snapshot = deepcopy(_USAGE)
    snapshot["estimated_cost_usd"] = round(snapshot["estimated_cost_usd"], 6)
    return snapshot
