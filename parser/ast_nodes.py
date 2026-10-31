"""Nodos del árbol sintáctico abstracto de MiniLang."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Ubicación de un nodo con offset final exclusivo."""

    start_position: int
    end_position: int
    line: int
    column: int


class AstNode:
    """Tipo base nominal para todos los nodos del AST."""

    span: SourceSpan


class Statement(AstNode):
    """Tipo base de declaraciones y sentencias."""


class Expression(AstNode):
    """Tipo base de expresiones."""


@dataclass(frozen=True, slots=True)
class Program(AstNode):
    statements: list[Statement]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Parameter(AstNode):
    type_name: str
    name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class VariableDeclaration(Statement):
    type_name: str
    name: str
    initializer: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class FunctionDeclaration(Statement):
    name: str
    parameters: list[Parameter]
    return_type: str
    body: "BlockStatement"
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Assignment(Statement):
    name: str
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ExpressionStatement(Statement):
    expression: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BlockStatement(Statement):
    statements: list[Statement]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class IfStatement(Statement):
    condition: Expression
    then_branch: Statement
    else_branch: Statement | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class WhileStatement(Statement):
    condition: Expression
    body: Statement
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ForStatement(Statement):
    initializer: VariableDeclaration | Assignment
    condition: Expression
    update: Assignment
    body: Statement
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ReturnStatement(Statement):
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class PrintStatement(Statement):
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class UnaryExpression(Expression):
    operator: str
    operand: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Literal(Expression):
    value: Any
    type_name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Identifier(Expression):
    name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class FunctionCall(Expression):
    name: str
    arguments: list[Expression]
    span: SourceSpan