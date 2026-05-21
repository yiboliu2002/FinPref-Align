"""Format conversion helpers for TRL style datasets."""

from __future__ import annotations

from typing import Any

from finpref.constants import SYSTEM_PROMPT


def user_content(row: dict[str, Any]) -> str:
    profile = row["user_profile"]
    product = row["product_info"]
    return (
        f"用户画像：风险承受能力{profile['risk_tolerance']}，投资期限{profile['investment_horizon']}，"
        f"流动性需求{profile['liquidity_need']}，投资经验{profile['investment_experience']}。"
        f"产品信息：{product['product_type']}，风险等级{product['risk_level']}，"
        f"波动{product['volatility']}，赎回/流动性{product['liquidity']}。"
        f"问题：{row['query']}"
    )


def prompt_messages(row: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content(row)},
    ]


def as_sft_row(row: dict[str, Any], answer: str, sample_id: str) -> dict[str, Any]:
    return {
        "id": sample_id,
        "messages": prompt_messages(row) + [{"role": "assistant", "content": answer}],
        "meta": row["meta"],
    }


def as_dpo_row(row: dict[str, Any], chosen: str, rejected: str, sample_id: str, rejected_type: str) -> dict[str, Any]:
    return {
        "id": sample_id,
        "prompt": prompt_messages(row),
        "chosen": [{"role": "assistant", "content": chosen}],
        "rejected": [{"role": "assistant", "content": rejected}],
        "meta": {**row["meta"], "rejected_type": rejected_type},
    }


def as_grpo_row(row: dict[str, Any], sample_id: str) -> dict[str, Any]:
    return {
        "id": sample_id,
        "prompt": prompt_messages(row),
        "expected_behavior": row.get("expected_behavior", []),
        "forbidden_behavior": row.get("forbidden_behavior", []),
        "meta": row["meta"],
    }

