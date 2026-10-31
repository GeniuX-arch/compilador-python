import pytest

from diagnostics import ErrorReporter
from diagnostics.compiler_error import CompilerError
from ir import IRGenerator
from lexer import Lexer
from parser.parser import Parser


def generate(source: str):
    reporter = ErrorReporter()
    tokens = Lexer(source, reporter).tokenize()
    program = Parser(tokens, reporter).parse()
    ir = IRGenerator(reporter).generate(program)
    return ir, reporter


def test_arithmetic_expression_generates_three_address_code() -> None:
    ir, reporter = generate("int resultado = 10 + 20 * 2;")

    assert not reporter.has_errors
    assert ir.render().splitlines() == [
        "t1 = 20 * 2",
        "t2 = 10 + t1",
        "resultado = t2",
    ]


def test_assignment_and_print_generate_instructions() -> None:
    ir, reporter = generate('string mensaje = "hola"; mensaje = "adios"; print(mensaje);')

    assert not reporter.has_errors
    assert ir.render().splitlines() == [
        'mensaje = "hola"',
        'mensaje = "adios"',
        "print mensaje",
    ]


def test_if_generates_labels_and_jumps() -> None:
    ir, reporter = generate("if (true) { print(1); } else { print(2); }")

    assert not reporter.has_errors
    assert ir.render().splitlines() == [
        "if true goto L1; goto L2",
        "L1:",
        "print 1",
        "goto L3",
        "L2:",
        "print 2",
        "L3:",
    ]


def test_while_and_for_generate_back_edges() -> None:
    ir, reporter = generate(
        "int i = 0; while (i < 2) i = i + 1; "
        "for (int j = 0; j < 2; j = j + 1) print(j);"
    )

    assert not reporter.has_errors
    output = ir.render()
    assert "goto L1" in output
    assert "goto L4" in output
    assert "i = t" in output
    assert "j = t" in output


def test_function_call_and_return_generate_function_region() -> None:
    ir, reporter = generate(
        "function int doble(int valor) { return valor * 2; } "
        "int resultado = doble(21);"
    )

    assert not reporter.has_errors
    assert ir.render().splitlines() == [
        "function doble(valor)",
        "t1 = valor * 2",
        "return t1",
        "end function doble",
        "t2 = call doble(21)",
        "resultado = t2",
    ]


def test_logical_operators_preserve_short_circuit_with_jumps() -> None:
    ir, reporter = generate("bool resultado = false && 1 < 2;")

    assert not reporter.has_errors
    assert "if false goto L1; goto L2" in ir.render()
    assert "L1:" in ir.render()


def test_ir_generation_is_blocked_when_previous_phase_has_errors() -> None:
    reporter = ErrorReporter()
    tokens = Lexer("int valor = \"texto\";", reporter).tokenize()
    program = Parser(tokens, reporter).parse()

    from semantic import SemanticAnalyzer

    SemanticAnalyzer(reporter).analyze(program)
    generator = IRGenerator(reporter)
    with pytest.raises(CompilerError, match="No se puede generar IR"):
        generator.generate(program)