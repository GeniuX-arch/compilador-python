"""Punto de entrada para ejecutar código MiniLang."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from diagnostics import ErrorReporter
from ir import IRGenerator
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from target import VirtualMachine

# ──────────────────────────────────────────────
# Escribe aquí tu código MiniLang:
# ──────────────────────────────────────────────
SOURCE = """
int x = 10;
float promedio = 8.5;
string saludo = "Hola Mundo";
bool esMayor = x > 5;
print(saludo);
"""
# ──────────────────────────────────────────────


def run(source: str) -> None:
    reporter = ErrorReporter()

    # ── Fase 1: Léxico ──────────────────────────
    print("=" * 50)
    print("FASE 1 — ANÁLISIS LÉXICO")
    print("=" * 50)
    lexer = Lexer(source, reporter)
    tokens = lexer.tokenize()
    for token in tokens:
        print(f"  [{token.type.name:20s}]  {token.value!r:20s}  línea {token.line}, col {token.column}")
    if reporter.has_errors:
        print("\n[ERROR] Errores lexicos encontrados:")
        for d in reporter.diagnostics:
            print(f"  {d}")
        return

    # ── Fase 2: Sintáctico ──────────────────────
    print("\n" + "=" * 50)
    print("FASE 2 — ANÁLISIS SINTÁCTICO (AST)")
    print("=" * 50)
    parser = Parser(tokens, reporter)
    program = parser.parse()
    print(f"  Sentencias en el AST: {len(program.statements)}")
    for stmt in program.statements:
        print(f"  >> {type(stmt).__name__}")
    if reporter.has_errors:
        print("\n[ERROR] Errores sintacticos encontrados:")
        for d in reporter.diagnostics:
            print(f"  {d}")
        return

    # ── Fase 3: Semántico ───────────────────────
    print("\n" + "=" * 50)
    print("FASE 3 — ANÁLISIS SEMÁNTICO")
    print("=" * 50)
    analyzer = SemanticAnalyzer(reporter)
    analyzer.analyze(program)
    if reporter.has_errors:
        print("[ERROR] Errores semanticos encontrados:")
        for d in reporter.diagnostics:
            print(f"  {d}")
        return
    print("  [OK] Sin errores semanticos.")

    # ── Fase 4+: IR y ejecución ─────────────────
    print("\n" + "=" * 50)
    print("EJECUCIÓN (Máquina Virtual)")
    print("=" * 50)
    ir_gen = IRGenerator(reporter)
    instructions = ir_gen.generate(program)
    vm = VirtualMachine()
    vm.execute(instructions)


if __name__ == "__main__":
    run(SOURCE)
