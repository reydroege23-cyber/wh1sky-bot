"""Safe arithmetic evaluator for the Telegram /calc command."""

from __future__ import annotations

import ast
import operator
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext


getcontext().prec = 28

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

MAX_EXPRESSION_LENGTH = 120
MAX_ABSOLUTE_RESULT = Decimal("1e18")
MAX_POWER_EXPONENT = Decimal("10")


class CalculationError(ValueError):
    """Raised when a user-supplied calculation is invalid or unsafe."""


def evaluate_expression(expression: str) -> Decimal:
    """Evaluate a simple arithmetic expression without executing code."""
    expression = expression.strip()
    if not expression:
        raise CalculationError("empty expression")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationError("expression too long")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate_node(tree.body)
    except (SyntaxError, InvalidOperation) as exc:
        raise CalculationError("invalid expression") from exc
    except DivisionByZero:
        raise ZeroDivisionError from None

    if abs(result) > MAX_ABSOLUTE_RESULT:
        raise CalculationError("result too large")
    return result


def format_decimal(value: Decimal) -> str:
    """Format Decimal output neatly for chat."""
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f").rstrip("0").rstrip(".")


def _evaluate_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculationError("unsupported value")
        return Decimal(str(node.value))

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER_EXPONENT:
            raise CalculationError("power too large")
        result = _BINARY_OPERATORS[type(node.op)](left, right)
        if abs(result) > MAX_ABSOLUTE_RESULT:
            raise CalculationError("result too large")
        return result

    raise CalculationError("unsupported expression")
