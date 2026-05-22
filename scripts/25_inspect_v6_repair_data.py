"""Inspect P1-public v6 repair-pair coverage."""

from __future__ import annotations

import argparse
import json
from collections import Counter

import _bootstrap  # noqa: F401
from finpref.utils.io import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpo_file", default="data/processed/dpo_train_p1_public_mix_v6.jsonl")
    parser.add_argument("--pair_source", default="public_v5_failure_repair")
    args = parser.parse_args()

    rows = read_jsonl(args.dpo_file)
    repair_rows = [row for row in rows if row.get("meta", {}).get("pair_source") == args.pair_source]
    rejected_counts = Counter(row["meta"]["rejected_type"] for row in repair_rows)
    case_counts = Counter(
        (
            row["meta"]["risk_level"],
            row["meta"]["risk_tolerance"],
            row["meta"]["query_type"],
            row["meta"]["risk_mismatch"],
            row["meta"]["rejected_type"],
        )
        for row in repair_rows
    )
    summary = {
        "dpo_rows": len(rows),
        "repair_rows": len(repair_rows),
        "pair_source": args.pair_source,
        "rejected_type_counts": dict(sorted(rejected_counts.items())),
        "case_counts": {json.dumps(k, ensure_ascii=False): v for k, v in sorted(case_counts.items())},
        "sample_chosen": repair_rows[0]["chosen"][0]["content"] if repair_rows else "",
        "sample_rejected": repair_rows[0]["rejected"][0]["content"] if repair_rows else "",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
