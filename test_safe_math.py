import pytest

from safe_math import CalculationError, evaluate_expression, format_decimal


def test_evaluate_basic_arithmetic():
    assert format_decimal(evaluate_expression("2 + 3 * 4")) == "14"
    assert format_decimal(evaluate_expression("(10 - 4) / 3")) == "2"


def test_rejects_code_execution():
    with pytest.raises(CalculationError):
        evaluate_expression("__import__('os').system('echo bad')")


def test_rejects_huge_power():
    with pytest.raises(CalculationError):
        evaluate_expression("2 ** 999")


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        evaluate_expression("1 / 0")
