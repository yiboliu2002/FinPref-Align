"""Summarize P1-public v3 rule-eval results against prior P1-public runs."""

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
    failures: dict[str, list[str]] = {}
    for fail_name, detail_field in DETAIL_FAIL_FIELDS.items():
        failures[fail_name] = [str(row.get("id")) for row in rows if not row.get(detail_field)]
    return failures


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", *METRIC_FIELDS])
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    headers = ["Model", "Compliance", "Risk", "Suitability", "Clarification", "Over-refusal", "Length"]
    lines = [
        "|" + "|".join(headers) + "|",
        "|" + "|".join(["---"] * len(headers)) + "|",
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
    return lines


def write_summary_markdown(path: Path, rows: list[dict[str, Any]], overlap: dict[str, Any]) -> None:
    target = ensure_parent(path)
    lines = ["# P1-public v3 Rule Summary", "", *markdown_table(rows)]

    lines.extend(
        [
            "",
            "## Failure Counts",
            "",
            "|Model|Compliance fail|Risk fail|Suitability fail|Clarification fail|",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, failures in overlap["failures"].items():
        lines.append(
            "|"
            + "|".join(
                [
                    name,
                    str(len(failures["compliance_fail"])),
                    str(len(failures["risk_fail"])),
                    str(len(failures["suitability_fail"])),
                    str(len(failures["clarification_fail"])),
                ]
            )
            + "|"
        )

    for label, diff in [("v2 vs v3 DPO", overlap["v2_vs_v3"]), ("v1 vs v3 DPO", overlap["v1_vs_v3"])]:
        lines.extend(
            [
                "",
                f"## {label}",
                "",
                f"- previous risk fail count: `{diff['prev_risk_fail_count']}`",
                f"- v3 risk fail count: `{diff['v3_risk_fail_count']}`",
                f"- shared risk fail count: `{diff['shared_risk_fail_count']}`",
                f"- v3 fixed risk fail ids: `{diff['v3_fixed_risk_fail_ids']}`",
                f"- v3 new risk fail ids: `{diff['v3_new_risk_fail_ids']}`",
                f"- previous suitability fail count: `{diff['prev_suitability_fail_count']}`",
                f"- v3 suitability fail count: `{diff['v3_suitability_fail_count']}`",
                f"- shared suitability fail count: `{diff['shared_suitability_fail_count']}`",
                f"- v3 fixed suitability fail ids: `{diff['v3_fixed_suitability_fail_ids']}`",
                f"- v3 new suitability fail ids: `{diff['v3_new_suitability_fail_ids']}`",
            ]
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in read_jsonl(path)}


def excerpt(text: str, limit: int = 700) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def write_failure_spotcheck(path: Path, v2_dir: Path, v3_dir: Path, overlap: dict[str, Any]) -> None:
    target = ensure_parent(path)
    v2_outputs = by_id(v2_dir / "dpo_outputs.jsonl")
    v3_outputs = by_id(v3_dir / "dpo_outputs.jsonl")
    v2_details = by_id(v2_dir / "dpo_rule_details.jsonl")
    v3_details = by_id(v3_dir / "dpo_rule_details.jsonl")
    focus_ids = sorted(
        set(overlap["v2_vs_v3"]["v3_new_suitability_fail_ids"])
        | set(overlap["v2_vs_v3"]["v3_fixed_risk_fail_ids"])
        | set(overlap["failures"]["P1-public DPO v3"]["suitability_fail"])
        | set(overlap["failures"]["P1-public DPO v3"]["risk_fail"])
    )

    lines = [
        "# P1-public v3 Failure Spot-check",
        "",
        f"- focus ids: `{focus_ids}`",
        f"- v3 risk fail ids: `{overlap['failures']['P1-public DPO v3']['risk_fail']}`",
        f"- v3 suitability fail ids: `{overlap['failures']['P1-public DPO v3']['suitability_fail']}`",
        "",
    ]
    for sample_id in focus_ids:
        v2_out = v2_outputs.get(sample_id, {})
        v3_out = v3_outputs.get(sample_id, {})
        lines.extend(
            [
                f"## {sample_id}",
                "",
                f"- meta: `{json.dumps(v3_out.get('meta', {}), ensure_ascii=False)}`",
                f"- v2 rule: `{json.dumps(v2_details.get(sample_id, {}), ensure_ascii=False)}`",
                f"- v3 rule: `{json.dumps(v3_details.get(sample_id, {}), ensure_ascii=False)}`",
                "",
                "### v2 response",
                "",
                excerpt(v2_out.get("response", "")),
                "",
                "### v3 response",
                "",
                excerpt(v3_out.get("response", "")),
                "",
            ]
        )
    target.write_text("\n".join(lines), encoding="utf-8")


def diff_failures(prev: dict[str, list[str]], v3: dict[str, list[str]]) -> dict[str, Any]:
    prev_risk = set(prev["risk_fail"])
    v3_risk = set(v3["risk_fail"])
    prev_suitability = set(prev["suitability_fail"])
    v3_suitability = set(v3["suitability_fail"])
    return {
        "prev_risk_fail_count": len(prev_risk),
        "v3_risk_fail_count": len(v3_risk),
        "shared_risk_fail_count": len(prev_risk & v3_risk),
        "v3_fixed_risk_fail_ids": sorted(prev_risk - v3_risk),
        "v3_new_risk_fail_ids": sorted(v3_risk - prev_risk),
        "prev_suitability_fail_count": len(prev_suitability),
        "v3_suitability_fail_count": len(v3_suitability),
        "shared_suitability_fail_count": len(prev_suitability & v3_suitability),
        "v3_fixed_suitability_fail_ids": sorted(prev_suitability - v3_suitability),
        "v3_new_suitability_fail_ids": sorted(v3_suitability - prev_suitability),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1_dir", default="outputs/eval/p1_public")
    parser.add_argument("--v2_dir", default="outputs/eval/p1_public_v2")
    parser.add_argument("--v3_dir", default="outputs/eval/p1_public_v3")
    parser.add_argument("--output_csv", default="outputs/eval/p1_public_v3/rule_summary.csv")
    parser.add_argument("--output_json", default="outputs/eval/p1_public_v3/failure_overlap.json")
    parser.add_argument("--output_md", default="reports/p1_public_v3_rule_summary.md")
    parser.add_argument("--spotcheck_md", default="reports/p1_public_v3_failure_spotcheck.md")
    args = parser.parse_args()

    p1_dir = Path(args.p1_dir)
    v2_dir = Path(args.v2_dir)
    v3_dir = Path(args.v3_dir)
    metric_paths = {
        "Base": p1_dir / "base_rule_metrics.json",
        "P1-public SFT": p1_dir / "sft_rule_metrics.json",
        "P1-public DPO v1": p1_dir / "dpo_rule_metrics.json",
        "P1-public DPO v2": v2_dir / "dpo_rule_metrics.json",
        "P1-public DPO v3": v3_dir / "dpo_rule_metrics.json",
    }
    detail_paths = {
        "Base": p1_dir / "base_rule_details.jsonl",
        "P1-public SFT": p1_dir / "sft_rule_details.jsonl",
        "P1-public DPO v1": p1_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v2": v2_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v3": v3_dir / "dpo_rule_details.jsonl",
    }

    rows = [metric_row(name, path) for name, path in metric_paths.items()]
    failures = {name: failure_ids(path) for name, path in detail_paths.items()}
    overlap = {
        "failures": failures,
        "v2_vs_v3": diff_failures(failures["P1-public DPO v2"], failures["P1-public DPO v3"]),
        "v1_vs_v3": diff_failures(failures["P1-public DPO v1"], failures["P1-public DPO v3"]),
    }

    write_csv(Path(args.output_csv), rows)
    ensure_parent(Path(args.output_json)).write_text(json.dumps(overlap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary_markdown(Path(args.output_md), rows, overlap)
    write_failure_spotcheck(Path(args.spotcheck_md), v2_dir, v3_dir, overlap)
    for row in rows:
        print(row)
    print(json.dumps(overlap["v2_vs_v3"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
