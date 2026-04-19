from enum import Enum, auto
from .errors import LexError


class TT(Enum):
    # Literals
    NUMBER  = auto()
    STRING  = auto()
    IDENT   = auto()

    # Keywords
    LET     = auto()
    FN      = auto()
    IF      = auto()
    ELIF    = auto()
    ELSE    = auto()
    WHILE   = auto()
    RETURN  = auto()
    TRUE    = auto()
    FALSE   = auto()
    NIL     = auto()
    AND     = auto()
    OR      = auto()
    NOT     = auto()
    PRINT   = auto()

    # Operators
    PLUS    = auto()
    MINUS   = auto()
    STAR    = auto()
    SLASH   = auto()
    PERCENT = auto()
    EQ      = auto()   # =
    EQEQ    = auto()   # ==
    BANGEQ  = auto()   # !=
    LT      = auto()   # <
    LTEQ    = auto()   # <=
    GT      = auto()   # >
    GTEQ    = auto()   # >=

    # Delimiters
    LPAREN  = auto()
    RPAREN  = auto()
    LBRACE  = auto()
    RBRACE  = auto()
    COMMA   = auto()
    NEWLINE = auto()
    SEMI    = auto()

    EOF     = auto()


KEYWORDS = {
    'let':    TT.LET,
    'fn':     TT.FN,
    'if':     TT.IF,
    'elif':   TT.ELIF,
    'else':   TT.ELSE,
    'while':  TT.WHILE,
    'return': TT.RETURN,
    'true':   TT.TRUE,
    'false':  TT.FALSE,
    'nil':    TT.NIL,
    'and':    TT.AND,
    'or':     TT.OR,
    'not':    TT.NOT,
    'print':  TT.PRINT,
}


class Token:
    def __init__(self, type, value, line):
        self.type  = type
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type.name}, {self.value!r}, line={self.line})'


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.tokens = []

    # ── helpers ──────────────────────────────────────────────────────────────

    def _error(self, msg):
        raise LexError(f'[line {self.line}] {msg}')

    def _peek(self, offset=0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else '\0'

    def _advance(self):
        c = self.source[self.pos]
        self.pos += 1
        if c == '\n':
            self.line += 1
        return c

    def _match(self, expected):
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.pos += 1
            return True
        return False

    def _add(self, type, value=None):
        self.tokens.append(Token(type, value, self.line))

    # ── public ────────────────────────────────────────────────────────────────

    def tokenize(self):
        while self.pos < len(self.source):
            self._scan_token()
        self._add(TT.EOF)
        return self.tokens

    # ── scanning ──────────────────────────────────────────────────────────────

    def _scan_token(self):
        c = self._advance()

        if c in ' \t\r':
            return

        if c == '#':                                  # line comment
            while self._peek() not in ('\n', '\0'):
                self._advance()
            return

        if c == '\n':
            # emit NEWLINE only after a meaningful token (statement separator)
            if self.tokens and self.tokens[-1].type not in (
                TT.NEWLINE, TT.LBRACE, TT.RBRACE, TT.COMMA, TT.SEMI, TT.EOF
            ):
                self._add(TT.NEWLINE)
            return

        single = {
            '+': TT.PLUS,  '-': TT.MINUS, '*': TT.STAR,
            '/': TT.SLASH, '%': TT.PERCENT,
            '(': TT.LPAREN, ')': TT.RPAREN,
            '{': TT.LBRACE, '}': TT.RBRACE,
            ',': TT.COMMA,  ';': TT.SEMI,
        }
        if c in single:
            self._add(single[c])
            return

        if c == '=':
            self._add(TT.EQEQ if self._match('=') else TT.EQ)
            return
        if c == '!':
            if self._match('='):
                self._add(TT.BANGEQ)
            else:
                self._error("unexpected character '!'")
            return
        if c == '<':
            self._add(TT.LTEQ if self._match('=') else TT.LT)
            return
        if c == '>':
            self._add(TT.GTEQ if self._match('=') else TT.GT)
            return

        if c in ('"', "'"):
            self._string(c)
            return
        if c.isdigit():
            self._number()
            return
        if c.isalpha() or c == '_':
            self._identifier()
            return

        self._error(f"unexpected character '{c}'")

    def _string(self, quote):
        start = self.pos
        while self._peek() != quote and self._peek() != '\0':
            if self._peek() == '\n':
                self._error('unterminated string')
            self._advance()
        if self._peek() == '\0':
            self._error('unterminated string')
        self._advance()                               # closing quote
        self._add(TT.STRING, self.source[start:self.pos - 1])

    def _number(self):
        start = self.pos - 1
        while self._peek().isdigit():
            self._advance()
        if (self._peek() == '.'
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1].isdigit()):
            self._advance()                           # consume '.'
            while self._peek().isdigit():
                self._advance()
        self._add(TT.NUMBER, float(self.source[start:self.pos]))

    def _identifier(self):
        start = self.pos - 1
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        text = self.source[start:self.pos]
        self._add(KEYWORDS.get(text, TT.IDENT), text)
