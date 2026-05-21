"""Build held-out eval data from seed cases."""

from __future__ import annotations

import argparse
from itertools import cycle, islice

from finpref.data.formatters import prompt_messages
from finpref.utils.io import read_jsonl, write_jsonl


def generate_eval(seed_rows: list[dict], num_cases: int) -> list[dict]:
    rows = []
    for idx, row in enumerate(islice(cycle(seed_rows), num_cases), start=1):
        rows.append(
            {
                "id": f"eval_{idx:06d}",
                "messages": prompt_messages(row),
                "expected_behavior": row.get("expected_behavior", []),
                "forbidden_behavior": row.get("forbidden_behavior", []),
                "meta": {**row.get("meta", {}), "difficulty": "easy"},
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_file", default="data/interim/seed_cases.jsonl")
    parser.add_argument("--output", default="data/processed/eval_finpref.jsonl")
    parser.add_argument("--num_cases", type=int, default=300)
    args = parser.parse_args()
    write_jsonl(args.output, generate_eval(read_jsonl(args.seed_file), args.num_cases))


if __name__ == "__main__":
    main()

