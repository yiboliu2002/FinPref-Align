from finpref.schema import FinancialCase, ProductInfo, UserProfile


def test_financial_case_accepts_known_query_type():
    profile = UserProfile(28, "stable", "low", "short_term", "high", "beginner", "down_payment", "none")
    product = ProductInfo("equity_fund", "R4", "T+1", "high", "1.5%", "none", False, "medium")
    case = FinancialCase("x", "suitability", "能买吗？", profile, product)
    assert case.to_dict()["query_type"] == "suitability"


def test_financial_case_rejects_unknown_query_type():
    profile = UserProfile(28, "stable", "low", "short_term", "high", "beginner", "down_payment", "none")
    product = ProductInfo("equity_fund", "R4", "T+1", "high", "1.5%", "none", False, "medium")
    try:
        FinancialCase("x", "unknown", "能买吗？", profile, product)
    except ValueError as exc:
        assert "Unsupported query_type" in str(exc)
    else:
        raise AssertionError("expected ValueError")

