from ledgerlens import ask


def make_fake(available_years, calls):
    def fake_search(question, limit, ticker=None, fiscal_year=None, mode="hybrid"):
        calls.append(fiscal_year)
        if fiscal_year in available_years:
            return [(1.0, {"ticker": ticker, "fiscal_year": fiscal_year, "chunk_id": "x"})]
        return []
    return fake_search


def test_falls_back_to_later_filing(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", make_fake({2024}, calls))
    points = ask.retrieve("What was Meta's total revenue in 2023?")
    assert calls == [2023, 2024]
    assert points[0]["fiscal_year"] == 2024


def test_no_fallback_when_year_exists(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", make_fake({2023}, calls))
    points = ask.retrieve("What was Meta's total revenue in 2023?")
    assert calls == [2023]
    assert points[0]["fiscal_year"] == 2023


def test_gives_up_after_two_later_years(monkeypatch):
    calls = []
    monkeypatch.setattr(ask, "search", make_fake(set(), calls))
    points = ask.retrieve("What was Meta's total revenue in 2023?")
    assert calls == [2023, 2024, 2025]
    assert points == []
