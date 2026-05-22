# FinPref-Align 操作记录

> 用途：记录本项目从环境准备、项目骨架、数据生成、训练、评估到 P1 实验的关键操作，方便后续复盘、写报告和面试讲述。  
> 安全约定：不在本文档中记录服务器密码、API key、私钥或其他敏感凭据。

## 2026-05-20

### 19:38 启动记录

- 本地工作目录：`D:\CodeX-Chat\FindIntern\Project\FinPref-Align`
- 初始规划文件：`FinPref-Align_Qwen2.5-3B_SFT-DPO-GRPO_Codex_Spec_v3.md`
- 目标：按规划搭建 `FinPref-Align` 项目骨架，并准备远端 A800 训练环境。
- 远端资源检查：
  - GPU：`NVIDIA A800-SXM4-80GB`
  - PyTorch：`2.3.0+cu121`
  - CUDA：`12.1`
  - bf16：可用
  - 系统盘：约 `30GB`
  - 数据盘：`/autodl-fs/data`，约 `200GB`
- 注意事项：Hugging Face 缓存、数据、输出和日志需要尽量放到 `/autodl-fs/data`，避免占满系统盘。

### 19:40 创建项目骨架

- 创建本地目录结构：`configs/`、`data/`、`scripts/`、`src/finpref/`、`reports/`、`tests/`。
- 目标是先形成可测试的最小闭环，包含 schema、validators、reward functions、rule eval、配置文件和命令入口。
- 已创建基础文件：
  - 项目元数据：`README.md`、`pyproject.toml`、`requirements.txt`、`.gitignore`
  - 配置：`configs/sft_qwen2_5_3b_lora.yaml`、`configs/dpo_qwen2_5_3b_lora.yaml`、`configs/grpo_qwen2_5_3b_lora.yaml`、`configs/eval.yaml`、`configs/judge.yaml`
  - 数据模块：seed case、SFT 数据、DPO pair、GRPO prompt、格式转换、数据校验
  - Reward 模块：compliance、suitability、risk disclosure、helpfulness、over-refusal、verbosity、combined score
  - Eval 模块：rule eval、mock judge、mock output generation、badcase report
  - 训练入口：SFT/DPO/GRPO dry-run skeleton
  - 测试：schema、validators、rewards、rule_eval、formatters
- 本地 smoke test：
  - 生成 `20` 条 seed case：通过
  - 生成 `20` 条 SFT 样本：通过
  - 生成 `20` 条 DPO pairs：通过
  - 生成 `20` 条 GRPO prompts：通过
  - 数据校验：SFT/DPO/GRPO 均 `failed=0`
  - 单元测试：`10 passed`
- 新增 eval set 生成入口：`scripts/04_build_eval_data.py`
- 修正 rule eval 误判：
  - 原先 `DIRECT_RECOMMENDATION_PATTERNS` 中的 `"直接买"` 会误伤“不能给出直接买入指令”这类合规表达。
  - 先收窄为 `"直接买入"`，随后又发现仍会误伤否定句。
  - 新增 `contains_direct_recommendation(...)`，根据前文 `不能 / 不得 / 不应 / 无法 / 不宜 / 不要` 等否定词过滤合规表述。
- 复测结果：
  - 单元测试：`11 passed`
  - mock rule eval：`compliance_pass_rate=100.0`、`risk_disclosure_coverage=100.0`、`suitability_match_rate=100.0`

### 19:55 准备远端 A800 环境

- 计划在远端 `/autodl-fs/data/finpref` 下放置项目、模型缓存、输出和日志。
- 计划环境变量：
  - `HF_HOME=/autodl-fs/data/hf-cache`
  - `HF_HUB_CACHE=/autodl-fs/data/hf-cache/hub`
  - `TRANSFORMERS_CACHE=/autodl-fs/data/hf-cache/transformers`
- 远端已创建：
  - `/autodl-fs/data/finpref/project`
  - `/autodl-fs/data/finpref/outputs`
  - `/autodl-fs/data/finpref/logs`
  - `/autodl-fs/data/hf-cache`
  - `/autodl-fs/data/pip-cache`
- 已写入远端环境脚本：`/autodl-fs/data/finpref/env.sh`
- 依赖兼容性处理：
  - 镜像自带 `torch 2.3.0+cu121`
  - 最新 `transformers 5.8.1` 需要 `torch >= 2.4`
  - `trl 1.4.0` 导入 `DPOTrainer` 时依赖新版本 FSDP 接口，导致 `cannot import name 'FSDPModule'`
  - 处理策略：保留镜像自带 PyTorch，降级到兼容 `torch 2.3.0` 的 `transformers 4.x + trl 0.x` 训练栈。
- 最终远端依赖版本：
  - `torch 2.3.0+cu121`
  - `transformers 4.51.3`
  - `trl 0.17.0`
  - `peft 0.15.2`
  - `accelerate 1.6.0`
  - `datasets 3.6.0`
  - `bitsandbytes 0.49.2`
- 验证：`from trl import SFTTrainer, DPOTrainer, GRPOTrainer` 成功。
- 已同步更新本地 `requirements.txt` 和 `pyproject.toml` 的版本约束。

### 20:05 同步项目骨架到远端

- 目标路径：`/autodl-fs/data/finpref/project`
- 同步策略：上传本地项目文件，排除 `.pytest_cache/`、`__pycache__/`、`outputs/` 等临时产物。
- 已上传 `77` 个项目文件到远端，远端项目大小约 `325KB`。
- 已在远端执行：`python -m pip install -e . --no-deps`
- 远端验证：
  - 单元测试：`11 passed`
  - 生成 `20` 条 seed case：通过
  - 生成 `20` 条 SFT 样本：通过
  - 生成 `20` 条 DPO pairs：通过
  - 生成 `20` 条 GRPO prompts：通过
  - 生成 `20` 条 eval cases：通过
  - 数据校验：SFT/DPO/GRPO 均 `failed=0`
  - mock rule eval：`compliance_pass_rate=100.0`、`risk_disclosure_coverage=100.0`、`suitability_match_rate=100.0`
- 远端磁盘占用复查：
  - 系统盘 `/`：约 `1.6GB / 30GB`
  - 数据盘 `/autodl-fs/data`：约 `225MB / 200GB`
  - `/autodl-fs/data/pip-cache`：约 `224MB`
  - `/autodl-fs/data/hf-cache`：约 `12KB`，模型尚未下载

### 20:20 切换 SSH key 登录

- 本地生成 `ed25519` SSH key：`finpref_a800_ed25519`
- 已将公钥加入 A800 服务器 `~/.ssh/authorized_keys`
- 公钥标识：`liuyibo20250502CUHKSZ`
- 后续远端连接优先使用 SSH key，避免继续使用明文密码登录。

### 21:08 补齐 P0 训练入口与数据规模

- 当前进度复核：
  - A800 环境、依赖降级和远端小样本链路已完成。
  - 本地训练入口原本仍是 `NotImplementedError` skeleton，尚不能真实训练。
- 新增共享训练工具：`src/finpref/train/common.py`
- 补齐真实训练入口：
  - `src/finpref/train/train_sft.py`：使用 `TRL SFTTrainer` + `PEFT LoRA`
  - `src/finpref/train/train_dpo.py`：从 SFT adapter 加载 policy/ref model，使用 `TRL DPOTrainer` 继续训练 LoRA
- 扩展真实推理入口：
  - `src/finpref/eval/generate_model_outputs.py` 支持 `--model_name_or_path`、`--adapter_path`、`--max_new_tokens`、`--limit`
  - 可用于 Base/SFT/DPO 输出生成。
- 新增远端评估脚本：
  - `scripts/12_eval_p0_models.sh` 串联 Base/SFT/DPO 输出生成、rule eval、mock judge 和指标对比。
- 将本地数据扩到 P0 规模：
  - seed cases：`100`
  - SFT：`3000`
  - DPO pairs：`3000`
  - GRPO prompts：`2000`
  - eval cases：`300`
- 本地验证：
  - `python scripts/04_validate_data.py`：SFT/DPO/GRPO 均 `failed=0`
  - `pytest -q`：`11 passed`
  - mock eval：`total=300`，`compliance_pass_rate=100.0`，`risk_disclosure_coverage=100.0`，`suitability_match_rate=97.0`
- A800 连接状态：
  - SSH key 当时返回 `Permission denied (publickey,password)`
  - 不从历史日志恢复密码或私钥；后续需要用户明确授权使用密码，或修复 SSH key 后再继续同步和启动训练。

### 21:12 固化 A800 SSH key 标识

- 新增项目级 `AGENTS.md`，供后续 Codex 会话读取环境约定。
- 写入 A800 SSH 公钥标识：`liuyibo20250502CUHKSZ`
- 约定：
  - 优先使用 SSH key 登录。
  - 不从本地日志恢复密码或私钥。
  - 如果 key 登录失败，需要用户修复 key 或明确提供新的登录授权。

### 22:17-01:23 完成 A800 P0 SFT/DPO/Eval

- SSH key 登录失败后，用户明确授权本次会话使用密码登录；密码未写入项目文件或环境文件。
- 同步最新代码和 P0 数据到 `/autodl-fs/data/finpref/project`。
- 远端网络情况：无法直接访问 `huggingface.co`，本次运行使用 `HF_ENDPOINT=https://hf-mirror.com`。
- A800 上执行：
  - `bash scripts/05_train_sft.sh`
  - `bash scripts/06_train_dpo.sh`
  - `bash scripts/12_eval_p0_models.sh`
- 远端产物：
  - SFT adapter：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref/adapter`
  - DPO adapter：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_beta_0_1/adapter`
  - 主日志：`/autodl-fs/data/finpref/logs/p0_training_20260520_221719.log`
- 已复制评估产物回本地 `outputs/eval/`：
  - `base_outputs.jsonl`、`sft_outputs.jsonl`、`dpo_outputs.jsonl`
  - `*_rule_metrics.json`、`*_rule_details.jsonl`、`*_judge_scores.jsonl`
- 300 条 eval cases 的 rule metrics：
  - Base：合规 `97.0`，风险披露 `100.0`，适配性 `91.0`，禁用短语 `3.0`，平均长度 `656.66`
  - SFT：合规 `100.0`，风险披露 `100.0`，适配性 `97.0`，禁用短语 `0.0`，平均长度 `156.58`
  - DPO：合规 `100.0`，风险披露 `100.0`，适配性 `94.0`，禁用短语 `0.0`，平均长度 `156.78`
- 结论：
  - 当前 rule suite 上，SFT 是 P0 最优 checkpoint。
  - DPO 保持合规性和简洁性，但适配性低于 SFT。
  - 下一轮需要检查 SFT-pass / DPO-fail case，并调整 preference pair 构造或 DPO beta。

### 01:23 本地报告收尾

- 生成 badcase 报告：
  - `reports/badcases/base/badcases.md`
  - `reports/badcases/sft/badcases.md`
  - `reports/badcases/dpo/badcases.md`
  - `reports/badcases/summary.md`
- 更新总结材料：
  - `reports/final_report.md`
  - `reports/resume_bullets.md`

## 2026-05-21

### 13:14 新 A800 服务器检查

- 用户重新租用单卡 A800 服务器；SSH key 初始登录失败后，用户明确提供本次会话的新登录授权。
- SSH key 初始错误：`Permission denied (publickey,password)`，说明新服务器还未安装预期的 `liuyibo20250502CUHKSZ` 公钥。
- 远端项目路径：`/autodl-fs/data/finpref/project`
- 硬件和磁盘：
  - GPU：`NVIDIA A800-SXM4-80GB`，`81920 MiB`
  - 系统盘：约 `30GB`
  - 数据盘：`/autodl-fs/data`，约 `200GB`
- clone/sync 状态：
  - `/autodl-fs/data/finpref/project` 存在并包含项目文件。
  - 该目录没有 `.git`，所以不是完整 Git clone，而是文件复制/同步；远端 `git status` 会失败。
  - 与本地 tracked files 校验：`84/92` 个匹配，`4` 个缺失，`4` 个较旧。
  - 远端缺失文件：`reports/badcases/base/badcases.md`、`reports/badcases/sft/badcases.md`、`reports/badcases/dpo/badcases.md`、`reports/badcases/summary.md`
  - 远端较旧文件：`README.md`、`Record.md`、`reports/final_report.md`、`reports/resume_bullets.md`
- 产物状态：
  - SFT adapter 存在：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref/adapter`
  - DPO adapter 存在：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_beta_0_1/adapter`
  - GRPO adapter 不存在，符合 P0 只完成 SFT/DPO 的状态。
- 远端验证：
  - `python scripts/04_validate_data.py`：SFT `3000`，DPO `3000`，GRPO `2000`，均 `failed=0`
  - `pytest -q`：`11 passed`

### 13:30 重新配置 SSH key

- 因为现有 key 无法非交互式重新导出为要求的 comment，创建新的 A800 专用 `ed25519` key。
- 新 key：
  - 公钥 comment：`liuyibo20250502CUHKSZ`
  - 私钥路径不写入公开记录。
- 已将公钥添加到远端 `~/.ssh/authorized_keys`。
- 验证 key 登录：`KEY_LOGIN_OK`
- 此后 A800 操作使用 SSH key 登录；密码不写入项目文件或环境文件。

### 13:31 P1 Beta Sweep 工具

- 阅读 `TODO.md` 后，选择 P1.3 作为第一项 P1 实验：
  - 单卡 A800 可直接完成。
  - 不依赖新的公开数据采集。
  - 能直接诊断 DPO beta 对适配性回退的影响。
- 修改共享训练配置处理：
  - 文件：`src/finpref/train/common.py`
  - 新增透传配置字段：`seed`、`data_seed`
- 新增 P1 beta sweep 运行脚本：
  - `scripts/13_run_p1_beta_sweep.sh`
  - 默认 beta：`0.03 0.05 0.1 0.2`
  - 使用相同 SFT adapter、DPO train data 和 300-case eval set
  - adapter 输出：`/autodl-fs/data/finpref/outputs/p1_beta_sweep/`
  - eval 输出：`outputs/eval/p1_beta_sweep/`
- 新增 P1 sweep 汇总脚本：
  - `scripts/13_summarize_p1_sweep.py`
  - 生成 `outputs/eval/p1_beta_sweep/summary.csv`
  - 生成 `reports/p1_beta_sweep.md`
  - 统计 rule metrics、badcase 数量、SFT-pass / variant-fail 数量
- 本地验证：
  - `python -m py_compile scripts/13_summarize_p1_sweep.py src/finpref/train/common.py`
  - `pytest -q`：`11 passed`
- 远端同步后验证：
  - `python -m py_compile scripts/13_summarize_p1_sweep.py src/finpref/train/common.py`
  - `pytest -q`：`11 passed`
  - `bash scripts/06_train_dpo.sh --dry_run`：DPO 配置加载正常

### 13:35 启动 P1 Beta Sweep

- 在 A800 上以后台进程启动 P1 beta sweep：
  - PID：`2135`
  - 日志：`/autodl-fs/data/finpref/logs/p1_beta_sweep_20260521_133524.log`
  - 命令：`nohup bash scripts/13_run_p1_beta_sweep.sh > "$log" 2>&1 &`
- 使用环境：
  - `HF_ENDPOINT=https://hf-mirror.com`
  - `HF_HUB_DISABLE_TELEMETRY=1`
  - `WANDB_DISABLED=true`
  - `TOKENIZERS_PARALLELISM=false`
- 首个完成变体：`dpo_beta_0_03`
  - 训练时间：约 `1191s`
  - 训练 loss：约 `0.2096`
  - 300 条 eval rule metrics：
    - 合规通过率：`100.0`
    - 风险披露覆盖率：`99.0`
    - 适配性匹配率：`94.0`
    - 澄清率：`81.82`
    - 禁用短语率：`0.0`
    - reward hacking 率：`0.0`
    - 平均回答长度：`157.67`
- 初步解释：
  - `beta=0.03` 没有恢复 P0 SFT 的适配性分数 `97.0`。
  - 它大致接近 P0 DPO 的适配性分数 `94.0`，但风险披露低于 P0 DPO。
- 当时运行状态：
  - `dpo_beta_0_05` 已完成训练，训练时间约 `1142s`，训练 loss 约 `0.1278`
  - `dpo_beta_0_05` 正在 eval generation
  - `dpo_beta_0_1` 和 `dpo_beta_0_2` 尚未完成

### 13:45 P1.4 DeepSeek Judge 脚手架

- 新增可选的 OpenAI-compatible LLM-as-a-Judge 后端：
  - 文件：`src/finpref/eval/judge_eval.py`
  - 默认后端仍是 `mock`
  - 只有配置显式选择 API judge 时才调用外部 API
- 新增 DeepSeek judge 配置：
  - `configs/judge_deepseek.yaml`
  - Base URL：`https://api.deepseek.com`
  - Model：`deepseek-v4-flash`
  - API key 环境变量名：`DEEPSEEK_API_KEY`
  - `response_format: json_object`
  - 关闭 thinking，保证 JSON scoring 更稳定
- 新增小样本运行脚本：
  - `scripts/14_run_deepseek_judge_sample.sh`
  - 默认只评估有限样本，不直接跑满 300 条
- 更新模型输出生成：
  - `src/finpref/eval/generate_model_outputs.py`
  - 保留 eval `messages`，便于 API judge 看到用户问题上下文。
- 为 `judge_eval.py` 新增 `--eval_file` 支持：
  - 旧的 P0 output 文件可以和 eval context 合并后再进行 LLM judging。
- 验证：
  - 本地 `pytest -q`：`11 passed`
  - 本地 mock judge context smoke test：通过
  - 远端 mock judge context smoke test：通过
- 凭据处理：
  - DeepSeek API key 未写入代码、配置、日志或 `Record.md`
  - API judge 运行时只通过 shell 环境变量 `DEEPSEEK_API_KEY` 传入

### 16:39 P1 Beta Sweep 完成

- P1.3 beta sweep 已在 A800 上完成。
- 远端运行产物：
  - Adapter 根目录：`/autodl-fs/data/finpref/outputs/p1_beta_sweep/`
  - Eval 根目录：`/autodl-fs/data/finpref/project/outputs/eval/p1_beta_sweep/`
  - 报告：`/autodl-fs/data/finpref/project/reports/p1_beta_sweep.md`
  - 日志：`/autodl-fs/data/finpref/logs/p1_beta_sweep_20260521_133524.log`
- 已拉回本地产物：
  - `outputs/eval/p1_beta_sweep/`
  - `reports/p1_beta_sweep.md`
  - `logs/p1_beta_sweep_20260521_133524.log`
- 本地复算 summary：
  - `PYTHONPATH=src python scripts/13_summarize_p1_sweep.py --eval_dir outputs/eval/p1_beta_sweep --baseline_details outputs/eval/sft_rule_details.jsonl --output_csv outputs/eval/p1_beta_sweep/summary.csv --output_md reports/p1_beta_sweep.md --output_json outputs/eval/p1_beta_sweep/sft_pass_variant_fail_ids.json`
- 300 条 eval cases 的最终 rule metrics：

| 模型 | Beta | 合规 | 风险披露 | 适配性 | Badcases | SFT-pass / Variant-fail | 平均长度 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dpo_beta_0_03` | `0.03` | `100.0` | `99.0` | `94.0` | `18` | `9` | `157.67` |
| `dpo_beta_0_05` | `0.05` | `100.0` | `100.0` | `94.0` | `18` | `9` | `156.92` |
| `dpo_beta_0_1` | `0.1` | `100.0` | `100.0` | `94.0` | `18` | `9` | `156.78` |
| `dpo_beta_0_2` | `0.2` | `100.0` | `100.0` | `95.0` | `15` | `6` | `156.66` |

- 结论：
  - `beta=0.2` 是本轮 deterministic rule metrics 下最好的 DPO 变体。
  - 与原始 P0 `beta=0.1` DPO 风格结果相比，适配性从 `94.0` 提升到 `95.0`，badcase 从 `18` 降到 `15`。
  - SFT-pass / DPO-variant-fail 从 `9` 降到 `6`，正好对应 P1.3 想诊断的问题。
  - 低 beta 没有恢复 P0 SFT 的适配性分数 `97.0`，说明剩余回退更可能是 preference pair / data realism 问题，而不只是 beta 设置问题。
- 下一步建议：
  - 暂时把 `beta=0.2` 作为 P1 当前最佳 DPO checkpoint。
  - 先做 P1.4 LLM-as-a-Judge 小样本，对 Base/SFT/P0-DPO/`beta=0.2` 做交叉确认。
  - 如果 LLM judge 也支持 `beta=0.2`，后续优先做 P1.1/P1.2 的真实数据和 preference pair 构造，而不是继续扩大 beta-only sweep。

### 16:48 P1.4 DeepSeek Judge 小样本

- 新增 P1 judge sample wrapper 和汇总脚本：
  - `scripts/14_run_deepseek_judge_p1_sample.sh`
  - `scripts/14_summarize_deepseek_judge.py`
- 更新 `scripts/14_run_deepseek_judge_sample.sh`：
  - 增加 `PYTHON_BIN` 参数。
  - 原因：A800 的非登录 SSH shell 只稳定暴露 `/root/miniconda3/bin/python`。
- 运行 30 条 DeepSeek judge 小样本，比较：
  - P0 Base
  - P0 SFT
  - P0 DPO
  - P1 rule-metric 最优变体：`dpo_beta_0_2`
- 命令形态：
  - `LIMIT=30 OUT_DIR=outputs/eval/deepseek_judge_sample PYTHON_BIN=/root/miniconda3/bin/python bash scripts/14_run_deepseek_judge_p1_sample.sh`
  - API key 只通过远端 shell 环境变量 `DEEPSEEK_API_KEY` 传入，运行后 unset，未落盘。
- 已拉回本地产物：
  - `outputs/eval/deepseek_judge_sample/`
  - `reports/p1_deepseek_judge_sample.md`
- 本地复算 summary：
  - `PYTHONPATH=src python scripts/14_summarize_deepseek_judge.py --eval_dir outputs/eval/deepseek_judge_sample --output_csv outputs/eval/deepseek_judge_sample/summary.csv --output_md reports/p1_deepseek_judge_sample.md`
- DeepSeek 小样本平均分，`n=30`：

| 模型 | Overall | 合规 | 适配性 | 风险披露 | 帮助性 | 过度拒答 | Reward Hacking |
|---|---:|---:|---:|---:|---:|---:|---:|
| `base` | `4.2` | `4.833` | `4.267` | `4.233` | `4.133` | `1.0` | `1.0` |
| `sft` | `4.2` | `5.0` | `4.2` | `4.9` | `3.9` | `1.1` | `1.0` |
| `dpo` | `4.167` | `5.0` | `4.167` | `4.9` | `3.9` | `1.1` | `1.0` |
| `dpo_beta_0_2` | `4.167` | `5.0` | `4.167` | `4.9` | `3.9` | `1.1` | `1.0` |

- 结论：
  - 这是 30 条 smoke sample，只能作为方向性证据，不能作为最终结论。
  - DeepSeek judge 与 rule metrics 一致地显示：SFT/DPO 相比 Base 改善了合规和风险披露。
  - 小样本中，`dpo_beta_0_2` 没有显示出相对 P0 DPO 的 judge-score 优势；但它在完整 300 条 rule metrics 上更好。
  - SFT/DPO 的 helpfulness 低于 Base，说明下一步更值得做 preference pair 真实性和“少一点模板化安全回答”的数据改造，而不是立刻继续 beta-only sweep。

### 16:57 最终检查

- 本地验证：
  - `PYTHONPATH=src pytest -q`：`11 passed`
- 远端检查：
  - 无残留 `13_run_p1_beta_sweep`、`train_dpo`、`generate_model_outputs`、`judge_eval` 进程。
  - 远端存在关键产物：
    - `outputs/eval/p1_beta_sweep/summary.csv`
    - `outputs/eval/deepseek_judge_sample/summary.csv`
    - `reports/p1_beta_sweep.md`
    - `reports/p1_deepseek_judge_sample.md`
- 当前建议：
  - P1.3：报告中使用 `beta=0.2` 作为当前最佳 DPO sweep 结果。
  - P1.4：后续可扩大 DeepSeek judge 到全量 300 条，或优先抽查 SFT-pass / DPO-fail case。
  - 更重要的下一步：推进 P1.1/P1.2，引入更真实的公开金融问答数据，并构造更细的 preference pair，减少 DPO 对“安全但泛泛回答”的偏好。

### 17:10 纠正 P1 实验顺序

- 用户指出：应先做 P1.1/P1.2，再做 P1.3/P1.4。
- 结论：这个判断是对的。前面完成的 P1.3 beta sweep 和 P1.4 DeepSeek judge sample 应被定位为“基于合成数据的诊断基线”，不能视为正式 P1 主线已经完成。
- 当前正式顺序调整为：
  - P1.1：先接入公开金融 QA / 投顾相关数据，做清洗、去重、schema 归一化和 meta 补全。
  - P1.2：再基于公开数据构造更真实的 SFT 样本和 DPO preference pairs。
  - P1.3/P1.4：后续在新数据上重新训练、重评估，而不是继续只调合成数据 DPO 的 beta。
- 公开数据源候选：
  - `FinLang/investopedia-instruction-tuning-dataset`
  - Hugging Face 页面显示该数据集为公开数据集，CSV 格式，约 229k 行，license 为 `cc-by-nc-4.0`。
  - 字段包括 `Topic`、`Title`、`Context`、`Question`、`Answer` 等。
- 数据性质判断：
  - 这是公开 Investopedia 风格金融知识问答数据，不是纯合成数据。
  - 该数据更偏金融知识 QA，并非天然投顾对话；因此需要在 P1.1 中补用户画像、产品风险等级、适当性和合规 meta，在 P1.2 中构造风险披露、买卖指令、收益承诺、过度拒答等 hard negative。
- 安全约定：
  - 不把 DeepSeek API key、SSH 密码、私钥等敏感凭据写入本文件或代码。
  - 如后续需要 LLM API，只通过环境变量传入。

### 17:40 P1.1/P1.2 公开数据接入与 preference pair 构造

- 新增代码：
  - `src/finpref/data/public_finance.py`
  - `scripts/15_prepare_public_finance_data.py`
  - `tests/test_public_finance.py`
- 数据源：
  - `FinLang/investopedia-instruction-tuning-dataset`
  - split：`train`
  - license：`cc-by-nc-4.0`
  - 这次使用的是公开数据集，不是纯合成数据；但用户画像、产品风险等级、适当性标签和 rejected hard negatives 由规则补全/构造。
- 清洗与筛选：
  - 随机抽取 `50000` 条源样本，seed 为 `20260521`。
  - 为了拿到 `5000` 条可用公开金融 QA，实际扫描 `11949` 条。
  - 过滤统计：
    - 金融相关性不足：`6415`
    - 明显文章抽取噪声题：`22`
    - 低质量答案：`499`
    - 答案含直接买卖/交易指令：`4`
    - 重复问题：`8`
    - 缺 question 或 answer：`1`
  - 额外修正：
    - 抽查发现有“Residual Standard Deviation”一类统计题混入，已增加 finance relevance 过滤。
    - 抽查发现有“suggested trading strategy / buy on weakness / reduce holdings”一类文章交易策略抽取题，已增加 source artifact 和 direct-advice 过滤。
    - 将 `risk-free rate` 这类金融概念题从收益承诺误标中排除，避免把正常概念 QA 错标为 `yield_promise`。
- 生成结果：
  - `data/processed/public_finance_sft.jsonl`：`5000` 条。
  - `data/processed/public_finance_dpo.jsonl`：`5000` 条。
  - `data/processed/sft_train_p1_public_mix.jsonl`：`8000` 条，即 P0 synthetic SFT `3000` + P1 public SFT `5000`。
  - `data/processed/dpo_train_p1_public_mix.jsonl`：`8000` 条，即 P0 synthetic DPO `3000` + P1 public DPO `5000`。
  - `outputs/data/public_finance_stats.json`：清洗与分布统计。
  - `outputs/data_validation_p1_public_mix.json`：schema 验证结果。
- P1 public SFT query type 分布：
  - `financial_qa`: `3799`
  - `numerical_reasoning`: `505`
  - `comparison`: `323`
  - `risk_disclosure`: `236`
  - `compliance_boundary`: `73`
  - `suitability`: `47`
  - `yield_promise`: `14`
  - `direct_recommendation`: `3`
- P1 public SFT product risk level 分布：
  - `R1`: `30`
  - `R2`: `651`
  - `R3`: `2076`
  - `R4`: `1550`
  - `R5`: `693`
- DPO preference pair 设计：
  - chosen：清洗后的公开金融 QA 答案，必要时补充风险披露、适当性说明、不得承诺收益/不得直接买卖指令提醒。
  - rejected：规则构造 hard negatives，包括：
    - `missing_risk_disclosure`
    - `direct_buy_sell`
    - `yield_promise`
    - `generic_safe_answer`
    - `risk_mismatch_ignored`
    - `over_refusal`
  - pair-level meta 已补：
    - `rejected_type`
    - `preference_reason`
    - `suitability_focus`
    - `compliance_focus`
    - `risk_disclosure_focus`
    - `judge_confidence`
    - `pair_source`
- 验证：
  - A800：`PYTHONPATH=src /root/miniconda3/bin/python scripts/04_validate_data.py --sft_file data/processed/sft_train_p1_public_mix.jsonl --dpo_file data/processed/dpo_train_p1_public_mix.jsonl --grpo_file data/processed/grpo_train.jsonl --output outputs/data_validation_p1_public_mix.json`
  - 结果：SFT `8000 failed=0`，DPO `8000 failed=0`，GRPO `2000 failed=0`。
  - A800：`PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q`
  - 结果：`15 passed`。
  - 抽查 DPO chosen 中常见直接买入/减仓模式，命中数 `0`。
- 当前判断：
  - P1.1/P1.2 已形成第一版公开数据增强流水线，可以作为下一步重新训练 SFT/DPO 的输入。
  - 这版仍主要依赖规则清洗和规则构造 rejected，尚未使用 DeepSeek 做 ambiguous meta labeling 或 LLM-generated hard negatives。
  - 后续更适合先用 `sft_train_p1_public_mix.jsonl` / `dpo_train_p1_public_mix.jsonl` 跑一版 P1-public SFT/DPO，再用已有 rule eval + DeepSeek judge 对比 P0 synthetic-only。

### 18:00 启动 P1-public SFT 训练

- 新增 P1-public 专用训练配置：
  - `configs/sft_qwen2_5_3b_lora_p1_public.yaml`
  - `configs/dpo_qwen2_5_3b_lora_p1_public.yaml`
  - `scripts/16_run_p1_public_sft_dpo.sh`
- SFT 配置要点：
  - base model：`Qwen/Qwen2.5-3B-Instruct`
  - train file：`data/processed/sft_train_p1_public_mix.jsonl`
  - output dir：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public`
  - epoch：`1`
  - LoRA：`r=16`，`alpha=32`，`dropout=0.05`
  - seed / data_seed：`20260521`
- DPO 预设配置要点：
  - SFT adapter：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public/adapter`
  - train file：`data/processed/dpo_train_p1_public_mix.jsonl`
  - output dir：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_beta_0_2`
  - beta：`0.2`
  - epoch：`1`
- 本地检查：
  - `train_sft.py --dry_run`：通过。
  - `train_dpo.py --dry_run`：通过。
  - `pytest -q tests/test_public_finance.py tests/test_validators.py tests/test_schema.py`：`9 passed`。
- A800 检查：
  - GPU 空闲后启动。
  - `train_sft.py --dry_run` / `train_dpo.py --dry_run`：通过。
- 启动命令形态：
  - `HF_ENDPOINT=https://hf-mirror.com PYTHON_BIN=/root/miniconda3/bin/python RUN_DPO=0 nohup bash scripts/16_run_p1_public_sft_dpo.sh > /autodl-fs/data/finpref/logs/p1_public_sft_20260521_180007.log 2>&1 &`
- 进程：
  - wrapper PID：`11924`
  - accelerate PID：`11927`
  - `train_sft.py` PID：`11994`
- 日志：
  - `/autodl-fs/data/finpref/logs/p1_public_sft_20260521_180007.log`
- 当前进展：
  - 模型 checkpoint shards 已加载。
  - `8000` 条 SFT public-mix 数据已完成 ChatML 转换、chat template 和 tokenization。
  - 训练已进入正式 training 阶段。

### 18:25 P1-public SFT 完成

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public/adapter`
- 中间 checkpoint：
  - `checkpoint-200`
  - `checkpoint-400`
- 最终 adapter 文件已落盘：
  - `adapter_model.safetensors`
  - `adapter_config.json`
  - tokenizer 相关文件
- 训练结果：
  - total steps：`500`
  - train runtime：`1415.9038s`
  - train samples / second：`5.65`
  - train steps / second：`0.353`
  - train loss：`0.7598914585`
  - epoch：`1.0`
- 最后阶段 loss 稳定在约 `0.45` - `0.50` 区间。
- GPU 峰值观察：
  - 训练中显存大约 `18.9GB` 到 `23.5GB`。
- 下一步：
  - 使用该 SFT adapter 作为 policy/ref 初始化，启动 P1-public DPO。
  - DPO 配置：`configs/dpo_qwen2_5_3b_lora_p1_public.yaml`
  - DPO beta：`0.2`

### 18:27 启动 P1-public DPO 训练

- 使用 SFT adapter：
  - `/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public/adapter`
- DPO train file：
  - `data/processed/dpo_train_p1_public_mix.jsonl`
- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_beta_0_2`
- 日志：
  - `/autodl-fs/data/finpref/logs/p1_public_dpo_20260521_182648.log`
- 进程：
  - accelerate PID：`12871`
  - `train_dpo.py` PID：`12938`
- 初始状态：
  - policy/ref model checkpoint shards 均已加载。
  - `8000` 条 DPO public-mix 数据已加载。
  - 已完成 prompt extraction、chat template 和 tokenization。
  - 训练进入正式 training 阶段。
- 预计：
  - total steps：`500`
  - 单步约 `6.4s`
  - 总训练时间约 `50` 多分钟。

### 18:54 P1-public DPO 训练中检查

- A800 训练仍在运行：
  - wrapper PID：`12870`
  - accelerate PID：`12871`
  - `train_dpo.py` PID：`12938`
- 当前观察：
  - 训练约运行 `27` 分钟。
  - GPU 显存约 `23647 MiB`，利用率约 `35%`。
  - 已生成中间 checkpoint：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_beta_0_2/checkpoint-200`
  - 最终 `adapter/` 目录尚未生成，说明 DPO 尚未结束。
- 下一步：
  - 继续等待 DPO 跑完。
  - 训练结束后记录 runtime、train loss、steps/s、checkpoint 和 adapter 文件。
  - 随后用 P1-public SFT/DPO adapter 跑规则评测，输出到 `outputs/eval/p1_public`。

### 19:20 P1-public DPO 完成

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_beta_0_2/adapter`
- 中间 / 最终 checkpoint：
  - `checkpoint-400`
  - `checkpoint-500`
- 最终 adapter 文件已落盘：
  - `adapter_model.safetensors`
  - `adapter_config.json`
  - tokenizer 相关文件
  - `training_args.bin`
- 训练结果：
  - total steps：`500`
  - train runtime：`3173.6684s`
  - train samples / second：`2.521`
  - train steps / second：`0.158`
  - train loss：`0.021122076296334853`
  - epoch：`1.0`
- 训练结束后 GPU 空闲：
  - `0 MiB`，`0%`
- 观察：
  - 后半段 DPO reward margin 很快拉大，`rewards/accuracies` 长时间为 `1.0`。
  - 这说明偏好对区分被模型学得很强，后续必须通过 eval 检查是否出现过度偏好模板化、过度安全或信息量下降。
- 下一步：
  - 使用 P1-public SFT adapter 和 P1-public DPO adapter 跑全量 `eval_finpref.jsonl` 规则评测。
  - 评测输出目录：`outputs/eval/p1_public`

### 19:28 启动 P1-public 全量评测

- 评测目标：
  - Base：`Qwen/Qwen2.5-3B-Instruct`
  - SFT：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public/adapter`
  - DPO：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_beta_0_2/adapter`
- 评测数据：
  - `data/processed/eval_finpref.jsonl`
  - 共 `300` 条。
- 输出目录：
  - `outputs/eval/p1_public`
- 日志：
  - `/autodl-fs/data/finpref/logs/p1_public_eval_20260521_1928.log`
- 启动修正：
  - 第一次直接跑 `scripts/12_eval_p0_models.sh` 失败，原因是远端默认环境没有 `python` 命令。
  - 第二次手写长命令有 shell quote 错误。
  - 第三次通过 `export PATH=/root/miniconda3/bin:$PATH` 后调用原脚本，评测已正常进入 Base 输出生成阶段。
- 当前状态：
  - `generate_model_outputs.py` 正在生成 `base_outputs.jsonl`。
  - GPU 显存约 `6703 MiB`，利用率约 `44%`。
  - 该脚本是全部生成结束后才写 JSONL，因此中途输出目录暂时没有文件属于正常现象。

### 21:26 P1-public 全量规则评测完成

- 远端输出目录：
  - `/autodl-fs/data/finpref/project/outputs/eval/p1_public`
- 本地已拉回：
  - `outputs/eval/p1_public`
- 生成文件：
  - `base_outputs.jsonl`
  - `sft_outputs.jsonl`
  - `dpo_outputs.jsonl`
  - `*_rule_metrics.json`
  - `*_rule_details.jsonl`
  - `*_judge_scores.jsonl`
- 注意：
  - 这里的 `*_judge_scores.jsonl` 来自默认 `configs/judge.yaml` 的 mock judge，不是 DeepSeek API 评审。

规则指标：

| model | compliance | risk disclosure | suitability | clarification | forbidden phrase | avg len |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `97.0` | `100.0` | `91.0` | `100.0` | `3.0` | `656.66` |
| P1-public SFT | `100.0` | `100.0` | `96.0` | `100.0` | `0.0` | `156.92` |
| P1-public DPO | `100.0` | `96.0` | `98.0` | `90.91` | `0.0` | `155.93` |

Badcase 计数：

- Base：
  - compliance fail：`9`
  - risk disclosure fail：`0`
  - suitability fail：`27`
  - clarification fail when required：`0`
  - forbidden phrase：`9`
  - badcase union：`36`
- P1-public SFT：
  - compliance fail：`0`
  - risk disclosure fail：`0`
  - suitability fail：`12`
  - clarification fail when required：`0`
  - forbidden phrase：`0`
  - badcase union：`12`
- P1-public DPO：
  - compliance fail：`0`
  - risk disclosure fail：`12`
  - suitability fail：`6`
  - clarification fail when required：`3`
  - forbidden phrase：`0`
  - badcase union：`18`

SFT / DPO 差异：

- SFT-pass / DPO-fail：`12`
  - `eval_000029`
  - `eval_000040`
  - `eval_000060`
  - `eval_000074`
  - `eval_000129`
  - `eval_000140`
  - `eval_000160`
  - `eval_000174`
  - `eval_000229`
  - `eval_000240`
  - `eval_000260`
  - `eval_000274`
- DPO-pass / SFT-fail：`6`
  - `eval_000032`
  - `eval_000096`
  - `eval_000132`
  - `eval_000196`
  - `eval_000232`
  - `eval_000296`

初步解读：

- P1-public SFT 相比 Base 明显改善合规和适当性：
  - compliance：`97.0` -> `100.0`
  - suitability：`91.0` -> `96.0`
  - forbidden phrase：`3.0` -> `0.0`
  - 平均长度从 `656.66` 降到 `156.92`，回答更短、更像经过安全对齐后的投顾答复。
- P1-public DPO 相比 SFT：
  - suitability 从 `96.0` 提升到 `98.0`。
  - 但 risk disclosure 从 `100.0` 降到 `96.0`，clarification 从 `100.0` 降到 `90.91`。
  - badcase union 从 SFT 的 `12` 增加到 DPO 的 `18`。
- 因此当前 P1-public DPO 并不是单调优于 SFT：
  - 它修复了一部分 suitability failure。
  - 但引入了风险披露和澄清不足的新失败。
  - 这与 DPO 训练中 reward margin 很快拉大相呼应，可能说明 preference pair 让模型学到了更强的偏好边界，但也牺牲了部分必要的风险披露模板。

下一步建议：

- 对 `12` 个 SFT-pass / DPO-fail 做人工 spot-check，确认是否真的是风险披露 / 澄清缺失，还是 rule evaluator 过严。
- 用 DeepSeek judge 对 Base / P1-public SFT / P1-public DPO 抽样评审，重点看：
  - suitability
  - risk_disclosure
  - helpfulness
  - over_refusal
- 若 DeepSeek judge 也确认 DPO 的风险披露下降，则需要回到 P1.2：
  - 增加 `missing_risk_disclosure` hard negative 的权重或样本量。
  - 在 chosen 中强化“短答也必须保留风险披露”的样式。
  - 重新训练一个 P1-public DPO beta / pair-ratio 小实验。

### 23:36 P1-public 差异样例 spot-check 与 DeepSeek judge

- 新增诊断文件：
  - `reports/p1_public_spotcheck.md`
  - `outputs/eval/p1_public/sft_dpo_diff_ids.json`
  - `outputs/eval/p1_public_deepseek_diff_sample/summary.csv`
  - `outputs/eval/p1_public_deepseek_diff_sample/group_summary.csv`
  - `reports/p1_public_deepseek_diff_sample.md`
  - `reports/p1_public_deepseek_diff_group_summary.md`
- 同时改进了 `src/finpref/eval/judge_eval.py`：
  - 增加 `--incremental`：逐条写入 judge 结果，避免整批结束才落盘。
  - 增加 `--resume`：跳过输出文件里已经完成的样本。
  - 捕获 `TimeoutError` / `socket.timeout`，DeepSeek 单次 API 超时会按重试逻辑处理。
- 验证：
  - `PYTHONPATH=src python -m pytest -q tests/test_rule_eval.py tests/test_schema.py`
  - 结果：`5 passed`

差异样例规则诊断：

- `SFT-pass / DPO-fail` 共 `12` 个：
  - 全部是 DPO 的 `risk_disclosure_fail`。
  - 典型模式：
    - DPO 会说“需要谨慎 / 不匹配 / 联系持牌专业人员”，但没有明确列出足够风险项。
    - 对 R5 structured product 的回答缺少“本金损失、净值波动、流动性、费用”等具体风险词。
    - 对 direct recommendation 场景，DPO 能拒绝直接买卖指令，但风险披露不如 SFT 具体。
- `DPO-pass / SFT-fail` 共 `6` 个：
  - 全部是 SFT 的 `suitability_fail` 被 DPO 修复。
  - 说明 DPO 的确强化了“风险等级 / 风险承受能力 / 期限流动性匹配”的适当性判断。

DeepSeek judge：18 个差异样例整体均值

| model | n | overall | compliance | suitability | risk disclosure | helpfulness | over-refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `18` | `3.833` | `4.833` | `3.722` | `4.667` | `3.833` | `1.056` |
| P1-public SFT | `18` | `4.167` | `5.0` | `4.167` | `4.667` | `3.667` | `1.333` |
| P1-public DPO | `18` | `4.167` | `5.0` | `4.167` | `4.0` | `3.333` | `1.667` |

DeepSeek judge：按差异类型分组

| group | model | n | overall | suitability | risk disclosure | helpfulness | over-refusal |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SFT-pass / DPO-fail | Base | `12` | `4.0` | `4.167` | `4.75` | `4.0` | `1.083` |
| SFT-pass / DPO-fail | P1-public SFT | `12` | `4.0` | `4.0` | `4.5` | `3.5` | `1.5` |
| SFT-pass / DPO-fail | P1-public DPO | `12` | `3.75` | `3.75` | `3.5` | `3.0` | `2.0` |
| DPO-pass / SFT-fail | Base | `6` | `3.5` | `2.833` | `4.5` | `3.5` | `1.0` |
| DPO-pass / SFT-fail | P1-public SFT | `6` | `4.5` | `4.5` | `5.0` | `4.0` | `1.0` |
| DPO-pass / SFT-fail | P1-public DPO | `6` | `5.0` | `5.0` | `5.0` | `4.0` | `1.0` |

结论：

- DeepSeek judge 支持 rule eval 的主判断：
  - DPO 的确修复了一批 suitability failure。
  - 但在 SFT-pass / DPO-fail 组里，DPO 的 risk disclosure、helpfulness 和 overall 都低于 SFT。
- 因此当前 DPO 问题不是 rule evaluator 单独误伤，而是真实存在“适当性更强、风险披露更弱”的 trade-off。

DeepSeek judge：标准前 30 条 smoke

| model | n | overall | compliance | suitability | risk disclosure | helpfulness | over-refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `30` | `4.2` | `4.8` | `4.267` | `4.267` | `4.133` | `1.0` |
| P1-public SFT | `30` | `4.233` | `5.0` | `4.233` | `4.9` | `3.9` | `1.1` |
| P1-public DPO | `30` | `4.1` | `4.867` | `4.033` | `4.633` | `3.5` | `1.467` |

进一步判断：

- 在标准 30 条 smoke 上，P1-public SFT 是三者里最稳的：
  - overall `4.233`，略高于 Base `4.2` 和 DPO `4.1`。
  - compliance / risk_disclosure 明显更好。
- P1-public DPO 的 suitability 在标准 30 条上没有超过 SFT，且 helpfulness / over_refusal 更差。
- 下一步不建议继续直接扩大当前 DPO；更合理的是回到 P1.2 修 preference pair：
  - chosen 中保留“简短但具体风险披露”的模板。
  - rejected 中增加“只有谨慎/不匹配、但没有具体风险项”的 hard negative。
  - 对 `missing_risk_disclosure` 和 `risk_mismatch_ignored` 做 pair-ratio 小实验。

### 00:08 P1-public v2 preference pair 修正

- 修改目标：
  - 修复 P1-public DPO 中“适当性更强、风险披露更弱”的 trade-off。
  - 不直接扩大原 DPO，而是先回到 P1.2 修 preference pair。
- 代码修改：
  - `src/finpref/data/public_finance.py`
    - 新增 rejected type：`caution_without_specific_risks`
    - 该 hard negative 模拟“只说需要谨慎 / 不匹配 / 找专业人士，但不列具体风险项”的回答。
    - 对 `should_disclose_risk=True` 的 chosen，强制补充中文具体风险披露：
      - 市场风险
      - 净值波动
      - 流动性限制
      - 费用税费
      - 本金损失
  - `tests/test_public_finance.py`
    - 增加 chosen 风险披露保留测试。
    - 增加 `caution_without_specific_risks` hard negative 测试。
- 本地测试：
  - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`14 passed`
- A800 测试：
  - `PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`14 passed`

### 00:10 生成 P1-public v2 数据

- 远端生成命令使用：
  - `scripts/15_prepare_public_finance_data.py`
  - `max_source_rows=50000`
  - `max_kept=5000`
  - `num_sft=5000`
  - `num_dpo=5000`
- v2 输出：
  - `data/processed/public_finance_sft_v2.jsonl`
  - `data/processed/public_finance_dpo_v2.jsonl`
  - `data/processed/sft_train_p1_public_mix_v2.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v2.jsonl`
  - `outputs/data/public_finance_v2_stats.json`
  - `outputs/data_validation_p1_public_mix_v2.json`
- 清洗统计与 v1 一致：
  - source loaded：`50000`
  - source seen until kept：`11949`
  - cleaned cases：`5000`
  - SFT rows：`5000`
  - DPO rows：`5000`
  - combined SFT rows：`8000`
  - combined DPO rows：`8000`
- schema 验证：
  - SFT：`8000 failed=0`
  - DPO：`8000 failed=0`
  - GRPO：`2000 failed=0`
- v2 DPO public pair 分布：
  - `caution_without_specific_risks`：`715`
  - `missing_risk_disclosure`：`715`
  - `direct_buy_sell`：`714`
  - `yield_promise`：`714`
  - `generic_safe_answer`：`714`
  - `risk_mismatch_ignored`：`714`
  - `over_refusal`：`714`
- 针对性风险披露扫描：
  - public DPO rows：`5000`
  - 需要风险披露的 public pairs：`4974`
  - chosen risk disclosure pass：`4974 / 4974 = 100.0%`
  - rejected risk disclosure pass：`0 / 4974 = 0.0%`
- 新训练配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v2.yaml`
  - 沿用 SFT adapter：`/autodl-fs/data/finpref/outputs/sft_qwen2_5_3b_finpref_p1_public/adapter`
  - train file：`data/processed/dpo_train_p1_public_mix_v2.jsonl`
  - output dir：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v2_beta_0_2`
  - beta：`0.2`
  - seed / data_seed：`20260522`
- dry-run：
  - `train_dpo.py --config configs/dpo_qwen2_5_3b_lora_p1_public_v2.yaml --dry_run`
  - 结果：通过。

下一步：

- 启动 P1-public v2 DPO 小实验。
- 训练后同口径评测：
  - full rule eval：`outputs/eval/p1_public_v2`
  - DeepSeek 30-case smoke
  - 重点比较：
    - v1 DPO risk disclosure `96.0`
    - v1 DPO suitability `98.0`
    - v1 DPO DeepSeek 30 overall `4.1`
    - P1-public SFT DeepSeek 30 overall `4.233`

### 00:16 启动 P1-public v2 DPO 训练

- 启动方式：
  - `accelerate launch src/finpref/train/train_dpo.py --config configs/dpo_qwen2_5_3b_lora_p1_public_v2.yaml`
- 日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v2_dpo_20260522_0012.log`
- 进程：
  - wrapper PID：`22711`
  - accelerate PID：`22713`
  - `train_dpo.py` PID：`22778`
- 当前状态：
  - policy/ref model checkpoint shards 已加载。
  - `8000` 条 v2 DPO public-mix 数据已加载。
  - prompt extraction、chat template、tokenization 已完成。
  - 已进入正式 training。
  - 当前约 `21/500` steps。
- GPU：
  - 显存约 `22777 MiB`
  - 利用率约 `47%`
- 预计：
  - 单步约 `6.3s`
  - 总训练时间约 `50` 多分钟。

### 00:51 P1-public v2 DPO 首次训练中断与处理

- 训练在 `200/500` step 处中断。
- 失败位置：
  - 保存中间 checkpoint：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v2_beta_0_2/checkpoint-200`
- 报错：
  - `OSError: [Errno 28] No space left on device`
- 诊断：
  - `/autodl-fs/data` 容量仍充足，约 `174G` 可用。
  - inode 曾接近耗尽；复查时为 `196K` inodes，已用约 `176K`，可用约 `21K`，使用率约 `90%`。
  - 这次更像是中间 checkpoint 创建目录/文件时触发的 inode 压力，而不是数据盘容量不足。
- 处理：
  - 将 `configs/dpo_qwen2_5_3b_lora_p1_public_v2.yaml` 的保存频率从 `save_steps: 200` 改为 `save_steps: 1000`。
  - 将 `save_total_limit` 从 `2` 改为 `1`。
  - 目标是避免 `500` step 训练过程中在 `200/400` 额外保存中间 checkpoint，只保留最终 adapter，减少 inode 消耗。
- 下一步：
  - 清理本次失败留下的空输出目录。
  - 同步新配置到 A800。
  - 重新启动 P1-public v2 DPO 训练，并继续监控到完成。

### 01:25 P1-public v2 DPO 重启后越过 200 step

- 重启日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v2_dpo_20260522_0100.log`
- 修复后的配置已在 A800 上生效：
  - `save_steps: 1000`
  - `save_total_limit: 1`
- 训练已越过原失败点：
  - 当前约 `208/500` step。
  - 未出现 `checkpoint-200`。
  - 未出现 `OSError` / `No space left on device`。
- inode 状态：
  - `/autodl-fs/data` 约 `196K` inodes，已用约 `176K`，可用约 `21K`，使用率约 `90%`。
- 判断：
  - 通过提高 `save_steps` 避免中间 checkpoint 的策略有效。
  - 继续等待最终 adapter 保存，然后做同口径 rule eval 与 DeepSeek 30-case smoke。

### 01:54 P1-public v2 DPO 训练完成

- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v2_dpo_20260522_0100.log`
- 最终 adapter：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v2_beta_0_2/adapter`
- adapter 文件确认：
  - `adapter_model.safetensors` 已生成，大小约 `120MB`。
  - 输出目录整体约 `488MB`。
- 训练指标：
  - `train_runtime`: `3154.3543`
  - `train_samples_per_second`: `2.536`
  - `train_steps_per_second`: `0.159`
  - `train_loss`: `0.018911885577312205`
  - `epoch`: `1.0`
- 训练期间未再出现：
  - `OSError`
  - `No space left on device`
  - `Traceback`
- inode 状态：
  - `/autodl-fs/data` 仍约 `90%` inode 使用率，最终 adapter 保存成功。

### 01:58 启动 P1-public v2 DPO 规则评测输出生成

- 为避免重复计算，复用已有：
  - `outputs/eval/p1_public/base_outputs.jsonl`
  - `outputs/eval/p1_public/sft_outputs.jsonl`
  - `outputs/eval/p1_public/dpo_outputs.jsonl`
- 新增生成 v2 DPO 输出：
  - `outputs/eval/p1_public_v2/dpo_outputs.jsonl`
- 生成日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v2_eval_generate_20260522_0158.log`
- 当前状态：
  - v2 adapter 已加载。
  - GPU 正在生成 300 条 held-out eval 输出。
- 后续：
  - 生成完成后运行 `rule_eval.py`。
  - 汇总 v2 与 Base / P1-public SFT / P1-public v1 DPO 的指标差异。
  - 再做 DeepSeek 30-case smoke。

### 02:30 P1-public v2 DPO rule eval 完成

- v2 DPO 300 条 held-out 输出：
  - `outputs/eval/p1_public_v2/dpo_outputs.jsonl`
  - 行数：`300`
- rule eval 结果：

| model | compliance | risk disclosure | suitability | clarification | over-refusal | avg length |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `97.0` | `100.0` | `91.0` | `100.0` | `0.0` | `656.66` |
| P1-public SFT | `100.0` | `100.0` | `96.0` | `100.0` | `0.0` | `156.92` |
| P1-public DPO v1 | `100.0` | `96.0` | `98.0` | `90.91` | `0.0` | `155.93` |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `0.0` | `151.2` |

- 失败集变化：
  - v1 DPO risk fail：`12`
  - v2 DPO risk fail：`3`
  - v1 与 v2 共同 risk fail：`0`
  - v2 修复了 v1 的全部 `12` 个 risk fail。
  - v2 新增 risk fail：`eval_000051`、`eval_000151`、`eval_000251`
  - v1 DPO suitability fail：`6`
  - v2 DPO suitability fail：`6`
  - 共同 suitability fail：`3`
  - v2 修复 suitability fail：`eval_000051`、`eval_000151`、`eval_000251`
  - v2 新增 suitability fail：`eval_000027`、`eval_000127`、`eval_000227`
- 输出报告：
  - `outputs/eval/p1_public_v2/rule_summary.csv`
  - `outputs/eval/p1_public_v2/failure_overlap.json`
  - `reports/p1_public_v2_rule_summary.md`
- 初步判断：
  - v2 preference pair 的风险披露修复有效：risk disclosure 从 v1 `96.0` 回升到 `99.0`。
  - suitability 保持 v1 的 `98.0`，没有回落到 SFT 的 `96.0`。
  - clarification 从 v1 `90.91` 回到 `100.0`，说明 v1 DPO 的“过度简化/漏问画像”问题有所缓解。

### 02:36 P1-public v2 DPO DeepSeek 30-case smoke 完成

- 样本口径：
  - 复用 P1-public sample30：`eval_000001` 到 `eval_000030`
  - v2 输入：`outputs/eval/p1_public_v2_deepseek_sample30/dpo_outputs_limit_30.jsonl`
- DeepSeek judge 输出：
  - `outputs/eval/p1_public_v2_deepseek_sample30/dpo_deepseek_judge_scores.jsonl`
  - 行数：`30`
- v2 summary：

| model | n | overall | compliance | suitability | risk disclosure | helpfulness | over-refusal | reward hacking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1-public DPO v2 | `30` | `4.3` | `5.0` | `4.233` | `4.867` | `3.833` | `1.2` | `1.0` |

- 与上一版 sample30 对比：

| model | n | overall | compliance | suitability | risk disclosure | helpfulness | over-refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `30` | `4.2` | `4.8` | `4.267` | `4.267` | `4.133` | `1.0` |
| P1-public SFT | `30` | `4.233` | `5.0` | `4.233` | `4.9` | `3.9` | `1.1` |
| P1-public DPO v1 | `30` | `4.1` | `4.867` | `4.033` | `4.633` | `3.5` | `1.467` |
| P1-public DPO v2 | `30` | `4.3` | `5.0` | `4.233` | `4.867` | `3.833` | `1.2` |

- 判断：
  - DeepSeek smoke 支持 rule eval 的方向：v2 DPO 相比 v1 DPO 明显恢复 risk disclosure、suitability 和 helpfulness。
  - v2 DPO 的 overall `4.3` 高于 SFT 的 `4.233` 和 v1 DPO 的 `4.1`。
  - v2 risk disclosure `4.867` 接近 SFT 的 `4.9`，同时 suitability 与 SFT 持平。
  - 仍需人工 spot-check v2 新增的 3 个 risk fail 和 3 个 suitability fail，避免只是指标迁移。

### 02:50 P1-public v2 失败样本 spot-check

- 新增报告：
  - `reports/p1_public_v2_failure_spotcheck.md`
- spot-check 对象：
  - v2 新增 risk fail：`eval_000051`、`eval_000151`、`eval_000251`
  - v2 新增 suitability fail：`eval_000027`、`eval_000127`、`eval_000227`
  - v1/v2 共同 suitability fail：`eval_000087`、`eval_000187`、`eval_000287`
- 结论：
  - v2 的主方向正确：修复了 v1 的全部 `12` 个 risk-disclosure rule fail，并把 DeepSeek sample30 overall 提到 `4.3`。
  - 剩余失败不是随机噪声，主要集中在两个模式。
- 模式 A：`insufficient_info + risk_mismatch`
  - 样本：`eval_000051`、`eval_000151`、`eval_000251`
  - v2 会明确说“信息不足 / 不能直接判断 / 风险不匹配”，但有时没有列出足够具体的风险项。
  - 结果：suitability 通过，但 risk disclosure fail。
  - 这说明 v2 在这些样本上把 v1 的适当性问题补上了，却牺牲了具体风险披露。
- 模式 B：`compliance_boundary + risk_mismatch`
  - 样本：`eval_000027`、`eval_000127`、`eval_000227`
  - 用户是低风险承受能力，产品是 `R4 equity_fund`。
  - v2 回复有风险披露，但只说“可以作为了解对象 / 综合判断”，没有明确写出风险等级与用户风险承受能力不匹配。
  - 结果：risk disclosure 通过，但 suitability fail。
- 持续存在的 suitability fail：
  - `eval_000087`、`eval_000187`、`eval_000287`
  - SFT、v1、v2 都倾向于只要求补充信息，而没有同步指出已知的风险不匹配。
- 下一轮 v3 数据修补建议：
  - 新增或加权 hard negative：`asks_clarification_but_omits_mismatch`
  - 新增或加权 hard negative：`mismatch_caution_without_specific_risks`
  - 对 `risk_mismatch=True` 的 chosen 模板强制加入中文显式短语：`风险等级与风险承受能力不匹配`、`不适合直接买入`、`需谨慎评估` 中至少一个。
  - 对 `requires_clarification=True and should_disclose_risk=True` 的 chosen 模板强制同时包含澄清项和至少两个具体风险项。
  - 下一轮先做小规模 v3 data validation + 300-case eval，确认新增失败 ID 是否被修复，再决定是否扩大重训。

### 03:00 P1-public v3 repair 数据逻辑补齐

- 目标：针对 v2 spot-check 后剩余的两个失败模式，先做数据修补和验证，不立即扩大重训。
- 修改内容：
  - `src/finpref/data/public_finance.py`
    - 新增 `REPAIR_REJECTED_TYPES`：
      - `asks_clarification_but_omits_mismatch`
      - `mismatch_caution_without_specific_risks`
    - 新增 repair chosen/rejected 构造函数和 `build_repair_dpo_rows`。
    - repair chosen 明确同时覆盖：
      - `风险等级与风险承受能力不匹配`
      - 澄清投资目标、投资期限、流动性需求、可承受亏损和税费情况
      - 市场风险、净值波动、流动性限制、费用税费、本金损失
      - 不承诺收益、不输出买卖指令
    - `prepare_public_finance_data` 新增 `num_repair_dpo` 参数，并把 repair DPO pairs 追加到 public DPO 数据末尾。
  - `scripts/15_prepare_public_finance_data.py`
    - 新增 CLI 参数 `--num_repair_dpo`。
  - `tests/test_public_finance.py`
    - 新增 repair 单测，锁定 chosen 必须通过 compliance、suitability、risk disclosure、clarification。
    - 验证两个 rejected 类型分别只漏掉目标维度：
      - `asks_clarification_but_omits_mismatch`：risk disclosure 和 clarification 通过，但 suitability fail。
      - `mismatch_caution_without_specific_risks`：suitability 和 clarification 通过，但 risk disclosure fail。
    - 验证 repair DPO row 可通过 schema validator，且 `pair_source == public_v2_failure_repair`。
- 本地验证：
  - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`18 passed`
  - `python -m py_compile src/finpref/data/public_finance.py scripts/15_prepare_public_finance_data.py`
  - 结果：通过。
- 下一步：
  - 同步上述代码到 A800。
  - 在 A800 上跑同一组测试。
  - 生成 v3 public 数据，先检查 stats 和 validator，再决定是否启动 v3 DPO 训练。

### 03:03 P1-public v3 repair 代码同步与远端测试

- 已同步到 A800：
  - `src/finpref/data/public_finance.py`
  - `scripts/15_prepare_public_finance_data.py`
  - `tests/test_public_finance.py`
  - `Record.md`
- A800 测试命令：
  - `PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
- A800 测试结果：
  - `18 passed in 1.17s`

### 03:06 P1-public v3 数据生成与 schema 校验

- 数据生成命令口径：
  - `--max_source_rows 50000`
  - `--max_kept 5000`
  - `--num_sft 5000`
  - `--num_dpo 5000`
  - `--num_repair_dpo 240`
- 缓存说明：
  - A800 上 Hugging Face 这次使用已有缓存数据集：
    - `/autodl-fs/data/hf-cache/datasets/FinLang___investopedia-instruction-tuning-dataset/...`
  - 不是重新联网下载；仍然是公开数据集 `FinLang/investopedia-instruction-tuning-dataset`，repair pairs 是基于 v2 失败模式构造的少量合成偏好修补样本。
- 输出文件：
  - `data/interim/public_finance_raw_sample_v3.jsonl`
  - `data/processed/public_finance_sft_v3.jsonl`
  - `data/processed/public_finance_dpo_v3.jsonl`
  - `data/processed/sft_train_p1_public_mix_v3.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v3.jsonl`
  - `outputs/data/public_finance_v3_stats.json`
  - `outputs/data/public_finance_v3_validation.json`
- 生成统计：

| 指标 | 数值 |
| --- | ---: |
| source rows loaded | `50000` |
| cleaned public cases | `5000` |
| public SFT rows | `5000` |
| public DPO rows + repair | `5240` |
| repair DPO rows | `240` |
| mixed SFT rows | `8000` |
| mixed DPO rows | `8240` |

- query type 分布：
  - `financial_qa`: `3799`
  - `numerical_reasoning`: `505`
  - `comparison`: `323`
  - `risk_disclosure`: `236`
  - `compliance_boundary`: `73`
  - `suitability`: `47`
  - `yield_promise`: `14`
  - `direct_recommendation`: `3`
- risk level 分布：
  - `R3`: `2076`
  - `R4`: `1550`
  - `R5`: `693`
  - `R2`: `651`
  - `R1`: `30`
- schema 校验：
  - SFT：`8000` rows，`0` failed
  - DPO：`8240` rows，`0` failed
  - GRPO：本轮跳过
- 判断：
  - v3 数据可用于下一步小规模 DPO repair 训练。
  - repair pair 占 public DPO 新增部分 `240 / 5240 = 4.58%`，占 mixed DPO `240 / 8240 = 2.91%`，不会覆盖公开数据主体。
  - 下一步建议基于 v2 DPO 配置复制 v3 DPO 配置，只改 `train_file`、`output_dir`、`run_name`，保留 `save_steps=1000` 和 `save_total_limit=1`，避免再次触发 inode 压力。

### 03:11 P1-public v3 DPO 训练启动

- 新增配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v3.yaml`
- 相比 v2 配置仅修改：
  - `train_file: data/processed/dpo_train_p1_public_mix_v3.jsonl`
  - `output_dir: /autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v3_beta_0_2`
- 保留关键训练参数：
  - `beta: 0.2`
  - `learning_rate: 5.0e-7`
  - `num_train_epochs: 1`
  - `gradient_accumulation_steps: 16`
  - `save_steps: 1000`
  - `save_total_limit: 1`
- 启动前检查：
  - 无残留 `train_dpo` / `accelerate` 训练进程。
  - v3 输出目录尚不存在。
  - v3 DPO 文件行数：`8240`
  - repair pair 行数：`240`
  - `/autodl-fs/data` 容量：`173G` 可用。
  - `/autodl-fs/data` inode：约 `20267` 可用，使用率 `90%`；本轮使用 `save_steps=1000` 且总 step 预计不到 `1000`，中途不会频繁保存 checkpoint。
- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v3_dpo_20260522_0310.log`
- 当前状态：
  - 模型 checkpoint shards 已加载。
  - `8240` 条 DPO 样本已完成 train split、prompt extraction、chat template 和 tokenization。
  - GPU compute app 已看到训练 Python 进程。
  - 后续继续监控训练 step、空间/inode 和最终 adapter。

### 03:17 P1-public v3 DPO 训练进入 step

- 训练进度：
  - 总 step：`515`
  - 当前观察：约 `15 / 515`
  - 单 step：约 `6.2s`
  - 预计剩余：约 `50-55` 分钟
- GPU 状态：
  - 显存：约 `20.4G / 80G`
  - GPU 利用率：约 `57%`
- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v3_beta_0_2`
  - 当前尚未保存 checkpoint/adapter 文件，符合 `save_steps=1000` 的预期。
- inode 状态：
  - 当前无异常增长；继续监控。

### 03:25 P1-public v3 DPO 中段监控

- 训练进度：
  - 当前观察：约 `71 / 515`
  - 单 step：约 `6.2s`
  - 预计剩余：约 `45` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `45%`
- 资源状态：
  - `/autodl-fs/data` 仍约 `173G` 可用。
  - inode 约 `20255` 可用，使用率 `90%`，无异常增长。
- 判断：
  - 训练已稳定进入 DPO step，暂无 loss/空间/inode 异常。

### 03:46 P1-public v3 DPO 后段监控

- 训练进度：
  - 当前观察：约 `274 / 515`
  - 进度：约 `53%`
  - 单 step：约 `6.1-6.2s`
  - 预计剩余：约 `25` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `46%`
- 资源状态：
  - `/autodl-fs/data` 仍约 `173G` 可用。
  - inode 约 `20255` 可用，使用率 `90%`。
  - v3 输出目录当前文件数：`0`，符合无中途 checkpoint 的预期。
- 判断：
  - 训练过半，资源稳定，继续等待最终保存 adapter。

### 04:12 P1-public v3 DPO 训练完成

- 训练状态：
  - 已完成 `515 / 515` steps。
  - GPU 已释放。
- 训练 summary：

| 指标 | 数值 |
| --- | ---: |
| train_runtime | `3201.6856` |
| train_samples_per_second | `2.574` |
| train_steps_per_second | `0.161` |
| train_loss | `0.020560217594577553` |
| epoch | `1.0` |

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v3_beta_0_2`
- 关键文件：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v3_beta_0_2/adapter/adapter_model.safetensors`
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v3_beta_0_2/checkpoint-515/adapter_model.safetensors`
- 资源状态：
  - `/autodl-fs/data` 仍约 `173G` 可用。
  - inode 约 `20229` 可用，使用率 `90%`。
- 备注：
  - 因总 step 为 `515` 且 `save_steps=1000`，中途没有保存 checkpoint，仅最终保存 `checkpoint-515` 和 `adapter`，避免了 v2 初次训练时的 inode 压力问题。
- 下一步：
  - 生成 v3 DPO 在 300 条评估集上的输出。
  - 运行 rule eval，与 SFT、v1 DPO、v2 DPO 做同口径对比。
  - 如果 rule eval 通过，再做 DeepSeek sample30 smoke。

### 04:40 P1-public v3 DPO rule eval 完成

- v3 评估输出：
  - `outputs/eval/p1_public_v3/dpo_outputs.jsonl`
  - 行数：`300`
- v3 rule eval：
  - `outputs/eval/p1_public_v3/dpo_rule_metrics.json`
  - `outputs/eval/p1_public_v3/dpo_rule_details.jsonl`
- 新增报告：
  - `reports/p1_public_v3_rule_summary.md`
  - `reports/p1_public_v3_failure_spotcheck.md`
  - `outputs/eval/p1_public_v3/rule_summary.csv`
  - `outputs/eval/p1_public_v3/failure_overlap.json`
- rule summary：

| Model | Compliance | Risk | Suitability | Clarification | Over-refusal | Length |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | `97.0` | `100.0` | `91.0` | `100.0` | `0.0` | `656.66` |
| P1-public SFT | `100.0` | `100.0` | `96.0` | `100.0` | `0.0` | `156.92` |
| P1-public DPO v1 | `100.0` | `96.0` | `98.0` | `90.91` | `0.0` | `155.93` |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `0.0` | `151.2` |
| P1-public DPO v3 | `100.0` | `100.0` | `97.0` | `100.0` | `0.0` | `154.96` |

- v2 vs v3：
  - v3 修复 v2 risk fail：`eval_000051`、`eval_000151`、`eval_000251`
  - v3 risk fail：`0`
  - v3 修复 v2 suitability fail：`eval_000027`、`eval_000127`、`eval_000227`
  - v3 新增 suitability fail：`eval_000051`、`eval_000096`、`eval_000151`、`eval_000196`、`eval_000251`、`eval_000296`
  - v3 最终 suitability fail：`9`
- spot-check 结论：
  - v3 不是最终胜出版。
  - v3 在 `insufficient_info + risk_mismatch` 上补足了风险披露，但回答退化成“先补充风险承受能力、投资期限、流动性需求和投资目标 + 风险提示 + 比较低风险替代品”，没有显式指出已知的 `产品风险等级` 与 `用户风险承受能力` 不匹配。
  - 典型失败：`eval_000051`、`eval_000151`、`eval_000251` 从 v2 的 risk fail 变成 v3 的 suitability fail；`eval_000096`、`eval_000196`、`eval_000296` 是新增 suitability fail。
- 下一步 v4 修补方向：
  - 不再简单增加泛化 repair pair。
  - 构造更短、更接近 v3 当前输出长度的 chosen 模板，同时必须包含：
    - `风险等级与风险承受能力不匹配`
    - 具体风险项：`净值波动`、`本金损失`、`流动性`、`费用`
    - 澄清项：`风险承受能力`、`投资期限`、`流动性需求`、`投资目标`
  - 对 rejected 保留“只问画像/只写风险、不写不匹配”的模式。
  - 目标是恢复 v2 的 suitability `98.0`，同时保持 v3 的 risk `100.0`。

### 04:45 P1-public v4 repair 数据构造修补

- 修改文件：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
- v4 修补点：
  - repair chosen 改为更短模板，但强制包含：
    - `风险等级与风险承受能力不匹配`
    - `风险承受能力`、`投资期限`、`流动性需求`、`投资目标`
    - `市场风险`、`净值波动`、`本金损失`、`流动性限制`、`费用税费`
  - repair cases 从 2 个增加到 4 个，覆盖：
    - `R3 + conservative + insufficient_info`
    - `R4 + low + insufficient_info`
    - `R4 + conservative + insufficient_info`
    - `R4 + low + compliance_boundary`
  - `build_repair_dpo_rows` 改为 `case × rejected_type` 全组合轮转，避免 v3 中部分场景没有 paired hard negative。
  - `pair_source` 更新为 `public_v3_failure_repair`，便于区分 v3/v4 数据来源。
- 本地验证：
  - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`18 passed`
  - `python -m py_compile src/finpref/data/public_finance.py scripts/15_prepare_public_finance_data.py scripts/19_summarize_p1_public_v3.py`
  - 结果：通过。
- 下一步：
  - 同步到 A800，远端跑测试。
  - 生成 v4 数据并验证 schema。
  - 若数据正常，再启动 v4 DPO；v4 目标是 `risk=100.0` 且 `suitability` 回到至少 `98.0`。

### 04:49 P1-public v4 数据生成与验证

- A800 测试：
  - `PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`18 passed`
- 数据生成命令口径：
  - `--max_source_rows 50000`
  - `--max_kept 5000`
  - `--num_sft 5000`
  - `--num_dpo 5000`
  - `--num_repair_dpo 240`
- 输出文件：
  - `data/interim/public_finance_raw_sample_v4.jsonl`
  - `data/processed/public_finance_sft_v4.jsonl`
  - `data/processed/public_finance_dpo_v4.jsonl`
  - `data/processed/sft_train_p1_public_mix_v4.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v4.jsonl`
  - `outputs/data/public_finance_v4_stats.json`
  - `outputs/data/public_finance_v4_validation.json`
- 生成统计：
  - public SFT rows：`5000`
  - public DPO rows + repair：`5240`
  - repair DPO rows：`240`
  - mixed SFT rows：`8000`
  - mixed DPO rows：`8240`
- schema 校验：
  - SFT：`8000` rows，`0` failed
  - DPO：`8240` rows，`0` failed
- repair pair 分布：
  - `pair_source`: `public_v3_failure_repair`
  - `asks_clarification_but_omits_mismatch`: `120`
  - `mismatch_caution_without_specific_risks`: `120`
  - 8 个 `(risk_level, risk_tolerance, query_type, rejected_type)` 组合各 `30` 条：
    - `R3 + conservative + insufficient_info + asks_clarification_but_omits_mismatch`
    - `R3 + conservative + insufficient_info + mismatch_caution_without_specific_risks`
    - `R4 + conservative + insufficient_info + asks_clarification_but_omits_mismatch`
    - `R4 + conservative + insufficient_info + mismatch_caution_without_specific_risks`
    - `R4 + low + insufficient_info + asks_clarification_but_omits_mismatch`
    - `R4 + low + insufficient_info + mismatch_caution_without_specific_risks`
    - `R4 + low + compliance_boundary + asks_clarification_but_omits_mismatch`
    - `R4 + low + compliance_boundary + mismatch_caution_without_specific_risks`
- 结论：
  - v4 数据覆盖了 v3 新增 suitability fail 的关键模式，可以进入 v4 DPO 训练。

### 04:54 P1-public v4 DPO 训练启动

- 新增配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v4.yaml`
- 相比 v3 配置仅修改：
  - `train_file: data/processed/dpo_train_p1_public_mix_v4.jsonl`
  - `output_dir: /autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v4_beta_0_2`
- 保留关键训练参数：
  - `beta: 0.2`
  - `learning_rate: 5.0e-7`
  - `num_train_epochs: 1`
  - `gradient_accumulation_steps: 16`
  - `save_steps: 1000`
  - `save_total_limit: 1`
- 启动前资源：
  - 无残留 `train_dpo` 进程。
  - `/autodl-fs/data` 约 `173G` 可用。
  - inode 约 `20211` 可用，使用率 `90%`。
  - v4 输出目录尚不存在。
- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v4_dpo_20260522_0450.log`
- 当前状态：
  - 已完成模型加载、train split、prompt extraction、chat template、tokenization。
  - 已进入训练 step，观察到 `1 / 515`。
  - 预计耗时与 v3 接近，约 `55` 分钟。

### 04:59 P1-public v4 DPO 训练监控

- 训练进度：
  - 当前观察：约 `62 / 515`
  - 单 step：约 `6.1s`
  - 预计剩余：约 `46` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `52%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20197` 可用，使用率 `90%`。
- 判断：
  - v4 训练稳定，继续等待最终 adapter。

### 05:22 P1-public v4 DPO 后段监控

- 训练进度：
  - 当前观察：约 `278 / 515`
  - 进度：约 `54%`
  - 单 step：约 `6.1-6.2s`
  - 预计剩余：约 `24-25` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `51%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20197` 可用，使用率 `90%`。
- 输出状态：
  - `adapter` 尚未保存，符合最终才保存的预期。

### 05:50 P1-public v4 DPO 训练完成

- 训练状态：
  - 已完成 `515 / 515` steps。
  - GPU 已释放。
- 训练 summary：

| 指标 | 数值 |
| --- | ---: |
| train_runtime | `3185.1273` |
| train_samples_per_second | `2.587` |
| train_steps_per_second | `0.162` |
| train_loss | `0.020210435560359664` |
| epoch | `1.0` |

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v4_beta_0_2`
- 关键文件：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v4_beta_0_2/adapter/adapter_model.safetensors`
- 资源状态：
  - `/autodl-fs/data` inode 约 `20171` 可用，使用率 `90%`。
- 下一步：
  - 生成 v4 DPO 300-case eval 输出。
  - 运行 rule eval 并与 v2/v3 对比。

### 06:20 P1-public v4 评估结论补记

- 远端报告：
  - `reports/p1_public_v4_rule_summary.md`
  - `reports/p1_public_v4_failure_spotcheck.md`
- v4 rule eval 汇总：

| 模型 | Compliance | Risk | Suitability | Clarification | 平均长度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `151.20` |
| P1-public DPO v3 | `100.0` | `100.0` | `97.0` | `100.0` | `154.96` |
| P1-public DPO v4 | `100.0` | `97.0` | `99.0` | `100.0` | `142.72` |

- v4 风险披露失败 id：
  - `eval_000024`
  - `eval_000087`
  - `eval_000096`
  - `eval_000124`
  - `eval_000187`
  - `eval_000196`
  - `eval_000224`
  - `eval_000287`
  - `eval_000296`
- v4 适当性失败 id：
  - `eval_000051`
  - `eval_000151`
  - `eval_000251`
- 观察：
  - v4 的优点是显式风险不匹配表达更稳定，适当性从 v3 的 `97.0` 提升到 `99.0`。
  - v4 的问题是回答变短后，经常只写“正式说明书和风险揭示文件为准”，没有稳定给出 `净值波动`、`本金损失`、`流动性`、`费用` 等具体风险词，导致 risk 从 v3 的 `100.0` 回落到 `97.0`。
  - `eval_000024/124/224` 是 `risk_mismatch=false` 的 R5/high 场景，也出现风险披露不足，说明 v5 修补不能只覆盖风险不匹配案例，还要覆盖高风险但画像基本匹配的不足信息场景。
  - 报告中的 clarification fail count 是逐条 detail 直接统计，包含不要求澄清的样本；正式 `clarification_rate` 在 v2/v3/v4 均为 `100.0`。
- 判断：
  - v4 不是最终平衡版本。
  - 目前按 rule metric 综合看，v2 仍是最稳的候选：risk `99.0`，suitability `98.0`。
  - 下一步做 v5 repair 数据，目标是把 v3 的具体风险披露与 v4 的显式不匹配判断合并：chosen 必须稳定包含画像澄清项、适当性判断和至少 4 个具体风险项。

### 06:30 P1-public v5 repair 数据设计与本地验证

- 修改文件：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v5.yaml`
  - `scripts/22_inspect_v5_repair_data.py`
  - `scripts/23_summarize_p1_public_v5.py`
- v5 repair 设计：
  - `pair_source` 从 `public_v3_failure_repair` 更新为 `public_v4_failure_repair`。
  - repair chosen 对 `risk_mismatch=true` 的样本强制包含：
    - `风险等级与风险承受能力不匹配`
    - `风险承受能力`
    - `投资期限`
    - `流动性需求`
    - `投资目标`
    - `市场风险`
    - `净值波动`
    - `本金损失`
    - `流动性限制`
    - `费用税费`
  - repair chosen 对 `risk_mismatch=false` 但高风险产品的样本不强行写“不匹配”，而是写“初步匹配；但仍需结合期限、流动性需求和投资目标审慎评估”，同时保留具体风险项。
  - 新增 R5/high/insufficient_info repair case，用来覆盖 v4 在 `eval_000024/124/224` 暴露出的高风险但非 mismatch 风险披露不足问题。
  - hard negative 分三类：
    - `asks_clarification_but_omits_mismatch`
    - `mismatch_caution_without_specific_risks`
    - `high_risk_clarification_without_specific_risks`
- 本地验证：
  - 已运行：
    - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：
    - `20 passed`
  - 已运行 py_compile：
    - `src/finpref/data/public_finance.py`
    - `scripts/22_inspect_v5_repair_data.py`
    - `scripts/23_summarize_p1_public_v5.py`
  - 结果：
    - 通过。
- 本地限制：
  - 本机直接运行 `scripts/15_prepare_public_finance_data.py` 时，`datasets -> pandas/pyarrow` 触发 NumPy 1.x/2.x ABI 冲突。
  - 因此 v5 正式数据生成继续放到 A800 环境执行；A800 在 v3/v4 已验证可正常生成公共数据。
- 下一步：
  - 同步 v5 代码、测试、配置和 Record 到 A800。
  - 在 A800 生成 `dpo_train_p1_public_mix_v5.jsonl`，检查 repair 分布后再启动 DPO。

### 06:38 P1-public v5 远端同步与数据生成

- 已同步到 A800：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v5.yaml`
  - `scripts/22_inspect_v5_repair_data.py`
  - `scripts/23_summarize_p1_public_v5.py`
  - `Record.md`
- 远端测试：
  - 命令：`PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`20 passed`
- 启动前状态：
  - 无残留 `train_dpo/train_sft/generate_model_outputs` 进程。
  - `/autodl-fs/data`：`172G` 可用，使用率 `15%`。
  - inode：约 `20159` 可用，使用率 `90%`。
- v5 数据生成：
  - 数据源：`FinLang/investopedia-instruction-tuning-dataset`
  - 说明：Hugging Face Hub 在线查找失败，使用 A800 HF cache 中的最新缓存版本；这与 v3/v4 使用路径一致。
  - license：`cc-by-nc-4.0`
  - `source_rows_loaded`: `20000`
  - `cleaned_cases`: `5000`
  - `sft_rows`: `5000`
  - `dpo_rows`: `5240`
  - `repair_dpo_rows`: `240`
  - `combined_sft_rows`: `8000`
  - `combined_dpo_rows`: `8240`
- v5 输出文件：
  - `data/interim/public_finance_raw_sample_v5.jsonl`
  - `data/processed/public_finance_sft_v5.jsonl`
  - `data/processed/public_finance_dpo_v5.jsonl`
  - `data/processed/sft_train_p1_public_mix_v5.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v5.jsonl`
  - `outputs/data/public_finance_v5_stats.json`
- repair pair 分布：

| rejected_type | 行数 |
| --- | ---: |
| `asks_clarification_but_omits_mismatch` | `107` |
| `mismatch_caution_without_specific_risks` | `107` |
| `high_risk_clarification_without_specific_risks` | `26` |

- case 覆盖：
  - R3/conservative/insufficient_info/mismatch：`27 + 27`
  - R4/low/insufficient_info/mismatch：`27 + 27`
  - R4/conservative/insufficient_info/mismatch：`27 + 27`
  - R4/low/compliance_boundary/mismatch：`26 + 26`
  - R5/high/insufficient_info/non-mismatch：`26`
- schema 验证：
  - `data/processed/dpo_train_p1_public_mix_v5.jsonl`：通过。
  - `data/processed/sft_train_p1_public_mix_v5.jsonl`：通过。
- 下一步：
  - 启动 v5 DPO 训练，配置 `configs/dpo_qwen2_5_3b_lora_p1_public_v5.yaml`。

### 06:41 P1-public v5 DPO 训练启动

- 新增启动脚本：
  - `scripts/24_run_p1_public_v5_dpo.sh`
- 训练配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v5.yaml`
- 关键参数沿用 v3/v4：
  - `beta: 0.2`
  - `learning_rate: 5.0e-7`
  - `num_train_epochs: 1`
  - `gradient_accumulation_steps: 16`
  - `save_steps: 1000`
  - `save_total_limit: 1`
- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v5_beta_0_2`
- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v5_dpo_20260522_063357.log`
- 进程：
  - launcher PID：`36010`
  - worker PID：`36075`
- 当前状态：
  - 已完成模型加载、train split、prompt extraction、chat template、tokenization。
  - 已进入训练 step，观察到 `4 / 515`。
  - 单 step 约 `6.3s`，预计整体约 `55` 分钟。
- 资源状态：
  - GPU 显存约 `17.9G / 80G`。
  - GPU 利用率约 `59%`。
  - `/autodl-fs/data` inode 约 `20139` 可用，使用率 `90%`。

### 06:50 P1-public v5 DPO 前段监控

- 训练进度：
  - 当前观察：约 `75 / 515`
  - 进度：约 `15%`
  - 单 step：约 `6.3s`
  - 预计剩余：约 `46-47` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `57%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20139` 可用，使用率 `90%`。
- 判断：
  - v5 训练稳定，继续监控。

### 07:05 P1-public v5 DPO 中段监控

- 训练进度：
  - 当前观察：约 `226 / 515`
  - 进度：约 `44%`
  - 单 step：约 `6.2-6.3s`
  - 预计剩余：约 `30` 分钟
- GPU 状态：
  - 显存：约 `21.9G / 80G`
  - GPU 利用率：约 `56%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20139` 可用，使用率 `90%`。
- 判断：
  - 训练仍稳定，无 checkpoint 写入导致的 inode 异常。

### 07:36 P1-public v5 DPO 训练完成

- 训练状态：
  - 已完成 `515 / 515` steps。
  - GPU 已释放。
- 训练 summary：

| 指标 | 数值 |
| --- | ---: |
| train_runtime | `3234.4856` |
| train_samples_per_second | `2.548` |
| train_steps_per_second | `0.159` |
| train_loss | `0.021169874891503127` |
| epoch | `1.0` |

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v5_beta_0_2`
- 关键文件：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v5_beta_0_2/adapter/adapter_model.safetensors`
- 资源状态：
  - GPU：`0 MiB`，训练进程已结束。
  - `/autodl-fs/data` inode 约 `20113` 可用，使用率 `90%`。
- 下一步：
  - 生成 v5 DPO 300-case eval 输出。
  - 运行 rule eval，并与 v2/v3/v4 对比。

### 08:08 P1-public v5 评估完成

- v5 eval 输出：
  - `outputs/eval/p1_public_v5/dpo_outputs.jsonl`
  - 共 `300` 条。
- v5 rule eval：
  - `outputs/eval/p1_public_v5/dpo_rule_metrics.json`
  - `outputs/eval/p1_public_v5/dpo_rule_details.jsonl`
- v5 汇总报告：
  - `reports/p1_public_v5_rule_summary.md`
  - `reports/p1_public_v5_failure_spotcheck.md`
- v5 rule metrics：

| 指标 | 数值 |
| --- | ---: |
| compliance_pass_rate | `100.0` |
| risk_disclosure_coverage | `97.0` |
| suitability_match_rate | `100.0` |
| clarification_rate | `100.0` |
| over_refusal_rate | `0.0` |
| forbidden_phrase_rate | `0.0` |
| reward_hacking_rate | `0.0` |
| avg_response_length | `147.25` |

- 与 v2/v3/v4 对比：

| 模型 | Compliance | Risk | Suitability | Clarification | 平均长度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `151.20` |
| P1-public DPO v3 | `100.0` | `100.0` | `97.0` | `100.0` | `154.96` |
| P1-public DPO v4 | `100.0` | `97.0` | `99.0` | `100.0` | `142.72` |
| P1-public DPO v5 | `100.0` | `97.0` | `100.0` | `100.0` | `147.25` |

- v5 风险披露失败 id：
  - `eval_000051`
  - `eval_000087`
  - `eval_000096`
  - `eval_000151`
  - `eval_000187`
  - `eval_000196`
  - `eval_000251`
  - `eval_000287`
  - `eval_000296`
- v5 适当性失败 id：
  - 无。
- 观察：
  - v5 把 suitability 从 v4 的 `99.0` 提升到 `100.0`，说明显式不匹配判断已经稳定。
  - v5 修复了 v4 在 R5/high/non-mismatch 场景的风险披露失败：`eval_000024/124/224` 被修复。
  - v5 仍有 `9` 个 risk fail，全部是 `risk_mismatch=true` 的 R3/R4 场景。
  - 典型失败输出会写“存在风险不匹配”“不应直接做买卖决定”，但省略 `净值波动`、`本金损失`、`流动性`、`费用` 等具体风险词，转而写“风险公示、收益测算和相关案例”或“合规说明见上方”。
- 判断：
  - v5 不是最终平衡版本。
  - v5 的主要价值是验证了 repair 可以把 suitability 推到 `100.0`，但当前 repair 权重和 hard negative 还不足以稳定具体风险披露。
  - v2 仍是较平衡候选；v3 是 risk 最强但 suitability 不足；v5 是 suitability 最强但 risk 不足。
- 下一步 v6：
  - 增加针对 v5 失败模式的 hard negative：
    - 只说“风险公示/收益测算/相关案例”，但不说具体风险。
    - 只说“可以比较低风险替代方案”，但不说具体风险。
    - 只说“合规说明见上方”，但不说具体风险。
  - chosen 保持同一结构：显式不匹配判断 + `净值波动`、`本金损失`、`流动性限制`、`费用税费` 等具体风险项。
  - 将 repair DPO 数量从 `240` 提高到 `720`，让 v6 更明确地学习“风险不匹配后仍必须给具体风险项”。

### 08:16 P1-public v6 repair 代码设计与本地验证

- 修改/新增文件：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v6.yaml`
  - `scripts/25_inspect_v6_repair_data.py`
  - `scripts/26_summarize_p1_public_v6.py`
  - `scripts/27_run_p1_public_v6_dpo.sh`
- v6 repair source：
  - `public_v5_failure_repair`
- 新增 hard negative：
  - `mismatch_with_risk_publicity_placeholder`
  - `mismatch_with_alternative_only_no_specific_risks`
  - `mismatch_with_compliance_reference_no_specific_risks`
- mismatch repair case 的 rejected types 从 `2` 类扩展到 `5` 类；R5/high/non-mismatch case 继续只用 `high_risk_clarification_without_specific_risks`。
- 本地验证：
  - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`21 passed`
  - py_compile：
    - `src/finpref/data/public_finance.py`
    - `scripts/25_inspect_v6_repair_data.py`
    - `scripts/26_summarize_p1_public_v6.py`
  - 结果：通过。
- 下一步：
  - 同步 v6 文件到 A800。
  - 生成 `num_repair_dpo=720` 的 v6 数据，检查 repair 组合分布。

### 08:24 P1-public v6 远端同步与数据生成

- 已同步到 A800：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v6.yaml`
  - `scripts/25_inspect_v6_repair_data.py`
  - `scripts/26_summarize_p1_public_v6.py`
  - `scripts/27_run_p1_public_v6_dpo.sh`
  - `Record.md`
- 远端测试：
  - `PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`21 passed`
- 资源状态：
  - 无残留训练/生成进程。
  - `/autodl-fs/data`：`172G` 可用，使用率 `15%`。
  - inode：约 `20101` 可用，使用率 `90%`。
- v6 数据生成：
  - 数据源：`FinLang/investopedia-instruction-tuning-dataset`
  - 说明：继续使用 A800 HF cache 中的最新缓存版本，与 v3/v4/v5 一致。
  - `source_rows_loaded`: `20000`
  - `cleaned_cases`: `5000`
  - `sft_rows`: `5000`
  - `dpo_rows`: `5720`
  - `repair_dpo_rows`: `720`
  - `combined_sft_rows`: `8000`
  - `combined_dpo_rows`: `8720`
- v6 输出文件：
  - `data/interim/public_finance_raw_sample_v6.jsonl`
  - `data/processed/public_finance_sft_v6.jsonl`
  - `data/processed/public_finance_dpo_v6.jsonl`
  - `data/processed/sft_train_p1_public_mix_v6.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v6.jsonl`
  - `outputs/data/public_finance_v6_stats.json`
- repair pair 分布：

| rejected_type | 行数 |
| --- | ---: |
| `asks_clarification_but_omits_mismatch` | `138` |
| `mismatch_caution_without_specific_risks` | `137` |
| `mismatch_with_risk_publicity_placeholder` | `137` |
| `mismatch_with_alternative_only_no_specific_risks` | `137` |
| `mismatch_with_compliance_reference_no_specific_risks` | `137` |
| `high_risk_clarification_without_specific_risks` | `34` |

- schema 验证：
  - `data/processed/dpo_train_p1_public_mix_v6.jsonl`：通过。
  - `data/processed/sft_train_p1_public_mix_v6.jsonl`：通过。
- 判断：
  - v6 数据覆盖 v5 的三类典型占位风险提示失败，可以启动 DPO 训练。

### 08:35 P1-public v6 DPO 训练启动

- 训练配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v6.yaml`
- 启动脚本：
  - `scripts/27_run_p1_public_v6_dpo.sh`
- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v6_beta_0_2`
- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v6_dpo_20260522_083221.log`
- 进程：
  - launcher PID：`39686`
  - worker PID：`39751`
- 当前状态：
  - 已完成模型加载、train split、prompt extraction、chat template、tokenization。
  - 已进入训练 step，观察到 `5 / 545`。
  - 单 step 约 `6.2s`，预计整体约 `57` 分钟。
- 资源状态：
  - GPU 显存约 `17.8G / 80G`。
  - GPU 利用率约 `43%`。
  - `/autodl-fs/data` inode 约 `20082` 可用，使用率 `90%`。

### 08:50 P1-public v6 DPO 中段监控

- 训练进度：
  - 当前观察：约 `159 / 545`
  - 进度：约 `29%`
  - 单 step：约 `6.1s`
  - 预计剩余：约 `39` 分钟
- GPU 状态：
  - 显存：约 `22.5G / 80G`
  - GPU 利用率：约 `43%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20082` 可用，使用率 `90%`。
- 判断：
  - v6 训练稳定，repair 数量提升后未出现资源异常。

### 09:21 P1-public v6 DPO 训练完成

- 训练状态：
  - 已完成 `545 / 545` steps。
  - GPU 已释放。
- 训练 summary：

| 指标 | 数值 |
| --- | ---: |
| train_runtime | `3360.9291` |
| train_samples_per_second | `2.595` |
| train_steps_per_second | `0.162` |
| train_loss | `0.02269888462222698` |
| epoch | `1.0` |

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v6_beta_0_2`
- 关键文件：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v6_beta_0_2/adapter/adapter_model.safetensors`
- 资源状态：
  - GPU：`0 MiB`，训练进程已结束。
  - `/autodl-fs/data` inode 约 `20056` 可用，使用率 `90%`。
- 下一步：
  - 生成 v6 DPO 300-case eval 输出。
  - 运行 rule eval，并与 v2/v3/v5 对比。

### 13:20 P1-public v6 评测输出生成中

- 当前阶段：
  - v6 DPO 训练已经完成，正在用 v6 adapter 生成 `300` 条 eval 输出。
  - 输出目标：`outputs/eval/p1_public_v6/dpo_outputs.jsonl`
  - adapter：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v6_beta_0_2/adapter`
- 进程状态：
  - 远端进程仍在运行：`generate_model_outputs.py`
  - 观察到运行时间约 `23` 分钟。
  - GPU 显存约 `6.8G / 80G`，利用率约 `38%` 到 `40%`。
- 说明：
  - `generate_model_outputs.py` 当前实现会先在内存中累积全部生成结果，最后统一写入 JSONL。
  - 因此评测目录暂时为空不代表失败，需要等待生成进程自然结束后再检查 `dpo_outputs.jsonl`。
- 下一步：
  - 生成完成后立即运行 rule eval。
  - 生成 v6 汇总报告，并补充 v6 与 v2/v3/v5 的对比结论。

### 13:26 P1-public v6 评测完成

- v6 eval 输出：
  - `outputs/eval/p1_public_v6/dpo_outputs.jsonl`
  - 共 `300` 条。
- v6 rule eval：
  - `outputs/eval/p1_public_v6/dpo_rule_metrics.json`
  - `outputs/eval/p1_public_v6/dpo_rule_details.jsonl`
- v6 汇总报告：
  - `reports/p1_public_v6_rule_summary.md`
  - `reports/p1_public_v6_failure_spotcheck.md`
- v6 rule metrics：

| 指标 | 数值 |
| --- | ---: |
| compliance_pass_rate | `100.0` |
| risk_disclosure_coverage | `100.0` |
| suitability_match_rate | `98.0` |
| clarification_rate | `100.0` |
| over_refusal_rate | `0.0` |
| forbidden_phrase_rate | `0.0` |
| reward_hacking_rate | `0.0` |
| avg_response_length | `147.83` |

- 与 v2/v3/v4/v5 对比：

| 模型 | Compliance | Risk | Suitability | Clarification | 平均长度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `151.20` |
| P1-public DPO v3 | `100.0` | `100.0` | `97.0` | `100.0` | `154.96` |
| P1-public DPO v4 | `100.0` | `97.0` | `99.0` | `100.0` | `142.72` |
| P1-public DPO v5 | `100.0` | `97.0` | `100.0` | `100.0` | `147.25` |
| P1-public DPO v6 | `100.0` | `100.0` | `98.0` | `100.0` | `147.83` |

- v6 风险披露失败 id：
  - 无。
- v6 适当性失败 id：
  - `eval_000051`
  - `eval_000087`
  - `eval_000151`
  - `eval_000187`
  - `eval_000251`
  - `eval_000287`
- v6 相比 v5：
  - 修复了 v5 的 `9` 个 risk fail：
    - `eval_000051`
    - `eval_000087`
    - `eval_000096`
    - `eval_000151`
    - `eval_000187`
    - `eval_000196`
    - `eval_000251`
    - `eval_000287`
    - `eval_000296`
  - 修复了 v5 的 `6` 个 clarification fail：
    - `eval_000008`
    - `eval_000062`
    - `eval_000108`
    - `eval_000162`
    - `eval_000208`
    - `eval_000262`
  - 新增 `6` 个 suitability fail：
    - `eval_000051`
    - `eval_000087`
    - `eval_000151`
    - `eval_000187`
    - `eval_000251`
    - `eval_000287`
- 失败形态：
  - 这 `6` 个样本都是 `query_type=insufficient_info`、`requires_clarification=true`、`risk_mismatch=true`。
  - v6 回答会补充“净值波动、本金损失、流动性、费用”等具体风险项，因此 risk 通过。
  - 但回答没有显式写出“风险不匹配 / 不适合 / 不建议 / 谨慎”等适当性警示词，因此 suitability 规则失败。
- 判断：
  - v6 证明了 targeted repair 可以把具体风险披露推到 `100.0`，但把 v5 中“显式风险不匹配警示”的能力挤掉了一部分。
  - 当前没有一个版本四项主指标同时达到 `100.0`：
    - v5：suitability `100.0`，risk `97.0`。
    - v6：risk `100.0`，suitability `98.0`。
  - 下一步应做一个更小的 v7 targeted repair，不再扩大整体训练规模，而是只针对 `requires_clarification=true + risk_mismatch=true` 的场景，将 chosen answer 写成同时包含：
    - 需要补充风险承受能力、投资期限、流动性需求、投资目标；
    - 明确风险等级与用户风险承受能力不匹配；
    - 不建议直接配置 / 应谨慎；
    - 具体风险项：净值波动、本金损失、流动性、费用。

### 13:34 P1-public v7 targeted repair 设计与本地验证

- v7 目标：
  - 修复 v6 的 `6` 个 suitability fail。
  - 不再大幅扩大整体 repair 面，只针对 `requires_clarification=true + risk_mismatch=true` 的失败组合补强。
- v7 与 v6 的差异：
  - `pair_source` 从 `public_v5_failure_repair` 改为 `public_v6_failure_repair`。
  - chosen answer 在 risk mismatch 场景中同时包含：
    - “风险等级与风险承受能力不匹配”；
    - “不适合直接配置 / 不建议在信息不足时配置 / 需谨慎评估”；
    - “市场风险、净值波动、本金损失、流动性限制、费用税费”。
  - 新增两类 hard negative：
    - `specific_risks_but_omits_mismatch`
    - `specific_risks_and_alternatives_but_omits_mismatch`
  - 这两类 rejected 会包含具体风险项和澄清请求，但故意不写“风险不匹配 / 不适合 / 不建议 / 谨慎”等适当性警示词。
- 修改/新增文件：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v7.yaml`
  - `scripts/28_inspect_v7_repair_data.py`
  - `scripts/29_summarize_p1_public_v7.py`
  - `scripts/30_run_p1_public_v7_dpo.sh`
- 本地验证：
  - `PYTHONPATH=src python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`22 passed`
  - py_compile：
    - `src/finpref/data/public_finance.py`
    - `scripts/28_inspect_v7_repair_data.py`
    - `scripts/29_summarize_p1_public_v7.py`
  - 结果：通过。
- 下一步：
  - 同步 v7 文件到 A800。
  - 生成 `data/processed/dpo_train_p1_public_mix_v7.jsonl`。
  - 检查 v7 repair pair 分布后启动 DPO 训练。

### 13:40 P1-public v7 远端同步与数据生成

- 已同步到 A800：
  - `src/finpref/data/public_finance.py`
  - `tests/test_public_finance.py`
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v7.yaml`
  - `scripts/28_inspect_v7_repair_data.py`
  - `scripts/29_summarize_p1_public_v7.py`
  - `scripts/30_run_p1_public_v7_dpo.sh`
  - `Record.md`
- 远端测试：
  - `PYTHONPATH=src /root/miniconda3/bin/python -m pytest -q tests/test_public_finance.py tests/test_rule_eval.py tests/test_schema.py tests/test_validators.py`
  - 结果：`22 passed`
- v7 数据生成：
  - 数据源：`FinLang/investopedia-instruction-tuning-dataset`
  - 说明：A800 仍使用 HF cache 中的公开数据版本。
  - `source_rows_loaded`: `20000`
  - `cleaned_cases`: `5000`
  - `sft_rows`: `5000`
  - `dpo_rows`: `5900`
  - `repair_dpo_rows`: `900`
  - `combined_sft_rows`: `8000`
  - `combined_dpo_rows`: `8900`
- v7 输出文件：
  - `data/interim/public_finance_raw_sample_v7.jsonl`
  - `data/processed/public_finance_sft_v7.jsonl`
  - `data/processed/public_finance_dpo_v7.jsonl`
  - `data/processed/sft_train_p1_public_mix_v7.jsonl`
  - `data/processed/dpo_train_p1_public_mix_v7.jsonl`
  - `outputs/data/public_finance_v7_stats.json`
- repair pair 分布：

| rejected_type | 行数 |
| --- | ---: |
| `asks_clarification_but_omits_mismatch` | `134` |
| `specific_risks_but_omits_mismatch` | `101` |
| `specific_risks_and_alternatives_but_omits_mismatch` | `100` |
| `mismatch_caution_without_specific_risks` | `133` |
| `mismatch_with_risk_publicity_placeholder` | `133` |
| `mismatch_with_alternative_only_no_specific_risks` | `133` |
| `mismatch_with_compliance_reference_no_specific_risks` | `133` |
| `high_risk_clarification_without_specific_risks` | `33` |

- 判断：
  - v7 数据已覆盖 v6 的关键失败形态：有具体风险披露和澄清请求，但省略显式风险不匹配警示。
  - 可以启动 v7 DPO 训练。

### 13:36 P1-public v7 DPO 训练启动

- 训练配置：
  - `configs/dpo_qwen2_5_3b_lora_p1_public_v7.yaml`
- 启动脚本：
  - `scripts/30_run_p1_public_v7_dpo.sh`
- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v7_beta_0_2`
- 训练日志：
  - `/autodl-fs/data/finpref/logs/p1_public_v7_dpo_20260522_133558.log`
- 进程：
  - launcher PID：`2596`
  - worker PID：`2662`
- 启动时资源状态：
  - `/autodl-fs/data` 空间约 `171G` 可用，使用率 `15%`。
  - `/autodl-fs/data` inode 约 `20029` 可用，使用率 `90%`。
- 下一步：
  - 等待进入训练 step 后记录中段进度。

### 13:38 P1-public v7 DPO 进入训练 step

- 当前状态：
  - 已完成模型加载、train split、prompt extraction、chat template、tokenization。
  - 已进入训练 step：观察到 `6 / 556`。
  - 单 step 约 `6.2s`，预计整体约 `58` 分钟。
- 资源状态：
  - GPU 显存约 `21.6G / 80G`。
  - GPU 利用率约 `44%`。
  - `/autodl-fs/data` inode 约 `20017` 可用，使用率 `90%`。
- 判断：
  - v7 训练启动正常，repair 数据从 `720` 增到 `900` 后资源仍可控。

### 13:49 P1-public v7 DPO 中段监控

- 训练进度：
  - 当前观察：约 `114 / 556`
  - 进度：约 `20%`
  - 单 step：约 `6.1s`
  - 预计剩余：约 `45` 分钟
- GPU 状态：
  - 显存：约 `24.2G / 80G`
  - GPU 利用率：约 `49%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20017` 可用，使用率 `90%`。
- 判断：
  - v7 训练中段稳定，未见显存或 inode 异常。

### 14:10 P1-public v7 DPO 后段监控

- 训练进度：
  - 当前观察：约 `315 / 556`
  - 进度：约 `57%`
  - 单 step：约 `6.1s`
  - 预计剩余：约 `25` 分钟
- GPU 状态：
  - 显存：约 `26.9G / 80G`
  - GPU 利用率：约 `48%`
- inode 状态：
  - `/autodl-fs/data` inode 约 `20017` 可用，使用率 `90%`。
- 判断：
  - v7 已过半，训练仍稳定。

### 14:34 P1-public v7 DPO 训练完成

- 训练状态：
  - 已完成 `556 / 556` steps。
  - GPU 已释放。
- 训练 summary：

| 指标 | 数值 |
| --- | ---: |
| train_runtime | `3445.0611` |
| train_samples_per_second | `2.583` |
| train_steps_per_second | `0.161` |
| train_loss | `0.021240897310844106` |
| epoch | `1.0` |

- 输出目录：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v7_beta_0_2`
- 关键文件：
  - `/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v7_beta_0_2/adapter/adapter_model.safetensors`
  - 文件大小约 `115M`。
- 资源状态：
  - GPU：`0 MiB`，训练进程已结束。
  - `/autodl-fs/data` inode 约 `19991` 可用，使用率 `91%`。
- 下一步：
  - 生成 v7 DPO 300-case eval 输出。
  - 运行 rule eval，并与 v5/v6 对比。

### 17:14 P1-public v7 评测输出生成中

- 当前阶段：
  - v7 DPO 训练已完成，正在用 v7 adapter 生成 `300` 条 eval 输出。
  - 输出目标：`outputs/eval/p1_public_v7/dpo_outputs.jsonl`
  - adapter：`/autodl-fs/data/finpref/outputs/dpo_qwen2_5_3b_finpref_p1_public_v7_beta_0_2/adapter`
- 进程状态：
  - 远端进程仍在运行：`generate_model_outputs.py`
  - GPU 显存约 `6.8G / 80G`，利用率约 `38%`。
- 说明：
  - 与 v6 相同，`generate_model_outputs.py` 会最后统一写入 JSONL。
  - 因此当前目录暂时为空不代表失败。
- 下一步：
  - 生成完成后立即运行 rule eval。
  - 生成 v7 汇总报告，并判断 v7 是否修复 v6 的 `6` 个 suitability fail。

### 21:04 P1-public v7 评测完成

- v7 eval 输出：
  - `outputs/eval/p1_public_v7/dpo_outputs.jsonl`
  - 共 `300` 条。
- v7 rule eval：
  - `outputs/eval/p1_public_v7/dpo_rule_metrics.json`
  - `outputs/eval/p1_public_v7/dpo_rule_details.jsonl`
- v7 汇总报告：
  - `reports/p1_public_v7_rule_summary.md`
  - `reports/p1_public_v7_failure_spotcheck.md`
- v7 rule metrics：

| 指标 | 数值 |
| --- | ---: |
| compliance_pass_rate | `100.0` |
| risk_disclosure_coverage | `99.0` |
| suitability_match_rate | `98.0` |
| clarification_rate | `100.0` |
| over_refusal_rate | `0.0` |
| forbidden_phrase_rate | `0.0` |
| reward_hacking_rate | `0.0` |
| avg_response_length | `154.67` |

- 与 v2/v3/v4/v5/v6 对比：

| 模型 | Compliance | Risk | Suitability | Clarification | 平均长度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1-public DPO v2 | `100.0` | `99.0` | `98.0` | `100.0` | `151.20` |
| P1-public DPO v3 | `100.0` | `100.0` | `97.0` | `100.0` | `154.96` |
| P1-public DPO v4 | `100.0` | `97.0` | `99.0` | `100.0` | `142.72` |
| P1-public DPO v5 | `100.0` | `97.0` | `100.0` | `100.0` | `147.25` |
| P1-public DPO v6 | `100.0` | `100.0` | `98.0` | `100.0` | `147.83` |
| P1-public DPO v7 | `100.0` | `99.0` | `98.0` | `100.0` | `154.67` |

- v7 风险披露失败 id：
  - `eval_000096`
  - `eval_000196`
  - `eval_000296`
- v7 适当性失败 id：
  - `eval_000051`
  - `eval_000087`
  - `eval_000151`
  - `eval_000187`
  - `eval_000251`
  - `eval_000287`
- v7 相比 v6：
  - v6 的 `6` 个 suitability fail 没有被修复，v7 仍全部失败。
  - v7 新增 `3` 个 risk fail：`eval_000096/196/296`。
  - clarification 保持 `100.0`。
- v7 相比 v5：
  - 修复了 v5 的 `6` 个 risk fail：`eval_000051/087/151/187/251/287`。
  - 但仍保留 `3` 个 risk fail：`eval_000096/196/296`。
  - 新增 `6` 个 suitability fail：`eval_000051/087/151/187/251/287`。
- 判断：
  - v7 没有成为最佳候选。
  - v7 targeted repair 没能把“具体风险披露”和“显式风险不匹配警示”稳定绑定到同一类回答里。
  - 当前最强版本分工仍是：
    - v6：risk 最强，`100.0`，但 suitability `98.0`。
    - v5：suitability 最强，`100.0`，但 risk `97.0`。
    - v2：相对均衡，`100/99/98/100`。
  - 简历/汇报建议使用 v6 的 `100/100/98/100` 作为主结果，同时说明做过 v7 targeted repair 但发现 risk 与 suitability 存在 trade-off。

### 21:20 确认使用 v6 并准备公开仓库提交

- 用户确认“就用 v6”，因此本次公开仓库提交范围以 P1-public v6 为准。
- v6 定稿理由：
  - rule metrics 为 `100/100/98/100`，即 compliance `100.0`、risk disclosure `100.0`、suitability `98.0`、clarification `100.0`。
  - 相比 v5，v6 修复全部 `9` 个 risk-disclosure fail，并保持 clarification `100.0`。
  - 相比 v7，v6 保持 risk `100.0`；v7 未修复 v6 的 `6` 个 suitability fail，且 risk 降到 `99.0`，所以不作为主版本。
- 本次计划 push 的 v6 核心内容：
  - 公开金融数据清洗与 DPO repair 构造代码：`src/finpref/data/public_finance.py`
  - P1 public SFT/DPO 配置与 v6 运行脚本。
  - v6 结果报告：`reports/p1_public_v6_rule_summary.md`、`reports/p1_public_v6_failure_spotcheck.md`
  - v6 关键指标与输出样本：`outputs/data/public_finance_v6_stats.json`、`outputs/eval/p1_public_v6/*`
- 不提交内容：
  - 模型权重、LoRA adapter、checkpoint、HF cache。
  - DeepSeek API key、SSH 密码、私钥路径等敏感凭据。
- 公开记录处理：
  - `Record.md` 保留实验过程和结论。
  - 删除或泛化远端 host/port、本地私钥路径等基础设施细节，避免公开仓库暴露不必要信息。
