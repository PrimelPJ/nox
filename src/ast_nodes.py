from dataclasses import dataclass, field
from typing import List, Optional, Any


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class NumberLit:
    value: float
    line:  int

@dataclass
class StringLit:
    value: str
    line:  int

@dataclass
class BoolLit:
    value: bool
    line:  int

@dataclass
class NilLit:
    line: int

@dataclass
class Identifier:
    name: str
    line: int

@dataclass
class BinOp:
    op:    str
    left:  Any
    right: Any
    line:  int

@dataclass
class UnaryOp:
    op:    str
    right: Any
    line:  int

@dataclass
class Assign:
    name:  str
    value: Any
    line:  int

@dataclass
class Call:
    callee: Any
    args:   List[Any]
    line:   int

@dataclass
class FnExpr:
    """Anonymous function expression: fn(params) { body }"""
    params: List[str]
    body:   List[Any]
    line:   int


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class LetStmt:
    name:  str
    value: Any
    line:  int

@dataclass
class PrintStmt:
    value: Any
    line:  int

@dataclass
class IfStmt:
    condition:      Any
    then_block:     List[Any]
    elif_branches:  List[Any]   # list of (condition, block) tuples
    else_block:     Optional[List[Any]]
    line:           int

@dataclass
class WhileStmt:
    condition: Any
    body:      List[Any]
    line:      int

@dataclass
class FnDecl:
    """Named function declaration statement."""
    name:   str
    params: List[str]
    body:   List[Any]
    line:   int

@dataclass
class ReturnStmt:
    value: Optional[Any]
    line:  int

@dataclass
class ExprStmt:
    expr: Any
    line: int
