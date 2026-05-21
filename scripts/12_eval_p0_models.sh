#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-3B-Instruct}"
SFT_ADAPTER="${SFT_ADAPTER:-/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref/adapter}"
DPO_ADAPTER="${DPO_ADAPTER:-/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_beta_0_1/adapter}"
EVAL_FILE="${EVAL_FILE:-data/processed/eval_finpref.jsonl}"
OUT_DIR="${OUT_DIR:-outputs/eval}"
LIMIT_ARGS=()

if [[ -n "${EVAL_LIMIT:-}" ]]; then
  LIMIT_ARGS=(--limit "${EVAL_LIMIT}")
fi

mkdir -p "${OUT_DIR}"

python src/finpref/eval/generate_model_outputs.py \
  --eval_file "${EVAL_FILE}" \
  --output_file "${OUT_DIR}/base_outputs.jsonl" \
  --model_name_or_path "${MODEL_NAME}" \
  "${LIMIT_ARGS[@]}"

python src/finpref/eval/generate_model_outputs.py \
  --eval_file "${EVAL_FILE}" \
  --output_file "${OUT_DIR}/sft_outputs.jsonl" \
  --model_name_or_path "${MODEL_NAME}" \
  --adapter_path "${SFT_ADAPTER}" \
  "${LIMIT_ARGS[@]}"

python src/finpref/eval/generate_model_outputs.py \
  --eval_file "${EVAL_FILE}" \
  --output_file "${OUT_DIR}/dpo_outputs.jsonl" \
  --model_name_or_path "${MODEL_NAME}" \
  --adapter_path "${DPO_ADAPTER}" \
  "${LIMIT_ARGS[@]}"

for name in base sft dpo; do
  python src/finpref/eval/rule_eval.py \
    --pred_file "${OUT_DIR}/${name}_outputs.jsonl" \
    --output_file "${OUT_DIR}/${name}_rule_metrics.json" \
    --details_file "${OUT_DIR}/${name}_rule_details.jsonl"

  python src/finpref/eval/judge_eval.py \
    --pred_file "${OUT_DIR}/${name}_outputs.jsonl" \
    --output_file "${OUT_DIR}/${name}_judge_scores.jsonl"
done

python src/finpref/eval/compare_models.py \
  "${OUT_DIR}/base_rule_metrics.json" \
  "${OUT_DIR}/sft_rule_metrics.json" \
  "${OUT_DIR}/dpo_rule_metrics.json"
