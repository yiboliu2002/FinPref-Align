# FinPref-Align

FinPref-Align is a financial business alignment project for retail wealth management, advisory Q&A, and financial customer service scenarios.

The project focuses on a practical post-training loop:

```text
business rules -> SFT data -> DPO preference pairs -> rule rewards / GRPO prompts
-> LoRA SFT -> DPO -> optional GRPO -> rule eval + LLM judge -> badcase report
```

## Current Scope

P0 is the reliable resume-ready target:

- Build 3k SFT samples and 3k DPO pairs.
- Train Qwen2.5-3B-Instruct with LoRA SFT and DPO.
- Evaluate Base / SFT / DPO with rule metrics and LLM-as-a-Judge.
- Produce final report, resume bullets, and badcase analysis.

P1 adds small-scale GRPO with rule rewards for stronger differentiation.

## Disclaimer

This project is for model alignment research and interview demonstration only. It is not investment advice and must not be used as a real financial advisory system.

## Quick Start

```bash
pip install -e ".[dev]"
python scripts/00_build_seed_data.py --num_cases 100 --output data/interim/seed_cases.jsonl
python scripts/01_generate_sft_data.py --seed_file data/interim/seed_cases.jsonl --num_samples 100 --output data/processed/sft_train.jsonl
python scripts/02_generate_preference_pairs.py --sft_file data/processed/sft_train.jsonl --num_pairs 100 --output data/processed/dpo_train.jsonl
python scripts/03_generate_grpo_prompts.py --seed_file data/interim/seed_cases.jsonl --num_prompts 50 --output data/processed/grpo_train.jsonl
python scripts/04_build_eval_data.py --seed_file data/interim/seed_cases.jsonl --num_cases 50 --output data/processed/eval_finpref.jsonl
python scripts/04_validate_data.py
pytest
```

## A800 P0 Training

On the remote A800 project directory:

```bash
cd /autodl-fs/data/finpref/project
source /autodl-fs/data/finpref/env.sh

python scripts/00_build_seed_data.py --num_cases 100 --output data/interim/seed_cases.jsonl
python scripts/01_generate_sft_data.py --seed_file data/interim/seed_cases.jsonl --num_samples 3000 --output data/processed/sft_train.jsonl
python scripts/02_generate_preference_pairs.py --sft_file data/processed/sft_train.jsonl --num_pairs 3000 --output data/processed/dpo_train.jsonl
python scripts/03_generate_grpo_prompts.py --seed_file data/interim/seed_cases.jsonl --num_prompts 2000 --output data/processed/grpo_train.jsonl
python scripts/04_build_eval_data.py --seed_file data/interim/seed_cases.jsonl --num_cases 300 --output data/processed/eval_finpref.jsonl
python scripts/04_validate_data.py

bash scripts/05_train_sft.sh
bash scripts/06_train_dpo.sh
bash scripts/12_eval_p0_models.sh
```

Use `EVAL_LIMIT=50 bash scripts/12_eval_p0_models.sh` for a quick smoke evaluation before running all eval cases.
