"""Instrucciones y programa de la IR de MiniLang."""

from dataclasses import dataclass

type Operand = str | int | float | bool


def format_operand(value: Operand) -> str:
    """Convierte un operando a su representación textual TAC."""

    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if value.startswith("__string__:"):
            return f'"{value.removeprefix("__string__:")}"'
        return value
    return str(value)


class Instruction:
    """Tipo base nominal para instrucciones de IR."""

    def render(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Assign(Instruction):
    target: str
    value: Operand

    def render(self) -> str:
        return f"{self.target} = {format_operand(self.value)}"


@dataclass(frozen=True, slots=True)
class BinaryOp(Instruction):
    target: str
    left: Operand
    operator: str
    right: Operand

    def render(self) -> str:
        return (
            f"{self.target} = {format_operand(self.left)} "
            f"{self.operator} {format_operand(self.right)}"
        )


@dataclass(frozen=True, slots=True)
class UnaryOp(Instruction):
    target: str
    operator: str
    operand: Operand

    def render(self) -> str:
        return f"{self.target} = {self.operator}{format_operand(self.operand)}"


@dataclass(frozen=True, slots=True)
class Label(Instruction):
    name: str

    def render(self) -> str:
        return f"{self.name}:"


@dataclass(frozen=True, slots=True)
class Jump(Instruction):
    target: str

    def render(self) -> str:
        return f"goto {self.target}"


@dataclass(frozen=True, slots=True)
class ConditionalJump(Instruction):
    condition: Operand
    true_target: str
    false_target: str

    def render(self) -> str:
        return (
            f"if {format_operand(self.condition)} goto {self.true_target}; "
            f"goto {self.false_target}"
        )


@dataclass(frozen=True, slots=True)
class FunctionBegin(Instruction):
    name: str
    parameters: tuple[str, ...]

    def render(self) -> str:
        parameters = ", ".join(self.parameters)
        return f"function {self.name}({parameters})"


@dataclass(frozen=True, slots=True)
class FunctionEnd(Instruction):
    name: str

    def render(self) -> str:
        return f"end function {self.name}"


@dataclass(frozen=True, slots=True)
class Call(Instruction):
    target: str
    function_name: str
    arguments: tuple[Operand, ...]

    def render(self) -> str:
        arguments = ", ".join(format_operand(argument) for argument in self.arguments)
        return f"{self.target} = call {self.function_name}({arguments})"


@dataclass(frozen=True, slots=True)
class Return(Instruction):
    value: Operand

    def render(self) -> str:
        return f"return {format_operand(self.value)}"


@dataclass(frozen=True, slots=True)
class Print(Instruction):
    value: Operand

    def render(self) -> str:
        return f"print {format_operand(self.value)}"


@dataclass(frozen=True, slots=True)
class IRProgram:
    """Secuencia ordenada de instrucciones intermedias."""

    instructions: tuple[Instruction, ...]

    def render(self) -> str:
        """Renderiza una instrucción por línea."""

        return "\n".join(instruction.render() for instruction in self.instructions)