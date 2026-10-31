"""Reglas de compatibilidad e inferencia de tipos."""

from .types import NUMERIC_TYPES, MiniType


class TypeChecker:
    """Aplica las reglas de tipos de MiniLang sin emitir diagnósticos."""

    @staticmethod
    def is_assignable(target: MiniType, value: MiniType) -> bool:
        return target is MiniType.ERROR or value is MiniType.ERROR or (
            target is value or (target is MiniType.FLOAT and value is MiniType.INT)
        )

    @staticmethod
    def unary_result(operator: str, operand: MiniType) -> MiniType:
        if operand is MiniType.ERROR:
            return MiniType.ERROR
        if operator == "!" and operand is MiniType.BOOL:
            return MiniType.BOOL
        if operator in {"+", "-"} and operand in NUMERIC_TYPES:
            return operand
        return MiniType.ERROR

    @staticmethod
    def binary_result(operator: str, left: MiniType, right: MiniType) -> MiniType:
        if MiniType.ERROR in {left, right}:
            return MiniType.ERROR
        if operator in {"+", "-", "*", "/", "%"}:
            return TypeChecker._arithmetic_result(operator, left, right)
        if operator in {"<", ">", "<=", ">="}:
            return TypeChecker._comparison_result(left, right)
        if operator in {"==", "!="}:
            return TypeChecker._equality_result(left, right)
        if operator in {"&&", "||"} and left is MiniType.BOOL and right is MiniType.BOOL:
            return MiniType.BOOL
        return MiniType.ERROR

    @staticmethod
    def _arithmetic_result(operator: str, left: MiniType, right: MiniType) -> MiniType:
        if operator == "+" and left is MiniType.STRING and right is MiniType.STRING:
            return MiniType.STRING
        if left is MiniType.INT and right is MiniType.INT:
            return MiniType.INT
        if operator != "%" and left in NUMERIC_TYPES and right in NUMERIC_TYPES:
            return MiniType.FLOAT
        return MiniType.ERROR

    @staticmethod
    def _comparison_result(left: MiniType, right: MiniType) -> MiniType:
        if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
            return MiniType.BOOL
        return MiniType.ERROR

    @staticmethod
    def _equality_result(left: MiniType, right: MiniType) -> MiniType:
        if left is right or {left, right} == {MiniType.INT, MiniType.FLOAT}:
            return MiniType.BOOL
        return MiniType.ERROR