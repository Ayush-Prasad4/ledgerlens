from types import SimpleNamespace

import pytest

from ledgerlens.formula_writer import FormulaError, parse_expression, write_formula

FACTS = [
    {"name": "sales_2024", "value": 391035.0, "ticker": "AAPL", "fiscal_year": 2024},
    {"name": "sales_2023", "value": 383285.0, "ticker": "AAPL", "fiscal_year": 2023},
]
GROWTH = "(sales_2024 - sales_2023) / sales_2023 * 100"


def patch_llm(monkeypatch, content=None, error=None, seen=None):
    def create(**kwargs):
        if seen is not None:
            seen.append(kwargs)
        if error:
            raise error
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr("ledgerlens.formula_writer.get_llm", lambda: client)


def test_parse_expression_ok():
    assert parse_expression('{"expression": " ' + GROWTH + ' "}') == GROWTH


@pytest.mark.parametrize(
    "text",
    ["not json", "[]", "{}", '{"expression": ""}', '{"expression": 5}', None],
)
def test_parse_expression_bad(text):
    with pytest.raises(FormulaError):
        parse_expression(text)


def test_allowed_constants():
    assert parse_expression('{"expression": "(a + b) / 2"}') == "(a + b) / 2"
    assert parse_expression('{"expression": "a / b * 100"}') == "a / b * 100"


def test_constant_not_allowed():
    with pytest.raises(FormulaError):
        parse_expression('{"expression": "a * 7"}')


def test_write_formula_ok(monkeypatch):
    seen = []
    patch_llm(monkeypatch, content='{"expression": "' + GROWTH + '"}', seen=seen)
    assert write_formula("Apple sales growth?", FACTS) == GROWTH
    user_message = seen[0]["messages"][1]["content"]
    assert "sales_2024 = 391035" in user_message
    assert "Apple sales growth?" in user_message


def test_write_formula_api_error(monkeypatch):
    patch_llm(monkeypatch, error=RuntimeError("boom"))
    with pytest.raises(FormulaError):
        write_formula("q", FACTS)


def test_write_formula_bad_output(monkeypatch):
    patch_llm(monkeypatch, content="here is the answer: 2%")
    with pytest.raises(FormulaError):
        write_formula("q", FACTS)
