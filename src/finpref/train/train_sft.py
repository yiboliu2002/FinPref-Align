"""LoRA SFT training entrypoint.

The full TRL implementation is intentionally isolated here so data and tests can run
before heavyweight training dependencies are installed.
"""

from __future__ import annotations

import argparse

from finpref.utils.io import read_yaml
from finpref.train.common import (
    adapter_output_dir,
    build_lora_config,
    config_kwargs,
    load_causal_lm,
    load_tokenizer,
    training_common_kwargs,
)


def train(config: dict) -> None:
    from datasets import load_dataset
    from trl import SFTConfig, SFTTrainer

    tokenizer = load_tokenizer(config["model_name_or_path"])
    model = load_causal_lm(config["model_name_or_path"], config)
    dataset = load_dataset("json", data_files=config["train_file"], split="train")

    args = SFTConfig(
        **config_kwargs(
            SFTConfig,
            {
                **training_common_kwargs(config),
                "max_length": config.get("max_seq_length", config.get("max_length", 2048)),
                "dataset_num_proc": config.get("dataset_num_proc"),
                "packing": bool(config.get("packing", False)),
                "completion_only_loss": config.get("completion_only_loss"),
            },
        )
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=build_lora_config(config),
    )
    trainer.train()
    adapter_dir = adapter_output_dir(config["output_dir"])
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/sft_qwen2_5_3b_lora.yaml")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    config = read_yaml(args.config)
    if args.dry_run:
        print({"status": "dry_run", "config": config})
        return
    train(config)


if __name__ == "__main__":
    main()
