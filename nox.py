#!/usr/bin/env python3
"""
nox — run a .nox script file.

    python nox.py <script.nox>
    python repl.py              # interactive REPL
"""
import sys
from src.lexer       import Lexer
from src.parser      import Parser
from src.interpreter import Interpreter
from src.errors      import NoxError


def run_source(source, interpreter=None):
    if interpreter is None:
        interpreter = Interpreter()
    tokens = Lexer(source).tokenize()
    ast    = Parser(tokens).parse()
    interpreter.run(ast)
    return interpreter


def main():
    if len(sys.argv) != 2:
        print("usage: python nox.py <script.nox>")
        print("       python repl.py  (for the interactive REPL)")
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path) as f:
            source = f.read()
    except FileNotFoundError:
        print(f"nox: no such file: '{path}'", file=sys.stderr)
        sys.exit(1)

    try:
        run_source(source)
    except NoxError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
