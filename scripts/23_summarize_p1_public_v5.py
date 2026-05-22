"""Summarize P1-public v5 rule-eval results against prior public DPO runs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


METRIC_FIELDS = [
    "compliance_pass_rate",
    "risk_disclosure_coverage",
    "suitability_match_rate",
    "clarification_rate",
    "over_refusal_rate",
    "forbidden_phrase_rate",
    "reward_hacking_rate",
    "avg_response_length",
]

DETAIL_FAIL_FIELDS = {
    "compliance_fail": "compliance_pass",
    "risk_fail": "risk_disclosure",
    "suitability_fail": "suitability_match",
    "clarification_fail": "clarification",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def metric_row(name: str, path: Path) -> dict[str, Any]:
    metrics = read_json(path)
    return {"model": name, **{field: metrics.get(field) for field in METRIC_FIELDS}}


def failure_ids(path: Path) -> dict[str, list[str]]:
    rows = read_jsonl(path)
    return {
        fail_name: [str(row.get("id")) for row in rows if not row.get(detail_field)]
        for fail_name, detail_field in DETAIL_FAIL_FIELDS.items()
    }


def diff_failures(prev: dict[str, list[str]], current: dict[str, list[str]], current_label: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for fail_name in ["risk_fail", "suitability_fail", "clarification_fail"]:
        prev_set = set(prev[fail_name])
        cur_set = set(current[fail_name])
        stem = fail_name.replace("_fail", "")
        result[f"prev_{stem}_fail_count"] = len(prev_set)
        result[f"{current_label}_{stem}_fail_count"] = len(cur_set)
        result[f"shared_{stem}_fail_count"] = len(prev_set & cur_set)
        result[f"{current_label}_fixed_{stem}_fail_ids"] = sorted(prev_set - cur_set)
        result[f"{current_label}_new_{stem}_fail_ids"] = sorted(cur_set - prev_set)
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", *METRIC_FIELDS])
        writer.writeheader()
        writer.writerows(rows)


def by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in read_jsonl(path)}


def excerpt(text: str, limit: int = 700) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def write_markdown(path: Path, rows: list[dict[str, Any]], overlap: dict[str, Any]) -> None:
    lines = [
        "# P1-public v5 Rule Summary",
        "",
        "|Model|Compliance|Risk|Suitability|Clarification|Over-refusal|Length|",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "|"
            + "|".join(
                [
                    str(row["model"]),
                    str(row["compliance_pass_rate"]),
                    str(row["risk_disclosure_coverage"]),
                    str(row["suitability_match_rate"]),
                    str(row["clarification_rate"]),
                    str(row["over_refusal_rate"]),
                    str(row["avg_response_length"]),
                ]
            )
            + "|"
        )
    lines.extend(["", "## Failure Counts", "", "|Model|Risk fail|Suitability fail|Clarification fail|", "|---|---:|---:|---:|"])
    for name, failures in overlap["failures"].items():
        lines.append(
            "|"
            + "|".join(
                [
                    name,
                    str(len(failures["risk_fail"])),
                    str(len(failures["suitability_fail"])),
                    str(len(failures["clarification_fail"])),
                ]
            )
            + "|"
        )
    for label, diff in overlap["diffs"].items():
        lines.extend(["", f"## {label}", "", "```json", json.dumps(diff, ensure_ascii=False, indent=2), "```"])
    ensure_parent(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_spotcheck(path: Path, compare_dirs: dict[str, Path], failures: dict[str, dict[str, list[str]]]) -> None:
    focus_ids = sorted(set(failures["P1-public DPO v5"]["risk_fail"]) | set(failures["P1-public DPO v5"]["suitability_fail"]))
    outputs = {name: by_id(directory / "dpo_outputs.jsonl") for name, directory in compare_dirs.items()}
    details = {name: by_id(directory / "dpo_rule_details.jsonl") for name, directory in compare_dirs.items()}
    lines = [
        "# P1-public v5 Failure Spot-check",
        "",
        f"- focus ids: `{focus_ids}`",
        f"- v5 risk fail ids: `{failures['P1-public DPO v5']['risk_fail']}`",
        f"- v5 suitability fail ids: `{failures['P1-public DPO v5']['suitability_fail']}`",
        "",
    ]
    for sample_id in focus_ids:
        lines.extend([f"## {sample_id}", ""])
        for name in ["P1-public DPO v2", "P1-public DPO v3", "P1-public DPO v4", "P1-public DPO v5"]:
            row = outputs[name].get(sample_id, {})
            detail = details[name].get(sample_id, {})
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- meta: `{json.dumps(row.get('meta', {}), ensure_ascii=False)}`",
                    f"- rule: `{json.dumps(detail, ensure_ascii=False)}`",
                    "",
                    excerpt(row.get("response", "")),
                    "",
                ]
            )
    ensure_parent(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1_dir", default="outputs/eval/p1_public")
    parser.add_argument("--v2_dir", default="outputs/eval/p1_public_v2")
    parser.add_argument("--v3_dir", default="outputs/eval/p1_public_v3")
    parser.add_argument("--v4_dir", default="outputs/eval/p1_public_v4")
    parser.add_argument("--v5_dir", default="outputs/eval/p1_public_v5")
    parser.add_argument("--output_csv", default="outputs/eval/p1_public_v5/rule_summary.csv")
    parser.add_argument("--output_json", default="outputs/eval/p1_public_v5/failure_overlap.json")
    parser.add_argument("--output_md", default="reports/p1_public_v5_rule_summary.md")
    parser.add_argument("--spotcheck_md", default="reports/p1_public_v5_failure_spotcheck.md")
    args = parser.parse_args()

    p1_dir = Path(args.p1_dir)
    v2_dir = Path(args.v2_dir)
    v3_dir = Path(args.v3_dir)
    v4_dir = Path(args.v4_dir)
    v5_dir = Path(args.v5_dir)
    metric_paths = {
        "Base": p1_dir / "base_rule_metrics.json",
        "P1-public SFT": p1_dir / "sft_rule_metrics.json",
        "P1-public DPO v1": p1_dir / "dpo_rule_metrics.json",
        "P1-public DPO v2": v2_dir / "dpo_rule_metrics.json",
        "P1-public DPO v3": v3_dir / "dpo_rule_metrics.json",
        "P1-public DPO v4": v4_dir / "dpo_rule_metrics.json",
        "P1-public DPO v5": v5_dir / "dpo_rule_metrics.json",
    }
    detail_paths = {
        "Base": p1_dir / "base_rule_details.jsonl",
        "P1-public SFT": p1_dir / "sft_rule_details.jsonl",
        "P1-public DPO v1": p1_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v2": v2_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v3": v3_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v4": v4_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v5": v5_dir / "dpo_rule_details.jsonl",
    }
    rows = [metric_row(name, path) for name, path in metric_paths.items()]
    failures = {name: failure_ids(path) for name, path in detail_paths.items()}
    overlap = {
        "failures": failures,
        "diffs": {
            "v2 vs v5": diff_failures(failures["P1-public DPO v2"], failures["P1-public DPO v5"], "v5"),
            "v3 vs v5": diff_failures(failures["P1-public DPO v3"], failures["P1-public DPO v5"], "v5"),
            "v4 vs v5": diff_failures(failures["P1-public DPO v4"], failures["P1-public DPO v5"], "v5"),
        },
    }
    write_csv(Path(args.output_csv), rows)
    ensure_parent(Path(args.output_json)).write_text(json.dumps(overlap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(Path(args.output_md), rows, overlap)
    write_spotcheck(
        Path(args.spotcheck_md),
        {
            "P1-public DPO v2": v2_dir,
            "P1-public DPO v3": v3_dir,
            "P1-public DPO v4": v4_dir,
            "P1-public DPO v5": v5_dir,
        },
        failures,
    )
    for row in rows:
        print(row)
    print(json.dumps(overlap["diffs"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
