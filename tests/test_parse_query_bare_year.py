import pytest

from ledgerlens.query_parser import parse_query


@pytest.mark.parametrize(
    "question, expected",
    [
        ("What was Amazon's net income in 2024?", ("AMZN", 2024)),
        ("Apple net sales in fiscal 2024", ("AAPL", 2024)),
        ("Apple net sales for the year ended September 28, 2024", ("AAPL", 2024)),
        ("Apple net sales on December 30, 2023", ("AAPL", None)),
        ("Apple net sales from 2023 to 2024", ("AAPL", None)),
        ("What was total revenue in 2024?", (None, 2024)),
        ("What does Microsoft do?", ("MSFT", None)),
    ],
)
def test_parse_query_bare_year(question, expected):
    assert parse_query(question) == expected
