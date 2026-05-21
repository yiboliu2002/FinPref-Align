"""Reward helper functions."""

from __future__ import annotations

from typing import Any


def completion_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        return "".join(str(m.get("content", "")) for m in completion if isinstance(m, dict))
    if isinstance(completion, dict):
        return str(completion.get("content", ""))
    return str(completion)


def batch_texts(completions: list[Any]) -> list[str]:
    return [completion_text(item) for item in completions]


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def contains_direct_recommendation(text: str, patterns: list[str]) -> bool:
    """Detect direct recommendation while avoiding negated compliance statements."""
    negations = ["不能", "不得", "不应", "无法", "不宜", "不要"]
    for pattern in patterns:
        start = text.find(pattern)
        while start != -1:
            context = text[max(0, start - 8) : start]
            if not any(negation in context for negation in negations):
                return True
            start = text.find(pattern, start + len(pattern))
    return False


def count_terms(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term in text)


def clip(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
