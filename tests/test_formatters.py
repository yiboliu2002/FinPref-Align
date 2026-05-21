from finpref.data.formatters import prompt_messages


def test_prompt_messages_contains_system_and_user():
    row = {
        "query": "能买吗？",
        "user_profile": {"risk_tolerance": "low", "investment_horizon": "short_term", "liquidity_need": "high", "investment_experience": "beginner"},
        "product_info": {"product_type": "equity_fund", "risk_level": "R4", "volatility": "high", "liquidity": "T+1"},
    }
    messages = prompt_messages(row)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "风险等级R4" in messages[1]["content"]

