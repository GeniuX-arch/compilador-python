"""Representación intermedia de tres direcciones para MiniLang."""

from .generator import IRGenerator
from .instructions import IRProgram
from .temporary import TemporaryFactory

__all__ = ["IRGenerator", "IRProgram", "TemporaryFactory"]