import pytest

from ledgerlens.extractor import verify_fact, verify_facts
from ledgerlens.facts import FactError

POINTS = [
    {
        "chunk_id": "c1",
        "ticker": "AAPL",
        "fiscal_year": 2024,
        "text": "Net sales were $391,035 million in 2024 and $383,285 million in 2023.",
    }
]
CHUNKS = {p["chunk_id"]: p for p in POINTS}


def good(**changes):
    fact = {
        "name": "sales_2024",
        "value": "391,035",
        "quote": "Net sales were $391,035 million in 2024",
        "chunk_id": "c1",
    }
    fact.update(changes)
    return fact


def test_valid_fact():
    result = verify_fact(good(), CHUNKS)
    assert result["value"] == 391035.0
    assert result["ticker"] == "AAPL"
    assert result["fiscal_year"] == 2024


def test_whitespace_in_quote_is_ignored():
    fact = good(quote="Net sales  were\n$391,035 million in 2024")
    assert verify_fact(fact, CHUNKS)["value"] == 391035.0


def test_quote_not_in_chunk():
    with pytest.raises(FactError):
        verify_fact(good(quote="Revenue was $391,035 million"), CHUNKS)


def test_value_not_in_quote():
    with pytest.raises(FactError):
        verify_fact(good(value="383,285"), CHUNKS)


def test_unknown_chunk_id():
    with pytest.raises(FactError):
        verify_fact(good(chunk_id="zzz"), CHUNKS)


@pytest.mark.parametrize("name", ["Sales 2024", "2024_sales", "", "a-b"])
def test_bad_name(name):
    with pytest.raises(FactError):
        verify_fact(good(name=name), CHUNKS)


def test_missing_field():
    fact = good()
    del fact["quote"]
    with pytest.raises(FactError):
        verify_fact(fact, CHUNKS)


def test_verify_facts_two_ok():
    second = good(
        name="sales_2023",
        value="383,285",
        quote="$383,285 million in 2023",
    )
    result = verify_facts([good(), second], POINTS)
    assert [f["name"] for f in result] == ["sales_2024", "sales_2023"]


def test_verify_facts_one_bad_rejects_all():
    bad = good(name="sales_2023", value="999,999")
    with pytest.raises(FactError):
        verify_facts([good(), bad], POINTS)


def test_verify_facts_duplicate_name():
    with pytest.raises(FactError):
        verify_facts([good(), good()], POINTS)


@pytest.mark.parametrize("raw", [[], None, "x"])
def test_verify_facts_empty_or_wrong_type(raw):
    with pytest.raises(FactError):
        verify_facts(raw, POINTS)
