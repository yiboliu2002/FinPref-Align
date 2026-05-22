"""Shared helpers for TRL/PEFT training entrypoints."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any


DEFAULT_LORA_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def adapter_output_dir(output_dir: str | Path) -> Path:
    return Path(output_dir) / "adapter"


def config_kwargs(config_cls: type, values: dict[str, Any]) -> dict[str, Any]:
    if is_dataclass(config_cls):
        allowed = {field.name for field in fields(config_cls)}
    else:
        allowed = set()
    return {key: value for key, value in values.items() if key in allowed and value is not None}


def training_common_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    save_steps = int(config.get("save_steps", 200))
    return {
        "output_dir": config["output_dir"],
        "num_train_epochs": config.get("num_train_epochs", 1),
        "per_device_train_batch_size": config.get("per_device_train_batch_size", 1),
        "gradient_accumulation_steps": config.get("gradient_accumulation_steps", 1),
        "learning_rate": config.get("learning_rate"),
        "seed": config.get("seed", 42),
        "data_seed": config.get("data_seed", config.get("seed", 42)),
        "warmup_ratio": config.get("warmup_ratio", 0.0),
        "lr_scheduler_type": config.get("lr_scheduler_type", "cosine"),
        "bf16": bool(config.get("bf16", False)),
        "fp16": bool(config.get("fp16", False)),
        "gradient_checkpointing": bool(config.get("gradient_checkpointing", False)),
        "gradient_checkpointing_kwargs": {"use_reentrant": False}
        if config.get("gradient_checkpointing", False)
        else None,
        "logging_steps": int(config.get("logging_steps", 10)),
        "save_steps": save_steps,
        "save_strategy": "steps",
        "save_total_limit": int(config.get("save_total_limit", 2)),
        "report_to": config.get("report_to", "none"),
        "remove_unused_columns": False,
        "optim": config.get("optim", "adamw_torch"),
    }


def build_lora_config(config: dict[str, Any]):
    from peft import LoraConfig, TaskType

    lora = config.get("lora", {})
    return LoraConfig(
        r=int(lora.get("r", 16)),
        lora_alpha=int(lora.get("alpha", 32)),
        lora_dropout=float(lora.get("dropout", 0.05)),
        target_modules=lora.get("target_modules", DEFAULT_LORA_TARGET_MODULES),
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )


def torch_dtype_from_config(config: dict[str, Any]):
    import torch

    if config.get("bf16", False):
        return torch.bfloat16
    if config.get("fp16", False):
        return torch.float16
    return torch.float32


def load_tokenizer(model_name_or_path: str):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_causal_lm(model_name_or_path: str, config: dict[str, Any]):
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch_dtype_from_config(config),
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    if config.get("gradient_checkpointing", False):
        model.config.use_cache = False
    return model
