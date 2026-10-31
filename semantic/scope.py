"""Ámbitos léxicos encadenados."""

from .symbol import Symbol


class Scope:
    """Un ámbito con búsqueda local y acceso a su padre."""

    def __init__(self, parent: "Scope | None" = None) -> None:
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> bool:
        """Declara un símbolo si el nombre aún no existe localmente."""

        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def resolve(self, name: str) -> Symbol | None:
        """Busca un nombre desde este ámbito hacia sus padres."""

        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        return self.parent.resolve(name) if self.parent is not None else None