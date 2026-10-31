"""Máquina virtual segura para la representación intermedia de MiniLang."""

import operator as operator_module
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from ir.instructions import (
    Assign,
    BinaryOp,
    Call,
    ConditionalJump,
    FunctionBegin,
    FunctionEnd,
    IRProgram,
    Jump,
    Label,
    Operand,
    Print,
    Return,
    UnaryOp,
)


class VirtualMachineError(RuntimeError):
    """Error de ejecución de una instrucción IR válida pero no ejecutable."""


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Resultado observable de una ejecución de MiniLang."""

    outputs: tuple[object, ...]
    return_value: object | None


@dataclass(slots=True)
class _FunctionInfo:
    begin: int
    end: int
    parameters: tuple[str, ...]


@dataclass(slots=True)
class _Frame:
    variables: dict[str, object]
    return_pc: int | None = None
    return_target: str | None = None


@dataclass(slots=True)
class _ExecutionState:
    labels: dict[str, int]
    functions: dict[str, _FunctionInfo]
    frames: list[_Frame]
    outputs: list[object]
    pc: int = 0
    return_value: object | None = None


class VirtualMachine:
    """Ejecuta TAC con operaciones explícitas, sin evaluar código fuente."""

    def __init__(self, output_sink: Callable[[object], None] | None = None) -> None:
        self.output_sink = output_sink

    def execute(self, program: IRProgram) -> ExecutionResult:
        """Ejecuta un programa IR y captura los valores enviados a ``print``."""

        labels = self._index_labels(program)
        functions = self._index_functions(program)
        state = _ExecutionState(labels, functions, [_Frame({})], [])
        handlers = {
            FunctionBegin: self._step_function_begin,
            FunctionEnd: self._step_function_end,
            Assign: self._step_assign,
            BinaryOp: self._step_binary,
            UnaryOp: self._step_unary,
            Label: self._step_label,
            Jump: self._step_jump,
            ConditionalJump: self._step_conditional_jump,
            Call: self._step_call,
            Return: self._step_return,
            Print: self._step_print,
        }
        while state.pc < len(program.instructions):
            instruction = program.instructions[state.pc]
            handler = cast(
                Callable[[object, _ExecutionState], int], handlers.get(type(instruction))
            )
            if handler is None:
                raise VirtualMachineError(f"Instrucción IR no soportada: {instruction!r}.")
            state.pc = handler(instruction, state)
        return ExecutionResult(tuple(state.outputs), state.return_value)

    @staticmethod
    def _step_function_begin(instruction: object, state: _ExecutionState) -> int:
        function = cast(FunctionBegin, instruction)
        if len(state.frames) == 1:
            return state.functions[function.name].end + 1
        return state.pc + 1

    @staticmethod
    def _step_function_end(instruction: object, state: _ExecutionState) -> int:
        if len(state.frames) == 1:
            return state.pc + 1
        state.pc, state.return_value = VirtualMachine._finish_frame(state.frames, None)
        return state.pc

    @staticmethod
    def _step_assign(instruction: object, state: _ExecutionState) -> int:
        assign = cast(Assign, instruction)
        value = VirtualMachine._resolve(assign.value, state.frames)
        VirtualMachine._store(state.frames, assign.target, value)
        return state.pc + 1

    @staticmethod
    def _step_binary(instruction: object, state: _ExecutionState) -> int:
        binary = cast(BinaryOp, instruction)
        left = VirtualMachine._resolve(binary.left, state.frames)
        right = VirtualMachine._resolve(binary.right, state.frames)
        value = VirtualMachine._binary(binary.operator, left, right)
        VirtualMachine._store(state.frames, binary.target, value)
        return state.pc + 1

    @staticmethod
    def _step_unary(instruction: object, state: _ExecutionState) -> int:
        unary = cast(UnaryOp, instruction)
        operand = VirtualMachine._resolve(unary.operand, state.frames)
        VirtualMachine._store(
            state.frames, unary.target, VirtualMachine._unary(unary.operator, operand)
        )
        return state.pc + 1

    @staticmethod
    def _step_label(instruction: object, state: _ExecutionState) -> int:
        return state.pc + 1

    @staticmethod
    def _step_jump(instruction: object, state: _ExecutionState) -> int:
        jump = cast(Jump, instruction)
        return VirtualMachine._label_pc(state.labels, jump.target)

    @staticmethod
    def _step_conditional_jump(instruction: object, state: _ExecutionState) -> int:
        jump = cast(ConditionalJump, instruction)
        condition = VirtualMachine._resolve(jump.condition, state.frames)
        target = jump.true_target if bool(condition) else jump.false_target
        return VirtualMachine._label_pc(state.labels, target)

    @staticmethod
    def _step_call(instruction: object, state: _ExecutionState) -> int:
        call = cast(Call, instruction)
        function = state.functions.get(call.function_name)
        if function is None:
            raise VirtualMachineError(f"Función IR no encontrada: {call.function_name}.")
        arguments = [VirtualMachine._resolve(argument, state.frames) for argument in call.arguments]
        if len(arguments) != len(function.parameters):
            raise VirtualMachineError(
                f"Cantidad de argumentos inválida para {call.function_name}."
            )
        state.frames.append(
            _Frame(
                dict(zip(function.parameters, arguments)),
                return_pc=state.pc + 1,
                return_target=call.target,
            )
        )
        return function.begin + 1

    @staticmethod
    def _step_return(instruction: object, state: _ExecutionState) -> int:
        if len(state.frames) == 1:
            raise VirtualMachineError("return fuera de una función.")
        return_instruction = cast(Return, instruction)
        value = VirtualMachine._resolve(return_instruction.value, state.frames)
        state.pc, state.return_value = VirtualMachine._finish_frame(state.frames, value)
        return state.pc

    def _step_print(self, instruction: object, state: _ExecutionState) -> int:
        print_instruction = cast(Print, instruction)
        value = self._resolve(print_instruction.value, state.frames)
        state.outputs.append(value)
        if self.output_sink is not None:
            self.output_sink(value)
        return state.pc + 1

    @staticmethod
    def _index_labels(program: IRProgram) -> dict[str, int]:
        return {
            instruction.name: index
            for index, instruction in enumerate(program.instructions)
            if isinstance(instruction, Label)
        }

    @staticmethod
    def _index_functions(program: IRProgram) -> dict[str, _FunctionInfo]:
        functions: dict[str, _FunctionInfo] = {}
        active: tuple[str, int, tuple[str, ...]] | None = None
        for index, instruction in enumerate(program.instructions):
            if isinstance(instruction, FunctionBegin):
                if active is not None or instruction.name in functions:
                    raise VirtualMachineError("Región de función IR duplicada o anidada.")
                active = (instruction.name, index, instruction.parameters)
            elif isinstance(instruction, FunctionEnd):
                if active is None or active[0] != instruction.name:
                    raise VirtualMachineError("Cierre de función IR sin apertura correspondiente.")
                name, begin, parameters = active
                functions[name] = _FunctionInfo(begin, index, parameters)
                active = None
        if active is not None:
            raise VirtualMachineError("Función IR sin cierre.")
        return functions

    @staticmethod
    def _label_pc(labels: dict[str, int], name: str) -> int:
        try:
            return labels[name]
        except KeyError as error:
            raise VirtualMachineError(f"Etiqueta IR no encontrada: {name}.") from error

    @staticmethod
    def _resolve(value: Operand, frames: list[_Frame]) -> object:
        if isinstance(value, str):
            if value.startswith("__string__:"):
                return value.removeprefix("__string__:")
            for frame in reversed(frames):
                if value in frame.variables:
                    return frame.variables[value]
            return value
        return value

    @staticmethod
    def _store(frames: list[_Frame], name: str, value: object) -> None:
        current = frames[-1].variables
        if name in current or len(frames) == 1:
            current[name] = value
            return
        global_variables = frames[0].variables
        if name in global_variables:
            global_variables[name] = value
            return
        current[name] = value

    @staticmethod
    def _unary(operator: str, operand: object) -> object:
        if operator == "!":
            return not bool(operand)
        if operator in {"+", "-"}:
            number = VirtualMachine._numeric(operand)
            return +number if operator == "+" else -number
        raise VirtualMachineError(f"Operador unario no soportado: {operator}.")

    @staticmethod
    def _binary(operator: str, left: object, right: object) -> object:
        if operator == "/":
            return VirtualMachine._divide(left, right)
        if operator == "&&":
            return bool(left) and bool(right)
        if operator == "||":
            return bool(left) or bool(right)
        operations = {
            "+": operator_module.add,
            "-": operator_module.sub,
            "*": operator_module.mul,
            "%": operator_module.mod,
            ">": operator_module.gt,
            "<": operator_module.lt,
            ">=": operator_module.ge,
            "<=": operator_module.le,
            "==": operator_module.eq,
            "!=": operator_module.ne,
        }
        operation = operations.get(operator)
        if operation is None:
            raise VirtualMachineError(f"Operador binario no soportado: {operator}.")
        try:
            return operation(cast(Any, left), cast(Any, right))
        except TypeError as error:
            raise VirtualMachineError(f"Operandos incompatibles para '{operator}'.") from error

    @staticmethod
    def _numeric(value: object) -> int | float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise VirtualMachineError("Se esperaba un operando numérico.")
        return value

    @staticmethod
    def _divide(left: object, right: object) -> int | float:
        left_number = VirtualMachine._numeric(left)
        right_number = VirtualMachine._numeric(right)
        if right_number == 0:
            raise VirtualMachineError("División por cero.")
        if isinstance(left_number, float) or isinstance(right_number, float):
            return left_number / right_number
        return int(left_number / right_number)

    @staticmethod
    def _finish_frame(frames: list[_Frame], value: object | None) -> tuple[int, object | None]:
        frame = frames.pop()
        caller = frames[-1]
        if frame.return_target is not None:
            caller.variables[frame.return_target] = value
        return frame.return_pc or 0, value