"""Suitability reward."""

from __future__ import annotations

from typing import Any

from finpref.constants import DIRECT_RECOMMENDATION_PATTERNS, SUITABILITY_CAUTION_TERMS
from finpref.rewards.utils import batch_texts, contains_any, contains_direct_recommendation


def suitability_score(text: str, meta: dict[str, Any] | None = None) -> float:
    meta = meta or {}
    if meta.get("risk_mismatch"):
        if contains_direct_recommendation(text, DIRECT_RECOMMENDATION_PATTERNS):
            return 0.0
        return 1.0 if contains_any(text, SUITABILITY_CAUTION_TERMS) else 0.3
    if meta.get("requires_clarification"):
        asks = ["风险承受能力", "投资期限", "流动性", "投资目标"]
        return 1.0 if sum(term in text for term in asks) >= 2 else 0.2
    return 0.8


def suitability_reward(prompts: list[Any], completions: list[Any], meta: list[dict[str, Any]] | None = None, **kwargs: Any) -> list[float]:
    metas = meta or [{} for _ in completions]
    return [suitability_score(text, item_meta) for text, item_meta in zip(batch_texts(completions), metas)]
