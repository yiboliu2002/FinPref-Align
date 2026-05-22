"""Write a spot-check report for P1-public v2 DPO rule-eval failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import shorten
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in read_jsonl(path)}


def clip(text: str, width: int = 360) -> str:
    return shorten(" ".join(text.split()), width=width, placeholder=" ...")


def case_block(
    case_id: str,
    v2_out: dict[str, dict[str, Any]],
    v1_out: dict[str, dict[str, Any]],
    v2_details: dict[str, dict[str, Any]],
    v1_details: dict[str, dict[str, Any]],
) -> list[str]:
    row = v2_out[case_id]
    meta = row.get("meta", {})
    user = row.get("messages", [{}])[-1].get("content", "")
    lines = [
        f"### {case_id}",
        "",
        f"- query_type: `{meta.get('query_type')}`",
        f"- risk_level / tolerance: `{meta.get('risk_level')}` / `{meta.get('risk_tolerance')}`",
        f"- risk_mismatch: `{meta.get('risk_mismatch')}`",
        f"- requires_clarification: `{meta.get('requires_clarification')}`",
        f"- v2 rule flags: `{v2_details[case_id]}`",
        f"- v1 rule flags: `{v1_details.get(case_id)}`",
        "",
        f"用户问题：{clip(user, 300)}",
        "",
        f"v2 回复：{clip(row.get('response', ''), 420)}",
        "",
        f"v1 回复：{clip(v1_out.get(case_id, {}).get('response', ''), 420)}",
        "",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1_dir", default="outputs/eval/p1_public")
    parser.add_argument("--v2_dir", default="outputs/eval/p1_public_v2")
    parser.add_argument("--output_md", default="reports/p1_public_v2_failure_spotcheck.md")
    args = parser.parse_args()

    p1_dir = Path(args.p1_dir)
    v2_dir = Path(args.v2_dir)
    overlap = read_json(v2_dir / "failure_overlap.json")
    v1_vs_v2 = overlap["v1_vs_v2"]

    v1_out = by_id(p1_dir / "dpo_outputs.jsonl")
    v2_out = by_id(v2_dir / "dpo_outputs.jsonl")
    v1_details = by_id(p1_dir / "dpo_rule_details.jsonl")
    v2_details = by_id(v2_dir / "dpo_rule_details.jsonl")

    new_risk = v1_vs_v2["v2_new_risk_fail_ids"]
    new_suitability = v1_vs_v2["v2_new_suitability_fail_ids"]
    shared_suitability = sorted(
        set(overlap["failures"]["P1-public DPO v1"]["suitability_fail"])
        & set(overlap["failures"]["P1-public DPO v2"]["suitability_fail"])
    )

    lines = [
        "# P1-public v2 Failure Spot-check",
        "",
        "## 结论",
        "",
        "- v2 的主方向是正确的：它修复了 v1 的全部 12 个 risk-disclosure rule fail，并把 DeepSeek sample30 overall 提到 4.3。",
        "- 剩余失败不是随机噪声，主要集中在两个模式。",
        "- 模式 A：`insufficient_info + risk_mismatch` 中，模型会明确风险不匹配或不能直接判断，但有时漏掉“净值波动 / 流动性 / 费用 / 本金损失”等具体风险词，导致 risk-disclosure rule fail。",
        "- 模式 B：`compliance_boundary + risk_mismatch` 中，模型给了泛化谨慎话术，但没有明确写出“风险等级与风险承受能力不匹配 / 不适合 / 需谨慎”，导致 suitability rule fail。",
        "- 这说明 v2 preference pairs 已修复“具体风险披露不足”的大头，但下一轮需要同时绑定三件事：澄清、具体风险、适当性不匹配。",
        "",
        "## 指标定位",
        "",
        f"- v1 risk fail: `{v1_vs_v2['v1_risk_fail_count']}`",
        f"- v2 risk fail: `{v1_vs_v2['v2_risk_fail_count']}`",
        f"- v2 new risk fail ids: `{', '.join(new_risk)}`",
        f"- v2 new suitability fail ids: `{', '.join(new_suitability)}`",
        f"- shared suitability fail ids: `{', '.join(shared_suitability)}`",
        "",
        "## 模式 A：新增 risk fail",
        "",
        "这些样本都指出了风险不匹配，但没有列出足够具体的风险项。v1 在这些样本上通常有具体风险披露，但没有明确适当性不匹配；v2 则把适当性补上了，却牺牲了具体风险项。",
        "",
    ]
    for case_id in new_risk:
        lines.extend(case_block(case_id, v2_out, v1_out, v2_details, v1_details))

    lines.extend(
        [
            "## 模式 B：新增 suitability fail",
            "",
            "这些样本都是低风险用户面对 R4 equity fund。v2 回复有风险披露，但只说“作为了解对象”“综合判断”，没有明确点出风险等级与用户风险承受能力不匹配。",
            "",
        ]
    )
    for case_id in new_suitability:
        lines.extend(case_block(case_id, v2_out, v1_out, v2_details, v1_details))

    lines.extend(
        [
            "## 持续存在的 suitability fail",
            "",
            "这些样本在 SFT、v1、v2 中都倾向于只要求补充信息，而没有同步指出已知的风险不匹配。它们适合作为下一版 hard negative 的重点来源。",
            "",
        ]
    )
    for case_id in shared_suitability:
        lines.extend(case_block(case_id, v2_out, v1_out, v2_details, v1_details))

    lines.extend(
        [
            "## v3 数据修补建议",
            "",
            "- 新增或加权 hard negative：`asks_clarification_but_omits_mismatch`，用于惩罚只问画像、不点出已知风险不匹配的回复。",
            "- 新增或加权 hard negative：`mismatch_caution_without_specific_risks`，用于惩罚只说不匹配但不列具体风险项的回复。",
            "- 对 `risk_mismatch=True` 的 chosen 模板强制加入中文显式短语：`风险等级与风险承受能力不匹配`、`不适合直接买入`、`需谨慎评估` 中至少一个。",
            "- 对 `requires_clarification=True and should_disclose_risk=True` 的 chosen 模板强制同时包含澄清项和至少两个具体风险项。",
            "- 下一轮不要立刻扩大数据量，先做小规模 v3 data validation + 300-case eval，确认新增 6 个失败 ID 是否被修复。",
            "",
        ]
    )

    target = Path(args.output_md)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
