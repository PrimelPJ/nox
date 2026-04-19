from .ast_nodes  import *
from .environment import Environment
from .errors      import NoxRuntimeError


# ── internal signals ──────────────────────────────────────────────────────────

class _ReturnSignal(Exception):
    """Used to unwind the call stack on a return statement."""
    def __init__(self, value):
        self.value = value


# ── runtime value for functions ───────────────────────────────────────────────

class NoxFunction:
    def __init__(self, name, params, body, closure):
        self.name    = name or '<lambda>'
        self.params  = params
        self.body    = body
        self.closure = closure          # the environment where the fn was defined

    def __repr__(self):
        return f'<fn {self.name}({", ".join(self.params)})>'


# ── interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    def __init__(self):
        self.globals = Environment()

    # ── public ───────────────────────────────────────────────────────────────

    def run(self, stmts):
        for stmt in stmts:
            self._exec(stmt, self.globals)

    # ── dispatch helpers ─────────────────────────────────────────────────────

    def _exec(self, node, env):
        name = type(node).__name__
        handler = getattr(self, f'_exec_{name}', None)
        if handler:
            return handler(node, env)
        self._error(f'unknown statement node: {name}')

    def _eval(self, node, env):
        name = type(node).__name__
        handler = getattr(self, f'_eval_{name}', None)
        if handler:
            return handler(node, env)
        self._error(f'unknown expression node: {name}')

    def _error(self, msg, line=None):
        prefix = f'[line {line}] ' if line else ''
        raise NoxRuntimeError(f'{prefix}{msg}')

    # ── statement executors ──────────────────────────────────────────────────

    def _exec_LetStmt(self, node, env):
        value = self._eval(node.value, env)
        env.define(node.name, value)

    def _exec_FnDecl(self, node, env):
        fn = NoxFunction(node.name, node.params, node.body, env)
        env.define(node.name, fn)

    def _exec_PrintStmt(self, node, env):
        print(self._stringify(self._eval(node.value, env)))

    def _exec_ExprStmt(self, node, env):
        self._eval(node.expr, env)

    def _exec_ReturnStmt(self, node, env):
        value = self._eval(node.value, env) if node.value else None
        raise _ReturnSignal(value)

    def _exec_IfStmt(self, node, env):
        if self._truthy(self._eval(node.condition, env)):
            self._exec_block(node.then_block, Environment(env))
            return
        for cond, block in node.elif_branches:
            if self._truthy(self._eval(cond, env)):
                self._exec_block(block, Environment(env))
                return
        if node.else_block is not None:
            self._exec_block(node.else_block, Environment(env))

    def _exec_WhileStmt(self, node, env):
        while self._truthy(self._eval(node.condition, env)):
            self._exec_block(node.body, Environment(env))

    def _exec_block(self, stmts, env):
        for stmt in stmts:
            self._exec(stmt, env)

    # ── expression evaluators ────────────────────────────────────────────────

    def _eval_NumberLit(self, node, env): return node.value
    def _eval_StringLit(self, node, env): return node.value
    def _eval_BoolLit  (self, node, env): return node.value
    def _eval_NilLit   (self, node, env): return None

    def _eval_Identifier(self, node, env):
        return env.get(node.name, node.line)

    def _eval_Assign(self, node, env):
        value = self._eval(node.value, env)
        env.assign(node.name, value, node.line)
        return value

    def _eval_FnExpr(self, node, env):
        return NoxFunction(None, node.params, node.body, env)

    def _eval_BinOp(self, node, env):
        op = node.op

        # short-circuit logical operators
        if op == 'and':
            left = self._eval(node.left, env)
            return left if not self._truthy(left) else self._eval(node.right, env)
        if op == 'or':
            left = self._eval(node.left, env)
            return left if self._truthy(left) else self._eval(node.right, env)

        left  = self._eval(node.left,  env)
        right = self._eval(node.right, env)

        if op == '+':
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            # string concatenation (auto-cast)
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            self._error("'+' requires numbers or strings", node.line)

        if op == '-': return self._num(left, node.line) - self._num(right, node.line)
        if op == '*': return self._num(left, node.line) * self._num(right, node.line)
        if op == '/':
            r = self._num(right, node.line)
            if r == 0:
                self._error('division by zero', node.line)
            return self._num(left, node.line) / r
        if op == '%': return self._num(left, node.line) % self._num(right, node.line)

        if op == '==': return left == right
        if op == '!=': return left != right
        if op == '<':  return self._num(left, node.line) <  self._num(right, node.line)
        if op == '<=': return self._num(left, node.line) <= self._num(right, node.line)
        if op == '>':  return self._num(left, node.line) >  self._num(right, node.line)
        if op == '>=': return self._num(left, node.line) >= self._num(right, node.line)

        self._error(f"unknown operator '{op}'", node.line)

    def _eval_UnaryOp(self, node, env):
        right = self._eval(node.right, env)
        if node.op == '-':   return -self._num(right, node.line)
        if node.op == 'not': return not self._truthy(right)
        self._error(f"unknown unary operator '{node.op}'", node.line)

    def _eval_Call(self, node, env):
        callee = self._eval(node.callee, env)
        args   = [self._eval(a, env) for a in node.args]

        if not isinstance(callee, NoxFunction):
            self._error(
                f"'{self._stringify(callee)}' is not callable — "
                f"only functions can be called",
                node.line,
            )

        if len(args) != len(callee.params):
            self._error(
                f"{callee.name}() expects {len(callee.params)} argument(s) "
                f"but got {len(args)}",
                node.line,
            )

        # new scope chained to the closure (not the call site!)
        call_env = Environment(callee.closure)
        for param, arg in zip(callee.params, args):
            call_env.define(param, arg)

        try:
            self._exec_block(callee.body, call_env)
        except _ReturnSignal as r:
            return r.value
        return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _truthy(self, val):
        if val is None or val is False:
            return False
        return True

    def _num(self, val, line):
        if isinstance(val, float):
            return val
        self._error(
            f"expected a number but got {type(val).__name__} "
            f"({self._stringify(val)!r})",
            line,
        )

    def _stringify(self, val):
        if val is None:            return 'nil'
        if val is True:            return 'true'
        if val is False:           return 'false'
        if isinstance(val, float):
            return str(int(val)) if val == int(val) else str(val)
        if isinstance(val, NoxFunction):
            return repr(val)
        return str(val)
