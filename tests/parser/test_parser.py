from diagnostics import DiagnosticCategory, ErrorReporter
from lexer import Lexer
from parser.ast_nodes import (
    BinaryExpression,
    ForStatement,
    FunctionCall,
    IfStatement,
    Literal,
    VariableDeclaration,
)
from parser.parser import Parser


def parse(source: str):
    reporter = ErrorReporter()
    tokens = Lexer(source, reporter).tokenize()
    program = Parser(tokens, reporter).parse()
    return program, reporter


def test_variable_declaration_builds_structured_ast() -> None:
    program, reporter = parse("int edad = 21;")

    declaration = program.statements[0]
    assert isinstance(declaration, VariableDeclaration)
    assert declaration.type_name == "int"
    assert declaration.name == "edad"
    assert isinstance(declaration.initializer, Literal)
    assert declaration.initializer.value == 21
    assert not reporter.has_errors


def test_operator_precedence_and_left_associativity() -> None:
    program, reporter = parse("int resultado = 10 + 20 * 2 - 3;")

    expression = program.statements[0].initializer
    assert isinstance(expression, BinaryExpression)
    assert expression.operator == "-"
    assert isinstance(expression.left, BinaryExpression)
    assert expression.left.operator == "+"
    assert isinstance(expression.left.right, BinaryExpression)
    assert expression.left.right.operator == "*"
    assert not reporter.has_errors


def test_parentheses_override_precedence() -> None:
    program, reporter = parse("int resultado = (10 + 20) * 2;")

    expression = program.statements[0].initializer
    assert isinstance(expression, BinaryExpression)
    assert expression.operator == "*"
    assert isinstance(expression.left, BinaryExpression)
    assert expression.left.operator == "+"
    assert not reporter.has_errors


def test_control_flow_function_call_and_nested_block() -> None:
    source = """
    function int doble(int valor) { return valor * 2; }
    if (true && 1 < 2) { print(doble(21)); }
    """
    program, reporter = parse(source)

    assert isinstance(program.statements[1], IfStatement)
    print_statement = program.statements[1].then_branch.statements[0]
    assert isinstance(print_statement.value, FunctionCall)
    assert not reporter.has_errors


def test_for_statement_parses_initializer_condition_update_and_body() -> None:
    program, reporter = parse("for (int i = 0; i < 3; i = i + 1) print(i);")

    statement = program.statements[0]
    assert isinstance(statement, ForStatement)
    assert statement.initializer.name == "i"
    assert statement.condition.operator == "<"
    assert statement.update.name == "i"
    assert not reporter.has_errors


def test_syntax_error_is_reported_and_parser_recovers() -> None:
    program, reporter = parse("int invalida = 10 + ; int correcta = 2;")

    assert reporter.has_errors
    assert reporter.diagnostics[0].category is DiagnosticCategory.SYNTAX
    assert reporter.diagnostics[0].code == "SYN003"
    assert len(program.statements) == 1
    assert program.statements[0].name == "correcta"


def test_missing_delimiter_reports_syntax_error() -> None:
    _, reporter = parse("int edad = 21")

    assert reporter.diagnostics[0].code == "SYN002"