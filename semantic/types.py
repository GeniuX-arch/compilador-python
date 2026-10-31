"""Sistema de tipos de MiniLang."""

from enum import Enum


class MiniType(Enum):
    """Tipos estáticos disponibles en MiniLang."""

    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    ERROR = "<error>"

    @classmethod
    def from_name(cls, name: str) -> "MiniType":
        """Convierte un nombre producido por el parser en un tipo MiniLang."""

        try:
            return cls(name)
        except ValueError:
            return cls.ERROR


NUMERIC_TYPES = frozenset({MiniType.INT, MiniType.FLOAT})