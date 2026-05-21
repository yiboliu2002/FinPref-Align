"""Generate simple badcase markdown reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from finpref.eval.rule_eval import evaluate_response
from finpref.utils.io import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred_file", required=False)
    parser.add_argument("--output_dir", default="reports/badcases")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.pred_file:
        print("Provide --pred_file to generate reports.")
        return
    rows = read_jsonl(args.pred_file)
    failures = []
    for row in rows:
        text = row.get("response") or row.get("answer") or row.get("output") or ""
        metrics = evaluate_response(text, row.get("meta", {}))
        if not metrics["compliance_pass"] or not metrics["suitability_match"] or metrics["over_refusal"]:
            failures.append((row, metrics))
    content = ["# Badcases", ""]
    for row, metrics in failures[:50]:
        content.extend([f"## {row.get('id')}", "", "```text", row.get("response", ""), "```", "", f"Metrics: `{metrics}`", ""])
    (output_dir / "badcases.md").write_text("\n".join(content), encoding="utf-8")


if __name__ == "__main__":
    main()

