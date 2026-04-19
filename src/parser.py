from .lexer   import TT
from .ast_nodes import *
from .errors   import ParseError


class Parser:
    """
    Recursive descent parser.

    Precedence (lowest → highest):
        assignment  (right-assoc)
        or
        and
        equality    == !=
        comparison  < <= > >=
        term        + -
        factor      * / %
        unary       - not
        call        expr(args)
        primary     literals, identifiers, grouped exprs, fn-exprs
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── utilities ────────────────────────────────────────────────────────────

    def _error(self, msg, line=None):
        line = line or self._peek().line
        raise ParseError(f'[line {line}] {msg}')

    def _peek(self, offset=0):
        i = self.pos + offset
        return self.tokens[min(i, len(self.tokens) - 1)]

    def _check(self, *types):
        return self._peek().type in types

    def _advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _match(self, *types):
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, type, msg):
        if self._check(type):
            return self._advance()
        self._error(msg)

    def _skip_newlines(self):
        while self._check(TT.NEWLINE, TT.SEMI):
            self._advance()

    def _end_stmt(self):
        while self._check(TT.NEWLINE, TT.SEMI):
            self._advance()

    # ── entry point ──────────────────────────────────────────────────────────

    def parse(self):
        stmts = []
        self._skip_newlines()
        while not self._check(TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return stmts

    # ── statements ───────────────────────────────────────────────────────────

    def _statement(self):
        t = self._peek().type
        if t == TT.LET:    return self._let_stmt()
        if t == TT.FN:     return self._fn_decl()
        if t == TT.IF:     return self._if_stmt()
        if t == TT.WHILE:  return self._while_stmt()
        if t == TT.RETURN: return self._return_stmt()
        if t == TT.PRINT:  return self._print_stmt()
        return self._expr_stmt()

    def _let_stmt(self):
        tok = self._advance()                          # consume 'let'
        name = self._expect(TT.IDENT, "expected variable name after 'let'")
        self._expect(TT.EQ, "expected '=' after variable name")
        value = self._expression()
        self._end_stmt()
        return LetStmt(name.value, value, tok.line)

    def _fn_decl(self):
        tok  = self._advance()                         # consume 'fn'
        name = self._expect(TT.IDENT, "expected function name after 'fn'")
        self._expect(TT.LPAREN, "expected '(' after function name")
        params = self._param_list()
        self._expect(TT.RPAREN, "expected ')'")
        body = self._block()
        return FnDecl(name.value, params, body, tok.line)

    def _if_stmt(self):
        tok = self._advance()                          # consume 'if'
        cond       = self._expression()
        then_block = self._block()

        elif_branches = []
        while self._check(TT.ELIF):
            self._advance()
            ec = self._expression()
            eb = self._block()
            elif_branches.append((ec, eb))

        else_block = None
        if self._match(TT.ELSE):
            else_block = self._block()

        return IfStmt(cond, then_block, elif_branches, else_block, tok.line)

    def _while_stmt(self):
        tok  = self._advance()                         # consume 'while'
        cond = self._expression()
        body = self._block()
        return WhileStmt(cond, body, tok.line)

    def _return_stmt(self):
        tok   = self._advance()                        # consume 'return'
        value = None
        if not self._check(TT.NEWLINE, TT.SEMI, TT.EOF, TT.RBRACE):
            value = self._expression()
        self._end_stmt()
        return ReturnStmt(value, tok.line)

    def _print_stmt(self):
        tok = self._advance()                          # consume 'print'
        self._expect(TT.LPAREN, "expected '(' after 'print'")
        value = self._expression()
        self._expect(TT.RPAREN, "expected ')' after print argument")
        self._end_stmt()
        return PrintStmt(value, tok.line)

    def _expr_stmt(self):
        expr = self._expression()
        self._end_stmt()
        return ExprStmt(expr, expr.line)

    def _block(self):
        self._expect(TT.LBRACE, "expected '{'")
        self._skip_newlines()
        stmts = []
        while not self._check(TT.RBRACE, TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        self._expect(TT.RBRACE, "expected '}'")
        return stmts

    def _param_list(self):
        params = []
        if not self._check(TT.RPAREN):
            params.append(self._expect(TT.IDENT, "expected parameter name").value)
            while self._match(TT.COMMA):
                params.append(self._expect(TT.IDENT, "expected parameter name").value)
        return params

    # ── expressions (precedence climbing) ────────────────────────────────────

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._logic_or()
        if self._check(TT.EQ):
            tok = self._advance()
            if not isinstance(expr, Identifier):
                self._error('invalid assignment target', tok.line)
            value = self._assignment()               # right-associative
            return Assign(expr.name, value, tok.line)
        return expr

    def _logic_or(self):
        left = self._logic_and()
        while self._check(TT.OR):
            op    = self._advance()
            right = self._logic_and()
            left  = BinOp('or', left, right, op.line)
        return left

    def _logic_and(self):
        left = self._equality()
        while self._check(TT.AND):
            op    = self._advance()
            right = self._equality()
            left  = BinOp('and', left, right, op.line)
        return left

    def _equality(self):
        left = self._comparison()
        while self._check(TT.EQEQ, TT.BANGEQ):
            op    = self._advance()
            sym   = '==' if op.type == TT.EQEQ else '!='
            right = self._comparison()
            left  = BinOp(sym, left, right, op.line)
        return left

    def _comparison(self):
        left = self._term()
        _map = {TT.LT: '<', TT.LTEQ: '<=', TT.GT: '>', TT.GTEQ: '>='}
        while self._check(*_map):
            op    = self._advance()
            right = self._term()
            left  = BinOp(_map[op.type], left, right, op.line)
        return left

    def _term(self):
        left = self._factor()
        while self._check(TT.PLUS, TT.MINUS):
            op    = self._advance()
            right = self._factor()
            left  = BinOp('+' if op.type == TT.PLUS else '-', left, right, op.line)
        return left

    def _factor(self):
        left = self._unary()
        _map = {TT.STAR: '*', TT.SLASH: '/', TT.PERCENT: '%'}
        while self._check(*_map):
            op    = self._advance()
            right = self._unary()
            left  = BinOp(_map[op.type], left, right, op.line)
        return left

    def _unary(self):
        if self._check(TT.MINUS):
            op    = self._advance()
            right = self._unary()
            return UnaryOp('-', right, op.line)
        if self._check(TT.NOT):
            op    = self._advance()
            right = self._unary()
            return UnaryOp('not', right, op.line)
        return self._call()

    def _call(self):
        expr = self._primary()
        while self._check(TT.LPAREN):
            tok  = self._advance()                   # consume '('
            args = []
            if not self._check(TT.RPAREN):
                args.append(self._expression())
                while self._match(TT.COMMA):
                    args.append(self._expression())
            self._expect(TT.RPAREN, "expected ')' after arguments")
            expr = Call(expr, args, tok.line)
        return expr

    def _primary(self):
        tok = self._advance()

        if tok.type == TT.NUMBER: return NumberLit(tok.value, tok.line)
        if tok.type == TT.STRING: return StringLit(tok.value, tok.line)
        if tok.type == TT.TRUE:   return BoolLit(True,  tok.line)
        if tok.type == TT.FALSE:  return BoolLit(False, tok.line)
        if tok.type == TT.NIL:    return NilLit(tok.line)
        if tok.type == TT.IDENT:  return Identifier(tok.value, tok.line)

        if tok.type == TT.LPAREN:
            expr = self._expression()
            self._expect(TT.RPAREN, "expected ')' after expression")
            return expr

        if tok.type == TT.FN:
            # anonymous function expression: fn(params) { body }
            self._expect(TT.LPAREN, "expected '(' in function expression")
            params = self._param_list()
            self._expect(TT.RPAREN, "expected ')'")
            body = self._block()
            return FnExpr(params, body, tok.line)

        self._error(f"unexpected token '{tok.value or tok.type.name}'", tok.line)
