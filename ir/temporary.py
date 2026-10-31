"""Generación determinista de temporales y etiquetas."""


class TemporaryFactory:
    """Produce nombres únicos dentro de una generación de IR."""

    def __init__(self) -> None:
        self._temporary_count = 0
        self._label_count = 0

    def temporary(self) -> str:
        self._temporary_count += 1
        return f"t{self._temporary_count}"

    def label(self) -> str:
        self._label_count += 1
        return f"L{self._label_count}"