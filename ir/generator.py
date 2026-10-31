"""Generador de código de tres direcciones desde el AST."""

from diagnostics import ErrorReporter
from diagnostics.compiler_error import CompilerError
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

from .instructions import (
    Assign,
    BinaryOp,
    Call,
    ConditionalJump,
    FunctionBegin,
    FunctionEnd,
    Instruction,
    IRProgram,
    Jump,
    Label,
    Operand,
    Print,
    Return,
    UnaryOp,
)
from .temporary import TemporaryFactory


class IRGenerator:
    """Transforma un AST semánticamente válido en instrucciones TAC."""

    def __init__(
        self,
        reporter: ErrorReporter | None = None,
        temporary_factory: TemporaryFactory | None = None,
    ) -> None:
        self.reporter = reporter
        self.temporaries = temporary_factory or TemporaryFactory()
        self._instructions: list[Instruction] = []

    def generate(self, program: Program) -> IRProgram:
        """Genera IR y rechaza explícitamente programas con errores previos."""

        if self.reporter is not None and self.reporter.has_errors:
            raise CompilerError("No se puede generar IR con diagnósticos pendientes.")
        self._instructions = []
        for statement in program.statements:
            self._generate_statement(statement)
        return IRProgram(tuple(self._instructions))

    def _generate_statement(self, statement: Statement) -> None:
        if isinstance(statement, VariableDeclaration):
            self._emit(Assign(statement.name, self._generate_expression(statement.initializer)))
        elif isinstance(statement, Assignment):
            self._emit(Assign(statement.name, self._generate_expression(statement.value)))
        elif isinstance(statement, ExpressionStatement):
            self._generate_expression(statement.expression)
        elif isinstance(statement, BlockStatement):
            for nested in statement.statements:
                self._generate_statement(nested)
        elif isinstance(statement, IfStatement):
            self._generate_if(statement)
        elif isinstance(statement, WhileStatement):
            self._generate_while(statement)
        elif isinstance(statement, ForStatement):
            self._generate_for(statement)
        elif isinstance(statement, FunctionDeclaration):
            self._generate_function(statement)
        elif isinstance(statement, ReturnStatement):
            self._emit(Return(self._generate_expression(statement.value)))
        elif isinstance(statement, PrintStatement):
            self._emit(Print(self._generate_expression(statement.value)))

    def _generate_function(self, declaration: FunctionDeclaration) -> None:
        parameters = tuple(parameter.name for parameter in declaration.parameters)
        self._emit(FunctionBegin(declaration.name, parameters))
        self._generate_statement(declaration.body)
        self._emit(FunctionEnd(declaration.name))

    def _generate_if(self, statement: IfStatement) -> None:
        then_label = self.temporaries.label()
        else_label = self.temporaries.label()
        end_label = self.temporaries.label()
        condition = self._generate_expression(statement.condition)
        self._emit(ConditionalJump(condition, then_label, else_label))
        self._emit(Label(then_label))
        self._generate_statement(statement.then_branch)
        self._emit(Jump(end_label))
        self._emit(Label(else_label))
        if statement.else_branch is not None:
            self._generate_statement(statement.else_branch)
        self._emit(Label(end_label))

    def _generate_while(self, statement: WhileStatement) -> None:
        start_label = self.temporaries.label()
        body_label = self.temporaries.label()
        end_label = self.temporaries.label()
        self._emit(Label(start_label))
        condition = self._generate_expression(statement.condition)
        self._emit(ConditionalJump(condition, body_label, end_label))
        self._emit(Label(body_label))
        self._generate_statement(statement.body)
        self._emit(Jump(start_label))
        self._emit(Label(end_label))

    def _generate_for(self, statement: ForStatement) -> None:
        self._generate_statement(statement.initializer)
        start_label = self.temporaries.label()
        body_label = self.temporaries.label()
        end_label = self.temporaries.label()
        self._emit(Label(start_label))
        condition = self._generate_expression(statement.condition)
        self._emit(ConditionalJump(condition, body_label, end_label))
        self._emit(Label(body_label))
        self._generate_statement(statement.body)
        self._generate_statement(statement.update)
        self._emit(Jump(start_label))
        self._emit(Label(end_label))

    def _generate_expression(self, expression: Expression) -> Operand:
        if isinstance(expression, Literal):
            return self._literal_operand(expression.value)
        if isinstance(expression, Identifier):
            return expression.name
        if isinstance(expression, UnaryExpression):
            operand = self._generate_expression(expression.operand)
            target = self.temporaries.temporary()
            self._emit(UnaryOp(target, expression.operator, operand))
            return target
        if isinstance(expression, BinaryExpression):
            return self._generate_binary(expression)
        if isinstance(expression, FunctionCall):
            arguments = tuple(
                self._generate_expression(argument) for argument in expression.arguments
            )
            target = self.temporaries.temporary()
            self._emit(Call(target, expression.name, arguments))
            return target
        raise CompilerError("Nodo de expresión no soportado por el generador de IR.")

    def _generate_binary(self, expression: BinaryExpression) -> str:
        if expression.operator in {"&&", "||"}:
            return self._generate_short_circuit(expression)
        left = self._generate_expression(expression.left)
        right = self._generate_expression(expression.right)
        target = self.temporaries.temporary()
        self._emit(BinaryOp(target, left, expression.operator, right))
        return target

    def _generate_short_circuit(self, expression: BinaryExpression) -> str:
        left = self._generate_expression(expression.left)
        right_label = self.temporaries.label()
        false_label = self.temporaries.label()
        end_label = self.temporaries.label()
        target = self.temporaries.temporary()
        if expression.operator == "&&":
            self._emit(ConditionalJump(left, right_label, false_label))
        else:
            self._emit(ConditionalJump(left, false_label, right_label))
        self._emit(Label(right_label))
        right = self._generate_expression(expression.right)
        self._emit(Assign(target, right))
        self._emit(Jump(end_label))
        self._emit(Label(false_label))
        self._emit(Assign(target, expression.operator == "||"))
        self._emit(Label(end_label))
        return target

    @staticmethod
    def _literal_operand(value: object) -> Operand:
        if isinstance(value, str):
            return f"__string__:{value}"
        if isinstance(value, (int, float, bool)):
            return value
        raise CompilerError("Literal no soportado por el generador de IR.")

    def _emit(self, instruction: Instruction) -> None:
        self._instructions.append(instruction)