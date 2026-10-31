"""Parser recursive descent para la gramática de MiniLang v1."""

from diagnostics import DiagnosticCategory, ErrorReporter
from diagnostics.compiler_error import CompilerError
from lexer import Token, TokenType

from .ast_nodes import (
    Assignment,
    BinaryExpression,
    BlockStatement,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionCall,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    Literal,
    Parameter,
    PrintStatement,
    Program,
    ReturnStatement,
    SourceSpan,
    Statement,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)


class _ParseError(CompilerError):
    """Interrumpe una producción para permitir sincronización posterior."""


class Parser:
    """Construye un AST y recopila errores sintácticos recuperables."""

    _TYPE_TOKENS = {TokenType.INT, TokenType.FLOAT, TokenType.STRING, TokenType.BOOL}
    _BINARY_LEVELS = (
        (TokenType.OR,),
        (TokenType.AND,),
        (TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL),
        (TokenType.GREATER, TokenType.LESS, TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL),
        (TokenType.PLUS, TokenType.MINUS),
        (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO),
    )

    def __init__(self, tokens: list[Token], reporter: ErrorReporter | None = None) -> None:
        self.tokens = tokens
        self.reporter = reporter or ErrorReporter()
        self._position = 0

    def parse(self) -> Program:
        """Analiza el programa completo y devuelve su raíz AST."""

        statements: list[Statement] = []
        while not self._check(TokenType.EOF):
            try:
                statements.append(self._parse_top_level_statement())
            except _ParseError:
                self._synchronize()
        return Program(statements, self._program_span(statements))

    def _parse_top_level_statement(self) -> Statement:
        if self._check(TokenType.FUNCTION):
            return self._parse_function_declaration()
        return self._parse_statement()

    def _parse_statement(self) -> Statement:
        if self._check(*self._TYPE_TOKENS):
            return self._parse_variable_declaration()
        if self._match(TokenType.FUNCTION):
            return self._parse_function_declaration(already_consumed=True)
        if self._match(TokenType.IF):
            return self._parse_if_statement()
        if self._match(TokenType.WHILE):
            return self._parse_while_statement()
        if self._match(TokenType.FOR):
            return self._parse_for_statement()
        if self._match(TokenType.RETURN):
            return self._parse_return_statement()
        if self._match(TokenType.PRINT):
            return self._parse_print_statement()
        if self._match(TokenType.LEFT_BRACE):
            return self._parse_block(already_consumed=True)
        return self._parse_expression_statement()

    def _parse_variable_declaration(self, *, require_semicolon: bool = True) -> VariableDeclaration:
        type_token = self._advance()
        name_token = self._expect(TokenType.IDENTIFIER, "Se esperaba un identificador.")
        self._expect(TokenType.ASSIGN, "Se esperaba '=' en la declaración.")
        initializer = self._parse_expression()
        end_token = (
            self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de la declaración.")
            if require_semicolon
            else self._previous
        )
        return VariableDeclaration(
            self._type_name(type_token),
            name_token.value,
            initializer,
            self._span(type_token, end_token),
        )

    def _parse_function_declaration(self, *, already_consumed: bool = False) -> FunctionDeclaration:
        function_token = self._previous if already_consumed else self._expect(TokenType.FUNCTION)
        return_type = self._advance()
        if return_type.type not in self._TYPE_TOKENS:
            self._syntax("SYN002", "Se esperaba el tipo de retorno de la función.", return_type)
        name_token = self._expect(TokenType.IDENTIFIER, "Se esperaba el nombre de la función.")
        self._expect(TokenType.LEFT_PAREN, "Se esperaba '('.")
        parameters: list[Parameter] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                parameter_type = self._advance()
                if parameter_type.type not in self._TYPE_TOKENS:
                    self._syntax("SYN002", "Se esperaba el tipo del parámetro.", parameter_type)
                parameter_name = self._expect(
                    TokenType.IDENTIFIER,
                    "Se esperaba el nombre del parámetro.",
                )
                parameters.append(
                    Parameter(
                        self._type_name(parameter_type),
                        parameter_name.value,
                        self._span(parameter_type, parameter_name),
                    )
                )
                if not self._match(TokenType.COMMA):
                    break
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')'.")
        body = self._parse_required_block()
        return FunctionDeclaration(
            name_token.value,
            parameters,
            self._type_name(return_type),
            body,
            self._span(function_token, self._token_at_end(body.span)),
        )

    def _parse_if_statement(self) -> IfStatement:
        if_token = self._previous
        self._expect(TokenType.LEFT_PAREN, "Se esperaba '(' después de 'if'.")
        condition = self._parse_expression()
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' después de la condición.")
        then_branch = self._parse_statement()
        else_branch = self._parse_statement() if self._match(TokenType.ELSE) else None
        end_span = else_branch.span if else_branch else then_branch.span
        return IfStatement(
            condition,
            then_branch,
            else_branch,
            self._span_from_token(if_token, end_span),
        )

    def _parse_while_statement(self) -> WhileStatement:
        while_token = self._previous
        self._expect(TokenType.LEFT_PAREN, "Se esperaba '(' después de 'while'.")
        condition = self._parse_expression()
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' después de la condición.")
        body = self._parse_statement()
        return WhileStatement(condition, body, self._span_from_token(while_token, body.span))

    def _parse_for_statement(self) -> ForStatement:
        for_token = self._previous
        self._expect(TokenType.LEFT_PAREN, "Se esperaba '(' después de 'for'.")
        if self._check(*self._TYPE_TOKENS):
            initializer = self._parse_variable_declaration(require_semicolon=False)
        else:
            initializer = self._parse_assignment(require_semicolon=False)
        self._expect(TokenType.SEMICOLON, "Se esperaba ';' después del inicializador.")
        condition = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de la condición.")
        update = self._parse_assignment(require_semicolon=False)
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' después de la actualización.")
        body = self._parse_statement()
        return ForStatement(
            initializer,
            condition,
            update,
            body,
            self._span_from_token(for_token, body.span),
        )

    def _parse_return_statement(self) -> ReturnStatement:
        return_token = self._previous
        value = self._parse_expression()
        end_token = self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de 'return'.")
        return ReturnStatement(value, self._span(return_token, end_token))

    def _parse_print_statement(self) -> PrintStatement:
        print_token = self._previous
        self._expect(TokenType.LEFT_PAREN, "Se esperaba '(' después de 'print'.")
        value = self._parse_expression()
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' después de la expresión.")
        end_token = self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de 'print'.")
        return PrintStatement(value, self._span(print_token, end_token))

    def _parse_block(self, *, already_consumed: bool = False) -> BlockStatement:
        left_brace = self._previous if already_consumed else self._expect(TokenType.LEFT_BRACE)
        statements: list[Statement] = []
        while not self._check(TokenType.RIGHT_BRACE, TokenType.EOF):
            try:
                statements.append(self._parse_statement())
            except _ParseError:
                self._synchronize()
        right_brace = self._expect(TokenType.RIGHT_BRACE, "Se esperaba '}'.")
        return BlockStatement(statements, self._span(left_brace, right_brace))

    def _parse_required_block(self) -> BlockStatement:
        return self._parse_block()

    def _parse_expression_statement(self) -> ExpressionStatement:
        expression = self._parse_expression()
        end_token = self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de la expresión.")
        return ExpressionStatement(expression, self._span_from_token(expression.span, end_token))

    def _parse_assignment(self, *, require_semicolon: bool = True) -> Assignment:
        name_token = self._expect(TokenType.IDENTIFIER, "Se esperaba un identificador asignable.")
        self._expect(TokenType.ASSIGN, "Se esperaba '=' en la asignación.")
        value = self._parse_expression()
        end_token = (
            self._expect(TokenType.SEMICOLON, "Se esperaba ';' después de la asignación.")
            if require_semicolon
            else self._previous
        )
        return Assignment(name_token.value, value, self._span(name_token, end_token))

    def _parse_expression(self) -> Expression:
        return self._parse_binary_level(0)

    def _parse_binary_level(self, level: int) -> Expression:
        if level == len(self._BINARY_LEVELS):
            return self._parse_unary()
        expression = self._parse_binary_level(level + 1)
        operators = self._BINARY_LEVELS[level]
        while self._check(*operators):
            operator = self._advance()
            right = self._parse_binary_level(level + 1)
            expression = BinaryExpression(
                expression,
                operator.value,
                right,
                self._span_from_token(expression.span, right.span),
            )
        return expression

    def _parse_unary(self) -> Expression:
        if self._match(TokenType.NOT, TokenType.MINUS, TokenType.PLUS):
            operator = self._previous
            operand = self._parse_unary()
            return UnaryExpression(
                operator.value,
                operand,
                self._span_from_token(operator, operand.span),
            )
        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        if self._check(
            TokenType.INTEGER_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.STRING_LITERAL,
            TokenType.TRUE,
            TokenType.FALSE,
        ):
            return self._parse_literal()
        if self._match(TokenType.IDENTIFIER):
            return self._parse_identifier_or_call()
        if self._match(TokenType.LEFT_PAREN):
            return self._parse_grouped_expression()
        self._syntax("SYN003", "Se esperaba una expresión.", self._current)
        raise AssertionError("_syntax siempre lanza _ParseError")

    def _parse_literal(self) -> Literal:
        token = self._advance()
        if token.type is TokenType.INTEGER_LITERAL:
            value, type_name = int(token.value), "int"
        elif token.type is TokenType.FLOAT_LITERAL:
            value, type_name = float(token.value), "float"
        elif token.type is TokenType.STRING_LITERAL:
            value, type_name = token.value, "string"
        else:
            value, type_name = token.type is TokenType.TRUE, "bool"
        return Literal(value, type_name, self._span(token, token))

    def _parse_identifier_or_call(self) -> Expression:
        name_token = self._previous
        if not self._match(TokenType.LEFT_PAREN):
            return Identifier(name_token.value, self._span(name_token, name_token))
        arguments: list[Expression] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                arguments.append(self._parse_expression())
                if not self._match(TokenType.COMMA):
                    break
        right_paren = self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' en la llamada.")
        return FunctionCall(name_token.value, arguments, self._span(name_token, right_paren))

    def _parse_grouped_expression(self) -> Expression:
        expression = self._parse_expression()
        self._expect(TokenType.RIGHT_PAREN, "Se esperaba ')' después de la expresión.")
        return expression

    def _expect(self, token_type: TokenType, message: str = "") -> Token:
        if self._check(token_type):
            return self._advance()
        self._syntax("SYN002", message or f"Se esperaba {token_type.name}.", self._current)
        raise AssertionError("_syntax siempre lanza _ParseError")

    def _syntax(self, code: str, message: str, token: Token) -> None:
        self.reporter.report(
            code,
            DiagnosticCategory.SYNTAX,
            message,
            token.line,
            token.column,
            start_position=token.start_position,
            end_position=token.end_position,
        )
        raise _ParseError(message)

    def _synchronize(self) -> None:
        while not self._check(TokenType.EOF):
            if self._previous.type is TokenType.SEMICOLON:
                return
            if self._check(
                TokenType.INT,
                TokenType.FLOAT,
                TokenType.STRING,
                TokenType.BOOL,
                TokenType.FUNCTION,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.RETURN,
                TokenType.PRINT,
                TokenType.LEFT_BRACE,
                TokenType.RIGHT_BRACE,
            ):
                return
            self._advance()

    @property
    def _current(self) -> Token:
        return self.tokens[self._position]

    @property
    def _previous(self) -> Token:
        return self.tokens[self._position - 1]

    def _advance(self) -> Token:
        if not self._check(TokenType.EOF):
            self._position += 1
        return self._previous

    def _check(self, *token_types: TokenType) -> bool:
        return self._current.type in token_types

    def _match(self, *token_types: TokenType) -> bool:
        if not self._check(*token_types):
            return False
        self._advance()
        return True

    @staticmethod
    def _type_name(token: Token) -> str:
        return token.value

    @staticmethod
    def _span(start: Token, end: Token) -> SourceSpan:
        return SourceSpan(start.start_position, end.end_position, start.line, start.column)

    @staticmethod
    def _span_from_token(start: Token | SourceSpan, end: Token | SourceSpan) -> SourceSpan:
        start_position = start.start_position
        line = start.line
        column = start.column
        end_position = end.end_position
        return SourceSpan(start_position, end_position, line, column)

    @staticmethod
    def _token_at_end(span: SourceSpan) -> Token:
        return Token(
            TokenType.EOF,
            "",
            span.line,
            span.column,
            span.end_position,
            span.end_position,
        )

    def _program_span(self, statements: list[Statement]) -> SourceSpan:
        if statements:
            return SourceSpan(
                statements[0].span.start_position,
                statements[-1].span.end_position,
                statements[0].span.line,
                statements[0].span.column,
            )
        token = self._current
        return self._span(token, token)