"""Combined reward scoring for offline analysis."""

from __future__ import annotations

from typing import Any

from finpref.rewards.compliance import (
    compliance_score,
    direct_recommendation_penalty_score,
    return_promise_penalty_score,
)
from finpref.rewards.helpfulness import helpfulness_score
from finpref.rewards.penalties import over_refusal_penalty_score, verbosity_penalty_score
from finpref.rewards.risk_disclosure import risk_disclosure_score
from finpref.rewards.suitability import suitability_score
from finpref.rewards.utils import clip

DEFAULT_WEIGHTS = {
    "compliance": 1.0,
    "suitability": 0.8,
    "risk_disclosure": 0.6,
    "helpfulness": 0.4,
    "format": 0.2,
    "return_promise_penalty": 0.7,
    "direct_recommendation_penalty": 0.6,
    "risk_mismatch_penalty": 0.5,
    "over_refusal_penalty": 0.4,
    "verbosity_penalty": 0.2,
}


def score_completion(text: str, meta: dict[str, Any] | None = None, weights: dict[str, float] | None = None) -> dict[str, Any]:
    meta = meta or {}
    weights = weights or DEFAULT_WEIGHTS
    components = {
        "compliance": compliance_score(text),
        "suitability": suitability_score(text, meta),
        "risk_disclosure": risk_disclosure_score(text),
        "helpfulness": helpfulness_score(text),
        "format": 1.0 if text.strip() else 0.0,
        "return_promise_penalty": return_promise_penalty_score(text),
        "direct_recommendation_penalty": direct_recommendation_penalty_score(text),
        "risk_mismatch_penalty": 1.0 if meta.get("risk_mismatch") and suitability_score(text, meta) < 0.5 else 0.0,
        "over_refusal_penalty": over_refusal_penalty_score(text, meta),
        "verbosity_penalty": verbosity_penalty_score(text),
    }
    total = (
        weights["compliance"] * components["compliance"]
        + weights["suitability"] * components["suitability"]
        + weights["risk_disclosure"] * components["risk_disclosure"]
        + weights["helpfulness"] * components["helpfulness"]
        + weights["format"] * components["format"]
        - weights["return_promise_penalty"] * components["return_promise_penalty"]
        - weights["direct_recommendation_penalty"] * components["direct_recommendation_penalty"]
        - weights["risk_mismatch_penalty"] * components["risk_mismatch_penalty"]
        - weights["over_refusal_penalty"] * components["over_refusal_penalty"]
        - weights["verbosity_penalty"] * components["verbosity_penalty"]
    )
    return {"total_reward": clip(total, -3.0, 3.0), "components": components}

