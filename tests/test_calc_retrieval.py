import pytest

from ledgerlens import calc_retrieval
from ledgerlens.calc_retrieval import query_variants, retrieve_for_metrics


@pytest.mark.parametrize(
    "metric, expected",
    [
        ("Net sales", ["Net sales", "Total net sales"]),
        ("Net income", ["Net income"]),
        ("Total revenues", ["Total revenues"]),
    ],
)
def test_query_variants(metric, expected):
    assert query_variants(metric) == expected


def fake_search_factory(calls, same=False):
    def fake_search(question, limit=5, ticker=None, fiscal_year=None, mode="hybrid"):
        calls.append((question, ticker, fiscal_year))
        if same:
            return [(1.0, {"chunk_id": f"{fiscal_year}-same"})]
        return [(1.0, {"chunk_id": f"{fiscal_year}-{question}-{r}"}) for r in range(limit)]

    return fake_search


def test_one_search_per_year_metric_variant(monkeypatch):
    calls = []
    monkeypatch.setattr(calc_retrieval, "search", fake_search_factory(calls))
    retrieve_for_metrics(["Net sales"], "AAPL", [2023, 2024])
    assert calls == [
        ("Net sales", "AAPL", 2023),
        ("Total net sales", "AAPL", 2023),
        ("Net sales", "AAPL", 2024),
        ("Total net sales", "AAPL", 2024),
    ]


def test_dedupes_same_chunk(monkeypatch):
    monkeypatch.setattr(calc_retrieval, "search", fake_search_factory([], same=True))
    points = retrieve_for_metrics(["Net sales"], "AAPL", [2023, 2024])
    assert [p["chunk_id"] for p in points] == ["2023-same", "2024-same"]


def test_cap_keeps_best_rank_first(monkeypatch):
    monkeypatch.setattr(calc_retrieval, "search", fake_search_factory([]))
    points = retrieve_for_metrics(["Net sales"], "AAPL", [2023, 2024], per_query=2, max_points=3)
    assert [p["chunk_id"] for p in points] == [
        "2023-Net sales-0",
        "2023-Total net sales-0",
        "2024-Net sales-0",
    ]


@pytest.mark.parametrize("ticker, years", [(None, [2024]), ("AAPL", [])])
def test_needs_ticker_and_years(monkeypatch, ticker, years):
    monkeypatch.setattr(calc_retrieval, "search", fake_search_factory([]))
    with pytest.raises(ValueError):
        retrieve_for_metrics(["Net sales"], ticker, years)
