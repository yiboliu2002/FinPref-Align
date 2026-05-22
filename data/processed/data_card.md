# FinPref-Align Data Card

This directory stores generated training and evaluation data.

- `sft_train.jsonl`: supervised fine-tuning conversations.
- `dpo_train.jsonl`: preference pairs with `prompt`, `chosen`, and `rejected`.
- `grpo_train.jsonl`: prompt-only training data plus metadata for rule rewards.
- `eval_finpref.jsonl`: held-out financial business evaluation cases.
- `public_finance_sft.jsonl`: P1 public finance QA rows normalized into the SFT message schema.
- `public_finance_dpo.jsonl`: P1 public finance QA preference pairs with rule-corrupted rejected answers.
- `sft_train_p1_public_mix.jsonl`: P0 synthetic SFT data plus P1 public finance SFT rows.
- `dpo_train_p1_public_mix.jsonl`: P0 synthetic DPO data plus P1 public finance DPO rows.

P0 generated data is synthetic and intended only for model alignment research. P1 public-data files use `FinLang/investopedia-instruction-tuning-dataset` (`cc-by-nc-4.0`) as a public finance QA source, then add rule-based cleaning, synthetic user/product metadata, and compliance-oriented preference pairs. Respect the upstream non-commercial license restriction when using the P1 public-data files.
