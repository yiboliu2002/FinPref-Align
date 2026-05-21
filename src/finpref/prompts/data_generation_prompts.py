"""Prompt templates for future LLM-assisted data generation."""

SFT_GENERATION_PROMPT = """你是金融业务数据标注专家。请生成一条高质量 SFT 样本。

场景：{query_type}
用户风险承受能力：{risk_tolerance}
投资期限：{investment_horizon}
流动性需求：{liquidity_need}
产品类型：{product_type}
产品风险等级：{risk_level}

要求：不承诺收益，不直接给买卖指令，结合用户画像与产品特征做适当性分析，并提示具体风险。
"""

DPO_GENERATION_PROMPT = """你是金融业务偏好数据构造专家。请基于给定 prompt 生成 chosen/rejected。

Prompt:
{prompt}

Chosen 应准确、有帮助、审慎合规。Rejected 应体现真实模型可能犯的错误：收益承诺、风险错配、缺风险提示、过度拒答或销售化表达。
"""

