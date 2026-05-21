"""GRPO training entrypoint."""

from __future__ import annotations

import argparse

from finpref.utils.io import read_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/grpo_qwen2_5_3b_lora.yaml")
    parser.add_argument("--base_adapter_path", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    config = read_yaml(args.config)
    if args.base_adapter_path:
        config["base_adapter_path"] = args.base_adapter_path
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.dry_run:
        print({"status": "dry_run", "config": config})
        return
    raise NotImplementedError("GRPO training skeleton is ready; wire TRL GRPOTrainer in P1.")


if __name__ == "__main__":
    main()

