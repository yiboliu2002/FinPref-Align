"""Helpfulness reward."""

from __future__ import annotations

from typing import Any

from finpref.rewards.utils import batch_texts

HELPFUL_TERMS = ["原因", "因为", "建议", "下一步", "可以比较", "产品说明书", "风险揭示", "补充"]


def helpfulness_score(text: str) -> float:
    hits = sum(term in text for term in HELPFUL_TERMS)
    if hits >= 3:
        return 1.0
    if hits >= 1:
        return 0.6
    return 0.2


def helpfulness_reward(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [helpfulness_score(text) for text in batch_texts(completions)]

