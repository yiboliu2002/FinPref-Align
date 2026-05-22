#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-configs/judge_deepseek.yaml}"
EVAL_DIR="${EVAL_DIR:-outputs/eval}"
EVAL_FILE="${EVAL_FILE:-data/processed/eval_finpref.jsonl}"
OUT_DIR="${OUT_DIR:-outputs/eval/deepseek_judge_sample}"
LIMIT="${LIMIT:-30}"
MODELS="${MODELS:-base sft dpo}"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required for DeepSeek judge evaluation." >&2
  exit 2
fi

mkdir -p "${OUT_DIR}"

for name in ${MODELS}; do
  pred_file="${EVAL_DIR}/${name}_outputs.jsonl"
  limited_file="${OUT_DIR}/${name}_outputs_limit_${LIMIT}.jsonl"
  if [[ ! -f "${pred_file}" ]]; then
    echo "Missing ${pred_file}; skipping ${name}" >&2
    continue
  fi
  "${PYTHON_BIN}" - "${pred_file}" "${limited_file}" "${LIMIT}" <<'PY'
import sys
from finpref.utils.io import read_jsonl, write_jsonl

src, dst, limit = sys.argv[1], sys.argv[2], int(sys.argv[3])
write_jsonl(dst, read_jsonl(src)[:limit])
PY
  "${PYTHON_BIN}" src/finpref/eval/judge_eval.py \
    --config "${CONFIG}" \
    --eval_file "${EVAL_FILE}" \
    --pred_file "${limited_file}" \
    --output_file "${OUT_DIR}/${name}_deepseek_judge_scores.jsonl"
done
