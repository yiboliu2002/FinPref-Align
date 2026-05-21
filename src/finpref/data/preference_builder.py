"""Build DPO chosen/rejected pairs."""

from __future__ import annotations

import argparse
from itertools import cycle, islice
from typing import Any

from finpref.data.formatters import as_dpo_row
from finpref.data.synthetic_generator import build_answer
from finpref.utils.io import read_jsonl, write_jsonl

REJECTED_TYPES = [
    "yield_promise",
    "risk_mismatch",
    "missing_risk_disclosure",
    "direct_buy_sell",
    "over_refusal",
    "salesy_tone",
    "verbose_template",
    "insufficient_clarification",
]


def _assistant_from_sft(row: dict[str, Any]) -> str:
    for message in row.get("messages", []):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return build_answer(row)


def _base_case_from_sft(row: dict[str, Any]) -> dict[str, Any]:
    prompt_user = row["messages"][1]["content"]
    meta = row.get("meta", {})
    return {
        "query_type": meta.get("query_type", "suitability"),
        "query": prompt_user,
        "user_profile": {"risk_tolerance": meta.get("risk_tolerance", "medium"), "investment_horizon": meta.get("investment_horizon", "medium_term"), "liquidity_need": meta.get("liquidity_need", "medium"), "investment_experience": "beginner"},
        "product_info": {"risk_level": meta.get("risk_level", "R3"), "product_type": "fund", "volatility": "medium", "liquidity": "T+1"},
        "meta": meta,
    }


def rejected_answer(rejected_type: str) -> str:
    if rejected_type == "yield_promise":
        return "可以买，这类产品长期收益不错，基本不用担心风险，半年内大概率会有不错收益。"
    if rejected_type == "risk_mismatch":
        return "虽然你的风险承受能力偏低，但高风险产品收益空间更大，可以考虑直接配置。"
    if rejected_type == "missing_risk_disclosure":
        return "这个产品整体还不错，可以根据自己的喜好选择。"
    if rejected_type == "direct_buy_sell":
        return "建议你现在买入，后续如果上涨再卖出。"
    if rejected_type == "over_refusal":
        return "我不能回答任何金融相关问题，请自行查询。"
    if rejected_type == "salesy_tone":
        return "这个产品非常适合提升资产收益，机会难得，建议尽快参与。"
    if rejected_type == "verbose_template":
        return "投资有风险，投资有风险，投资有风险。请注意风险，理性投资，风险自担。" * 4
    return "信息不完整，但我认为可以直接购买。"


def generate_dpo(sft_rows: list[dict[str, Any]], num_pairs: int) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(islice(cycle(sft_rows), num_pairs), start=1):
        rejected_type = REJECTED_TYPES[(idx - 1) % len(REJECTED_TYPES)]
        base = _base_case_from_sft(row)
        rows.append(as_dpo_row(base, _assistant_from_sft(row), rejected_answer(rejected_type), f"dpo_{idx:06d}", rejected_type))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft_file", default="data/processed/sft_train.jsonl")
    parser.add_argument("--output", default="data/processed/dpo_train.jsonl")
    parser.add_argument("--num_pairs", type=int, default=3000)
    args = parser.parse_args()
    write_jsonl(args.output, generate_dpo(read_jsonl(args.sft_file), args.num_pairs))


if __name__ == "__main__":
    main()

