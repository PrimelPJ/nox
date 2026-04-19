#!/usr/bin/env python3
"""
nox REPL — interactive shell.

    python repl.py
"""
import sys
from src.lexer       import Lexer
from src.parser      import Parser
from src.interpreter import Interpreter
from src.errors      import NoxError

BANNER = r"""
  ███╗   ██╗ ██████╗ ██╗  ██╗
  ████╗  ██║██╔═══██╗╚██╗██╔╝
  ██╔██╗ ██║██║   ██║ ╚███╔╝
  ██║╚██╗██║██║   ██║ ██╔██╗
  ██║ ╚████║╚██████╔╝██╔╝ ██╗
  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝

  a small language that fits in your pocket
  type 'exit' to quit · python 3.8+
"""


def main():
    print(BANNER)
    interpreter = Interpreter()

    while True:
        try:
            line = input('nox> ')
        except (EOFError, KeyboardInterrupt):
            print('\nbye.')
            break

        stripped = line.strip()
        if not stripped:
            continue
        if stripped in ('exit', 'quit'):
            print('bye.')
            break

        try:
            tokens = Lexer(line).tokenize()
            ast    = Parser(tokens).parse()
            interpreter.run(ast)
        except NoxError as e:
            print(f'  error: {e}')


if __name__ == '__main__':
    main()
