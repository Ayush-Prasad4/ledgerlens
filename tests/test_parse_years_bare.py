import pytest

from ledgerlens.query_parser import parse_years


@pytest.mark.parametrize(
    "question, expected",
    [
        ("How much did Amazon's net income change from 2023 to 2024?", [2023, 2024]),
        ("What was Meta's revenue in 2024?", [2024]),
        ("Compare Apple's net sales in fiscal 2024 with 2023", [2023, 2024]),
        ("Apple net sales on December 30, 2023", []),
        ("Apple net sales for the year ended September 28, 2024", [2024]),
        ("What does Microsoft do?", []),
    ],
)
def test_parse_years_with_bare_years(question, expected):
    assert parse_years(question) == expected
