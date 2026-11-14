"""MiniLang IDE — Interfaz gráfica para el compilador MiniLang."""

import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, ".")

from diagnostics import ErrorReporter
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer

# ── Paleta de colores (tema oscuro) ─────────────────────────────────────────
C = {
    "bg_main":    "#1e1e2e",
    "bg_editor":  "#11111b",
    "bg_panel":   "#181825",
    "bg_surface": "#313244",
    "bg_overlay": "#45475a",
    "fg_text":    "#cdd6f4",
    "fg_muted":   "#6c7086",
    "fg_sub":     "#a6adc8",
    "green":      "#a6e3a1",
    "red":        "#f38ba8",
    "yellow":     "#f9e2af",
    "blue":       "#89b4fa",
    "purple":     "#cba6f7",
    "teal":       "#94e2d5",
    "peach":      "#fab387",
    "bg_err":     "#3b1218",
    "bg_err_col": "#5a1020",
}

EXAMPLE = """\
// Programa de ejemplo en MiniLang
int contador = 0;
float promedio = 8.5;
string saludo = "Hola Mundo";
bool activo = contador > 0;
print(saludo);
"""


# ── Utilidades de widget ─────────────────────────────────────────────────────

def make_text(parent, **kw) -> tk.Text:
    defaults = dict(
        bg=C["bg_panel"], fg=C["fg_text"],
        relief="flat", bd=0,
        highlightthickness=0,
        selectbackground=C["bg_surface"],
        selectforeground=C["fg_text"],
        inactiveselectbackground=C["bg_surface"],
    )
    defaults.update(kw)
    return tk.Text(parent, **defaults)


def make_label(parent, **kw) -> tk.Label:
    defaults = dict(bg=C["bg_main"], fg=C["fg_text"])
    defaults.update(kw)
    return tk.Label(parent, **defaults)


def make_frame(parent, **kw) -> tk.Frame:
    defaults = dict(bg=C["bg_main"])
    defaults.update(kw)
    return tk.Frame(parent, **defaults)


# ── Panel de una fase ────────────────────────────────────────────────────────

class PhasePanel(tk.Frame):
    """Muestra el estado (espera / pasó / falló / omitida) de una fase."""

    STATES = {
        "wait": ("ESPERANDO", C["fg_muted"],  C["bg_surface"]),
        "pass": ("  PASÓ  ",  C["bg_editor"], C["green"]),
        "fail": ("  FALLÓ ",  C["bg_editor"], C["red"]),
        "skip": (" OMITIDA",  C["bg_editor"], C["peach"]),
    }

    def __init__(self, parent, num: int, title: str):
        super().__init__(parent, bg=C["bg_panel"], bd=0, highlightthickness=1,
                         highlightbackground=C["bg_surface"])
        self._build(num, title)

    def _build(self, num: int, title: str):
        # ── Cabecera ──────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["bg_surface"])
        hdr.pack(fill="x")

        tk.Label(
            hdr, text=f" FASE {num} ", font=("Consolas", 9, "bold"),
            bg=C["purple"], fg=C["bg_editor"], pady=4, padx=4,
        ).pack(side="left")

        tk.Label(
            hdr, text=f"  {title}", font=("Segoe UI", 10, "bold"),
            bg=C["bg_surface"], fg=C["fg_text"],
        ).pack(side="left")

        self._badge = tk.Label(
            hdr, text=" ESPERANDO ", font=("Segoe UI", 8, "bold"),
            bg=C["bg_surface"], fg=C["fg_muted"], padx=8, pady=4,
        )
        self._badge.pack(side="right", padx=6)

        # ── Cuerpo con scroll ─────────────────────────────────────────
        body = tk.Frame(self, bg=C["bg_panel"])
        body.pack(fill="both", expand=True)

        sb = tk.Scrollbar(body, bg=C["bg_overlay"], troughcolor=C["bg_panel"],
                          relief="flat", width=6, bd=0)
        sb.pack(side="right", fill="y")

        self._text = make_text(
            body, font=("Consolas", 10), wrap="word",
            state="disabled", cursor="arrow", pady=8, padx=12,
            yscrollcommand=sb.set,
        )
        self._text.pack(fill="both", expand=True)
        sb.config(command=self._text.yview)

        # Tags de color
        self._text.tag_configure("ok",    foreground=C["green"])
        self._text.tag_configure("err",   foreground=C["red"])
        self._text.tag_configure("warn",  foreground=C["yellow"])
        self._text.tag_configure("token", foreground=C["blue"])
        self._text.tag_configure("node",  foreground=C["purple"])
        self._text.tag_configure("sym",   foreground=C["teal"])
        self._text.tag_configure("muted", foreground=C["fg_muted"])
        self._text.tag_configure("sub",   foreground=C["fg_sub"])
        self._text.tag_configure("code",  foreground=C["peach"])
        self._text.tag_configure("bold",  font=("Consolas", 10, "bold"))

    # ── API pública ───────────────────────────────────────────────────────────

    def reset(self):
        self._set_badge("wait")
        self._write([])

    def show_pass(self, segments: list[tuple[str, str]]):
        self._set_badge("pass")
        self._write(segments)

    def show_fail(self, segments: list[tuple[str, str]]):
        self._set_badge("fail")
        self._write(segments)

    def show_skip(self):
        self._set_badge("skip")
        self._write([
            ("Esta fase no se ejecutó porque una fase anterior falló.\n", "warn"),
            ("Corrige los errores anteriores y vuelve a compilar.", "muted"),
        ])

    # ── Internos ──────────────────────────────────────────────────────────────

    def _set_badge(self, state: str):
        text, fg, bg = self.STATES[state]
        self._badge.config(text=text, fg=fg, bg=bg)

    def _write(self, segments: list[tuple[str, str]]):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        for text, tag in segments:
            self._text.insert("end", text, tag)
        self._text.config(state="disabled")


# ── Ventana principal ────────────────────────────────────────────────────────

class MiniLangIDE(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("MiniLang IDE")
        self.configure(bg=C["bg_main"])
        self.minsize(960, 620)
        self.geometry("1280x780")
        self._build()
        self._load_example()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build(self):
        self._build_topbar()
        self._build_body()
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=C["bg_editor"], pady=10, padx=16)
        bar.pack(fill="x")

        # Logo
        tk.Label(
            bar, text="MiniLang IDE", bg=C["bg_editor"],
            fg=C["purple"], font=("Segoe UI", 15, "bold"),
        ).pack(side="left")

        tk.Label(
            bar, text="  Léxico  →  Sintáctico  →  Semántico",
            bg=C["bg_editor"], fg=C["fg_muted"], font=("Segoe UI", 10),
        ).pack(side="left", padx=8)

        # Botones
        self._btn_compile = self._btn(
            bar, "▶   Compilar", C["purple"], C["bg_editor"],
            self._compile, side="right",
        )
        self._btn(bar, "  Ejemplo  ", C["bg_overlay"], C["fg_text"],
                  self._load_example, side="right", padx=(0, 8))
        self._btn(bar, "  Limpiar  ", C["bg_overlay"], C["fg_text"],
                  self._clear, side="right", padx=(0, 6))

    def _btn(self, parent, text, bg, fg, cmd, side="left", padx=0):
        b = tk.Button(
            parent, text=text, font=("Segoe UI", 10, "bold"),
            bg=bg, fg=fg, relief="flat", cursor="hand2",
            padx=14, pady=6, command=cmd,
            activebackground=C["bg_overlay"], activeforeground=C["fg_text"],
            bd=0, highlightthickness=0,
        )
        b.pack(side=side, padx=padx)
        return b

    def _build_body(self):
        paned = tk.PanedWindow(
            self, orient="horizontal", bg=C["bg_main"],
            sashwidth=6, sashpad=0, sashrelief="flat",
            handlesize=0,
        )
        paned.pack(fill="both", expand=True, padx=8, pady=(6, 0))

        # ── Editor (izquierda) ────────────────────────────────────────
        left = make_frame(self)
        paned.add(left, minsize=360, width=520)

        make_label(left, text="EDITOR", font=("Segoe UI", 8, "bold"),
                   fg=C["fg_muted"], pady=2, anchor="w").pack(fill="x", padx=4)

        editor_wrap = tk.Frame(left, bg=C["bg_editor"], highlightthickness=1,
                               highlightbackground=C["bg_surface"])
        editor_wrap.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Números de línea
        self._ln = make_text(
            editor_wrap, width=4, font=("Consolas", 12),
            bg="#181825", fg=C["fg_muted"],
            state="disabled", cursor="arrow", pady=8,
        )
        self._ln.pack(side="left", fill="y")

        # Scrollbar vertical
        vsb = tk.Scrollbar(editor_wrap, bg=C["bg_overlay"],
                           troughcolor=C["bg_editor"], relief="flat", width=8, bd=0)
        vsb.pack(side="right", fill="y")

        # Editor de código
        self._ed = make_text(
            editor_wrap, font=("Consolas", 12), bg=C["bg_editor"],
            fg=C["fg_text"], insertbackground=C["purple"],
            wrap="none", undo=True, pady=8, padx=10,
            yscrollcommand=self._on_vscroll,
        )
        self._ed.pack(fill="both", expand=True)
        vsb.config(command=self._ed.yview)
        self._vsb = vsb

        # Tecla Ctrl+Enter = compilar
        self._ed.bind("<Control-Return>", lambda _: self._compile())
        self._ed.bind("<KeyRelease>",     self._on_key)
        self._ed.bind("<Configure>",      self._on_key)

        # Tags de resaltado de errores
        self._ed.tag_configure("err_line", background=C["bg_err"])
        self._ed.tag_configure("err_col",  background=C["bg_err_col"])

        # ── Fases (derecha) ───────────────────────────────────────────
        right = make_frame(self)
        paned.add(right, minsize=380)

        make_label(right, text="RESULTADOS DE COMPILACIÓN",
                   font=("Segoe UI", 8, "bold"),
                   fg=C["fg_muted"], pady=2, anchor="w").pack(fill="x", padx=4)

        phases = make_frame(right)
        phases.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        phases.columnconfigure(0, weight=1)
        for i in range(3):
            phases.rowconfigure(i, weight=1)

        self._p1 = PhasePanel(phases, 1, "ANÁLISIS LÉXICO")
        self._p1.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        self._p2 = PhasePanel(phases, 2, "ANÁLISIS SINTÁCTICO")
        self._p2.grid(row=1, column=0, sticky="nsew", pady=(0, 4))

        self._p3 = PhasePanel(phases, 3, "ANÁLISIS SEMÁNTICO")
        self._p3.grid(row=2, column=0, sticky="nsew")

    def _build_statusbar(self):
        self._status = tk.Label(
            self, text="Listo  —  Ctrl+Enter para compilar",
            font=("Segoe UI", 9), bg=C["bg_editor"],
            fg=C["fg_muted"], anchor="w", padx=12, pady=4,
        )
        self._status.pack(fill="x", side="bottom")

    # ── Gestión del editor ────────────────────────────────────────────────────

    def _on_vscroll(self, *args):
        self._vsb.set(*args)
        self._sync_linenos()

    def _on_key(self, _=None):
        self._update_linenos()

    def _update_linenos(self):
        content = self._ed.get("1.0", "end-1c")
        n = content.count("\n") + 1
        self._ln.config(state="normal")
        self._ln.delete("1.0", "end")
        for i in range(1, n + 1):
            self._ln.insert("end", f"{i:>3}\n")
        self._ln.config(state="disabled")
        self._sync_linenos()

    def _sync_linenos(self):
        self._ln.yview_moveto(self._ed.yview()[0])

    def _load_example(self):
        self._ed.delete("1.0", "end")
        self._ed.insert("end", EXAMPLE)
        self._update_linenos()
        self._reset_phases()
        self._status.config(text="Ejemplo cargado  —  Ctrl+Enter para compilar")

    def _clear(self):
        self._ed.delete("1.0", "end")
        self._update_linenos()
        self._reset_phases()
        self._status.config(text="Editor limpiado.")

    def _reset_phases(self):
        self._p1.reset()
        self._p2.reset()
        self._p3.reset()
        self._ed.tag_remove("err_line", "1.0", "end")
        self._ed.tag_remove("err_col",  "1.0", "end")

    # ── Compilación ───────────────────────────────────────────────────────────

    def _compile(self):
        self._reset_phases()
        source = self._ed.get("1.0", "end")
        self._btn_compile.config(state="disabled", text="  Compilando...  ")
        self._status.config(text="Compilando...")
        threading.Thread(target=self._run, args=(source,), daemon=True).start()

    def _run(self, source: str):
        """Ejecuta las 3 fases en un hilo secundario y actualiza la UI."""

        # ── FASE 1: Léxico ────────────────────────────────────────────
        rep1 = ErrorReporter()
        tokens = Lexer(source, rep1).tokenize()

        if rep1.has_errors:
            segs, positions = self._error_segments(rep1, source)
            header = [("Se encontraron errores léxicos.\n", "err"),
                      ("El lexer no pudo tokenizar parte del código.\n\n", "muted")]
            self.after(0, lambda: self._p1.show_fail(header + segs))
            self.after(0, lambda: self._p2.show_skip())
            self.after(0, lambda: self._p3.show_skip())
            self.after(0, lambda: self._mark_errors(positions))
            msg = f"LÉXICO falló  —  {len(rep1.diagnostics)} error(es). El análisis se detuvo."
            self.after(0, lambda: self._finish(msg, ok=False))
            return

        # Fase 1 OK → mostrar tokens
        segs: list[tuple[str, str]] = [
            (f"{len(tokens) - 1} tokens generados correctamente.\n\n", "ok"),
        ]
        for tok in tokens[:-1]:  # excluir EOF
            segs += [
                (f"  {tok.type.name:<22}", "token"),
                (f"  {tok.value!r:<22}", "sub"),
                (f"  L{tok.line}:C{tok.column}\n", "muted"),
            ]
        self.after(0, lambda s=segs: self._p1.show_pass(s))

        # ── FASE 2: Sintáctico ────────────────────────────────────────
        rep2 = ErrorReporter()
        program = Parser(tokens, rep2).parse()

        if rep2.has_errors:
            segs2, positions2 = self._error_segments(rep2, source)
            header2 = [("Se encontraron errores sintácticos.\n", "err"),
                       ("El parser no pudo construir el árbol AST.\n\n", "muted")]
            self.after(0, lambda: self._p2.show_fail(header2 + segs2))
            self.after(0, lambda: self._p3.show_skip())
            self.after(0, lambda: self._mark_errors(positions2))
            msg2 = f"SINTÁCTICO falló  —  {len(rep2.diagnostics)} error(es). El análisis se detuvo."
            self.after(0, lambda: self._finish(msg2, ok=False))
            return

        # Fase 2 OK → mostrar nodos del AST
        segs2 = [
            (f"AST construido con {len(program.statements)} sentencia(s).\n\n", "ok"),
        ]
        for stmt in program.statements:
            span = stmt.span
            segs2 += [
                ("  ● ", "muted"),
                (f"{type(stmt).__name__}", "node"),
                (f"   L{span.line}:C{span.column}\n", "muted"),
            ]
        self.after(0, lambda s=segs2: self._p2.show_pass(s))

        # ── FASE 3: Semántico ─────────────────────────────────────────
        rep3 = ErrorReporter()
        analyzer = SemanticAnalyzer(rep3)
        analyzer.analyze(program)

        if rep3.has_errors:
            segs3, positions3 = self._error_segments(rep3, source)
            header3 = [("Se encontraron errores semánticos.\n", "err"),
                       ("El analizador detectó problemas de tipos o nombres.\n\n", "muted")]
            self.after(0, lambda: self._p3.show_fail(header3 + segs3))
            self.after(0, lambda: self._mark_errors(positions3))
            msg3 = f"SEMÁNTICO falló  —  {len(rep3.diagnostics)} error(es)."
            self.after(0, lambda: self._finish(msg3, ok=False))
            return

        # Fase 3 OK → mostrar tabla de símbolos global
        syms = analyzer.symbols.global_scope.symbols
        segs3 = [
            ("Análisis completo sin errores.\n\n", "ok"),
            ("Tabla de símbolos (ámbito global):\n\n", "sub"),
        ]
        if syms:
            # Cabecera de tabla
            segs3 += [
                (f"  {'NOMBRE':<16}", "muted"),
                (f"{'TIPO':<10}", "muted"),
                (f"{'CLASE':<14}", "muted"),
                ("LÍNEA\n", "muted"),
                ("  " + "─" * 48 + "\n", "muted"),
            ]
            for sym in syms.values():
                segs3 += [
                    (f"  {sym.name:<16}", "sym"),
                    (f"{sym.type.value:<10}", "token"),
                    (f"{sym.kind.value:<14}", "code"),
                    (f"L{sym.declaration_span.line}\n", "muted"),
                ]
        else:
            segs3.append(("  (sin símbolos globales)\n", "muted"))

        self.after(0, lambda s=segs3: self._p3.show_pass(s))
        self.after(0, lambda: self._finish(
            "Compilación exitosa  —  Las 3 fases pasaron correctamente.", ok=True))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _error_segments(
        self, reporter: ErrorReporter, source: str
    ) -> tuple[list[tuple[str, str]], list[tuple[int, int]]]:
        """Convierte diagnósticos en segmentos de texto y lista de posiciones."""
        segs: list[tuple[str, str]] = []
        positions: list[tuple[int, int]] = []
        for d in reporter.diagnostics:
            segs += [
                (f"  [{d.code}] ", "err"),
                (f"Línea {d.line}, Columna {d.column}\n", "warn"),
                (f"  {d.message}\n", "sub"),
            ]
            # Mostrar el fragmento de código con el caret
            excerpt = d._excerpt(source)
            if excerpt:
                line_text, caret = excerpt
                segs += [
                    (f"  {line_text}\n", "code"),
                    (f"  {caret}\n\n", "err"),
                ]
            else:
                segs.append(("\n", "muted"))
            positions.append((d.line, d.column))
        return segs, positions

    def _mark_errors(self, positions: list[tuple[int, int]]):
        """Resalta las líneas y columnas con error en el editor."""
        self._ed.tag_remove("err_line", "1.0", "end")
        self._ed.tag_remove("err_col",  "1.0", "end")
        for line, col in positions:
            self._ed.tag_add("err_line", f"{line}.0", f"{line}.end")
            start_col = max(col - 1, 0)
            end_col   = col + 1
            self._ed.tag_add("err_col", f"{line}.{start_col}", f"{line}.{end_col}")
        if positions:
            self._ed.see(f"{positions[0][0]}.0")

    def _finish(self, msg: str, ok: bool):
        color = C["green"] if ok else C["red"]
        self._status.config(text=f"  {msg}", fg=color)
        self._btn_compile.config(state="normal", text="▶   Compilar")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MiniLangIDE()
    app.mainloop()
