"""Dataclasses and schema helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from finpref.constants import QUERY_TYPES


@dataclass(frozen=True)
class UserProfile:
    age: int
    income_stability: str
    risk_tolerance: str
    investment_horizon: str
    liquidity_need: str
    investment_experience: str
    objective: str
    loss_tolerance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductInfo:
    product_type: str
    risk_level: str
    liquidity: str
    volatility: str
    fees: str
    lockup_period: str
    principal_protection: bool
    complexity: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinancialCase:
    id: str
    query_type: str
    query: str
    user_profile: UserProfile
    product_info: ProductInfo
    expected_behavior: list[str] = field(default_factory=list)
    forbidden_behavior: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.query_type not in QUERY_TYPES:
            raise ValueError(f"Unsupported query_type: {self.query_type}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["user_profile"] = self.user_profile.to_dict()
        data["product_info"] = self.product_info.to_dict()
        return data

