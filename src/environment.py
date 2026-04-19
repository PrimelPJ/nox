from .errors import NoxRuntimeError


class Environment:
    """
    A single scope frame.  Each function call or block gets its own
    Environment that points to its enclosing scope via `parent`.
    Variable lookup and assignment walk the chain upward, which is
    exactly what makes closures work.
    """

    def __init__(self, parent=None):
        self.vars   = {}
        self.parent = parent

    def define(self, name, value):
        """Create a new binding in THIS scope (let / fn / param)."""
        self.vars[name] = value

    def get(self, name, line=None):
        """Resolve a name by walking up the scope chain."""
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise NoxRuntimeError(f"[line {line}] undefined variable '{name}'")

    def assign(self, name, value, line=None):
        """
        Update an existing binding wherever it lives in the chain.
        This lets inner functions mutate variables in outer scopes.
        """
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value, line)
            return
        raise NoxRuntimeError(f"[line {line}] undefined variable '{name}'")

    def __repr__(self):
        return f'Env({list(self.vars.keys())})'
