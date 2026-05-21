"""Penalty rewards for over-refusal and verbosity."""

from __future__ import annotations

from typing import Any

from finpref.constants import OVER_REFUSAL_PATTERNS
from finpref.rewards.utils import batch_texts, contains_any


def over_refusal_penalty_score(text: str, meta: dict[str, Any] | None = None) -> float:
    meta = meta or {}
    if meta.get("over_refusal_probe") and contains_any(text, OVER_REFUSAL_PATTERNS):
        return 1.0
    return 0.0


def verbosity_penalty_score(text: str) -> float:
    length = len(text)
    if length < 80:
        return 0.2
    if length > 700:
        return 1.0
    if text.count("投资有风险") > 2:
        return 0.8
    return 0.0


def over_refusal_penalty(prompts: list[Any], completions: list[Any], meta: list[dict[str, Any]] | None = None, **kwargs: Any) -> list[float]:
    metas = meta or [{} for _ in completions]
    return [-over_refusal_penalty_score(text, item_meta) for text, item_meta in zip(batch_texts(completions), metas)]


def verbosity_penalty(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [-verbosity_penalty_score(text) for text in batch_texts(completions)]

