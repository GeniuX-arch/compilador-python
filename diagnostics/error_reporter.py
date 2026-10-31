"""Acumulador centralizado de diagnósticos."""

from collections.abc import Iterator

from .diagnostic import Diagnostic, DiagnosticCategory, Severity


class ErrorReporter:
    """Recopila diagnósticos sin mezclar su almacenamiento con el lexer."""

    def __init__(self) -> None:
        self._diagnostics: list[Diagnostic] = []

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        """Devuelve los diagnósticos en el orden en que fueron generados."""

        return tuple(self._diagnostics)

    @property
    def has_errors(self) -> bool:
        """Indica si existe al menos un error."""

        return any(item.severity is Severity.ERROR for item in self._diagnostics)

    @property
    def error_count(self) -> int:
        """Cantidad de diagnósticos con severidad de error."""

        return sum(item.severity is Severity.ERROR for item in self._diagnostics)

    @property
    def warning_count(self) -> int:
        """Cantidad de diagnósticos con severidad de advertencia."""

        return sum(item.severity is Severity.WARNING for item in self._diagnostics)

    def report(
        self,
        code: str,
        category: DiagnosticCategory,
        message: str,
        line: int,
        column: int,
        *,
        start_position: int | None = None,
        end_position: int | None = None,
        severity: Severity = Severity.ERROR,
    ) -> None:
        """Añade un diagnóstico con su ubicación de origen."""

        self._diagnostics.append(
            Diagnostic(
                code=code,
                category=category,
                message=message,
                line=line,
                column=column,
                severity=severity,
                start_position=start_position,
                end_position=end_position,
            )
        )

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._diagnostics)

    def format_diagnostics(self, source: str | None = None, source_name: str = "<source>") -> str:
        """Formatea todos los diagnósticos en su orden de emisión."""

        return "\n\n".join(
            diagnostic.format(source, source_name) for diagnostic in self._diagnostics
        )