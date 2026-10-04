import pytest

from ledgerlens.extractor import verify_fact
from ledgerlens.facts import FactError, number_in_text

QUOTE = "Net income (loss) | $33,364 | $(2,722) | $30,425"
CHUNKS = {"AMZN-2023-0121": {"chunk_id": "AMZN-2023-0121", "text": QUOTE, "ticker": "AMZN", "fiscal_year": 2023}}


def _fact(value):
    return {"name": "amzn_net_income_2022", "value": value, "quote": QUOTE, "chunk_id": "AMZN-2023-0121"}


def test_bare_number_inside_brackets_is_rejected():
    assert number_in_text("2,722", QUOTE) is False


def test_bracketed_value_is_accepted():
    assert number_in_text("(2,722)", QUOTE) is True


def test_dollar_bracketed_value_is_accepted():
    assert number_in_text("$(2,722)", QUOTE) is True


def test_plain_numbers_still_found():
    assert number_in_text("30,425", QUOTE) is True
    assert number_in_text("33,364", QUOTE) is True
    assert number_in_text("2,722", "Revenue | 2,722 | 3,000") is True


def test_verify_fact_rejects_dropped_brackets():
    with pytest.raises(FactError, match="value not found in quote"):
        verify_fact(_fact("2,722"), CHUNKS)


def test_verify_fact_keeps_negative_sign():
    assert verify_fact(_fact("(2,722)"), CHUNKS)["value"] == -2722.0


def test_verify_fact_dollar_bracket_keeps_negative_sign():
    assert verify_fact(_fact("$(2,722)"), CHUNKS)["value"] == -2722.0
