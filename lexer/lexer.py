"""Lexer manual para MiniLang.

El recorrido es lineal y aplica maximal munch para operadores y literales.
"""

from diagnostics import DiagnosticCategory, ErrorReporter

from .token import Token
from .token_type import TokenType


class Lexer:
    """Convierte texto MiniLang en tokens y acumula errores recuperables."""

    _KEYWORDS = {
        "int": TokenType.INT,
        "float": TokenType.FLOAT,
        "string": TokenType.STRING,
        "bool": TokenType.BOOL,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "while": TokenType.WHILE,
        "for": TokenType.FOR,
        "function": TokenType.FUNCTION,
        "return": TokenType.RETURN,
        "print": TokenType.PRINT,
    }
    _TWO_CHARACTER_TOKENS = {
        "==": TokenType.EQUAL_EQUAL,
        "!=": TokenType.NOT_EQUAL,
        ">=": TokenType.GREATER_EQUAL,
        "<=": TokenType.LESS_EQUAL,
        "&&": TokenType.AND,
        "||": TokenType.OR,
    }
    _ONE_CHARACTER_TOKENS = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.MULTIPLY,
        "/": TokenType.DIVIDE,
        "%": TokenType.MODULO,
        ">": TokenType.GREATER,
        "<": TokenType.LESS,
        "!": TokenType.NOT,
        "=": TokenType.ASSIGN,
        ";": TokenType.SEMICOLON,
        ",": TokenType.COMMA,
        "(": TokenType.LEFT_PAREN,
        ")": TokenType.RIGHT_PAREN,
        "{": TokenType.LEFT_BRACE,
        "}": TokenType.RIGHT_BRACE,
    }

    def __init__(self, source: str, reporter: ErrorReporter | None = None) -> None:
        self.source = source
        self.reporter = reporter or ErrorReporter()
        self._position = 0
        self._line = 1
        self._column = 1

    def tokenize(self) -> list[Token]:
        """Tokeniza toda la fuente y siempre termina con ``EOF``."""

        tokens: list[Token] = []
        while not self._at_end:
            if self._skip_whitespace_and_comments():
                continue
            if self._at_end:
                break

            character = self._current
            if self._is_identifier_start(character):
                tokens.append(self._scan_identifier())
            elif character.isdigit():
                tokens.append(self._scan_number())
            elif character == '"':
                tokens.append(self._scan_string())
            else:
                token = self._scan_operator_or_delimiter()
                if token is not None:
                    tokens.append(token)
                else:
                    self._report("LEX001", f"Carácter no reconocido: {character!r}")
                    self._advance()

        tokens.append(
            Token(
                type=TokenType.EOF,
                value="",
                line=self._line,
                column=self._column,
                start_position=self._position,
                end_position=self._position,
            )
        )
        return tokens

    @property
    def _at_end(self) -> bool:
        return self._position >= len(self.source)

    @property
    def _current(self) -> str:
        return self.source[self._position]

    def _peek(self, offset: int = 1) -> str:
        position = self._position + offset
        return "" if position >= len(self.source) else self.source[position]

    def _advance(self) -> str:
        character = self._current
        self._position += 1
        if character == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return character

    def _skip_whitespace_and_comments(self) -> bool:
        consumed = False
        while not self._at_end:
            if self._current.isspace():
                self._advance()
                consumed = True
                continue
            if self._current == "/" and self._peek() == "/":
                self._skip_line_comment()
                consumed = True
                continue
            if self._current == "/" and self._peek() == "*":
                self._skip_block_comment()
                consumed = True
                continue
            break
        return consumed

    def _skip_line_comment(self) -> None:
        self._advance()
        self._advance()
        while not self._at_end and self._current != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        start_line, start_column, start_position = self._line, self._column, self._position
        self._advance()
        self._advance()
        while not self._at_end and not (self._current == "*" and self._peek() == "/"):
            self._advance()
        if self._at_end:
            self._report(
                "LEX003",
                "Comentario de bloque sin cerrar.",
                line=start_line,
                column=start_column,
                start_position=start_position,
            )
        else:
            self._advance()
            self._advance()

    @staticmethod
    def _is_identifier_start(character: str) -> bool:
        return character == "_" or "a" <= character <= "z" or "A" <= character <= "Z"

    @staticmethod
    def _is_identifier_part(character: str) -> bool:
        return Lexer._is_identifier_start(character) or character.isdigit()

    def _scan_identifier(self) -> Token:
        start_position, line, column = self._position, self._line, self._column
        while not self._at_end and self._is_identifier_part(self._current):
            self._advance()
        value = self.source[start_position:self._position]
        token_type = self._KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, line, column, start_position, self._position)

    def _scan_number(self) -> Token:
        start_position, line, column = self._position, self._line, self._column
        while not self._at_end and self._current.isdigit():
            self._advance()

        token_type = TokenType.INTEGER_LITERAL
        if not self._at_end and self._current == ".":
            token_type = TokenType.FLOAT_LITERAL
            self._advance()
            if not self._consume_digits():
                self._report("LEX004", "Literal decimal inválido.", line, column, start_position)

        if self._has_invalid_numeric_suffix:
            self._consume_invalid_numeric_suffix()
            self._report("LEX004", "Literal numérico inválido.", line, column, start_position)

        value = self.source[start_position:self._position]
        return Token(token_type, value, line, column, start_position, self._position)

    def _consume_digits(self) -> bool:
        start_position = self._position
        while not self._at_end and self._current.isdigit():
            self._advance()
        return start_position != self._position

    @property
    def _has_invalid_numeric_suffix(self) -> bool:
        return not self._at_end and (
            self._current == "." or self._is_identifier_start(self._current)
        )

    def _consume_invalid_numeric_suffix(self) -> None:
        while not self._at_end and (
            self._current == "." or self._is_identifier_part(self._current)
        ):
            self._advance()

    def _scan_string(self) -> Token:
        start_position, line, column = self._position, self._line, self._column
        self._advance()
        characters: list[str] = []
        escapes = {"\\": "\\", '"': '"', "n": "\n", "t": "\t"}
        closed = False

        while not self._at_end:
            character = self._current
            if character == '"':
                self._advance()
                closed = True
                break
            if character == "\n":
                break
            if character == "\\":
                self._advance()
                if self._at_end:
                    break
                escaped = self._advance()
                characters.append(escapes.get(escaped, escaped))
            else:
                characters.append(self._advance())

        if not closed:
            self._report("LEX002", "Cadena sin cerrar.", line, column, start_position)

        return Token(
            TokenType.STRING_LITERAL,
            "".join(characters),
            line,
            column,
            start_position,
            self._position,
        )

    def _scan_operator_or_delimiter(self) -> Token | None:
        start_position, line, column = self._position, self._line, self._column
        two_character = self.source[self._position:self._position + 2]
        token_type = self._TWO_CHARACTER_TOKENS.get(two_character)
        if token_type is not None:
            self._advance()
            self._advance()
            return Token(token_type, two_character, line, column, start_position, self._position)

        token_type = self._ONE_CHARACTER_TOKENS.get(self._current)
        if token_type is None:
            return None
        value = self._advance()
        return Token(token_type, value, line, column, start_position, self._position)

    def _report(
        self,
        code: str,
        message: str,
        line: int | None = None,
        column: int | None = None,
        start_position: int | None = None,
    ) -> None:
        self.reporter.report(
            code,
            DiagnosticCategory.LEXICAL,
            message,
            self._line if line is None else line,
            self._column if column is None else column,
            start_position=self._position if start_position is None else start_position,
            end_position=self._position,
        )