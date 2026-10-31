"""Token producido por el lexer de MiniLang."""

from dataclasses import dataclass

from .token_type import TokenType


@dataclass(frozen=True, slots=True)
class Token:
    """Unidad léxica con valor y posición dentro del texto fuente.

    Las posiciones son offsets de Python y ``end_position`` es exclusivo.
    ``line`` y ``column`` empiezan en uno.
    """

    type: TokenType
    value: str
    line: int
    column: int
    start_position: int
    end_position: int