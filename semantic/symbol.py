"""Símbolos registrados durante el análisis semántico."""

from dataclasses import dataclass, field
from enum import Enum

from parser.ast_nodes import SourceSpan

from .types import MiniType


class SymbolKind(Enum):
    """Categorías de nombres declarados."""

    VARIABLE = "variable"
    PARAMETER = "parameter"
    FUNCTION = "function"


@dataclass(frozen=True, slots=True)
class Symbol:
    """Descripción semántica de una variable, parámetro o función."""

    name: str
    type: MiniType
    kind: SymbolKind
    declaration_span: SourceSpan
    parameters: tuple[MiniType, ...] = field(default_factory=tuple)
    return_type: MiniType | None = None