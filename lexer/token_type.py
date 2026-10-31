"""Categorías de tokens reconocidas por MiniLang."""

from enum import Enum, auto


class TokenType(Enum):
    """Tipos léxicos de la primera versión de MiniLang."""

    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    TRUE = auto()
    FALSE = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FUNCTION = auto()
    RETURN = auto()
    PRINT = auto()

    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQUAL = auto()
    LESS_EQUAL = auto()
    EQUAL_EQUAL = auto()
    NOT_EQUAL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    ASSIGN = auto()

    SEMICOLON = auto()
    COMMA = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    EOF = auto()