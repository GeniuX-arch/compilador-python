"""Modelo de diagnósticos de fuente."""

from dataclasses import dataclass
from enum import Enum


class DiagnosticCategory(Enum):
    """Fase que originó el diagnóstico."""

    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    INTERNAL = "internal"


class Severity(Enum):
    """Severidad de un diagnóstico."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Error o advertencia localizado en el código fuente."""

    code: str
    category: DiagnosticCategory
    message: str
    line: int
    column: int
    severity: Severity = Severity.ERROR
    start_position: int | None = None
    end_position: int | None = None
