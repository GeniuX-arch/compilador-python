"""Excepciones reservadas para fallos no recuperables del compilador."""


class CompilerError(Exception):
    """Error interno o fallo no recuperable de una fase del compilador."""

    def __init__(self, message: str, code: str = "INT001") -> None:
        super().__init__(message)
        self.code = code
        self.message = message