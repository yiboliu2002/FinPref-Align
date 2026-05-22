# TODO: FinPref-Align Next Steps

This file tracks the next iteration after the completed P0 SFT-DPO pipeline.

## P1: Single-A800 / CPU / API Work

P1 should stay feasible on a single A800 80GB machine, plus CPU preprocessing and optional LLM API calls. The goal is to improve data realism, diagnose DPO behavior, and strengthen evaluation before moving to multi-card experiments.

## P1.1: Public Data Integration

- Collect public finance QA / investment advisory style datasets.
- Normalize public data into the project SFT message schema:
  - `system`
  - `user`
  - `assistant`
  - `meta`
- Add a cleaning pipeline for:
  - duplicated questions;
  - low-quality or overly generic answers;
  - answers containing direct buy/sell instructions;
  - answers that promise returns;
  - answers without risk disclosure.
- Enrich public QA rows with structured metadata:
  - user risk tolerance;
  - investment horizon;
  - liquidity need;
  - product risk level;
  - query type;
  - `risk_mismatch`;
  - `requires_clarification`;
  - `should_disclose_risk`;
  - `should_refuse_direct_advice`.
- Use rule-based labeling where possible, and use an LLM API for ambiguous cases.

## P1.2: More Realistic DPO Pair Construction

- Convert cleaned public SFT data into DPO preference pairs.
- Construct `chosen` / `rejected` pairs using a mix of:
  - original high-quality public answers as `chosen`;
  - rule-corrupted variants as `rejected`;
  - LLM-generated safer/better answers as `chosen`;
  - LLM-generated flawed answers as hard negatives;
  - LLM-as-a-Judge comparisons to decide chosen vs rejected.
- Add pair-level metadata:
  - `rejected_type`;
  - `preference_reason`;
  - `suitability_focus`;
  - `compliance_focus`;
  - `risk_disclosure_focus`;
  - `judge_confidence`.
- Focus especially on SFT-pass / DPO-fail patterns from P0:
  - cases where DPO gives a safe but overly generic answer;
  - cases where DPO misses product-user suitability;
  - cases where DPO asks for clarification when the eval expects a clear cautionary judgment.

## P1.3: Single-Card 3B DPO Hyperparameter Sweep

The current P0 DPO run used:

```yaml
beta: 0.1
learning_rate: 5.0e-7
num_train_epochs: 1
```

Run a controlled sweep while keeping the same SFT adapter, data, and eval set.

### Beta Sweep

- `beta = 0.03`
- `beta = 0.05`
- `beta = 0.1`
- `beta = 0.2`

Track:

- compliance pass rate;
- risk disclosure coverage;
- suitability match rate;
- badcase count;
- average response length;
- SFT-pass / DPO-fail case count.

### Learning Rate Sweep

If beta sweep is not enough, test:

- `learning_rate = 2e-7`
- `learning_rate = 5e-7`
- `learning_rate = 1e-6`

### Epoch Sweep

Only after beta/lr diagnosis:

- `num_train_epochs = 0.5`
- `num_train_epochs = 1`
- `num_train_epochs = 2`

Watch for over-conservative templates and suitability regression.

## P1.4: Evaluation Upgrade

- Add an LLM-as-a-Judge backend beyond the current deterministic mock judge.
- Score at least:
  - compliance;
  - suitability;
  - risk disclosure;
  - helpfulness;
  - over-refusal;
  - factuality;
  - verbosity;
  - reward hacking.
- Sample and manually inspect:
  - Base badcases;
  - SFT remaining badcases;
  - DPO suitability failures;
  - SFT-pass / DPO-fail cases.
- Add an eval report that separates:
  - rule metrics;
  - LLM judge metrics;
  - human spot-check notes.

## P1.5: Optional Single-Card 7B Smoke Test

- Try 7B SFT LoRA on a single A800 after P1.1-P1.4 are stable.
- Keep batch size small and use gradient checkpointing.
- Treat this as a smoke test, not the main scale-up result.
- Only attempt 7B DPO on single card if memory is comfortable, or use QLoRA/reference-model memory optimizations.

## P2: Multi-Card / Higher-Cost Work

P2 should include experiments that are slower, more expensive, or likely to benefit from multiple GPUs. These are not required for the resume-ready P0/P1 story, but they are natural research extensions.

## P2.1: Multi-Card 7B Scale-Up

- Run the improved pipeline on a 7B base model after P1 diagnosis.
- Compare:
  - 3B SFT vs 7B SFT;
  - 3B DPO vs 7B DPO;
  - SFT vs DPO under the same model size.
- Keep the interpretation careful:
  - 7B may improve capacity and suitability;
  - 7B does not guarantee DPO will outperform SFT without better preference pairs.
- Prefer multi-card for 7B DPO if policy + reference model memory becomes tight.

## P2.2: GRPO Extension

- Use existing `data/processed/grpo_train.jsonl` prompts as a starting point.
- Implement reward functions for:
  - compliance;
  - risk disclosure;
  - suitability;
  - helpfulness;
  - over-refusal penalty;
  - verbosity penalty.
- Run small-scale GRPO only after SFT-DPO behavior is stable.
- Compare SFT / DPO / GRPO on the same eval suite.
- For 7B GRPO or larger rollout batches, prefer multi-card because rollout generation and policy updates are throughput-heavy.

## P2.3: Larger Sweeps and Ablations

- Run larger hyperparameter sweeps after the P1 beta/lr diagnosis:
  - beta;
  - learning rate;
  - epochs;
  - DPO pair mixture ratio;
  - data scale;
  - model size.
- Add ablations for:
  - synthetic-only vs public-data-augmented;
  - rule-labeled vs LLM-labeled meta;
  - rule-generated rejected vs LLM-generated rejected;
  - SFT-only vs SFT+DPO vs SFT+DPO+GRPO.
- Use multi-card when running multiple variants in parallel or when using larger models.

## Engineering Hygiene

- Keep credentials, API keys, private data, and model cache files out of git.
- Do not commit full model checkpoints or adapter outputs unless intentionally using Git LFS or an external model hub.
- Keep `README.md`, `reports/final_report.md`, and `reports/finpref_interview_playbook.pdf` updated after each major experiment.
- Add scripts for automated experiment tables:
  - sweep config generation;
  - batch evaluation;
  - metrics comparison;
  - SFT-pass / DPO-fail extraction.
