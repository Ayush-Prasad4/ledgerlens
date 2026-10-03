import pytest

from ledgerlens.calculator import CalculatorError
from ledgerlens.formula import evaluate_formula

FACTS = [
    {"name": "sales_2024", "value": 391035.0},
    {"name": "sales_2023", "value": 383285.0},
]


def test_growth_percent():
    numeric, result = evaluate_formula("(sales_2024 - sales_2023) / sales_2023 * 100", FACTS)
    assert result == pytest.approx(2.0220, abs=1e-3)
    assert not any(c.isalpha() for c in numeric)


def test_unknown_name_rejected():
    with pytest.raises(CalculatorError):
        evaluate_formula("sales_2025 - sales_2024", FACTS)


@pytest.mark.parametrize("expression", ["__import__('os').system('ls')", "open('x')"])
def test_injection_rejected(expression):
    with pytest.raises(CalculatorError):
        evaluate_formula(expression, FACTS)


def test_negative_value():
    facts = [{"name": "a", "value": -5.0}, {"name": "b", "value": 2.0}]
    assert evaluate_formula("a * b", facts)[1] == pytest.approx(-10.0)


def test_empty_expression():
    with pytest.raises(CalculatorError):
        evaluate_formula("  ", FACTS)


def test_division_by_zero_fact():
    facts = [{"name": "a", "value": 5.0}, {"name": "b", "value": 0.0}]
    with pytest.raises(CalculatorError):
        evaluate_formula("a / b", facts)
