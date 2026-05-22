"""Public finance QA cleaning and preference-pair construction."""

from __future__ import annotations

import hashlib
import html
import re
from collections import Counter
from itertools import islice
from typing import Any, Iterable

from finpref.constants import PRODUCT_RISK_ORDER, RISK_ORDER
from finpref.data.formatters import as_dpo_row, as_sft_row
from finpref.utils.io import read_jsonl, write_json, write_jsonl

SOURCE_DATASET = "FinLang/investopedia-instruction-tuning-dataset"
SOURCE_LICENSE = "cc-by-nc-4.0"

DIRECT_ADVICE_PATTERNS = [
    r"\byou should buy\b",
    r"\byou should sell\b",
    r"\bshould be bought\b",
    r"\bshould be sold\b",
    r"\bbuy now\b",
    r"\bsell now\b",
    r"\bbuy .* on weakness\b",
    r"\breduce holdings\b",
    r"\bincrease holdings\b",
    r"\baccumulate shares\b",
    r"\binitiate (a )?position\b",
    r"\bgo long\b",
    r"\bgo short\b",
    r"\bgo all in\b",
    r"\bput all your money\b",
    r"\bload up on\b",
    r"\bmust buy\b",
    r"\bstrong buy\b",
    r"\bstrong sell\b",
    r"建议你买入",
    r"建议你卖出",
    r"直接买入",
    r"马上卖",
]

RETURN_PROMISE_PATTERNS = [
    r"\bguaranteed profit\b",
    r"\bguaranteed return\b",
    r"\bguaranteed to make money\b",
    r"\bcannot lose money\b",
    r"\brisk[- ]free investment\b",
    r"\bsure to make money\b",
    r"\bno downside\b",
    r"保证收益",
    r"稳赚不赔",
    r"一定赚钱",
]

RISK_DISCLOSURE_TERMS = [
    "risk",
    "risks",
    "loss",
    "losses",
    "volatile",
    "volatility",
    "fluctuat",
    "liquidity",
    "market",
    "credit",
    "default",
    "interest rate",
    "fee",
    "fees",
    "tax",
    "principal",
    "not guaranteed",
    "rate changes",
    "风险",
    "亏损",
    "波动",
    "流动性",
    "本金",
]

LOW_QUALITY_PATTERNS = [
    r"\bas an ai language model\b",
    r"\bi cannot provide any information\b",
    r"\bi don't know\b",
    r"\bno answer\b",
]

REJECTED_TYPES = [
    "caution_without_specific_risks",
    "missing_risk_disclosure",
    "direct_buy_sell",
    "yield_promise",
    "generic_safe_answer",
    "risk_mismatch_ignored",
    "over_refusal",
]

REPAIR_REJECTED_TYPES = [
    "asks_clarification_but_omits_mismatch",
    "mismatch_caution_without_specific_risks",
    "mismatch_with_risk_publicity_placeholder",
    "mismatch_with_alternative_only_no_specific_risks",
    "mismatch_with_compliance_reference_no_specific_risks",
    "high_risk_clarification_without_specific_risks",
]
REPAIR_PAIR_SOURCE = "public_v5_failure_repair"

FINANCE_RELEVANCE_TERMS = [
    "401(k)",
    "annuity",
    "apr",
    "asset allocation",
    "bond",
    "broker",
    "capital gain",
    "certificate of deposit",
    "credit",
    "crypto",
    "debt",
    "dividend",
    "equity",
    "etf",
    "expense ratio",
    "fiduciary",
    "financial advisor",
    "fixed income",
    "fund",
    "home equity",
    "insurance",
    "interest rate",
    "ira",
    "liquidity",
    "loan",
    "mortgage",
    "mutual fund",
    "option",
    "portfolio",
    "retirement",
    "risk tolerance",
    "roth",
    "saving",
    "share",
    "stock",
    "tax",
    "treasury",
    "volatility",
    "yield",
    "本金",
    "保险",
    "债券",
    "基金",
    "投资",
    "收益",
    "股票",
    "贷款",
    "退休",
    "风险",
]

SOURCE_ARTIFACT_PATTERNS = [
    r"\baccessed date\b",
    r"\bwhere can more information be found\b",
    r"\bwhat percentage or rate is being referred to\b",
    r"\bwhat is being referred to in the given text\b",
    r"\bunnamed experiment\b",
    r"\bwhich companies has .* partnered\b",
    r"\bsuggested trading strategy\b",
    r"\btrading strategy .* according to the passage\b",
]


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalized_question(question: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", question.lower()).strip()


def _hash_int(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _term_in_text(term: str, text: str) -> bool:
    lowered_term = term.lower()
    if re.fullmatch(r"[a-z0-9]+(?: [a-z0-9]+)*", lowered_term):
        pattern = r"(?<![a-z0-9])" + re.escape(lowered_term).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return lowered_term in text


def _has_any_term(terms: Iterable[str], text: str) -> bool:
    lowered = text.lower()
    return any(_term_in_text(term, lowered) for term in terms)


def contains_direct_advice(text: str) -> bool:
    return _contains_any(text, DIRECT_ADVICE_PATTERNS)


def contains_return_promise(text: str) -> bool:
    return _contains_any(text, RETURN_PROMISE_PATTERNS)


def contains_risk_disclosure(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in RISK_DISCLOSURE_TERMS)


def is_low_quality_answer(answer: str) -> bool:
    if len(answer) < 40:
        return True
    if len(set(answer.lower().split())) < 8:
        return True
    return _contains_any(answer, LOW_QUALITY_PATTERNS)


def finance_relevance_score(question: str, title: str, context: str) -> int:
    question_title = f"{question} {title}".lower()
    context_lower = context.lower()
    score = 0
    for term in FINANCE_RELEVANCE_TERMS:
        if _term_in_text(term, question_title):
            score += 2
        elif _term_in_text(term, context_lower):
            score += 1
    return score


def is_source_artifact_question(question: str) -> bool:
    lowered = question.lower()
    return any(re.search(pattern, lowered) for pattern in SOURCE_ARTIFACT_PATTERNS)


def build_public_query(question: str, title: str) -> str:
    cleaned_question = re.sub(
        r"^(in|according to|based on)\s+(the\s+)?(given\s+)?(text\s+)?passage,?\s*",
        "",
        question,
        flags=re.IGNORECASE,
    ).strip()
    if title and title.lower() not in cleaned_question.lower():
        return f"{title} — {cleaned_question}"
    return cleaned_question


def infer_query_type(question: str, title: str, topic: str) -> str:
    text = f"{question} {title} {topic}".lower()
    if any(term in text for term in ["guarantee", "guaranteed", "promised return", "safe return", "no risk", "cannot lose", "稳赚", "保证收益"]):
        return "yield_promise"
    if (
        re.search(r"\b(should|can|could)\s+i\s+(buy|sell|invest|short|hold)\b", text)
        or re.search(r"\bwould\s+you\s+(buy|sell|invest|short|hold)\b", text)
        or re.search(r"\bis\s+it\s+(worth\s+)?(buying|selling|investing)\b", text)
    ):
        return "direct_recommendation"
    if any(term in text for term in ["suitable", "right for me", "for my portfolio", "for retirement", "risk tolerance"]):
        return "suitability"
    if "risk" in text or "drawback" in text or "downside" in text:
        return "risk_disclosure"
    if any(term in text for term in ["compare", "comparison", "difference between", "versus", " vs "]):
        return "comparison"
    if any(term in text for term in ["calculate", "formula", "how much", "interest rate", "apr", "yield"]):
        return "numerical_reasoning"
    if any(term in text for term in ["legal", "regulation", "disclosure", "fiduciary", "suitability rule"]):
        return "compliance_boundary"
    return "financial_qa"


def infer_product_info(question: str, title: str, topic: str, context: str) -> dict[str, Any]:
    text = f"{topic} {title} {question} {context}".lower()
    rules: list[tuple[tuple[str, ...], dict[str, Any]]] = [
        (("crypto", "bitcoin", "ethereum", "token"), {"product_type": "crypto_asset", "risk_level": "R5", "liquidity": "T+0", "volatility": "very_high", "principal_protection": False, "complexity": "high"}),
        (("option", "futures", "derivative", "margin", "leverage", "short selling"), {"product_type": "derivative", "risk_level": "R5", "liquidity": "T+0", "volatility": "very_high", "principal_protection": False, "complexity": "high"}),
        (("penny stock", "stock", "equity", "share"), {"product_type": "equity", "risk_level": "R4", "liquidity": "T+1", "volatility": "high", "principal_protection": False, "complexity": "medium"}),
        (("high-yield bond", "junk bond"), {"product_type": "high_yield_bond", "risk_level": "R4", "liquidity": "T+1", "volatility": "high", "principal_protection": False, "complexity": "medium"}),
        (("etf", "mutual fund", "index fund", "fund"), {"product_type": "fund", "risk_level": "R3", "liquidity": "T+1", "volatility": "medium", "principal_protection": False, "complexity": "medium"}),
        (("bond", "treasury", "fixed income"), {"product_type": "bond", "risk_level": "R2", "liquidity": "T+1", "volatility": "medium", "principal_protection": False, "complexity": "medium"}),
        (("annuity", "insurance"), {"product_type": "insurance_annuity", "risk_level": "R3", "liquidity": "limited", "volatility": "medium", "principal_protection": False, "complexity": "high"}),
        (("mortgage", "home equity", "loan", "credit card", "debt"), {"product_type": "credit_product", "risk_level": "R3", "liquidity": "limited", "volatility": "medium", "principal_protection": False, "complexity": "medium"}),
        (("retirement", "401(k)", "ira", "roth"), {"product_type": "retirement_account", "risk_level": "R3", "liquidity": "limited", "volatility": "medium", "principal_protection": False, "complexity": "medium"}),
        (("cd ", "certificate of deposit", "savings account", "money market"), {"product_type": "cash_equivalent", "risk_level": "R1", "liquidity": "T+0", "volatility": "low", "principal_protection": True, "complexity": "low"}),
    ]
    for tokens, product in rules:
        if _has_any_term(tokens, text):
            return {
                "fees": "source-dependent; check official disclosure documents",
                "lockup_period": "source-dependent",
                **product,
            }
    return {
        "product_type": "financial_topic",
        "risk_level": "R2",
        "liquidity": "source-dependent",
        "volatility": "medium",
        "fees": "source-dependent; check official disclosure documents",
        "lockup_period": "source-dependent",
        "principal_protection": False,
        "complexity": "medium",
    }


def infer_user_profile(question: str, product_info: dict[str, Any]) -> dict[str, Any]:
    seed = _hash_int(question)
    product_risk = PRODUCT_RISK_ORDER.get(product_info["risk_level"], 3)
    if product_risk >= 4:
        risk_tolerance = ["conservative", "low", "medium", "high"][seed % 4]
    elif product_risk <= 2:
        risk_tolerance = ["conservative", "low", "medium"][seed % 3]
    else:
        risk_tolerance = ["low", "medium", "high"][seed % 3]

    lowered = question.lower()
    if any(term in lowered for term in ["retirement", "mortgage", "college", "long term", "401(k)", "ira"]):
        horizon = "long_term"
        liquidity_need = "low"
    elif any(term in lowered for term in ["day trading", "short term", "emergency", "credit card", "loan"]):
        horizon = "short_term"
        liquidity_need = "high"
    else:
        horizon = ["short_term", "medium_term", "long_term"][seed % 3]
        liquidity_need = ["high", "medium", "low"][seed % 3]

    experience = ["beginner", "intermediate", "experienced"][seed % 3]
    objective = ["capital_preservation", "income", "growth", "education"][seed % 4]
    loss_tolerance = {"conservative": "none", "low": "small", "medium": "moderate", "high": "large", "aggressive": "large"}[risk_tolerance]
    return {
        "age": 24 + seed % 45,
        "income_stability": ["unstable", "stable", "variable"][seed % 3],
        "risk_tolerance": risk_tolerance,
        "investment_horizon": horizon,
        "liquidity_need": liquidity_need,
        "investment_experience": experience,
        "objective": objective,
        "loss_tolerance": loss_tolerance,
    }


def risk_mismatch(profile: dict[str, Any], product_info: dict[str, Any]) -> bool:
    user_score = RISK_ORDER.get(profile["risk_tolerance"], 3)
    product_score = PRODUCT_RISK_ORDER.get(product_info["risk_level"], 3)
    return product_score > user_score + 1


def _source_value(row: dict[str, Any], *names: str) -> str:
    lowered = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        if name in row:
            return clean_text(row[name])
        if name.lower() in lowered:
            return clean_text(lowered[name.lower()])
    return ""


def normalize_public_row(row: dict[str, Any], index: int, split: str = "train") -> tuple[dict[str, Any] | None, str | None]:
    question = _source_value(row, "Question", "question")
    answer = _source_value(row, "Answer", "answer")
    topic = _source_value(row, "Topic", "topic")
    title = _source_value(row, "Title", "title")
    context = _source_value(row, "Context", "context")

    if not question or not answer:
        return None, "missing_question_or_answer"
    if len(question) < 15:
        return None, "question_too_short"
    if is_source_artifact_question(question):
        return None, "source_artifact_question"
    relevance_score = finance_relevance_score(question, title, context)
    if relevance_score < 2:
        return None, "finance_irrelevant"
    if is_low_quality_answer(answer):
        return None, "low_quality_answer"
    if contains_direct_advice(answer):
        return None, "direct_instruction_answer"
    if contains_return_promise(answer):
        return None, "return_promise_answer"

    query_type = infer_query_type(question, title, topic)
    product_info = infer_product_info(question, title, topic, context)
    profile = infer_user_profile(question, product_info)
    mismatch = risk_mismatch(profile, product_info)
    should_refuse_direct_advice = query_type in {"yield_promise", "direct_recommendation"}
    requires_clarification = query_type in {"suitability", "direct_recommendation"} or should_refuse_direct_advice
    should_disclose_risk = query_type in {"suitability", "risk_disclosure", "yield_promise", "direct_recommendation", "comparison"} or product_info["risk_level"] != "R1"
    answer_has_risk_disclosure = contains_risk_disclosure(answer)

    expected_behavior = [
        "Preserve useful public finance QA content",
        "Do not promise returns",
        "Do not give direct buy/sell instructions",
    ]
    if should_disclose_risk:
        expected_behavior.append("Include risk disclosure")
    if mismatch:
        expected_behavior.append("Point out product-user risk mismatch")
    if requires_clarification:
        expected_behavior.append("Ask for or state missing suitability information")

    forbidden_behavior = [
        "Guaranteed returns",
        "Direct buy/sell order",
        "Ignoring risk disclosure",
        "Over-refusal of educational finance QA",
    ]

    meta = {
        "query_type": query_type,
        "risk_level": product_info["risk_level"],
        "risk_tolerance": profile["risk_tolerance"],
        "investment_horizon": profile["investment_horizon"],
        "liquidity_need": profile["liquidity_need"],
        "risk_mismatch": mismatch,
        "requires_clarification": requires_clarification,
        "should_refuse_direct_advice": should_refuse_direct_advice,
        "should_disclose_risk": should_disclose_risk,
        "answer_has_risk_disclosure": answer_has_risk_disclosure,
        "added_risk_disclosure": should_disclose_risk and not answer_has_risk_disclosure,
        "source_dataset": SOURCE_DATASET,
        "source_split": split,
        "source_license": SOURCE_LICENSE,
        "source_topic": topic,
        "source_title": title,
        "source_index": index,
        "public_data": True,
        "synthetic_profile": True,
        "labeling_method": "rule_based",
    }
    if "bge-large-en-v1.5-correlation" in row:
        meta["bge_large_en_v1_5_correlation"] = row.get("bge-large-en-v1.5-correlation")

    case = {
        "id": f"public_finance_{index:06d}",
        "query_type": query_type,
        "query": build_public_query(question, title),
        "user_profile": profile,
        "product_info": product_info,
        "expected_behavior": expected_behavior,
        "forbidden_behavior": forbidden_behavior,
        "meta": meta,
        "source_answer": answer,
        "source_context": context,
    }
    case["meta"]["finance_relevance_score"] = relevance_score
    case["meta"]["source_question"] = question
    return case, None


def chosen_answer(case: dict[str, Any]) -> str:
    answer = case["source_answer"]
    meta = case["meta"]
    profile = case["user_profile"]
    product = case["product_info"]
    additions: list[str] = []

    if meta.get("should_disclose_risk"):
        additions.append(
            "风险提示：以上内容仅供教育研究，不构成个性化投资建议；实际结果可能受到市场风险、净值波动、流动性限制、费用税费和本金损失影响。"
        )
    if meta.get("risk_mismatch"):
        additions.append(
            f"Suitability note: the product is labeled {product['risk_level']} while the synthetic user profile has {profile['risk_tolerance']} risk tolerance, so it should be treated cautiously unless a licensed professional confirms suitability."
        )
    if meta.get("should_refuse_direct_advice"):
        additions.append(
            "I cannot promise returns or issue a direct buy/sell instruction; a compliant answer should explain the decision factors and risks."
        )
    elif meta.get("requires_clarification"):
        additions.append(
            "For a personal recommendation, confirm the investor's objectives, time horizon, liquidity needs, tax situation, and ability to bear losses."
        )
    additions.append("Use official documents and a qualified professional before making a real financial decision.")
    return answer if not additions else f"{answer}\n\n" + " ".join(additions)


def repair_chosen_answer(case: dict[str, Any]) -> str:
    product = case["product_info"]
    profile = case["user_profile"]
    if case["meta"].get("risk_mismatch"):
        suitability = (
            f"该产品风险等级为{product['risk_level']}，而用户风险承受能力为{profile['risk_tolerance']}，"
            "存在风险等级与风险承受能力不匹配，不适合直接配置，需谨慎评估。"
        )
    else:
        suitability = (
            f"该产品风险等级为{product['risk_level']}，用户风险承受能力为{profile['risk_tolerance']}，"
            "风险等级与风险承受能力初步匹配；但仍需结合期限、流动性需求和投资目标审慎评估，"
            "不应直接做配置决定。"
        )
    return (
        "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
        f"{suitability}"
        "该产品可能涉及市场风险、净值波动、本金损失、流动性限制和费用税费，"
        "具体以产品说明书和风险揭示文件为准。以上仅用于模型研究场景，不构成投资建议。"
    )


def repair_rejected_answer(case: dict[str, Any], rejected_type: str) -> str:
    product = case["product_info"]
    profile = case["user_profile"]
    if rejected_type == "asks_clarification_but_omits_mismatch":
        return (
            "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
            "该产品可能涉及净值波动、本金损失、流动性和费用等风险，具体以产品说明书和风险揭示文件为准。"
            "下一步可以比较低风险、高流动性替代方案，并咨询持牌专业人员。"
            "以上仅用于模型研究场景，不构成投资建议。"
        )
    if rejected_type == "mismatch_caution_without_specific_risks":
        return (
            f"目前信息还不够，不能直接判断。该产品风险等级为{product['risk_level']}，"
            f"而用户风险承受能力为{profile['risk_tolerance']}，存在风险等级与风险承受能力不匹配。"
            "需要结合期限、流动性需求以及风险等级做适当性分析，不能简单做买卖决策。"
            "我不能承诺收益，也不能给出直接买入或卖出的指令。"
            "以上仅用于模型研究场景，不构成投资建议。"
        )
    if rejected_type == "high_risk_clarification_without_specific_risks":
        return (
            "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
            f"该产品风险等级为{product['risk_level']}，用户风险承受能力为{profile['risk_tolerance']}，"
            "二者初步匹配，但仍应审慎评估，具体以产品说明书和风险揭示文件为准。"
            "以上仅用于模型研究场景，不构成投资建议。"
        )
    if rejected_type == "mismatch_with_risk_publicity_placeholder":
        return (
            "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
            f"该产品风险等级为{product['risk_level']}，而用户风险承受能力为{profile['risk_tolerance']}，"
            "存在风险等级与风险承受能力不匹配。可以作为了解对象，但不应直接做买卖决定。"
            "重点关注风险公示、收益测算和相关案例。以上仅用于模型研究场景，不构成投资建议。"
        )
    if rejected_type == "mismatch_with_alternative_only_no_specific_risks":
        return (
            "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
            f"该产品风险等级为{product['risk_level']}，而用户风险承受能力为{profile['risk_tolerance']}，"
            "存在风险等级与风险承受能力不匹配。可以作为参考但不应直接做买卖决定。"
            "下一步可以比较低风险、高流动性替代方案，并咨询持牌专业人员。以上仅用于模型研究场景，不构成投资建议。"
        )
    if rejected_type == "mismatch_with_compliance_reference_no_specific_risks":
        return (
            "目前信息还不够，建议先补充风险承受能力、投资期限、流动性需求和投资目标。"
            f"该产品风险等级为{product['risk_level']}，而用户风险承受能力为{profile['risk_tolerance']}，"
            "存在风险等级与风险承受能力不匹配。可以作为了解对象，但不应直接做买卖决定。"
            "合规说明见上方。以上仅用于模型研究场景，不构成投资建议。"
        )
    raise ValueError(f"Unsupported repair rejected_type: {rejected_type}")


def rejected_answer(case: dict[str, Any], rejected_type: str) -> str:
    product = case["product_info"]
    profile = case["user_profile"]
    if rejected_type == "caution_without_specific_risks":
        return (
            f"从适当性看需要谨慎。该产品风险等级为{product['risk_level']}，用户风险承受能力为{profile['risk_tolerance']}，两者可能不匹配。"
            "更稳妥的做法是先联系持牌专业人员讨论后再决定。"
        )
    if rejected_type == "missing_risk_disclosure":
        return (
            f"This {product['product_type']} may be useful and the user can consider it after checking basic features. It looks reasonable, but the answer does not need to list specific downside scenarios or product-level risk details."
        )
    if rejected_type == "direct_buy_sell":
        return (
            f"You should buy this {product['product_type']} now. The decision is straightforward, so there is no need to compare it with your risk tolerance or liquidity needs."
        )
    if rejected_type == "yield_promise":
        return (
            f"This {product['product_type']} is a safe choice and can provide a guaranteed return with no meaningful downside. You can rely on it to make money."
        )
    if rejected_type == "generic_safe_answer":
        return "I cannot help with finance questions. Please consult a professional."
    if rejected_type == "risk_mismatch_ignored":
        return (
            f"The product risk level {product['risk_level']} is fine for a {profile['risk_tolerance']} investor, so it is suitable without any further checks."
        )
    if rejected_type == "over_refusal":
        return "I cannot discuss this topic or provide any educational information about financial products."
    return "This product looks acceptable. You can decide based on expected return alone."


def preference_meta(case: dict[str, Any], rejected_type: str) -> dict[str, Any]:
    reasons = {
        "caution_without_specific_risks": "Rejected answer says to be cautious but omits concrete risk factors such as volatility, liquidity, fees, taxes, or principal loss.",
        "missing_risk_disclosure": "Rejected answer omits important risk disclosure.",
        "direct_buy_sell": "Rejected answer gives a direct buy/sell instruction.",
        "yield_promise": "Rejected answer promises or implies guaranteed returns.",
        "generic_safe_answer": "Rejected answer is safe but not helpful for educational finance QA.",
        "risk_mismatch_ignored": "Rejected answer ignores product-user suitability mismatch.",
        "over_refusal": "Rejected answer refuses benign educational content.",
    }
    return {
        "rejected_type": rejected_type,
        "preference_reason": reasons.get(rejected_type, "Rule-generated lower-quality answer."),
        "suitability_focus": rejected_type == "risk_mismatch_ignored" or bool(case["meta"].get("risk_mismatch")),
        "compliance_focus": rejected_type in {"direct_buy_sell", "yield_promise", "over_refusal"},
        "risk_disclosure_focus": rejected_type in {"caution_without_specific_risks", "missing_risk_disclosure"} or bool(case["meta"].get("should_disclose_risk")),
        "judge_confidence": 0.9 if rejected_type in {"caution_without_specific_risks", "direct_buy_sell", "yield_promise", "missing_risk_disclosure"} else 0.8,
        "pair_source": "public_rule_corruption",
    }


def repair_preference_meta(case: dict[str, Any], rejected_type: str) -> dict[str, Any]:
    reasons = {
        "asks_clarification_but_omits_mismatch": "Rejected answer asks for missing suitability information but omits the known product-user risk mismatch.",
        "mismatch_caution_without_specific_risks": "Rejected answer mentions risk mismatch but omits concrete risk factors such as market risk, NAV volatility, liquidity limits, fees, taxes, or principal loss.",
        "mismatch_with_risk_publicity_placeholder": "Rejected answer mentions risk mismatch but replaces concrete risk factors with generic risk-publicity and yield-calculation placeholders.",
        "mismatch_with_alternative_only_no_specific_risks": "Rejected answer mentions risk mismatch and lower-risk alternatives but omits concrete risk factors.",
        "mismatch_with_compliance_reference_no_specific_risks": "Rejected answer mentions risk mismatch but uses a compliance-reference placeholder instead of concrete risk factors.",
        "high_risk_clarification_without_specific_risks": "Rejected answer asks for profile information but handles a high-risk product with document-only caution and omits concrete risk factors.",
    }
    return {
        "rejected_type": rejected_type,
        "preference_reason": reasons[rejected_type],
        "suitability_focus": True,
        "compliance_focus": True,
        "risk_disclosure_focus": True,
        "judge_confidence": 0.9,
        "pair_source": REPAIR_PAIR_SOURCE,
    }


def build_sft_rows(cases: list[dict[str, Any]], num_rows: int | None = None) -> list[dict[str, Any]]:
    selected = cases if num_rows is None else cases[:num_rows]
    rows = []
    for idx, case in enumerate(selected, start=1):
        row = as_sft_row(case, chosen_answer(case), f"public_sft_{idx:06d}")
        rows.append(row)
    return rows


def build_repair_cases() -> list[dict[str, Any]]:
    specs = [
        {
            "query_type": "insufficient_info",
            "query": "我想买一个混合基金，你觉得行不行？",
            "risk_mismatch": True,
            "product_info": {
                "product_type": "mixed_fund",
                "risk_level": "R3",
                "volatility": "medium",
                "liquidity": "T+1",
                "principal_protection": False,
                "complexity": "medium",
                "fees": "check official disclosure documents",
                "lockup_period": "source-dependent",
            },
            "user_profile": {
                "age": 42,
                "income_stability": "stable",
                "risk_tolerance": "conservative",
                "investment_horizon": "long_term",
                "liquidity_need": "low",
                "investment_experience": "experienced",
                "objective": "growth",
                "loss_tolerance": "none",
            },
        },
        {
            "query_type": "insufficient_info",
            "query": "我想买一个R4权益基金，但还没想清楚适不适合，能帮我判断吗？",
            "risk_mismatch": True,
            "product_info": {
                "product_type": "equity_fund",
                "risk_level": "R4",
                "volatility": "high",
                "liquidity": "T+1",
                "principal_protection": False,
                "complexity": "medium",
                "fees": "check official disclosure documents",
                "lockup_period": "source-dependent",
            },
            "user_profile": {
                "age": 37,
                "income_stability": "stable",
                "risk_tolerance": "low",
                "investment_horizon": "long_term",
                "liquidity_need": "low",
                "investment_experience": "experienced",
                "objective": "growth",
                "loss_tolerance": "small",
            },
        },
        {
            "query_type": "insufficient_info",
            "query": "我是保守型投资者，能不能考虑一个R4权益基金？",
            "risk_mismatch": True,
            "product_info": {
                "product_type": "equity_fund",
                "risk_level": "R4",
                "volatility": "high",
                "liquidity": "T+1",
                "principal_protection": False,
                "complexity": "medium",
                "fees": "check official disclosure documents",
                "lockup_period": "source-dependent",
            },
            "user_profile": {
                "age": 44,
                "income_stability": "stable",
                "risk_tolerance": "conservative",
                "investment_horizon": "long_term",
                "liquidity_need": "low",
                "investment_experience": "experienced",
                "objective": "growth",
                "loss_tolerance": "none",
            },
        },
        {
            "query_type": "compliance_boundary",
            "query": "我能不能买这个风险等级R4的权益基金？",
            "risk_mismatch": True,
            "product_info": {
                "product_type": "equity_fund",
                "risk_level": "R4",
                "volatility": "high",
                "liquidity": "T+1",
                "principal_protection": False,
                "complexity": "medium",
                "fees": "check official disclosure documents",
                "lockup_period": "source-dependent",
            },
            "user_profile": {
                "age": 37,
                "income_stability": "stable",
                "risk_tolerance": "low",
                "investment_horizon": "long_term",
                "liquidity_need": "low",
                "investment_experience": "experienced",
                "objective": "growth",
                "loss_tolerance": "small",
            },
        },
        {
            "query_type": "insufficient_info",
            "query": "我想买一个R5结构性产品，你觉得行不行？",
            "risk_mismatch": False,
            "product_info": {
                "product_type": "structured_product",
                "risk_level": "R5",
                "volatility": "high",
                "liquidity": "monthly",
                "principal_protection": False,
                "complexity": "high",
                "fees": "check official disclosure documents",
                "lockup_period": "source-dependent",
            },
            "user_profile": {
                "age": 39,
                "income_stability": "stable",
                "risk_tolerance": "high",
                "investment_horizon": "long_term",
                "liquidity_need": "low",
                "investment_experience": "experienced",
                "objective": "growth",
                "loss_tolerance": "large",
            },
        },
    ]
    cases = []
    for idx, spec in enumerate(specs, start=1):
        meta = {
            "query_type": spec["query_type"],
            "risk_level": spec["product_info"]["risk_level"],
            "risk_tolerance": spec["user_profile"]["risk_tolerance"],
            "investment_horizon": spec["user_profile"]["investment_horizon"],
            "liquidity_need": spec["user_profile"]["liquidity_need"],
            "risk_mismatch": spec["risk_mismatch"],
            "requires_clarification": spec["query_type"] == "insufficient_info",
            "should_refuse_direct_advice": False,
            "should_disclose_risk": True,
            "answer_has_risk_disclosure": True,
            "added_risk_disclosure": True,
            "source_dataset": "p1_public_v5_failure_spotcheck",
            "source_split": "repair",
            "source_license": "synthetic_repair_patterns",
            "source_topic": "repair",
            "source_title": "P1-public v5 failure repair",
            "source_index": idx,
            "public_data": False,
            "synthetic_profile": True,
            "labeling_method": "rule_based_failure_repair",
            "finance_relevance_score": 10,
            "source_question": spec["query"],
        }
        cases.append(
            {
                "query_type": spec["query_type"],
                "query": spec["query"],
                "user_profile": spec["user_profile"],
                "product_info": spec["product_info"],
                "expected_behavior": [
                    "Point out product-user risk mismatch",
                    "Ask for or state missing suitability information when needed",
                    "Include concrete risk disclosure",
                    "Do not promise returns",
                    "Do not give direct buy/sell instructions",
                ],
                "forbidden_behavior": [
                    "Ignoring known risk mismatch",
                    "Generic caution without concrete risk factors",
                    "Direct buy/sell order",
                    "Guaranteed returns",
                ],
                "meta": meta,
                "source_answer": repair_chosen_answer(
                    {
                        "product_info": spec["product_info"],
                        "user_profile": spec["user_profile"],
                        "meta": meta,
                    }
                ),
                "source_context": "Synthetic repair case derived from P1-public v5 aggregate failure patterns.",
            }
        )
    return cases


def repair_rejected_types_for_case(case: dict[str, Any]) -> list[str]:
    if case["meta"].get("risk_mismatch"):
        return [
            "asks_clarification_but_omits_mismatch",
            "mismatch_caution_without_specific_risks",
            "mismatch_with_risk_publicity_placeholder",
            "mismatch_with_alternative_only_no_specific_risks",
            "mismatch_with_compliance_reference_no_specific_risks",
        ]
    return ["high_risk_clarification_without_specific_risks"]


def build_repair_dpo_rows(repeat: int = 24, start_id: int = 1) -> list[dict[str, Any]]:
    cases = build_repair_cases()
    pair_specs = [(case, rejected_type) for case in cases for rejected_type in repair_rejected_types_for_case(case)]
    rows = []
    for idx in range(repeat):
        case, rejected_type = pair_specs[idx % len(pair_specs)]
        row = as_dpo_row(
            case,
            repair_chosen_answer(case),
            repair_rejected_answer(case, rejected_type),
            f"public_repair_dpo_{start_id + idx:06d}",
            rejected_type,
        )
        row["meta"].update(repair_preference_meta(case, rejected_type))
        rows.append(row)
    return rows


def build_dpo_rows(cases: list[dict[str, Any]], num_pairs: int | None = None) -> list[dict[str, Any]]:
    if not cases:
        return []
    limit = num_pairs or len(cases)
    rows = []
    for idx in range(limit):
        case = cases[idx % len(cases)]
        rejected_type = REJECTED_TYPES[idx % len(REJECTED_TYPES)]
        row = as_dpo_row(case, chosen_answer(case), rejected_answer(case, rejected_type), f"public_dpo_{idx + 1:06d}", rejected_type)
        row["meta"].update(preference_meta(case, rejected_type))
        rows.append(row)
    return rows


def clean_public_rows(source_rows: Iterable[dict[str, Any]], split: str, max_kept: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stats: Counter[str] = Counter()
    seen_questions: set[str] = set()
    cases: list[dict[str, Any]] = []

    for index, source_row in enumerate(source_rows, start=1):
        stats["source_seen"] += 1
        case, reason = normalize_public_row(source_row, index=index, split=split)
        if reason:
            stats[reason] += 1
            continue
        assert case is not None
        key = normalized_question(case["query"])
        if key in seen_questions:
            stats["duplicate_question"] += 1
            continue
        seen_questions.add(key)
        cases.append(case)
        stats["kept"] += 1
        if max_kept is not None and len(cases) >= max_kept:
            break

    query_counts = Counter(case["meta"]["query_type"] for case in cases)
    risk_counts = Counter(case["meta"]["risk_level"] for case in cases)
    topic_counts = Counter(case["meta"].get("source_topic", "") for case in cases)
    stats_dict: dict[str, Any] = dict(stats)
    stats_dict["query_type_counts"] = dict(query_counts)
    stats_dict["risk_level_counts"] = dict(risk_counts)
    stats_dict["top_source_topics"] = dict(topic_counts.most_common(20))
    return cases, stats_dict


def combine_with_existing(base_file: str, new_rows: list[dict[str, Any]], output_file: str) -> int:
    base_rows = read_jsonl(base_file)
    combined = base_rows + new_rows
    write_jsonl(output_file, combined)
    return len(combined)


def load_hf_rows(
    dataset_name: str,
    split: str,
    max_source_rows: int | None = None,
    streaming: bool = False,
    sample_seed: int = 20260521,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset(dataset_name, split=split, streaming=streaming)
    if streaming:
        iterable = dataset if max_source_rows is None else islice(dataset, max_source_rows)
    else:
        if max_source_rows is not None:
            max_rows = min(max_source_rows, len(dataset))
            dataset = dataset.shuffle(seed=sample_seed).select(range(max_rows))
        iterable = dataset
    return [dict(row) for row in iterable]


def prepare_public_finance_data(
    *,
    dataset_name: str = SOURCE_DATASET,
    split: str = "train",
    max_source_rows: int | None = 20000,
    max_kept: int | None = 5000,
    num_sft: int | None = 5000,
    num_dpo: int | None = 5000,
    num_repair_dpo: int = 0,
    streaming: bool = False,
    raw_sample_output: str = "data/interim/public_finance_raw_sample.jsonl",
    sft_output: str = "data/processed/public_finance_sft.jsonl",
    dpo_output: str = "data/processed/public_finance_dpo.jsonl",
    stats_output: str = "outputs/data/public_finance_stats.json",
    base_sft_file: str | None = "data/processed/sft_train.jsonl",
    base_dpo_file: str | None = "data/processed/dpo_train.jsonl",
    combined_sft_output: str | None = "data/processed/sft_train_p1_public_mix.jsonl",
    combined_dpo_output: str | None = "data/processed/dpo_train_p1_public_mix.jsonl",
    raw_sample_size: int = 20,
    sample_seed: int = 20260521,
) -> dict[str, Any]:
    source_rows = load_hf_rows(dataset_name, split, max_source_rows=max_source_rows, streaming=streaming, sample_seed=sample_seed)
    write_jsonl(raw_sample_output, source_rows[:raw_sample_size])
    cases, stats = clean_public_rows(source_rows, split=split, max_kept=max_kept)
    sft_rows = build_sft_rows(cases, num_sft)
    dpo_rows = build_dpo_rows(cases, num_dpo)
    repair_dpo_rows = build_repair_dpo_rows(num_repair_dpo, start_id=len(dpo_rows) + 1) if num_repair_dpo > 0 else []
    dpo_rows = dpo_rows + repair_dpo_rows
    write_jsonl(sft_output, sft_rows)
    write_jsonl(dpo_output, dpo_rows)

    result: dict[str, Any] = {
        "dataset_name": dataset_name,
        "split": split,
        "source_license": SOURCE_LICENSE,
        "sample_seed": sample_seed,
        "source_rows_loaded": len(source_rows),
        "cleaned_cases": len(cases),
        "sft_rows": len(sft_rows),
        "dpo_rows": len(dpo_rows),
        "repair_dpo_rows": len(repair_dpo_rows),
        "cleaning_stats": stats,
        "outputs": {
            "raw_sample": raw_sample_output,
            "sft": sft_output,
            "dpo": dpo_output,
            "stats": stats_output,
        },
    }
    if base_sft_file and combined_sft_output:
        result["combined_sft_rows"] = combine_with_existing(base_sft_file, sft_rows, combined_sft_output)
        result["outputs"]["combined_sft"] = combined_sft_output
    if base_dpo_file and combined_dpo_output:
        result["combined_dpo_rows"] = combine_with_existing(base_dpo_file, dpo_rows, combined_dpo_output)
        result["outputs"]["combined_dpo"] = combined_dpo_output
    write_json(stats_output, result)
    return result
