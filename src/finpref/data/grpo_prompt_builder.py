"""Build prompt-only GRPO data."""

from __future__ import annotations

import argparse
from itertools import cycle, islice

from finpref.data.formatters import as_grpo_row
from finpref.utils.io import read_jsonl, write_jsonl


def generate_grpo(seed_rows: list[dict], num_prompts: int) -> list[dict]:
    return [
        as_grpo_row(row, f"grpo_{idx:06d}")
        for idx, row in enumerate(islice(cycle(seed_rows), num_prompts), start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_file", default="data/interim/seed_cases.jsonl")
    parser.add_argument("--output", default="data/processed/grpo_train.jsonl")
    parser.add_argument("--num_prompts", type=int, default=1000)
    args = parser.parse_args()
    write_jsonl(args.output, generate_grpo(read_jsonl(args.seed_file), args.num_prompts))


if __name__ == "__main__":
    main()

