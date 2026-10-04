import pytest

from ledgerlens.facts import FactError, number_in_text, parse_number


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("391,035", 391035.0),
        ("$391,035", 391035.0),
        ("637959", 637959.0),
        ("12.5", 12.5),
        ("(1,234)", -1234.0),
    ],
)
def test_parse_number_ok(raw, expected):
    assert parse_number(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "1,23", "12.", "1e5", None])
def test_parse_number_bad(raw):
    with pytest.raises(FactError):
        parse_number(raw)


def test_number_in_text_found():
    assert number_in_text("391,035", "Net sales were $391,035 million in 2024.")
    assert number_in_text("391,035", "total was 391,035.")


def test_number_in_text_bracketed_means_negative():
    # (391,035) is a negative number in a filing: a bare "391,035" would drop the sign,
    # so it must be rejected; the value has to carry its brackets.
    assert not number_in_text("391,035", "(391,035)")
    assert number_in_text("(391,035)", "(391,035)")


def test_number_in_text_not_inside_bigger_number():
    assert not number_in_text("391,035", "value 1,391,035 million")
    assert not number_in_text("391,035", "value 391,0351")
    assert not number_in_text("391,035", "value 391,035.7")


def test_number_in_text_missing():
    assert not number_in_text("391,035", "Net sales were 383,285 million")
    assert not number_in_text("", "anything")
