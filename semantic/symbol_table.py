"""Tabla de símbolos y operaciones de ámbito."""

from collections.abc import Iterator
from contextlib import contextmanager

from .scope import Scope
from .symbol import Symbol


class SymbolTable:
    """Administra el ámbito actual y sus ámbitos léxicos anidados."""

    def __init__(self) -> None:
        self.global_scope = Scope()
        self.current_scope = self.global_scope

    def declare(self, symbol: Symbol) -> bool:
        return self.current_scope.declare(symbol)

    def resolve(self, name: str) -> Symbol | None:
        return self.current_scope.resolve(name)

    def enter_scope(self) -> None:
        self.current_scope = Scope(self.current_scope)

    def exit_scope(self) -> None:
        if self.current_scope.parent is None:
            raise RuntimeError("No se puede salir del ámbito global.")
        self.current_scope = self.current_scope.parent

    @contextmanager
    def scope(self) -> Iterator[None]:
        self.enter_scope()
        try:
            yield
        finally:
            self.exit_scope()