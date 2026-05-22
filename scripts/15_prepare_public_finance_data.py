import argparse
import json

import _bootstrap  # noqa: F401
from finpref.data.public_finance import SOURCE_DATASET, prepare_public_finance_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare P1 public finance SFT and DPO data.")
    parser.add_argument("--dataset_name", default=SOURCE_DATASET)
    parser.add_argument("--split", default="train")
    parser.add_argument("--max_source_rows", type=int, default=20000)
    parser.add_argument("--max_kept", type=int, default=5000)
    parser.add_argument("--num_sft", type=int, default=5000)
    parser.add_argument("--num_dpo", type=int, default=5000)
    parser.add_argument("--num_repair_dpo", type=int, default=0)
    parser.add_argument("--streaming", action="store_true")
    parser.add_argument("--sample_seed", type=int, default=20260521)
    parser.add_argument("--raw_sample_output", default="data/interim/public_finance_raw_sample.jsonl")
    parser.add_argument("--sft_output", default="data/processed/public_finance_sft.jsonl")
    parser.add_argument("--dpo_output", default="data/processed/public_finance_dpo.jsonl")
    parser.add_argument("--stats_output", default="outputs/data/public_finance_stats.json")
    parser.add_argument("--base_sft_file", default="data/processed/sft_train.jsonl")
    parser.add_argument("--base_dpo_file", default="data/processed/dpo_train.jsonl")
    parser.add_argument("--combined_sft_output", default="data/processed/sft_train_p1_public_mix.jsonl")
    parser.add_argument("--combined_dpo_output", default="data/processed/dpo_train_p1_public_mix.jsonl")
    parser.add_argument("--no_combine", action="store_true")
    args = parser.parse_args()

    result = prepare_public_finance_data(
        dataset_name=args.dataset_name,
        split=args.split,
        max_source_rows=args.max_source_rows,
        max_kept=args.max_kept,
        num_sft=args.num_sft,
        num_dpo=args.num_dpo,
        num_repair_dpo=args.num_repair_dpo,
        streaming=args.streaming,
        raw_sample_output=args.raw_sample_output,
        sft_output=args.sft_output,
        dpo_output=args.dpo_output,
        stats_output=args.stats_output,
        base_sft_file=None if args.no_combine else args.base_sft_file,
        base_dpo_file=None if args.no_combine else args.base_dpo_file,
        combined_sft_output=None if args.no_combine else args.combined_sft_output,
        combined_dpo_output=None if args.no_combine else args.combined_dpo_output,
        sample_seed=args.sample_seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
