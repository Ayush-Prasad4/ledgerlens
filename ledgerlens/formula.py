import re

from ledgerlens.calculator import CalculatorError, calculate

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def evaluate_formula(expression, facts):
    """Replace fact names in the expression with their verified values, then calculate.

    Returns (numeric_expression, result). Raises CalculatorError on any problem.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise CalculatorError("empty expression")
    values = {f["name"]: f["value"] for f in facts}
    unknown = sorted({n for n in _IDENT.findall(expression) if n not in values})
    if unknown:
        raise CalculatorError(f"unknown names: {unknown}")
    numeric = _IDENT.sub(lambda m: f"({values[m.group(0)]!r})", expression)
    return numeric, calculate(numeric)
