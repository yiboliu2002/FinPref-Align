"""Summarize P1 DPO sweep metrics.

The summary keeps the P1 sweep easy to compare with the P0 SFT checkpoint:
for each DPO variant it records headline rule metrics, total badcases, and
how many examples pass under SFT but fail under the variant.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from finpref.utils.io import ensure_parent, read_jsonl, write_json


SUMMARY_FIELDS = [
    "model",
    "beta",
    "total",
    "compliance_pass_rate",
    "risk_disclosure_coverage",
    "suitability_match_rate",
    "forbidden_phrase_rate",
    "over_refusal_rate",
    "reward_hacking_rate",
    "avg_response_length",
    "badcase_count",
    "sft_pass_variant_fail_count",
]


def is_pass(details: dict[str, Any]) -> bool:
    return (
        bool(details.get("compliance_pass"))
        and bool(details.get("suitability_match"))
        and not bool(details.get("over_refusal"))
        and not bool(details.get("reward_hacking"))
    )


def beta_from_name(name: str) -> float | None:
    match = re.search(r"beta_([0-9]+(?:_[0-9]+)?)", name)
    if not match:
        return None
    return float(match.group(1).replace("_", "."))


def format_beta(beta: float | None) -> str:
    return "" if beta is None else f"{beta:g}"


def load_baseline(path: str | None) -> dict[Any, dict[str, Any]]:
    if not path:
        return {}
    return {row.get("id"): row for row in read_jsonl(path)}


def variant_summary(metric_file: Path, baseline: dict[Any, dict[str, Any]]) -> tuple[dict[str, Any], list[Any]]:
    model = metric_file.name.removesuffix("_rule_metrics.json")
    metrics = json.loads(metric_file.read_text(encoding="utf-8"))
    details_file = metric_file.with_name(f"{model}_rule_details.jsonl")
    details = read_jsonl(details_file) if details_file.exists() else []
    variant_fail_ids = [row.get("id") for row in details if not is_pass(row)]
    sft_pass_variant_fail_ids = [
        row.get("id")
        for row in details
        if row.get("id") in baseline and is_pass(baseline[row.get("id")]) and not is_pass(row)
    ]
    beta = beta_from_name(model)
    row = {
        "model": model,
        "beta": format_beta(beta),
        "badcase_count": len(variant_fail_ids),
        "sft_pass_variant_fail_count": len(sft_pass_variant_fail_ids),
        **{key: metrics.get(key, "") for key in SUMMARY_FIELDS if key not in {"model", "beta", "badcase_count", "sft_pass_variant_fail_count"}},
    }
    return row, sft_pass_variant_fail_ids


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: str, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    headers = [
        "Model",
        "Beta",
        "Compliance",
        "Risk",
        "Suitability",
        "Badcases",
        "SFT-pass / Variant-fail",
        "Avg Len",
    ]
    lines = ["# P1 DPO Beta Sweep", "", "|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append(
            "|"
            + "|".join(
                [
                    str(row["model"]),
                    str(row["beta"]),
                    str(row["compliance_pass_rate"]),
                    str(row["risk_disclosure_coverage"]),
                    str(row["suitability_match_rate"]),
                    str(row["badcase_count"]),
                    str(row["sft_pass_variant_fail_count"]),
                    str(row["avg_response_length"]),
                ]
            )
            + "|"
        )
    lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval_dir", default="outputs/eval/p1_beta_sweep")
    parser.add_argument("--baseline_details", default="outputs/eval/sft_rule_details.jsonl")
    parser.add_argument("--output_csv", default="outputs/eval/p1_beta_sweep/summary.csv")
    parser.add_argument("--output_md", default="reports/p1_beta_sweep.md")
    parser.add_argument("--output_json", default="outputs/eval/p1_beta_sweep/sft_pass_variant_fail_ids.json")
    args = parser.parse_args()

    eval_dir = Path(args.eval_dir)
    baseline = load_baseline(args.baseline_details if Path(args.baseline_details).exists() else None)
    rows = []
    fail_ids: dict[str, list[Any]] = {}
    for metric_file in sorted(eval_dir.glob("*_rule_metrics.json"), key=lambda path: (beta_from_name(path.name) is None, beta_from_name(path.name) or 0.0, path.name)):
        row, ids = variant_summary(metric_file, baseline)
        rows.append(row)
        fail_ids[row["model"]] = ids

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, rows)
    write_json(args.output_json, fail_ids)
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
