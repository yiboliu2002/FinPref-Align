#!/usr/bin/env bash
set -euo pipefail
mkdir -p outputs/eval
python src/finpref/eval/generate_model_outputs.py --mock --eval_file data/processed/eval_finpref.jsonl --output_file outputs/eval/mock_outputs.jsonl
python src/finpref/eval/rule_eval.py --pred_file outputs/eval/mock_outputs.jsonl --output_file outputs/eval/mock_rule_metrics.json --details_file outputs/eval/mock_rule_details.jsonl
python src/finpref/eval/judge_eval.py --pred_file outputs/eval/mock_outputs.jsonl --output_file outputs/eval/mock_judge_scores.jsonl

