from diagnostics import ErrorReporter
from ir import IRGenerator
from lexer import Lexer
from parser.parser import Parser
from semantic import SemanticAnalyzer
from target import ExecutionResult, VirtualMachine


def compile_to_ir(source: str):
    reporter = ErrorReporter()
    tokens = Lexer(source, reporter).tokenize()
    program = Parser(tokens, reporter).parse()
    SemanticAnalyzer(reporter).analyze(program)
    assert not reporter.has_errors
    return IRGenerator(reporter).generate(program)


def test_vm_executes_arithmetic_and_print() -> None:
    result = VirtualMachine().execute(compile_to_ir("int total = 10 + 2 * 3; print(total);"))

    assert result == ExecutionResult((16,), None)


def test_vm_executes_conditionals_and_loops() -> None:
    result = VirtualMachine().execute(
        compile_to_ir(
            "int i = 0; while (i < 3) i = i + 1; "
            "if (i == 3) print(\"ok\"); else print(\"error\");"
        )
    )

    assert result.outputs == ("ok",)


def test_vm_executes_function_calls_and_returns() -> None:
    result = VirtualMachine().execute(
        compile_to_ir(
            "function int doble(int valor) { return valor * 2; } "
            "int resultado = doble(21); print(resultado);"
        )
    )

    assert result.outputs == (42,)


def test_vm_preserves_short_circuit() -> None:
    result = VirtualMachine().execute(
        compile_to_ir("bool resultado = false && 1 / 0 > 0; print(resultado);")
    )

    assert result.outputs == (False,)


def test_vm_reports_division_by_zero() -> None:
    import pytest

    from target import VirtualMachineError

    ir = compile_to_ir("print(1 / 0);")
    virtual_machine = VirtualMachine()
    with pytest.raises(VirtualMachineError, match="División por cero"):
        virtual_machine.execute(ir)