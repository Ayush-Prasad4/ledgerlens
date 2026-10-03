import ast
import math
import operator

MAX_LENGTH = 200

_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class CalculatorError(ValueError):
    pass


def _eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError("only numbers are allowed")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left = _eval(node.left)
        right = _eval(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise CalculatorError("division by zero")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise CalculatorError(f"not allowed: {type(node).__name__}")


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip():
        raise CalculatorError("empty expression")
    if len(expression) > MAX_LENGTH:
        raise CalculatorError("expression too long")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("invalid expression") from exc
    try:
        result = float(_eval(tree.body))
    except OverflowError as exc:
        raise CalculatorError("number too large") from exc
    if not math.isfinite(result):
        raise CalculatorError("result is not a finite number")
    return result
