#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"
CONFIG="${CONFIG:-configs/dpo_qwen2_5_3b_lora_p1_public_v5.yaml}"
LOG_DIR="${LOG_DIR:-/autodl-fs/data/finpref/logs}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/p1_public_v5_dpo_${RUN_ID}.log}"

mkdir -p "${LOG_DIR}"

export HF_HOME="${HF_HOME:-/autodl-fs/data/hf-cache}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-/autodl-fs/data/hf-cache/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/autodl-fs/data/hf-cache/transformers}"
export HF_HUB_DISABLE_TELEMETRY="${HF_HUB_DISABLE_TELEMETRY:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export PYTHONPATH="${PYTHONPATH:-src}"

nohup "${PYTHON_BIN}" -m accelerate.commands.launch src/finpref/train/train_dpo.py --config "${CONFIG}" > "${LOG_FILE}" 2>&1 &
PID="$!"

echo "pid=${PID}"
echo "log=${LOG_FILE}"
