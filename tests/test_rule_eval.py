from finpref.eval.rule_eval import evaluate_response


def test_rule_eval_flags_forbidden_phrase():
    metrics = evaluate_response("建议你买入，这个产品保证收益。", {})
    assert metrics["compliance_pass"] is False
    assert metrics["forbidden_phrase"] is True


def test_rule_eval_accepts_cautious_risk_mismatch_answer():
    text = "不建议直接配置。该产品风险较高，可能出现净值波动和本金损失，与你的风险承受能力不匹配。"
    metrics = evaluate_response(text, {"risk_mismatch": True})
    assert metrics["compliance_pass"] is True
    assert metrics["suitability_match"] is True
    assert metrics["risk_disclosure"] is True


def test_rule_eval_does_not_flag_negated_direct_recommendation():
    text = "我不能给出直接买入或卖出的指令，但可以说明净值波动和本金损失风险。"
    metrics = evaluate_response(text, {})
    assert metrics["compliance_pass"] is True
