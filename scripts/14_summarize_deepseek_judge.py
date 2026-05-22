"""Summarize DeepSeek judge sample scores."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from finpref.utils.io import ensure_parent, read_jsonl


SCORE_FIELDS = [
    "factuality",
    "compliance",
    "suitability",
    "risk_disclosure",
    "helpfulness",
    "over_refusal",
    "verbosity",
    "reward_hacking",
    "overall",
]


def mean(rows: list[dict[str, Any]], field: str) -> float:
    return round(sum(float(row.get(field, 0)) for row in rows) / len(rows), 3)


def model_name(path: Path) -> str:
    return path.name.removesuffix("_deepseek_judge_scores.jsonl")


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "n", *SCORE_FIELDS])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: str, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    headers = ["Model", "N", "Overall", "Compliance", "Suitability", "Risk", "Helpful", "Over-refusal", "Reward hacking"]
    lines = ["# P1 DeepSeek Judge Sample", "", "|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append(
            "|"
            + "|".join(
                [
                    str(row["model"]),
                    str(row["n"]),
                    str(row["overall"]),
                    str(row["compliance"]),
                    str(row["suitability"]),
                    str(row["risk_disclosure"]),
                    str(row["helpfulness"]),
                    str(row["over_refusal"]),
                    str(row["reward_hacking"]),
                ]
            )
            + "|"
        )
    lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval_dir", default="outputs/eval/deepseek_judge_sample")
    parser.add_argument("--output_csv", default="outputs/eval/deepseek_judge_sample/summary.csv")
    parser.add_argument("--output_md", default="reports/p1_deepseek_judge_sample.md")
    args = parser.parse_args()

    rows = []
    for score_file in sorted(Path(args.eval_dir).glob("*_deepseek_judge_scores.jsonl")):
        scores = read_jsonl(score_file)
        if not scores:
            continue
        rows.append({"model": model_name(score_file), "n": len(scores), **{field: mean(scores, field) for field in SCORE_FIELDS}})

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, rows)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
