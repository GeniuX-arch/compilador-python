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

    def format(self, source: str | None = None, source_name: str = "<source>") -> str:
        """Renderiza el diagnóstico con ubicación y fragmento opcional."""

        severity = self.severity.value.upper()
        category = self.category.value.upper()
        lines = [
            f"{severity} {category} [{self.code}]",
            f"Archivo: {source_name}",
            f"Línea: {self.line}",
            f"Columna: {self.column}",
            self.message,
        ]
        excerpt = self._excerpt(source)
        if excerpt is not None:
            text, marker = excerpt
            lines.extend([text, marker])
        return "\n".join(lines)

    def _excerpt(self, source: str | None) -> tuple[str, str] | None:
        if source is None or self.line < 1:
            return None
        source_lines = source.splitlines()
        if self.line > len(source_lines):
            return None
        text = source_lines[self.line - 1]
        start = max(self.column - 1, 0)
        width = 1
        if self.start_position is not None and self.end_position is not None:
            width = max(self.end_position - self.start_position, 1)
        return text, f"{' ' * start}{'^' * width}"
