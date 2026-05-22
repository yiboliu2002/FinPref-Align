"""Summarize P1-public v2 rule-eval results against prior P1-public runs."""

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


def write_markdown(path: Path, rows: list[dict[str, Any]], overlap: dict[str, Any]) -> None:
    target = ensure_parent(path)
    headers = ["Model", "Compliance", "Risk", "Suitability", "Clarification", "Over-refusal", "Length"]
    lines = [
        "# P1-public v2 Rule Summary",
        "",
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

    lines.extend(
        [
            "",
            "## v1 vs v2 DPO",
            "",
            f"- v1 risk fail ids: `{overlap['v1_vs_v2']['v1_risk_fail_count']}`",
            f"- v2 risk fail ids: `{overlap['v1_vs_v2']['v2_risk_fail_count']}`",
            f"- shared risk fail ids: `{overlap['v1_vs_v2']['shared_risk_fail_count']}`",
            f"- v1 suitability fail ids: `{overlap['v1_vs_v2']['v1_suitability_fail_count']}`",
            f"- v2 suitability fail ids: `{overlap['v1_vs_v2']['v2_suitability_fail_count']}`",
            f"- shared suitability fail ids: `{overlap['v1_vs_v2']['shared_suitability_fail_count']}`",
            "",
        ]
    )
    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1_dir", default="outputs/eval/p1_public")
    parser.add_argument("--v2_dir", default="outputs/eval/p1_public_v2")
    parser.add_argument("--output_csv", default="outputs/eval/p1_public_v2/rule_summary.csv")
    parser.add_argument("--output_json", default="outputs/eval/p1_public_v2/failure_overlap.json")
    parser.add_argument("--output_md", default="reports/p1_public_v2_rule_summary.md")
    args = parser.parse_args()

    p1_dir = Path(args.p1_dir)
    v2_dir = Path(args.v2_dir)
    metric_paths = {
        "Base": p1_dir / "base_rule_metrics.json",
        "P1-public SFT": p1_dir / "sft_rule_metrics.json",
        "P1-public DPO v1": p1_dir / "dpo_rule_metrics.json",
        "P1-public DPO v2": v2_dir / "dpo_rule_metrics.json",
    }
    detail_paths = {
        "Base": p1_dir / "base_rule_details.jsonl",
        "P1-public SFT": p1_dir / "sft_rule_details.jsonl",
        "P1-public DPO v1": p1_dir / "dpo_rule_details.jsonl",
        "P1-public DPO v2": v2_dir / "dpo_rule_details.jsonl",
    }

    rows = [metric_row(name, path) for name, path in metric_paths.items()]
    failures = {name: failure_ids(path) for name, path in detail_paths.items()}

    v1_risk = set(failures["P1-public DPO v1"]["risk_fail"])
    v2_risk = set(failures["P1-public DPO v2"]["risk_fail"])
    v1_suitability = set(failures["P1-public DPO v1"]["suitability_fail"])
    v2_suitability = set(failures["P1-public DPO v2"]["suitability_fail"])
    overlap = {
        "failures": failures,
        "v1_vs_v2": {
            "v1_risk_fail_count": len(v1_risk),
            "v2_risk_fail_count": len(v2_risk),
            "shared_risk_fail_count": len(v1_risk & v2_risk),
            "v2_fixed_risk_fail_ids": sorted(v1_risk - v2_risk),
            "v2_new_risk_fail_ids": sorted(v2_risk - v1_risk),
            "v1_suitability_fail_count": len(v1_suitability),
            "v2_suitability_fail_count": len(v2_suitability),
            "shared_suitability_fail_count": len(v1_suitability & v2_suitability),
            "v2_fixed_suitability_fail_ids": sorted(v1_suitability - v2_suitability),
            "v2_new_suitability_fail_ids": sorted(v2_suitability - v1_suitability),
        },
    }

    write_csv(Path(args.output_csv), rows)
    ensure_parent(Path(args.output_json)).write_text(json.dumps(overlap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(Path(args.output_md), rows, overlap)
    for row in rows:
        print(row)
    print(overlap["v1_vs_v2"])


if __name__ == "__main__":
    main()
