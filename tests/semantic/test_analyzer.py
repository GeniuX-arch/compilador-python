from diagnostics import ErrorReporter
from lexer import Lexer
from parser.parser import Parser
from semantic import MiniType, SemanticAnalyzer


def analyze(source: str):
    reporter = ErrorReporter()
    tokens = Lexer(source, reporter).tokenize()
    program = Parser(tokens, reporter).parse()
    SemanticAnalyzer(reporter).analyze(program)
    return reporter


def semantic_codes(source: str) -> list[str]:
    return [diagnostic.code for diagnostic in analyze(source).diagnostics]


def test_valid_program_with_numeric_promotion_and_function_call() -> None:
    reporter = analyze(
        """
        function float mitad(float valor) { return valor / 2.0; }
        int edad = 21;
        float resultado = mitad(edad);
        if (edad > 18 && resultado > 0.0) { print(resultado); }
        """
    )

    assert not reporter.has_errors


def test_undeclared_name_is_reported() -> None:
    assert "SEM001" in semantic_codes("int resultado = desconocida + 10;")


def test_duplicate_declaration_is_reported() -> None:
    assert "SEM002" in semantic_codes("int edad = 21; int edad = 30;")


def test_incompatible_assignment_and_operation_are_reported() -> None:
    codes = semantic_codes('int edad = "Carlos"; int suma = 10 + "Hola";')

    assert codes.count("SEM003") == 2


def test_condition_must_be_boolean() -> None:
    assert "SEM004" in semantic_codes('if (10) { print("Hola"); }')


def test_block_scope_hides_variable_after_block() -> None:
    codes = semantic_codes("{ int interna = 1; } print(interna);")

    assert "SEM001" in codes


def test_shadowing_is_allowed_in_nested_scope() -> None:
    reporter = analyze("int valor = 1; { string valor = \"texto\"; print(valor); }")

    assert not reporter.has_errors


def test_function_signature_and_return_are_checked() -> None:
    codes = semantic_codes(
        "function int suma(int a, int b) { return a + b; } "
        "int resultado = suma(1);"
    )

    assert "SEM005" in codes


def test_return_outside_function_is_reported() -> None:
    assert "SEM006" in semantic_codes("return 1;")


def test_type_system_maps_ast_names() -> None:
    assert MiniType.from_name("float") is MiniType.FLOAT
    assert MiniType.from_name("unknown") is MiniType.ERROR
