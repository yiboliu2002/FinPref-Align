"""Compliance reward and penalties."""

from __future__ import annotations

from typing import Any

from finpref.constants import DIRECT_RECOMMENDATION_PATTERNS, RETURN_PROMISE_PATTERNS
from finpref.rewards.utils import batch_texts, contains_any, contains_direct_recommendation


def compliance_score(text: str) -> float:
    if contains_any(text, RETURN_PROMISE_PATTERNS) or contains_direct_recommendation(text, DIRECT_RECOMMENDATION_PATTERNS):
        return 0.0
    return 1.0


def return_promise_penalty_score(text: str) -> float:
    return 1.0 if contains_any(text, RETURN_PROMISE_PATTERNS) else 0.0


def direct_recommendation_penalty_score(text: str) -> float:
    return 1.0 if contains_direct_recommendation(text, DIRECT_RECOMMENDATION_PATTERNS) else 0.0


def compliance_reward(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [compliance_score(text) for text in batch_texts(completions)]


def return_promise_penalty(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [-return_promise_penalty_score(text) for text in batch_texts(completions)]


def direct_recommendation_penalty(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [-direct_recommendation_penalty_score(text) for text in batch_texts(completions)]
