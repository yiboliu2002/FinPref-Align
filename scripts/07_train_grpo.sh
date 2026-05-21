#!/usr/bin/env bash
set -euo pipefail
accelerate launch src/finpref/train/train_grpo.py --config configs/grpo_qwen2_5_3b_lora.yaml "$@"

