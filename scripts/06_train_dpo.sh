#!/usr/bin/env bash
set -euo pipefail
accelerate launch src/finpref/train/train_dpo.py --config configs/dpo_qwen2_5_3b_lora.yaml "$@"

