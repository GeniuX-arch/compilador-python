"""Excepciones reservadas para fallos no recuperables del compilador."""


class CompilerError(Exception):
    """Error interno o fallo no recuperable de una fase del compilador."""