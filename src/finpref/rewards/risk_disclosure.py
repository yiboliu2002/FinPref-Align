"""Risk disclosure reward."""

from __future__ import annotations

from typing import Any

from finpref.constants import RISK_TERMS
from finpref.rewards.utils import batch_texts, count_terms


def risk_disclosure_score(text: str) -> float:
    count = count_terms(text, RISK_TERMS)
    if count >= 2:
        return 1.0
    if "风险" in text:
        return 0.4
    return 0.0


def risk_disclosure_reward(prompts: list[Any], completions: list[Any], **kwargs: Any) -> list[float]:
    return [risk_disclosure_score(text) for text in batch_texts(completions)]

