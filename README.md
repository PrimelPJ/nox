# nox

```
  ███╗   ██╗ ██████╗ ██╗  ██╗
  ████╗  ██║██╔═══██╗╚██╗██╔╝
  ██╔██╗ ██║██║   ██║ ╚███╔╝
  ██║╚██╗██║██║   ██║ ██╔██╗
  ██║ ╚████║╚██████╔╝██╔╝ ██╗
  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
```

A dynamically-typed, interpreted programming language built from scratch in Python.
Nox has first-class functions, lexical scoping, and closures — implemented in ~700 lines
of hand-written interpreter code with no parsing libraries.

---

## Quick look

```nox
# Closures — functions that remember where they were born

fn make_counter(start) {
    let count = start
    fn tick() {
        count = count + 1
        return count
    }
    return tick
}

let c1 = make_counter(0)
let c2 = make_counter(100)

print(c1())   # 1
print(c1())   # 2
print(c2())   # 101  — independent state
print(c1())   # 3    — unaffected by c2
```

```nox
# Higher-order functions and anonymous fn expressions

fn apply_n(n, func) {
    let i = 0
    while i < n {
        print(func(i))
        i = i + 1
    }
}

apply_n(5, fn(x) { return x * x * x })   # cubes: 0 1 8 27 64
```

---

## How it works

Source text passes through three stages before anything runs:

```
source text
    │
    ▼
┌─────────┐    tokens     ┌─────────┐     AST       ┌─────────────┐
│  Lexer  │ ────────────► │ Parser  │ ────────────► │ Interpreter │ → output
└─────────┘               └─────────┘               └─────────────┘
src/lexer.py           src/parser.py            src/interpreter.py
```

**Lexer** (`src/lexer.py`) — walks the source character by character and
emits a flat list of typed tokens.  Handles comments, string literals,
multi-character operators (`==`, `!=`, `<=`, `>=`), and newline-as-statement-separator.

**Parser** (`src/parser.py`) — a hand-written recursive descent parser that
consumes the token stream and builds an Abstract Syntax Tree (AST).  Operator
precedence is encoded directly in the call hierarchy (no Pratt parser, no
grammar tables).

**AST nodes** (`src/ast_nodes.py`) — plain Python dataclasses, one per
language construct: `LetStmt`, `FnDecl`, `IfStmt`, `WhileStmt`, `BinOp`,
`Call`, `FnExpr`, etc.

**Interpreter** (`src/interpreter.py`) — a tree-walk evaluator that
recursively visits every node and executes it.  Closures work because
each `NoxFunction` captures the `Environment` it was defined in, not the
one it's called from.

**Environment** (`src/environment.py`) — a linked chain of scope frames.
Variable lookup and assignment walk the chain upward, which is what allows
inner functions to read and mutate variables in their enclosing scopes.

---

## Language reference

### Variables
```nox
let x = 42
let name = "nox"
let flag = true
let nothing = nil

x = x + 1      # reassignment (no 'let')
```

### Types
| Type    | Examples              |
|---------|-----------------------|
| number  | `0`, `3.14`, `-7`    |
| string  | `"hello"`, `'world'` |
| boolean | `true`, `false`       |
| nil     | `nil`                 |
| fn      | `fn(x) { return x }` |

### Operators
```nox
# arithmetic
x + y    x - y    x * y    x / y    x % y

# comparison
x == y   x != y   x < y   x <= y   x > y   x >= y

# logical (short-circuit)
x and y   x or y   not x

# string concatenation (auto-cast)
"score: " + 99   # → "score: 99"
```

### Control flow
```nox
if x > 10 {
    print("big")
} elif x > 5 {
    print("mid")
} else {
    print("small")
}

let i = 0
while i < 5 {
    print(i)
    i = i + 1
}
```

### Functions
```nox
# named declaration
fn add(a, b) {
    return a + b
}

# anonymous expression (first-class value)
let double = fn(x) { return x * 2 }

# functions are values — pass them around
fn apply(f, x) { return f(x) }
print(apply(double, 21))    # 42
```

### Closures
```nox
fn make_adder(n) {
    return fn(x) { return x + n }
}

let add10 = make_adder(10)
let add25 = make_adder(25)

print(add10(5))    # 15
print(add25(5))    # 30
```

Each call to `make_adder` creates a fresh scope.  The returned function
closes over that scope and keeps it alive.  `add10` and `add25` are
completely independent.

### Recursion
```nox
fn fibonacci(n) {
    if n <= 1 { return n }
    return fibonacci(n - 1) + fibonacci(n - 2)
}

print(fibonacci(10))    # 55
```

---

## Getting started

Requires Python 3.8+.  No dependencies.

```bash
git clone https://github.com/YOUR_USERNAME/nox
cd nox

# run a script
python nox.py examples/fibonacci.nox

# interactive REPL
python repl.py

# run the test suite
python -m pytest tests/ -v
```

---

## Project structure

```
nox/
├── src/
│   ├── lexer.py          tokenizer — source text → token stream
│   ├── parser.py         recursive descent parser → AST
│   ├── ast_nodes.py      dataclass definitions for every AST node
│   ├── interpreter.py    tree-walk evaluator — executes the AST
│   ├── environment.py    lexical scope frames with parent-chain lookup
│   └── errors.py         LexError · ParseError · NoxRuntimeError
├── examples/
│   ├── fibonacci.nox     recursive fibonacci sequence
│   ├── fizzbuzz.nox      fizzbuzz via if/elif/else chains
│   ├── closures.nox      independent counter closures
│   ├── higher_order.nox  first-class fns, currying, anonymous exprs
│   └── strings.nox       string ops, booleans, nil
├── tests/
│   ├── test_lexer.py     token-level unit tests
│   └── test_interpreter.py end-to-end output tests
├── nox.py                CLI entry point
└── repl.py               interactive REPL with persistent state
```

---

## Test suite

```
$ python -m pytest tests/ -v

tests/test_interpreter.py::TestArithmetic::test_add          PASSED
tests/test_interpreter.py::TestArithmetic::test_precedence   PASSED
tests/test_interpreter.py::TestBooleans::test_short_circuit  PASSED
tests/test_interpreter.py::TestClosures::test_make_adder     PASSED
tests/test_interpreter.py::TestClosures::test_counter_independence  PASSED
tests/test_interpreter.py::TestClosures::test_anonymous_fn   PASSED
tests/test_interpreter.py::TestRecursion::test_fibonacci     PASSED
tests/test_interpreter.py::TestRecursion::test_factorial     PASSED
... (57 tests total)

57 passed in 0.37s
```

---

## Error messages

Nox reports errors with line numbers and specific descriptions:

```
# undefined variable
print(z)
Error: [line 1] undefined variable 'z'

# wrong number of arguments
fn f(x) { return x }
f(1, 2)
Error: [line 2] f() expects 1 argument(s) but got 2

# division by zero
print(10 / 0)
Error: [line 1] division by zero

# type error
print("hello" - 1)
Error: [line 1] expected a number but got str ('hello')
```

---

## Extending nox

The codebase is designed to be extended.  Each new feature touches exactly
the right files and nothing else:

| Feature | Files to touch |
|---------|---------------|
| New operator | `lexer.py` (token) · `parser.py` (precedence level) · `interpreter.py` (eval) |
| New statement | `ast_nodes.py` (node) · `parser.py` (`_statement`) · `interpreter.py` (`_exec_*`) |
| Built-in function | `interpreter.py` (add a `NoxBuiltin` class + call dispatch) |
| Arrays / lists | `ast_nodes.py` · `parser.py` (literal syntax) · `interpreter.py` (runtime type) |
| Bytecode VM | Add `compiler.py` (AST → bytecode) · `vm.py` (stack machine) |

Suggested next steps: arrays, a `for x in list` loop, built-in functions
(`len`, `type`, `str`, `num`), and a bytecode compiler + stack VM instead
of tree-walking.

---

## References

- [Crafting Interpreters](https://craftinginterpreters.com) — Robert Nystrom
- [Writing an Interpreter in Go](https://interpreterbook.com) — Thorsten Ball
- [Structure and Interpretation of Computer Programs](https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pubs/6515/sicp.zip/index.html)

---

*Built from scratch. No parsing libraries. No external dependencies.*
