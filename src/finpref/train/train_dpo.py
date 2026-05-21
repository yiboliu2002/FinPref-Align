"""LoRA DPO training entrypoint."""

from __future__ import annotations

import argparse

from finpref.utils.io import read_yaml
from finpref.train.common import (
    adapter_output_dir,
    config_kwargs,
    load_causal_lm,
    load_tokenizer,
    training_common_kwargs,
)


def train(config: dict) -> None:
    from datasets import load_dataset
    from peft import PeftModel
    from trl import DPOConfig, DPOTrainer

    tokenizer = load_tokenizer(config["model_name_or_path"])
    tokenizer.padding_side = "left"

    policy_base = load_causal_lm(config["model_name_or_path"], config)
    policy = PeftModel.from_pretrained(policy_base, config["sft_adapter_path"], is_trainable=True)

    ref_base = load_causal_lm(config["model_name_or_path"], config)
    ref_model = PeftModel.from_pretrained(ref_base, config["sft_adapter_path"], is_trainable=False)
    ref_model.eval()

    dataset = load_dataset("json", data_files=config["train_file"], split="train")
    args = DPOConfig(
        **config_kwargs(
            DPOConfig,
            {
                **training_common_kwargs(config),
                "max_prompt_length": config.get("max_prompt_length", 1024),
                "max_length": config.get("max_length", 2048),
                "max_completion_length": config.get("max_completion_length"),
                "beta": config.get("beta", 0.1),
                "loss_type": config.get("loss_type", "sigmoid"),
                "dataset_num_proc": config.get("dataset_num_proc"),
            },
        )
    )
    trainer = DPOTrainer(
        model=policy,
        ref_model=ref_model,
        args=args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    adapter_dir = adapter_output_dir(config["output_dir"])
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dpo_qwen2_5_3b_lora.yaml")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    config = read_yaml(args.config)
    if args.dry_run:
        print({"status": "dry_run", "config": config})
        return
    train(config)


if __name__ == "__main__":
    main()
