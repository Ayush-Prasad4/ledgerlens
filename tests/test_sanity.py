from ledgerlens.agent import check_node
from ledgerlens.calculate import FAILURE_PREFIX
from ledgerlens.sanity import sanity_check

GROWTH_Q = "By what percent did Meta's total revenue grow from fiscal 2023 to fiscal 2024?"
ONE_YEAR_Q = "What was Apple's net sales in fiscal 2024?"


def calc(facts, result=1.0):
    return {
        "ok": True,
        "facts": [{"name": n, "fiscal_year": fy, "ticker": "X", "value": 1.0} for n, fy in facts],
        "result": result,
    }


def test_growth_question_with_comparative_year_passes():
    c = calc([("meta_total_revenue_2024", 2024), ("meta_total_revenue_2023", 2024)])
    assert sanity_check(GROWTH_Q, c) == (True, "")


def test_single_year_ratio_passes():
    q = "What was Microsoft's research and development expense as a percent of its total revenue in fiscal 2025?"
    c = calc([("msft_research_and_development_2025", 2025), ("msft_total_revenue_2025", 2025)])
    assert sanity_check(q, c) == (True, "")


def test_relative_year_question_passes():
    q = "How did Apple's net sales in fiscal 2024 change from the year before?"
    c = calc([("aapl_net_sales_2024", 2024), ("aapl_net_sales_2023", 2024)])
    assert sanity_check(q, c)[0] is True


def test_number_from_a_filing_before_its_year_fails():
    ok, reason = sanity_check(ONE_YEAR_Q, calc([("aapl_net_sales_2026", 2024)]))
    assert not ok and "FY2024" in reason


def test_number_older_than_three_columns_fails():
    ok, reason = sanity_check(ONE_YEAR_Q, calc([("aapl_net_sales_2021", 2024)]))
    assert not ok and "FY2024" in reason


def test_name_without_year_fails():
    ok, reason = sanity_check(ONE_YEAR_Q, calc([("aapl_net_sales", 2024)]))
    assert not ok and "which year" in reason


def test_missing_asked_year_fails():
    c = calc([("meta_total_revenue_2024", 2024), ("meta_total_revenue_2024_again", 2024)])
    ok, reason = sanity_check(GROWTH_Q, c)
    assert not ok and "2023" in reason


def test_non_finite_result_fails():
    for bad in (float("inf"), float("nan")):
        ok, reason = sanity_check(ONE_YEAR_Q, calc([("aapl_net_sales_2024", 2024)], result=bad))
        assert not ok and "finite" in reason


def test_unknown_filing_year_fails():
    ok, reason = sanity_check(ONE_YEAR_Q, calc([("aapl_net_sales_2024", None)]))
    assert not ok and "unknown filing year" in reason


def test_check_node_passes_a_good_calculation_through():
    state = {"question": ONE_YEAR_Q, "answer": "Result: 1.00", "calculation": calc([("aapl_net_sales_2024", 2024)])}
    assert check_node(state) == {"answer": "Result: 1.00"}


def test_check_node_replaces_the_answer_when_the_gate_fails():
    state = {"question": ONE_YEAR_Q, "answer": "Result: 1.00", "calculation": calc([("aapl_net_sales_2026", 2024)])}
    out = check_node(state)
    assert out["answer"].startswith(FAILURE_PREFIX)
    assert out["sources"] == []
    assert out["calculation"]["ok"] is False


def test_check_node_leaves_an_existing_refusal_alone():
    state = {"question": ONE_YEAR_Q, "answer": FAILURE_PREFIX + "no facts returned", "calculation": {"ok": False, "error": "no facts returned"}}
    assert check_node(state) == {"answer": FAILURE_PREFIX + "no facts returned"}
