from diagnostics import DiagnosticCategory, ErrorReporter
from lexer import Lexer, TokenType


def lex(source: str):
    reporter = ErrorReporter()
    tokens = Lexer(source, reporter).tokenize()
    return tokens, reporter


def test_keywords_identifiers_and_literals() -> None:
    tokens, reporter = lex('int edad = 21; float altura = 1.88; bool activo = true;')

    assert [token.type for token in tokens] == [
        TokenType.INT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INTEGER_LITERAL,
        TokenType.SEMICOLON,
        TokenType.FLOAT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.FLOAT_LITERAL,
        TokenType.SEMICOLON,
        TokenType.BOOL,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.TRUE,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert tokens[1].value == "edad"
    assert tokens[8].value == "1.88"
    assert not reporter.has_errors


def test_string_escapes_are_decoded_in_token_value() -> None:
    tokens, reporter = lex(r'string texto = "hola\n\"mundo";')

    assert tokens[3].type is TokenType.STRING_LITERAL
    assert tokens[3].value == 'hola\n"mundo'
    assert not reporter.has_errors


def test_operators_use_maximal_munch() -> None:
    tokens, reporter = lex("== != >= <= && || = ! > <")

    assert [token.type for token in tokens[:-1]] == [
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.GREATER_EQUAL,
        TokenType.LESS_EQUAL,
        TokenType.AND,
        TokenType.OR,
        TokenType.ASSIGN,
        TokenType.NOT,
        TokenType.GREATER,
        TokenType.LESS,
    ]
    assert not reporter.has_errors


def test_comments_are_ignored_and_positions_continue() -> None:
    tokens, reporter = lex("// comentario\n/* bloque\n */ int valor = 2;")

    assert tokens[0].type is TokenType.INT
    assert tokens[0].line == 3
    assert tokens[0].column == 5
    assert not reporter.has_errors


def test_token_positions_use_one_based_line_column_and_exclusive_end() -> None:
    tokens, reporter = lex("int x")

    assert tokens[0].start_position == 0
    assert tokens[0].end_position == 3
    assert tokens[1].line == 1
    assert tokens[1].column == 5
    assert tokens[-1].start_position == 5
    assert not reporter.has_errors


def test_invalid_character_is_reported_and_lexer_recovers() -> None:
    tokens, reporter = lex("int edad = 10 @;")

    assert tokens[-2].type is TokenType.SEMICOLON
    assert reporter.diagnostics[0].code == "LEX001"
    assert reporter.diagnostics[0].category is DiagnosticCategory.LEXICAL
    assert reporter.diagnostics[0].line == 1
    assert reporter.diagnostics[0].column == 15


def test_unclosed_string_is_reported() -> None:
    tokens, reporter = lex('string nombre = "Carlos;')

    assert tokens[-2].type is TokenType.STRING_LITERAL
    assert reporter.diagnostics[0].code == "LEX002"


def test_unclosed_block_comment_is_reported() -> None:
    tokens, reporter = lex("/* comentario")

    assert tokens[-1].type is TokenType.EOF
    assert reporter.diagnostics[0].code == "LEX003"


def test_invalid_numeric_literals_are_reported() -> None:
    tokens, reporter = lex("float a = 1.; int b = 12abc;")

    assert tokens[-1].type is TokenType.EOF
    assert [diagnostic.code for diagnostic in reporter.diagnostics] == ["LEX004", "LEX004"]