"""Análisis semántico sobre el AST de MiniLang."""

from diagnostics import DiagnosticCategory, ErrorReporter
from parser.ast_nodes import (
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
    PrintStatement,
    Program,
    ReturnStatement,
    Statement,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)

from .symbol import Symbol, SymbolKind
from .symbol_table import SymbolTable
from .type_checker import TypeChecker
from .types import MiniType


class SemanticAnalyzer:
    """Resuelve nombres, administra ámbitos y valida tipos del programa."""

    def __init__(
        self,
        reporter: ErrorReporter | None = None,
        symbol_table: SymbolTable | None = None,
    ) -> None:
        self.reporter = reporter or ErrorReporter()
        self.symbols = symbol_table or SymbolTable()
        self.type_checker = TypeChecker()
        self._function_return_types: list[MiniType] = []

    def analyze(self, program: Program) -> None:
        """Analiza el programa completo y acumula diagnósticos semánticos."""

        self._predeclare_functions(program)
        for statement in program.statements:
            self._visit_statement(statement)

    def _predeclare_functions(self, program: Program) -> None:
        for statement in program.statements:
            if not isinstance(statement, FunctionDeclaration):
                continue
            symbol = Symbol(
                statement.name,
                MiniType.ERROR,
                SymbolKind.FUNCTION,
                statement.span,
                tuple(
                    MiniType.from_name(parameter.type_name)
                    for parameter in statement.parameters
                ),
                MiniType.from_name(statement.return_type),
            )
            if not self.symbols.declare(symbol):
                self._error(
                    "SEM002", f"El nombre '{statement.name}' ya está declarado.", statement
                )

    def _visit_statement(self, statement: Statement) -> None:
        if isinstance(statement, VariableDeclaration):
            self._visit_variable_declaration(statement)
        elif isinstance(statement, FunctionDeclaration):
            self._visit_function_declaration(statement)
        elif isinstance(statement, Assignment):
            self._visit_assignment(statement)
        elif isinstance(statement, ExpressionStatement):
            self._infer_expression(statement.expression)
        elif isinstance(statement, BlockStatement):
            with self.symbols.scope():
                for nested in statement.statements:
                    self._visit_statement(nested)
        elif isinstance(statement, IfStatement):
            self._require_boolean(
                statement.condition, "SEM004", "La condición de 'if' debe ser bool."
            )
            self._infer_expression(statement.condition)
            self._visit_statement(statement.then_branch)
            if statement.else_branch is not None:
                self._visit_statement(statement.else_branch)
        elif isinstance(statement, WhileStatement):
            self._require_boolean(
                statement.condition, "SEM004", "La condición de 'while' debe ser bool."
            )
            self._infer_expression(statement.condition)
            self._visit_statement(statement.body)
        elif isinstance(statement, ForStatement):
            with self.symbols.scope():
                self._visit_statement(statement.initializer)
                self._require_boolean(
                    statement.condition, "SEM004", "La condición de 'for' debe ser bool."
                )
                self._infer_expression(statement.condition)
                self._visit_assignment(statement.update)
                self._visit_statement(statement.body)
        elif isinstance(statement, ReturnStatement):
            self._visit_return(statement)
        elif isinstance(statement, PrintStatement):
            self._infer_expression(statement.value)

    def _visit_variable_declaration(self, declaration: VariableDeclaration) -> None:
        value_type = self._infer_expression(declaration.initializer)
        declared_type = MiniType.from_name(declaration.type_name)
        self._require_assignable(declared_type, value_type, declaration)
        symbol = Symbol(declaration.name, declared_type, SymbolKind.VARIABLE, declaration.span)
        if not self.symbols.declare(symbol):
            self._error(
                "SEM002", f"La variable '{declaration.name}' ya está declarada.", declaration
            )

    def _visit_function_declaration(self, declaration: FunctionDeclaration) -> None:
        if self.symbols.current_scope is not self.symbols.global_scope:
            self._error(
                "SEM007",
                "Las funciones solo pueden declararse en el ámbito global.",
                declaration,
            )
        with self.symbols.scope():
            for parameter in declaration.parameters:
                parameter_type = MiniType.from_name(parameter.type_name)
                symbol = Symbol(
                    parameter.name, parameter_type, SymbolKind.PARAMETER, parameter.span
                )
                if not self.symbols.declare(symbol):
                    self._error(
                        "SEM002", f"El parámetro '{parameter.name}' está duplicado.", parameter
                    )
            return_type = MiniType.from_name(declaration.return_type)
            self._function_return_types.append(return_type)
            self._visit_statement(declaration.body)
            self._function_return_types.pop()

    def _visit_assignment(self, assignment: Assignment) -> None:
        symbol = self.symbols.resolve(assignment.name)
        value_type = self._infer_expression(assignment.value)
        if symbol is None:
            self._error("SEM001", f"El nombre '{assignment.name}' no está declarado.", assignment)
            return
        if symbol.kind is SymbolKind.FUNCTION:
            self._error(
                "SEM007",
                f"'{assignment.name}' es una función y no se puede asignar.",
                assignment,
            )
            return
        self._require_assignable(symbol.type, value_type, assignment)

    def _visit_return(self, statement: ReturnStatement) -> None:
        value_type = self._infer_expression(statement.value)
        if not self._function_return_types:
            self._error("SEM006", "'return' solo puede usarse dentro de una función.", statement)
            return
        self._require_assignable(self._function_return_types[-1], value_type, statement, "SEM006")

    def _infer_expression(self, expression: Expression) -> MiniType:
        if isinstance(expression, Literal):
            return MiniType.from_name(expression.type_name)
        if isinstance(expression, Identifier):
            symbol = self.symbols.resolve(expression.name)
            if symbol is None:
                self._error(
                    "SEM001", f"El nombre '{expression.name}' no está declarado.", expression
                )
                return MiniType.ERROR
            if symbol.kind is SymbolKind.FUNCTION:
                self._error(
                    "SEM007",
                    f"La función '{expression.name}' requiere una llamada.",
                    expression,
                )
                return MiniType.ERROR
            return symbol.type
        if isinstance(expression, UnaryExpression):
            operand_type = self._infer_expression(expression.operand)
            result = self.type_checker.unary_result(expression.operator, operand_type)
            if result is MiniType.ERROR and operand_type is not MiniType.ERROR:
                self._error(
                    "SEM003",
                    f"Operador '{expression.operator}' inválido para {operand_type.value}.",
                    expression,
                )
            return result
        if isinstance(expression, BinaryExpression):
            left_type = self._infer_expression(expression.left)
            right_type = self._infer_expression(expression.right)
            result = self.type_checker.binary_result(expression.operator, left_type, right_type)
            if (
                result is MiniType.ERROR
                and left_type is not MiniType.ERROR
                and right_type is not MiniType.ERROR
            ):
                self._error(
                    "SEM003",
                    f"Operador '{expression.operator}' inválido entre "
                    f"{left_type.value} y {right_type.value}.",
                    expression,
                )
            return result
        if isinstance(expression, FunctionCall):
            return self._infer_call(expression)
        return MiniType.ERROR

    def _infer_call(self, call: FunctionCall) -> MiniType:
        symbol = self.symbols.resolve(call.name)
        argument_types = tuple(self._infer_expression(argument) for argument in call.arguments)
        if symbol is None:
            self._error("SEM001", f"La función '{call.name}' no está declarada.", call)
            return MiniType.ERROR
        if symbol.kind is not SymbolKind.FUNCTION:
            self._error("SEM005", f"'{call.name}' no es una función.", call)
            return MiniType.ERROR
        if len(argument_types) != len(symbol.parameters):
            self._error(
                "SEM005",
                f"La función '{call.name}' esperaba {len(symbol.parameters)} argumentos.",
                call,
            )
        else:
            for expected, actual in zip(symbol.parameters, argument_types):
                if not self.type_checker.is_assignable(expected, actual):
                    self._error(
                        "SEM005",
                        f"Argumento incompatible en la llamada a '{call.name}'.",
                        call,
                    )
        return symbol.return_type or MiniType.ERROR

    def _require_boolean(self, expression: Expression, code: str, message: str) -> None:
        expression_type = self._infer_expression(expression)
        if expression_type not in {MiniType.BOOL, MiniType.ERROR}:
            self._error(code, message, expression)

    def _require_assignable(
        self,
        target: MiniType,
        value: MiniType,
        node: Statement,
        code: str = "SEM003",
    ) -> None:
        if not self.type_checker.is_assignable(target, value):
            self._error(
                "SEM003" if code == "SEM003" else code,
                f"No se puede asignar {value.value} a {target.value}.",
                node,
            )

    def _error(self, code: str, message: str, node: object) -> None:
        span = node.span
        self.reporter.report(
            code,
            DiagnosticCategory.SEMANTIC,
            message,
            span.line,
            span.column,
            start_position=span.start_position,
            end_position=span.end_position,
        )