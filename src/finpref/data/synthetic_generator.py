"""Template-based SFT data generator."""

from __future__ import annotations

import argparse
from itertools import islice, cycle
from typing import Any

from finpref.data.formatters import as_sft_row
from finpref.utils.io import read_jsonl, write_jsonl


def build_answer(row: dict[str, Any]) -> str:
    meta = row["meta"]
    product = row["product_info"]
    profile = row["user_profile"]
    parts: list[str] = []
    if meta.get("requires_clarification"):
        parts.append("目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。")
    elif meta.get("risk_mismatch"):
        parts.append(
            f"从适当性看，需要谨慎。该产品风险等级为{product['risk_level']}，"
            f"而你的风险承受能力为{profile['risk_tolerance']}，存在风险不匹配。"
        )
    else:
        parts.append(
            f"可以把该产品作为了解对象，但不应直接做买卖决定。需要结合你的{profile['investment_horizon']}期限、"
            f"{profile['liquidity_need']}流动性需求和风险承受能力综合判断。"
        )
    parts.append(
        f"该产品可能涉及净值波动、本金损失、流动性和费用等风险，具体以产品说明书和风险揭示文件为准。"
    )
    if row["query_type"] in {"yield_promise", "direct_recommendation"}:
        parts.append("我不能承诺收益，也不能给出直接买入或卖出的指令；更合规的做法是提供风险分析和决策框架。")
    else:
        parts.append("下一步可以比较低风险、高流动性替代方案，并咨询持牌专业人员。")
    parts.append("以上仅用于模型研究场景，不构成投资建议。")
    return "".join(parts)


def generate_sft(seed_rows: list[dict[str, Any]], num_samples: int) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(islice(cycle(seed_rows), num_samples), start=1):
        rows.append(as_sft_row(row, build_answer(row), f"sft_{idx:06d}"))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_file", default="data/interim/seed_cases.jsonl")
    parser.add_argument("--output", default="data/processed/sft_train.jsonl")
    parser.add_argument("--num_samples", type=int, default=3000)
    args = parser.parse_args()
    write_jsonl(args.output, generate_sft(read_jsonl(args.seed_file), args.num_samples))


if __name__ == "__main__":
    main()

