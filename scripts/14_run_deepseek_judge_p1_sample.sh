#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-configs/judge_deepseek.yaml}"
EVAL_FILE="${EVAL_FILE:-data/processed/eval_finpref.jsonl}"
OUT_DIR="${OUT_DIR:-outputs/eval/deepseek_judge_sample}"
LIMIT="${LIMIT:-30}"
P0_MODELS="${P0_MODELS:-base sft dpo}"
P1_EVAL_DIR="${P1_EVAL_DIR:-outputs/eval/p1_beta_sweep}"
P1_MODELS="${P1_MODELS:-dpo_beta_0_2}"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required for DeepSeek judge evaluation." >&2
  exit 2
fi

CONFIG="${CONFIG}" \
EVAL_FILE="${EVAL_FILE}" \
OUT_DIR="${OUT_DIR}" \
LIMIT="${LIMIT}" \
MODELS="${P0_MODELS}" \
PYTHON_BIN="${PYTHON_BIN}" \
bash scripts/14_run_deepseek_judge_sample.sh

CONFIG="${CONFIG}" \
EVAL_FILE="${EVAL_FILE}" \
EVAL_DIR="${P1_EVAL_DIR}" \
OUT_DIR="${OUT_DIR}" \
LIMIT="${LIMIT}" \
MODELS="${P1_MODELS}" \
PYTHON_BIN="${PYTHON_BIN}" \
bash scripts/14_run_deepseek_judge_sample.sh
