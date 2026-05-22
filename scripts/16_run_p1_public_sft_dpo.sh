#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python}"
SFT_CONFIG="${SFT_CONFIG:-configs/sft_qwen2_5_3b_lora_p1_public.yaml}"
DPO_CONFIG="${DPO_CONFIG:-configs/dpo_qwen2_5_3b_lora_p1_public.yaml}"
RUN_DPO="${RUN_DPO:-1}"

export HF_HOME="${HF_HOME:-/autodl-fs/data/hf-cache}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-/autodl-fs/data/hf-cache/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/autodl-fs/data/hf-cache/transformers}"
export HF_HUB_DISABLE_TELEMETRY="${HF_HUB_DISABLE_TELEMETRY:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export PYTHONPATH="${PYTHONPATH:-src}"

"${PYTHON_BIN}" -m accelerate.commands.launch src/finpref/train/train_sft.py --config "${SFT_CONFIG}"

if [[ "${RUN_DPO}" == "1" ]]; then
  "${PYTHON_BIN}" -m accelerate.commands.launch src/finpref/train/train_dpo.py --config "${DPO_CONFIG}"
fi
