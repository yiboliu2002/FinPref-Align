"""Inspect P1-public v4 repair-pair coverage."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpo_file", default="data/processed/dpo_train_p1_public_mix_v4.jsonl")
    parser.add_argument("--pair_source", default="public_v3_failure_repair")
    args = parser.parse_args()

    rows = [json.loads(line) for line in Path(args.dpo_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    repair_rows = [row for row in rows if row.get("meta", {}).get("pair_source") == args.pair_source]
    rejected_counts = Counter(row["meta"]["rejected_type"] for row in repair_rows)
    combo_counts = Counter(
        (
            row["meta"]["risk_level"],
            row["meta"]["risk_tolerance"],
            row["meta"]["query_type"],
            row["meta"]["rejected_type"],
        )
        for row in repair_rows
    )
    result = {
        "dpo_rows": len(rows),
        "repair_rows": len(repair_rows),
        "pair_source": args.pair_source,
        "rejected_type_counts": dict(rejected_counts),
        "combo_counts": {" | ".join(combo): count for combo, count in sorted(combo_counts.items())},
        "sample_chosen": repair_rows[0]["chosen"][0]["content"] if repair_rows else "",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
