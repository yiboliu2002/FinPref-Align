# Badcase Summary

Generated from `outputs/eval/*_rule_details.jsonl` after the A800 P0 run.

| Model | Cases | Any Badcase | Compliance Failures | Suitability Failures | Forbidden Phrase Cases | Over-Refusal Cases |
|---|---:|---:|---:|---:|---:|---:|
| Base | 300 | 36 | 9 | 27 | 9 | 0 |
| SFT | 300 | 9 | 0 | 9 | 0 | 0 |
| DPO | 300 | 18 | 0 | 18 | 0 | 0 |

Per-model markdown samples:

- `reports/badcases/base/badcases.md`
- `reports/badcases/sft/badcases.md`
- `reports/badcases/dpo/badcases.md`

Main takeaway: SFT is the best P0 checkpoint on the current rule suite. DPO keeps the compliance gains but regresses on suitability compared with SFT, so the next iteration should inspect SFT-pass / DPO-fail pairs and tune preference construction or beta.
