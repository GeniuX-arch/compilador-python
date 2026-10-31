"""Backends objetivo de MiniLang."""

from .vm import ExecutionResult, VirtualMachine, VirtualMachineError

__all__ = ["ExecutionResult", "VirtualMachine", "VirtualMachineError"]