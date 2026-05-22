#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-configs/judge_deepseek.yaml}"
EVAL_FILE="${EVAL_FILE:-data/processed/eval_finpref.jsonl}"
PRED_FILE="${PRED_FILE:-outputs/eval/p1_public_v2_deepseek_sample30/dpo_outputs_limit_30.jsonl}"
OUT_FILE="${OUT_FILE:-outputs/eval/p1_public_v2_deepseek_sample30/dpo_deepseek_judge_scores.jsonl}"
PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  IFS= read -r DEEPSEEK_API_KEY || true
fi

DEEPSEEK_API_KEY="$(printf '%s' "${DEEPSEEK_API_KEY:-}" | tr -d '\r\n')"
if [[ -z "${DEEPSEEK_API_KEY}" ]]; then
  echo "DEEPSEEK_API_KEY is required via env or stdin." >&2
  exit 2
fi
export DEEPSEEK_API_KEY

PYTHONPATH=src "${PYTHON_BIN}" src/finpref/eval/judge_eval.py \
  --config "${CONFIG}" \
  --eval_file "${EVAL_FILE}" \
  --pred_file "${PRED_FILE}" \
  --output_file "${OUT_FILE}" \
  --incremental \
  --resume
