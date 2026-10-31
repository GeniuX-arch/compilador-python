# MiniLang

MiniLang es un lenguaje educativo y tipado estáticamente, junto con un compilador implementado manualmente en Python 3.12+. El proyecto se construirá por fases: lexer, parser y AST, análisis semántico, diagnósticos, representación intermedia y, posteriormente, generación de código objetivo.

La especificación formal de la primera versión está en [docs/minilang-spec.md](docs/minilang-spec.md). Durante la Fase 0 no se implementa todavía ningún componente ejecutable.

## Estado del proyecto

- Fase 0: diseño y especificación, completada en `docs/minilang-spec.md`.
- Fase 1: lexer manual, diagnósticos léxicos y pruebas, completada.
- Fase 2: parser recursive descent, AST, recuperación sintáctica y pruebas, completada.
- Fase 3: tabla de símbolos, ámbitos, tipos y análisis semántico, completada.
- Fase 4: diagnósticos centralizados, formato localizado y pruebas, completada.
- Fase 5: representación intermedia TAC, temporales, etiquetas y pruebas, completada.
- Fase 6: máquina virtual objetivo para ejecutar la IR, completada.

## Principios

- Cada fase tiene una responsabilidad independiente.
- El parser construye un AST; no realiza validación semántica.
- El análisis semántico trabaja sobre el AST, no sobre texto fuente.
- La IR solo se genera para programas sin errores previos.
- No se utilizarán generadores automáticos de parsers ni `eval()` o `exec()`.

## Próximo paso

Las fases principales del compilador están implementadas. Las siguientes mejoras pueden centrarse en una interfaz `Compiler` de extremo a extremo, ejemplos ejecutables y ampliaciones del lenguaje.
