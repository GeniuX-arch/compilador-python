from diagnostics import DiagnosticCategory, ErrorReporter, Severity
from diagnostics.compiler_error import CompilerError


def test_diagnostic_format_includes_source_excerpt_and_caret() -> None:
    source = "int edad = 10 @;"
    reporter = ErrorReporter()
    reporter.report(
        "LEX001",
        DiagnosticCategory.LEXICAL,
        "Carácter no reconocido: '@'",
        1,
        15,
        start_position=14,
        end_position=15,
    )

    output = reporter.format_diagnostics(source, "example.ml")

    assert "ERROR LEXICAL [LEX001]" in output
    assert "Archivo: example.ml" in output
    assert "Línea: 1" in output
    assert "int edad = 10 @;" in output
    assert "              ^" in output


def test_reporter_counts_errors_and_warnings() -> None:
    reporter = ErrorReporter()
    reporter.report("SEM001", DiagnosticCategory.SEMANTIC, "Nombre desconocido.", 2, 1)
    reporter.report(
        "SEM-WARN",
        DiagnosticCategory.SEMANTIC,
        "Advertencia.",
        2,
        1,
        severity=Severity.WARNING,
    )

    assert reporter.has_errors
    assert reporter.error_count == 1
    assert reporter.warning_count == 1


def test_reporter_can_accumulate_diagnostics_from_multiple_phases() -> None:
    reporter = ErrorReporter()
    reporter.report("LEX001", DiagnosticCategory.LEXICAL, "Error léxico.", 1, 1)
    reporter.report("SYN002", DiagnosticCategory.SYNTAX, "Error sintáctico.", 1, 2)
    reporter.report("SEM003", DiagnosticCategory.SEMANTIC, "Error semántico.", 1, 3)

    output = reporter.format_diagnostics()

    assert [item.code for item in reporter.diagnostics] == ["LEX001", "SYN002", "SEM003"]
    assert output.count("ERROR") == 3


def test_compiler_error_preserves_internal_code_and_message() -> None:
    error = CompilerError("Estado imposible.", code="INT001")

    assert error.code == "INT001"
    assert error.message == "Estado imposible."
    assert str(error) == "Estado imposible."