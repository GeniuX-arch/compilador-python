# Especificación de MiniLang v1

## 1. Propósito y alcance

MiniLang v1 es un lenguaje imperativo pequeño, con tipos estáticos, bloques anidados y funciones. Su objetivo es servir como contrato estable para implementar manualmente el compilador educativo.

El flujo de compilación será:

```text
fuente -> lexer -> tokens -> parser -> AST -> análisis semántico -> IR
```

La v1 incluye:

- tipos `int`, `float`, `string` y `bool`;
- declaraciones locales y globales con inicialización obligatoria;
- reasignación mediante `=`;
- expresiones aritméticas, relacionales, de igualdad y lógicas;
- bloques, `if`, `else`, `while` y `for`;
- funciones con parámetros tipados y tipo de retorno;
- `return` y `print`;
- comentarios de línea y de bloque;
- diagnósticos con ubicación de origen.

La v1 no incluye `break`, `continue`, arrays, objetos, operadores ternarios, `null`, sobrecarga, clases, `void` ni conversiones explícitas. Se podrán añadir en versiones posteriores sin cambiar el contrato de las fases existentes.

## 2. Decisiones que corrigen ambigüedades

1. La lista aritmética incompleta se corrige a `+`, `-`, `*`, `/` y `%`.
2. Una declaración siempre exige inicializador: `int edad = 21;`. Esto mantiene la regla inicial `TYPE IDENTIFIER ASSIGN EXPRESSION SEMICOLON` y evita un estado no inicializado en v1.
3. `for` usa sintaxis C: `for (inicializador; condición; actualización) bloque`. El inicializador puede ser una declaración o una asignación; sus tres partes son obligatorias en v1.
4. Una función se declara como `function T nombre(parámetros) bloque`, donde `T` es un tipo de retorno. No existe `void` en v1.
5. Las asignaciones son sentencias y no expresiones. Por tanto, `a = b = 1` no es válido y no hay asignaciones dentro de expresiones.
6. `print` es una sentencia con una expresión: `print(valor);`.
7. Los operadores `&&` y `||` tienen evaluación de cortocircuito. La IR deberá conservar ese comportamiento mediante saltos.
8. Las llaves crean un ámbito léxico para bloques. El ámbito de un `for` incluye su inicializador, condición, actualización y cuerpo.

## 3. Alfabeto léxico

El lexer consume Unicode como texto de Python, pero las reglas del lenguaje para identificadores son ASCII en v1:

```text
letra        = "A".."Z" | "a".."z" | "_" ;
dígito       = "0".."9" ;
identificador = letra, { letra | dígito } ;
```

Los espacios, tabuladores, retornos de carro y saltos de línea separan tokens y se ignoran, excepto para actualizar línea y columna. Los comentarios también se descartan:

- `//` hasta el siguiente salto de línea;
- `/*` hasta el primer `*/`, incluso atravesando líneas.

Un comentario de bloque sin cierre es un error léxico.

### 3.1. Palabras reservadas

| Texto | Token | Uso |
|---|---|---|
| `int` | `INT` | tipo entero |
| `float` | `FLOAT` | tipo decimal |
| `string` | `STRING` | tipo cadena |
| `bool` | `BOOL` | tipo booleano |
| `true` | `TRUE` | literal booleano |
| `false` | `FALSE` | literal booleano |
| `if` | `IF` | selección |
| `else` | `ELSE` | alternativa |
| `while` | `WHILE` | bucle |
| `for` | `FOR` | bucle C |
| `function` | `FUNCTION` | declaración de función |
| `return` | `RETURN` | retorno |
| `print` | `PRINT` | salida |

Una palabra reservada nunca produce `IDENTIFIER`.

### 3.2. Literales

| Forma | Token | Valor semántico |
|---|---|---|
| `0` o `[1-9][0-9]*` | `INTEGER_LITERAL` | `int` |
| `0.0` o `[0-9]+\.[0-9]+` | `FLOAT_LITERAL` | `float` |
| `"..."` | `STRING_LITERAL` | `string` |
| `true` / `false` | `TRUE` / `FALSE` | `bool` |

Los enteros no llevan signo: el signo es un operador unario. Los decimales deben contener dígitos a ambos lados del punto; `.5`, `5.` y notación científica no pertenecen a v1. Las cadenas usan comillas dobles y permiten `\\`, `\"`, `\n` y `\t`. Una cadena sin cierre es un error léxico.

El lexer debe usar maximal munch para elegir `==` antes que `=`, `!=` antes que `!`, `>=` antes que `>`, `<=` antes que `<`, `&&` antes que `&` y `||` antes que `|`.

### 3.3. Tabla completa de tokens

| Categoría | Lexemas | Tokens |
|---|---|---|
| Tipos | `int`, `float`, `string`, `bool` | `INT`, `FLOAT`, `STRING`, `BOOL` |
| Control | `if`, `else`, `while`, `for` | `IF`, `ELSE`, `WHILE`, `FOR` |
| Funciones | `function`, `return`, `print` | `FUNCTION`, `RETURN`, `PRINT` |
| Booleanos | `true`, `false` | `TRUE`, `FALSE` |
| Identificador | patrón de identificador | `IDENTIFIER` |
| Literales | entero, decimal, cadena | `INTEGER_LITERAL`, `FLOAT_LITERAL`, `STRING_LITERAL` |
| Aritméticos | `+ - * / %` | `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `MODULO` |
| Relacionales | `> < >= <=` | `GREATER`, `LESS`, `GREATER_EQUAL`, `LESS_EQUAL` |
| Igualdad | `== !=` | `EQUAL_EQUAL`, `NOT_EQUAL` |
| Lógicos | `&& || !` | `AND`, `OR`, `NOT` |
| Asignación | `=` | `ASSIGN` |
| Delimitadores | `; , ( ) { }` | `SEMICOLON`, `COMMA`, `LEFT_PAREN`, `RIGHT_PAREN`, `LEFT_BRACE`, `RIGHT_BRACE` |
| Fin | fin de fuente | `EOF` |

No se reconocen otros caracteres. Un carácter aislado `&` o `|` es un error léxico, no un operador válido.

## 4. Gramática EBNF

Las producciones siguientes describen la sintaxis de v1. La notación `{ X }` significa cero o más repeticiones, `[ X ]` una parte opcional y las comillas representan tokens por su lexema.

```ebnf
program             = { variable_declaration | function_declaration
                      | non_declaration_statement } ;

declaration         = variable_declaration | function_declaration ;

variable_declaration = type, identifier, "=", expression, ";" ;

function_declaration = "function", type, identifier, "(", [ parameter_list ], ")", block ;
parameter_list      = parameter, { ",", parameter } ;
parameter           = type, identifier ;

type                = "int" | "float" | "string" | "bool" ;
identifier          = IDENTIFIER ;

statement           = variable_declaration | non_declaration_statement ;
non_declaration_statement = assignment_statement
                    | if_statement
                    | while_statement
                    | for_statement
                    | return_statement
                    | print_statement
                    | expression_statement
                    | block ;

assignment_statement = identifier, "=", expression, ";" ;

if_statement        = "if", "(", expression, ")", statement,
                      [ "else", statement ] ;
while_statement     = "while", "(", expression, ")", statement ;

for_statement       = "for", "(", for_initializer, ";", expression,
                      ";", assignment, ")", statement ;
for_initializer     = variable_declaration_no_semicolon | assignment ;
variable_declaration_no_semicolon = type, identifier, "=", expression ;
assignment          = identifier, "=", expression ;

return_statement    = "return", expression, ";" ;
print_statement     = "print", "(", expression, ")", ";" ;
expression_statement = expression, ";" ;
block               = "{", { variable_declaration | function_declaration
                              | non_declaration_statement }, "}" ;

expression          = logical_or ;
logical_or          = logical_and, { "||", logical_and } ;
logical_and         = equality, { "&&", equality } ;
equality            = comparison, { ( "==" | "!=" ), comparison } ;
comparison          = additive, { ( ">" | "<" | ">=" | "<=" ), additive } ;
additive            = multiplicative, { ( "+" | "-" ), multiplicative } ;
multiplicative      = unary, { ( "*" | "/" | "%" ), unary } ;
unary               = [ "!" | "-" | "+" ], unary | primary ;
primary             = INTEGER_LITERAL
                    | FLOAT_LITERAL
                    | STRING_LITERAL
                    | "true"
                    | "false"
                    | function_call
                    | identifier_expression
                    | "(", expression, ")" ;
identifier_expression = IDENTIFIER ;
function_call       = IDENTIFIER, "(", [ argument_list ], ")" ;
argument_list       = expression, { ",", expression } ;
```

Notas de desambiguación:

- `function_call` se reconoce cuando un identificador va seguido de `(`; no se permiten llamadas a expresiones arbitrarias.
- La alternativa `declaration` en `program` y `block` permite funciones y variables. El análisis semántico decidirá si una declaración de función es válida en el contexto concreto; la primera implementación puede restringir las funciones a nivel global y reportarlo como error semántico fuera de ese ámbito.
- `if`, `while` y `for` reciben cualquier `statement`, por lo que una sola sentencia no necesita llaves. Las llaves son necesarias para agrupar varias sentencias.
- `return` siempre lleva expresión porque v1 no tiene `void`.
- El cuerpo de una función es un `block`; sus parámetros entran en el ámbito de ese cuerpo.

## 5. Precedencia y asociatividad

De mayor a menor precedencia:

| Nivel | Operadores | Asociatividad |
|---:|---|---|
| 8 | `()` | agrupación |
| 7 | `!`, `+`, `-` unarios | derecha |
| 6 | `*`, `/`, `%` | izquierda |
| 5 | `+`, `-` binarios | izquierda |
| 4 | `>`, `<`, `>=`, `<=` | izquierda |
| 3 | `==`, `!=` | izquierda |
| 2 | `&&` | izquierda |
| 1 | `||` | izquierda |

La gramática elimina la ambigüedad mediante un método de parser por nivel: `parse_logical_or`, `parse_logical_and`, `parse_equality`, `parse_comparison`, `parse_additive`, `parse_multiplicative`, `parse_unary` y `parse_primary`. Los operadores binarios se representan con `BinaryExpression`; los unarios con `UnaryExpression`.

## 6. Modelo del AST

Todos los nodos conservan un `SourceSpan` con posición inicial y final. La ubicación se utiliza para diagnósticos y no cambia la semántica.

### Sentencias y declaraciones

- `Program(declarations_and_statements)`
- `VariableDeclaration(type_name, name, initializer)`
- `Assignment(name, value)`
- `ExpressionStatement(expression)`
- `BlockStatement(statements)`
- `IfStatement(condition, then_branch, else_branch?)`
- `WhileStatement(condition, body)`
- `ForStatement(initializer, condition, update, body)`
- `FunctionDeclaration(name, parameters, return_type, body)`
- `ReturnStatement(value)`
- `PrintStatement(value)`

### Expresiones

- `BinaryExpression(left, operator, right)`
- `UnaryExpression(operator, operand)`
- `Literal(value, type)`
- `Identifier(name)`
- `FunctionCall(name, arguments)`

El lexer no construye nodos y el parser no asigna tipos semánticos. El campo `type` de `Literal` describe únicamente el tipo intrínseco del literal; el resto de tipos se resuelve en análisis semántico.

## 7. Reglas semánticas

### 7.1. Tipos y valores

| Tipo | Valores |
|---|---|
| `int` | enteros con signo |
| `float` | números de punto flotante |
| `string` | cadenas |
| `bool` | `true` o `false` |

No hay valor nulo en v1. La división `/` produce `float` si alguno de sus operandos es `float`; la división entre dos `int` produce `int` mediante división entera. El comportamiento de división por cero es un diagnóstico semántico si puede determinarse durante el análisis, y un error de ejecución de la futura máquina objetivo en caso contrario.

### 7.2. Compatibilidad de asignación

La asignación es válida cuando:

| Desde | Hacia | Resultado |
|---|---|---|
| `int` | `int` | permitido |
| `float` | `float` | permitido |
| `string` | `string` | permitido |
| `bool` | `bool` | permitido |
| `int` | `float` | permitido, conversión implícita a `float` |
| cualquier otro par | | error `SEM_TYPE_MISMATCH` |

No se permite conversión implícita de `float` a `int`, ni entre tipos numéricos y `bool` o `string`.

### 7.3. Operadores

- `+`, `-`, `*`: aceptan dos operandos numéricos; el resultado es `int` si ambos son `int`, y `float` en otro caso. `+` también concatena dos `string` y devuelve `string`.
- `/`: acepta dos operandos numéricos y devuelve `int` si ambos son `int`, o `float` en otro caso.
- `%`: acepta dos operandos `int` y devuelve `int`.
- Comparaciones `<`, `>`, `<=`, `>=`: aceptan dos operandos numéricos compatibles y devuelven `bool`.
- Igualdad `==`, `!=`: acepta operandos del mismo tipo o `int`/`float` en cualquier orden; devuelve `bool`. No compara `string` con números.
- `&&`, `||`: exigen dos `bool` y devuelven `bool`.
- `!`: exige `bool` y devuelve `bool`.
- `+` y `-` unarios: exigen un operando numérico y conservan su tipo.

No se aplican conversiones implícitas arbitrarias dentro de operaciones. El análisis semántico debe emitir un error en `10 + "Hola"`, `!1` o `true < false`.

### 7.4. Declaraciones, uso y asignaciones

- Una variable debe declararse antes de usarse en el orden de análisis.
- No puede haber dos símbolos con el mismo nombre en el mismo ámbito.
- Un ámbito interno puede sombrear un nombre de un ámbito externo. El nombre interno gana dentro de ese ámbito y el externo permanece visible después de salir.
- Una asignación solo puede dirigirse a una variable existente, nunca a una función.
- El inicializador se analiza antes de completar la declaración, por lo que `int x = x;` es uso antes de declaración.
- Las funciones se registran en el ámbito global antes de analizar sus cuerpos, permitiendo llamadas recursivas y llamadas a funciones declaradas más adelante. Sus cuerpos se validan después de registrar sus firmas.

### 7.5. Control de flujo

- La condición de `if`, `while` y `for` debe ser `bool`.
- Cada bloque crea un ámbito nuevo.
- El ámbito creado para el `for` cubre su inicializador, condición, actualización y cuerpo.
- La actualización del `for` es una asignación simple; no puede ser una declaración ni una llamada en v1.
- No se exige análisis de rutas de retorno en la primera implementación. Una función no `void` debe contener al menos un `return` compatible; en futuras versiones se podrá exigir retorno en todas las rutas.

### 7.6. Funciones

- Las funciones tienen nombre único en el ámbito global.
- Los parámetros tienen tipo y se comportan como variables locales del cuerpo.
- No se permiten parámetros duplicados.
- Una llamada debe referirse a una función declarada y usar exactamente la cantidad de argumentos declarada.
- Cada argumento debe ser asignable al tipo de su parámetro, aplicando solo `int` a `float`.
- El valor de cada `return` debe ser asignable al tipo de retorno de la función.
- `return` fuera de una función es un error.
- Las funciones no son valores: no se pueden asignar ni pasar como argumentos.

### 7.7. `print`

`print` recibe exactamente una expresión de cualquier tipo v1 y no produce un valor. La validación de salida o formato queda fuera del análisis semántico.

## 8. Diagnósticos

El sistema común de diagnósticos tendrá categoría, código, severidad, mensaje y `SourceSpan`. Los errores de fuente no deben detener necesariamente la recopilación de diagnósticos cuando la recuperación sea segura.

Códigos mínimos previstos:

| Fase | Código | Situación |
|---|---|---|
| Léxica | `LEX001` | carácter no reconocido |
| Léxica | `LEX002` | cadena sin cerrar |
| Léxica | `LEX003` | comentario de bloque sin cerrar |
| Léxica | `LEX004` | literal numérico inválido |
| Sintáctica | `SYN001` | token inesperado |
| Sintáctica | `SYN002` | token esperado ausente |
| Sintáctica | `SYN003` | expresión incompleta |
| Semántica | `SEM001` | variable o función no declarada |
| Semántica | `SEM002` | declaración duplicada |
| Semántica | `SEM003` | incompatibilidad de tipos |
| Semántica | `SEM004` | condición no booleana |
| Semántica | `SEM005` | llamada con firma inválida |
| Semántica | `SEM006` | retorno inválido |
| Semántica | `SEM007` | uso de asignación inválida |
| Interna | `INT001` | estado imposible del compilador |

El lexer avanzará hasta un punto de sincronización después de un carácter inválido o una cadena problemática. El parser sincronizará en `;`, `}` o el inicio de una declaración conocida. La recuperación no debe inventar nodos semánticamente válidos; cuando no pueda continuar con seguridad, descartará la sentencia dañada y seguirá recopilando diagnósticos.

## 9. Arquitectura del compilador

La estructura objetivo es:

```text
minilang/
├── main.py
├── pyproject.toml
├── README.md
├── docs/
│   └── minilang-spec.md
├── examples/
│   ├── valid/
│   └── invalid/
├── lexer/
│   ├── __init__.py
│   ├── lexer.py
│   ├── token.py
│   └── token_type.py
├── parser/
│   ├── __init__.py
│   ├── parser.py
│   └── ast_nodes.py
├── semantic/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── symbol_table.py
│   ├── symbol.py
│   ├── types.py
│   ├── scope.py
│   └── type_checker.py
├── diagnostics/
│   ├── __init__.py
│   ├── compiler_error.py
│   ├── diagnostic.py
│   └── error_reporter.py
├── ir/
│   ├── __init__.py
│   ├── instructions.py
│   ├── generator.py
│   └── temporary.py
├── utils/
│   ├── __init__.py
│   └── source_reader.py
└── tests/
    ├── lexer/
    ├── parser/
    ├── semantic/
    ├── ir/
    └── integration/
```

Responsabilidades:

- `lexer`: recorre caracteres y produce tokens con valor y posición. No conoce AST ni tipos semánticos.
- `parser`: consume tokens con recursive descent y produce AST. No consulta la tabla de símbolos.
- `parser/ast_nodes.py`: define únicamente las estructuras sintácticas y sus ubicaciones.
- `semantic`: administra ámbitos y símbolos, resuelve nombres, verifica tipos y valida reglas contextuales.
- `diagnostics`: define diagnósticos y errores internos con formato común.
- `ir`: transforma AST semánticamente válido en instrucciones de tres direcciones, temporales y etiquetas.
- `utils`: lectura de archivos y metadatos de fuente.
- `main.py`: interfaz mínima y coordinación; la compilación se expondrá mediante una función `compile_source(source)` o una clase `Compiler`, sin mezclarla con impresión de consola.

Dependencias permitidas para v1: biblioteca estándar de Python y `pytest` para pruebas. No se usarán ANTLR, Lark, PLY ni equivalentes.

## 10. Criterios de aceptación por fase

### Fase 0: especificación

- La gramática cubre cada construcción de v1 y no contiene alternativas ambiguas conocidas.
- Cada lexema de la gramática tiene un token definido.
- La precedencia y asociatividad coinciden con la gramática.
- Las reglas de tipos, ámbitos, funciones y diagnósticos están documentadas.
- El AST previsto puede representar todas las producciones sintácticas.
- No se inicia código del lexer antes de revisar esta especificación.

### Fase 1: lexer

- Reconoce palabras reservadas, identificadores, literales, operadores y delimitadores.
- Aplica maximal munch y emite `EOF`.
- Conserva línea, columna, posición inicial y final.
- Reporta caracteres inválidos, números inválidos, cadenas y comentarios sin cerrar.
- Tiene pruebas unitarias de tokens, posiciones, comentarios y errores.

### Fase 2: parser y AST

- Implementa recursive descent por niveles de precedencia.
- Produce nodos estructurados, nunca expresiones como texto.
- Acepta programas válidos de variables, control de flujo y funciones.
- Reporta errores sintácticos localizados y recupera cuando sea seguro.
- Tiene pruebas de precedencia, asociatividad, agrupación y delimitadores.

### Fase 3: semántica

- Gestiona símbolos, ámbitos anidados y sombreado.
- Detecta uso antes de declaración y duplicados.
- Verifica asignaciones, operaciones, condiciones, llamadas y retornos.
- Aplica únicamente la conversión `int` a `float`.
- Tiene pruebas unitarias y de integración para cada categoría.

### Fase 4: diagnósticos

- Usa una estructura común para errores léxicos, sintácticos y semánticos.
- Incluye código, categoría, severidad, mensaje y ubicación.
- Distingue errores de fuente de errores internos.
- Puede mostrar múltiples diagnósticos sin errores secundarios excesivos.

### Fase 5: IR

- Solo se ejecuta tras un análisis semántico exitoso.
- Genera instrucciones de tres direcciones para declaraciones, asignaciones, expresiones, comparaciones, saltos, llamadas y retornos.
- Usa temporales y etiquetas deterministas en las pruebas.
- Conserva cortocircuito de `&&` y `||`.

### Fase 6: código objetivo

- Es independiente de lexer, parser y analizador semántico.
- No ejecuta fuente arbitraria mediante `eval()` o `exec()`.
- Conserva el comportamiento validado por la IR.

## 11. Casos de referencia

Programa válido:

```minilang
int edad = 21;
float altura = 1.88;
string nombre = "Carlos";
bool activo = true;
int resultado = edad + 10;

function int duplicar(int valor) {
    return valor * 2;
}

if (activo && edad > 18) {
    print(nombre);
} else {
    print("inactivo");
}
```

Errores que deben reconocerse en fases distintas:

```minilang
int edad = 10 @;                 // LEX001
int incompleta = 10 + ;          // SYN003
int texto = "Carlos";            // SEM003
int resultado = desconocida + 10; // SEM001
int suma = 10 + "Hola";          // SEM003
if (10) { print("Hola"); }       // SEM004
```

## 12. Decisiones pendientes para versiones futuras

- Si se añade `void` y cómo se expresan funciones sin retorno.
- Si la división entera debe truncar hacia cero o si `/` debe producir siempre `float`.
- Arrays y acceso indexado.
- `break` y `continue`.
- Análisis de retorno en todas las rutas.
- Conversión explícita y nuevos tipos.
- Formato exacto de la futura generación de código objetivo.
