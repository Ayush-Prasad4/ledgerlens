from ledgerlens.edgar import find_10k_filings

FAKE = {
    "filings": {
        "recent": {
            "form": ["8-K", "10-K", "10-Q", "10-K", "10-K", "10-K"],
            "accessionNumber": [
                "0000320193-24-000001",
                "0000320193-23-000106",
                "0000320193-23-000077",
                "0000320193-22-000108",
                "0000320193-21-000105",
                "0000320193-20-000096",
            ],
            "primaryDocument": ["a.htm", "aapl-20230930.htm", "q.htm", "b.htm", "c.htm", "d.htm"],
            "reportDate": [
                "2024-01-01",
                "2023-09-30",
                "2023-07-01",
                "2022-09-24",
                "2021-09-25",
                "2020-09-26",
            ],
        }
    }
}


def test_only_10k_and_limit():
    result = find_10k_filings(FAKE, "0000320193", limit=2)
    assert len(result) == 2
    assert all(f["form"] == "10-K" for f in result)
    assert [f["fiscal_year"] for f in result] == [2023, 2022]


def test_url_is_built_correctly():
    first = find_10k_filings(FAKE, "0000320193", limit=1)[0]
    assert first["url"] == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"
    )
