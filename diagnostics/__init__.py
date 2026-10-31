"""Diagnósticos compartidos por las fases del compilador."""

from .diagnostic import Diagnostic, DiagnosticCategory, Severity
from .error_reporter import ErrorReporter

__all__ = ["Diagnostic", "DiagnosticCategory", "ErrorReporter", "Severity"]