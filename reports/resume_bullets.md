# Resume Bullets

- Built FinPref-Align, a finance-domain alignment pipeline for Qwen2.5-3B-Instruct covering data normalization, SFT formatting, DPO preference-pair construction, reward/rule evaluation, badcase analysis, and A800 training orchestration.
- Generated and validated a P0 dataset with 3,000 SFT samples, 3,000 DPO pairs, 2,000 GRPO prompts, and 300 held-out evaluation cases; data validators passed with `failed=0` and the local test suite passed with `11 passed`.
- Implemented LoRA SFT and DPO training entrypoints with TRL/PEFT, remote A800 run scripts, model-output generation, rule metrics, deterministic judge scoring, and Base/SFT/DPO comparison tooling.
- Ran Qwen2.5-3B-Instruct LoRA SFT and DPO on an A800; SFT improved rule compliance from 97.0% to 100.0%, suitability from 91.0% to 97.0%, removed forbidden direct-advice phrasing from 3.0% to 0.0%, and reduced average response length from 656.66 to 156.58.
- Evaluated the DPO adapter on the same 300-case suite; DPO preserved 100.0% compliance and 0.0% forbidden-phrase rate, while suitability reached 94.0%, revealing a concrete follow-up target for preference-pair quality and beta tuning.
- Produced badcase reports showing total rule badcases decreased from 36 for Base to 9 for SFT and 18 for DPO, with remaining failures concentrated in fine-grained suitability matching.
