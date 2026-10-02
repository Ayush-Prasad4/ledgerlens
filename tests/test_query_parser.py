from ledgerlens.query_parser import parse_query


def test_company_and_fiscal_year():
    assert parse_query("What were Alphabet's total revenues in fiscal 2023?") == ("GOOGL", 2023)


def test_fy_notation():
    assert parse_query("Apple FY2024 net sales?") == ("AAPL", 2024)


def test_year_from_fiscal_year_end_date_calendar_company():
    assert parse_query("How many employees did Amazon have as of December 31, 2023?") == ("AMZN", 2023)
    assert parse_query("Meta's DAP for December 2024?") == ("META", 2024)


def test_year_from_fiscal_year_end_date_non_calendar_company():
    assert parse_query("Microsoft headcount as of June 30, 2025?") == ("MSFT", 2025)


def test_date_outside_fiscal_year_end_month_gives_no_year():
    assert parse_query("Meta's DAP for March 2024?") == ("META", None)


def test_two_companies_is_ambiguous():
    assert parse_query("Apple's deal with Google in fiscal 2024?") == (None, 2024)


def test_nothing_found():
    assert parse_query("What are the main risk factors?") == (None, None)
