import pytest

from ledgerlens.calculator import CalculatorError, calculate


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("1 + 2", 3.0),
        ("(150 - 100) / 100 * 100", 50.0),
        ("-5 + 2", -3.0),
        ("10 / 4", 2.5),
        ("2 * (3 + 4)", 14.0),
    ],
)
def test_valid_expressions(expression, expected):
    assert calculate(expression) == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('ls')",
        "open('x')",
        "2 ** 3",
        "9 ** 9 ** 9",
        "a + 1",
        "1 / 0",
        "'abc'",
        "True + 1",
        "1j + 1",
        "[1, 2]",
        "",
        "   ",
        "1 +",
        "1" * 201,
        "1e308 * 10",
    ],
)
def test_rejects_unsafe_or_bad_input(expression):
    with pytest.raises(CalculatorError):
        calculate(expression)
