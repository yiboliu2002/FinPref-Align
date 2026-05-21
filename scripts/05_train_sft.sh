#!/usr/bin/env bash
set -euo pipefail
accelerate launch src/finpref/train/train_sft.py --config configs/sft_qwen2_5_3b_lora.yaml "$@"

