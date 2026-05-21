import argparse
import _bootstrap  # noqa: F401
from finpref.data.validators import validate_rows
from finpref.utils.io import read_jsonl, write_json


def _maybe_validate(kind: str, path: str | None) -> dict:
    if not path:
        return {"kind": kind, "skipped": True}
    return validate_rows(kind, read_jsonl(path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft_file", default="data/processed/sft_train.jsonl")
    parser.add_argument("--dpo_file", default="data/processed/dpo_train.jsonl")
    parser.add_argument("--grpo_file", default="data/processed/grpo_train.jsonl")
    parser.add_argument("--output", default="outputs/data_validation.json")
    args = parser.parse_args()
    result = {
        "sft": _maybe_validate("sft", args.sft_file),
        "dpo": _maybe_validate("dpo", args.dpo_file),
        "grpo": _maybe_validate("grpo", args.grpo_file),
    }
    write_json(args.output, result)
    print(result)


if __name__ == "__main__":
    main()

