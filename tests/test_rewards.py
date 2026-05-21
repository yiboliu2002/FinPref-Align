from finpref.rewards.combined import score_completion


def test_score_completion_penalizes_yield_promise():
    result = score_completion("这个产品保证收益，没有风险，可以放心买。", {"risk_mismatch": True})
    assert result["components"]["return_promise_penalty"] == 1.0
    assert result["components"]["compliance"] == 0.0


def test_score_completion_rewards_risk_disclosure():
    text = "该产品存在净值波动、本金损失和流动性风险，需要结合投资期限谨慎判断。"
    result = score_completion(text, {"risk_mismatch": True})
    assert result["components"]["risk_disclosure"] == 1.0

