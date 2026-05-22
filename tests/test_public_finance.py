from finpref.data.public_finance import (
    build_dpo_rows,
    build_repair_cases,
    build_repair_dpo_rows,
    repair_rejected_types_for_case,
    build_sft_rows,
    chosen_answer,
    clean_public_rows,
    repair_chosen_answer,
    repair_rejected_answer,
    rejected_answer,
)
from finpref.eval.rule_eval import evaluate_response
from finpref.data.validators import validate_dpo_row, validate_sft_row


def test_public_finance_rows_build_valid_sft_and_dpo():
    rows = [
        {
            "Question": "What are the risks of investing in a stock ETF for retirement?",
            "Answer": "A stock ETF can provide diversification, but it still has market risk, volatility, possible loss, fees, taxes, and liquidity considerations. It should be evaluated against time horizon and risk tolerance.",
            "Topic": "Investing",
            "Title": "ETF risks",
            "Context": "Exchange traded funds are market products.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert stats["kept"] == 1
    assert cases[0]["meta"]["source_dataset"] == "FinLang/investopedia-instruction-tuning-dataset"
    assert cases[0]["meta"]["should_disclose_risk"] is True

    sft_row = build_sft_rows(cases, 1)[0]
    dpo_row = build_dpo_rows(cases, 1)[0]
    assert validate_sft_row(sft_row) == []
    assert validate_dpo_row(dpo_row) == []
    assert dpo_row["meta"]["preference_reason"]


def test_public_finance_filter_rejects_direct_advice_answer():
    rows = [
        {
            "Question": "Should I invest in this stock?",
            "Answer": "You should buy now because this is a strong buy and the upside is obvious.",
            "Topic": "Investing",
            "Title": "Stock pick",
            "Context": "Stocks can fluctuate.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert cases == []
    assert stats["direct_instruction_answer"] == 1


def test_public_finance_filter_rejects_source_artifacts():
    rows = [
        {
            "Question": "In the given passage, how are residual values calculated for an unnamed experiment with a linear equation yest = 1x + 2?",
            "Answer": "Residual values are calculated by comparing predicted values with observed values.",
            "Topic": "mortgage",
            "Title": "Residual Standard Deviation: Definition, Formula, and Examples",
            "Context": "A statistics passage.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert cases == []
    assert stats["source_artifact_question"] == 1


def test_public_finance_filter_rejects_article_trading_strategy():
    rows = [
        {
            "Question": "What is the suggested trading strategy for Raytheon Technologies stock according to the passage?",
            "Answer": "The suggested trading strategy is to buy Raytheon Technologies stock on weakness and reduce holdings on strength.",
            "Topic": "market+news",
            "Title": "Raytheon Technologies Drops Then Pops on Earnings Beat",
            "Context": "A market news article.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert cases == []
    assert stats["source_artifact_question"] == 1


def test_public_finance_chosen_always_keeps_specific_risk_disclosure():
    rows = [
        {
            "Question": "What are the risks of investing in a stock ETF for retirement?",
            "Answer": "A stock ETF can provide diversification and broad market exposure for long-term investors.",
            "Topic": "Investing",
            "Title": "ETF risks",
            "Context": "Exchange traded funds are market products with fees and liquidity considerations.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert stats["kept"] == 1
    answer = chosen_answer(cases[0])
    metrics = evaluate_response(answer, cases[0]["meta"])
    assert metrics["risk_disclosure"] is True


def test_public_finance_caution_without_specific_risks_is_hard_negative():
    rows = [
        {
            "Question": "Should I invest in a crypto fund if I am conservative?",
            "Answer": "Crypto funds are volatile products and can involve market risk, liquidity constraints, fees, taxes, and principal loss.",
            "Topic": "Crypto",
            "Title": "Crypto fund suitability",
            "Context": "Crypto assets can fluctuate significantly.",
        }
    ]
    cases, stats = clean_public_rows(rows, "train")

    assert stats["kept"] == 1
    rejected = rejected_answer(cases[0], "caution_without_specific_risks")
    metrics = evaluate_response(rejected, cases[0]["meta"])
    assert metrics["suitability_match"] is True
    assert metrics["risk_disclosure"] is False


def test_public_finance_repair_chosen_covers_v2_failure_modes():
    cases = build_repair_cases()
    assert {
        (case["meta"]["risk_level"], case["meta"]["risk_tolerance"], case["meta"]["query_type"], case["meta"]["risk_mismatch"])
        for case in cases
    } == {
        ("R3", "conservative", "insufficient_info", True),
        ("R4", "low", "insufficient_info", True),
        ("R4", "conservative", "insufficient_info", True),
        ("R4", "low", "compliance_boundary", True),
        ("R5", "high", "insufficient_info", False),
    }
    for case in cases:
        answer = repair_chosen_answer(case)
        for term in ["净值波动", "本金损失", "流动性", "费用"]:
            assert term in answer
        if case["meta"]["risk_mismatch"]:
            assert "风险等级与风险承受能力不匹配" in answer
        metrics = evaluate_response(repair_chosen_answer(case), case["meta"])
        assert metrics["compliance_pass"] is True
        assert metrics["suitability_match"] is True
        assert metrics["risk_disclosure"] is True
        assert metrics["clarification"] is True


def test_public_finance_repair_rejected_omits_known_mismatch():
    case = build_repair_cases()[0]
    rejected = repair_rejected_answer(case, "asks_clarification_but_omits_mismatch")
    metrics = evaluate_response(rejected, case["meta"])

    assert metrics["compliance_pass"] is True
    assert metrics["risk_disclosure"] is True
    assert metrics["clarification"] is True
    assert metrics["suitability_match"] is False


def test_public_finance_repair_rejected_omits_specific_risks():
    case = build_repair_cases()[1]
    rejected = repair_rejected_answer(case, "mismatch_caution_without_specific_risks")
    metrics = evaluate_response(rejected, case["meta"])

    assert metrics["compliance_pass"] is True
    assert metrics["suitability_match"] is True
    assert metrics["clarification"] is True
    assert metrics["risk_disclosure"] is False


def test_public_finance_repair_rejected_high_risk_omits_specific_risks():
    case = [item for item in build_repair_cases() if item["meta"]["risk_mismatch"] is False][0]
    rejected = repair_rejected_answer(case, "high_risk_clarification_without_specific_risks")
    metrics = evaluate_response(rejected, case["meta"])

    assert metrics["compliance_pass"] is True
    assert metrics["suitability_match"] is True
    assert metrics["clarification"] is True
    assert metrics["risk_disclosure"] is False


def test_public_finance_repair_rejected_placeholders_omit_specific_risks():
    case = build_repair_cases()[0]
    for rejected_type in [
        "mismatch_with_risk_publicity_placeholder",
        "mismatch_with_alternative_only_no_specific_risks",
        "mismatch_with_compliance_reference_no_specific_risks",
    ]:
        rejected = repair_rejected_answer(case, rejected_type)
        metrics = evaluate_response(rejected, case["meta"])

        assert metrics["compliance_pass"] is True
        assert metrics["suitability_match"] is True
        assert metrics["clarification"] is True
        assert metrics["risk_disclosure"] is False


def test_public_finance_repair_dpo_rows_are_valid_and_tagged():
    rows = build_repair_dpo_rows(repeat=21, start_id=5001)

    assert len(rows) == 21
    assert {row["meta"]["pair_source"] for row in rows} == {"public_v5_failure_repair"}
    assert {row["meta"]["rejected_type"] for row in rows} == {
        "asks_clarification_but_omits_mismatch",
        "mismatch_caution_without_specific_risks",
        "mismatch_with_risk_publicity_placeholder",
        "mismatch_with_alternative_only_no_specific_risks",
        "mismatch_with_compliance_reference_no_specific_risks",
        "high_risk_clarification_without_specific_risks",
    }
    assert {(row["meta"]["risk_level"], row["meta"]["risk_tolerance"], row["meta"]["rejected_type"]) for row in rows} == {
        ("R3", "conservative", "asks_clarification_but_omits_mismatch"),
        ("R3", "conservative", "mismatch_caution_without_specific_risks"),
        ("R3", "conservative", "mismatch_with_risk_publicity_placeholder"),
        ("R3", "conservative", "mismatch_with_alternative_only_no_specific_risks"),
        ("R3", "conservative", "mismatch_with_compliance_reference_no_specific_risks"),
        ("R4", "low", "asks_clarification_but_omits_mismatch"),
        ("R4", "low", "mismatch_caution_without_specific_risks"),
        ("R4", "low", "mismatch_with_risk_publicity_placeholder"),
        ("R4", "low", "mismatch_with_alternative_only_no_specific_risks"),
        ("R4", "low", "mismatch_with_compliance_reference_no_specific_risks"),
        ("R4", "conservative", "asks_clarification_but_omits_mismatch"),
        ("R4", "conservative", "mismatch_caution_without_specific_risks"),
        ("R4", "conservative", "mismatch_with_risk_publicity_placeholder"),
        ("R4", "conservative", "mismatch_with_alternative_only_no_specific_risks"),
        ("R4", "conservative", "mismatch_with_compliance_reference_no_specific_risks"),
        ("R5", "high", "high_risk_clarification_without_specific_risks"),
    }
    assert rows[0]["id"] == "public_repair_dpo_005001"
    assert all(validate_dpo_row(row) == [] for row in rows)


def test_public_finance_repair_pair_specs_only_apply_relevant_hard_negatives():
    mismatch_case = build_repair_cases()[0]
    non_mismatch_case = [item for item in build_repair_cases() if item["meta"]["risk_mismatch"] is False][0]

    assert repair_rejected_types_for_case(mismatch_case) == [
        "asks_clarification_but_omits_mismatch",
        "mismatch_caution_without_specific_risks",
        "mismatch_with_risk_publicity_placeholder",
        "mismatch_with_alternative_only_no_specific_risks",
        "mismatch_with_compliance_reference_no_specific_risks",
    ]
    assert repair_rejected_types_for_case(non_mismatch_case) == ["high_risk_clarification_without_specific_risks"]
