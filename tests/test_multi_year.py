import pytest

from ledgerlens import ask
from ledgerlens.query_parser import parse_years


@pytest.mark.parametrize(
    "question, expected",
    [
        ("By what percent did Apple's net sales grow from fiscal 2023 to fiscal 2024?", [2023, 2024]),
        ("Apple net sales growth from fiscal 2023 to 2024", [2023, 2024]),
        ("Microsoft revenue for fiscal year 2025 and fiscal year 2024", [2024, 2025]),
        ("What was Amazon's FY2024 revenue?", [2024]),
        ("What is Apple's main business?", []),
        ("Apple net sales for the year ended September 30, 2024 versus September 28, 2023", [2023, 2024]),
    ],
)
def test_parse_years(question, expected):
    assert parse_years(question) == expected


def fake_search_factory(calls):
    def fake_search(question, limit=5, ticker=None, fiscal_year=None, mode="hybrid"):
        calls.append((ticker, fiscal_year))
        payload = {"chunk_id": f"{ticker}-{fiscal_year}", "ticker": ticker, "fiscal_year": fiscal_year}
        return [(1.0, payload)]

    return fake_search


def test_retrieve_one_search_per_year(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", fake_search_factory(calls))
    points = ask.retrieve("Apple net sales growth from fiscal 2023 to fiscal 2024")
    assert calls == [("AAPL", 2023), ("AAPL", 2024)]
    assert [p["chunk_id"] for p in points] == ["AAPL-2023", "AAPL-2024"]


def test_retrieve_single_year_unchanged(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", fake_search_factory(calls))
    ask.retrieve("What was Apple's net sales in fiscal 2024?")
    assert calls == [("AAPL", 2024)]


def test_retrieve_two_years_without_company_unchanged(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", fake_search_factory(calls))
    ask.retrieve("Compare net sales in fiscal 2023 to fiscal 2024")
    assert calls == [(None, 2023)]
