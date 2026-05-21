# FinPref-Align Data Card

This directory stores generated training and evaluation data.

- `sft_train.jsonl`: supervised fine-tuning conversations.
- `dpo_train.jsonl`: preference pairs with `prompt`, `chosen`, and `rejected`.
- `grpo_train.jsonl`: prompt-only training data plus metadata for rule rewards.
- `eval_finpref.jsonl`: held-out financial business evaluation cases.

Generated data is synthetic and intended only for model alignment research.

