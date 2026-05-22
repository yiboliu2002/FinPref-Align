#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-3B-Instruct}"
BASE_CONFIG="${BASE_CONFIG:-configs/dpo_qwen2_5_3b_lora.yaml}"
CONFIG_DIR="${CONFIG_DIR:-configs/generated/p1_beta_sweep}"
OUT_ROOT="${OUT_ROOT:-/autodl-fs/data/finpref/outputs/p1_beta_sweep}"
EVAL_FILE="${EVAL_FILE:-data/processed/eval_finpref.jsonl}"
EVAL_DIR="${EVAL_DIR:-outputs/eval/p1_beta_sweep}"
SUMMARY_MD="${SUMMARY_MD:-reports/p1_beta_sweep.md}"
SEED="${SEED:-42}"
BETAS="${BETAS:-0.03 0.05 0.1 0.2}"
LIMIT_ARGS=()

if [[ -n "${EVAL_LIMIT:-}" ]]; then
  LIMIT_ARGS=(--limit "${EVAL_LIMIT}")
fi

mkdir -p "${CONFIG_DIR}" "${OUT_ROOT}" "${EVAL_DIR}" "$(dirname "${SUMMARY_MD}")"

for beta in ${BETAS}; do
  beta_label="${beta//./_}"
  run_name="dpo_beta_${beta_label}"
  config_file="${CONFIG_DIR}/${run_name}.yaml"
  output_dir="${OUT_ROOT}/${run_name}"
  adapter_path="${output_dir}/adapter"

  python - "${BASE_CONFIG}" "${config_file}" "${beta}" "${output_dir}" "${SEED}" "${run_name}" <<'PY'
import sys
from pathlib import Path

import yaml

base_config, config_file, beta, output_dir, seed, run_name = sys.argv[1:]
with Path(base_config).open("r", encoding="utf-8") as f:
    config = yaml.safe_load(f) or {}

config["beta"] = float(beta)
config["output_dir"] = output_dir
config["seed"] = int(seed)
config["data_seed"] = int(seed)
config["run_name"] = run_name
config["save_total_limit"] = 1

target = Path(config_file)
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("w", encoding="utf-8") as f:
    yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
PY

  if [[ ! -f "${adapter_path}/adapter_model.safetensors" ]]; then
    echo "===== Training ${run_name} ====="
    accelerate launch src/finpref/train/train_dpo.py --config "${config_file}"
  else
    echo "===== Skipping ${run_name}; adapter already exists ====="
  fi

  echo "===== Evaluating ${run_name} ====="
  python src/finpref/eval/generate_model_outputs.py \
    --eval_file "${EVAL_FILE}" \
    --output_file "${EVAL_DIR}/${run_name}_outputs.jsonl" \
    --model_name_or_path "${MODEL_NAME}" \
    --adapter_path "${adapter_path}" \
    "${LIMIT_ARGS[@]}"

  python src/finpref/eval/rule_eval.py \
    --pred_file "${EVAL_DIR}/${run_name}_outputs.jsonl" \
    --output_file "${EVAL_DIR}/${run_name}_rule_metrics.json" \
    --details_file "${EVAL_DIR}/${run_name}_rule_details.jsonl"

  python src/finpref/eval/judge_eval.py \
    --eval_file "${EVAL_FILE}" \
    --pred_file "${EVAL_DIR}/${run_name}_outputs.jsonl" \
    --output_file "${EVAL_DIR}/${run_name}_judge_scores.jsonl"
done

python scripts/13_summarize_p1_sweep.py \
  --eval_dir "${EVAL_DIR}" \
  --baseline_details outputs/eval/sft_rule_details.jsonl \
  --output_csv "${EVAL_DIR}/summary.csv" \
  --output_md "${SUMMARY_MD}" \
  --output_json "${EVAL_DIR}/sft_pass_variant_fail_ids.json"
