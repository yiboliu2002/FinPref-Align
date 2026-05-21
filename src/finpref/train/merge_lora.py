"""Merge LoRA adapter into a base model."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--adapter_path", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    print(f"Merge requested: {args.model_name_or_path} + {args.adapter_path} -> {args.output_dir}")
    raise NotImplementedError("Implement PEFT merge after training is wired.")


if __name__ == "__main__":
    main()

