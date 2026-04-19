import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.lexer       import Lexer
from src.parser      import Parser
from src.interpreter import Interpreter
from src.errors      import NoxError, NoxRuntimeError
import pytest


def run(source):
    """Run nox source and return printed output as a string."""
    buf  = io.StringIO()
    orig = sys.stdout
    sys.stdout = buf
    try:
        tokens = Lexer(source).tokenize()
        ast    = Parser(tokens).parse()
        Interpreter().run(ast)
    finally:
        sys.stdout = orig
    return buf.getvalue().strip()


class TestArithmetic:
    def test_add(self):        assert run('print(2 + 3)')    == '5'
    def test_sub(self):        assert run('print(10 - 4)')   == '6'
    def test_mul(self):        assert run('print(3 * 4)')    == '12'
    def test_div(self):        assert run('print(10 / 4)')   == '2.5'
    def test_mod(self):        assert run('print(10 % 3)')   == '1'
    def test_neg(self):        assert run('print(-7)')       == '-7'
    def test_precedence(self): assert run('print(2 + 3 * 4)') == '14'
    def test_parens(self):     assert run('print((2 + 3) * 4)') == '20'

    def test_div_zero(self):
        with pytest.raises(NoxRuntimeError):
            run('print(1 / 0)')


class TestVariables:
    def test_let(self):
        assert run('let x = 42\nprint(x)') == '42'

    def test_reassign(self):
        assert run('let x = 1\nx = 2\nprint(x)') == '2'

    def test_undefined(self):
        with pytest.raises(NoxRuntimeError):
            run('print(z)')


class TestStrings:
    def test_concat(self):
        assert run('print("hello" + " " + "world")') == 'hello world'

    def test_number_coerce(self):
        assert run('print("score: " + 99)') == 'score: 99'


class TestBooleans:
    def test_true(self):  assert run('print(true)')  == 'true'
    def test_false(self): assert run('print(false)') == 'false'
    def test_not(self):   assert run('print(not false)') == 'true'
    def test_and(self):   assert run('print(true and false)') == 'false'
    def test_or(self):    assert run('print(false or true)')  == 'true'

    def test_short_circuit_and(self):
        # right side should NOT be evaluated if left is false
        assert run('print(false and (1/0 > 0))') == 'false'

    def test_short_circuit_or(self):
        assert run('print(true or (1/0 > 0))') == 'true'


class TestComparison:
    def test_lt(self):  assert run('print(1 < 2)')  == 'true'
    def test_gt(self):  assert run('print(2 > 1)')  == 'true'
    def test_eq(self):  assert run('print(3 == 3)') == 'true'
    def test_neq(self): assert run('print(3 != 4)') == 'true'
    def test_lte(self): assert run('print(2 <= 2)') == 'true'
    def test_gte(self): assert run('print(3 >= 3)') == 'true'


class TestNil:
    def test_nil_print(self):   assert run('print(nil)')        == 'nil'
    def test_nil_eq(self):      assert run('let x = nil\nprint(x == nil)') == 'true'
    def test_nil_falsy(self):
        assert run('if nil { print("yes") } else { print("no") }') == 'no'


class TestIfElse:
    def test_if_true(self):
        assert run('if 1 < 2 { print("yes") }') == 'yes'

    def test_if_false_else(self):
        assert run('if 1 > 2 { print("a") } else { print("b") }') == 'b'

    def test_elif(self):
        src = 'let x = 5\nif x > 10 { print("big") } elif x > 3 { print("mid") } else { print("small") }'
        assert run(src) == 'mid'

    def test_nested(self):
        src = 'if true { if false { print("a") } else { print("b") } }'
        assert run(src) == 'b'


class TestWhile:
    def test_basic(self):
        src = 'let i = 0\nwhile i < 3 { print(i)\ni = i + 1 }'
        assert run(src) == '0\n1\n2'

    def test_zero_iterations(self):
        assert run('while false { print("x") }') == ''


class TestFunctions:
    def test_basic(self):
        assert run('fn add(a, b) { return a + b }\nprint(add(3, 4))') == '7'

    def test_no_return(self):
        assert run('fn noop() { let x = 1 }\nprint(noop())') == 'nil'

    def test_wrong_arity(self):
        with pytest.raises(NoxRuntimeError):
            run('fn f(x) { return x }\nf(1, 2)')


class TestClosures:
    def test_make_adder(self):
        src = '''
fn make_adder(n) {
    fn adder(x) { return x + n }
    return adder
}
let add5 = make_adder(5)
print(add5(10))
'''
        assert run(src) == '15'

    def test_counter_independence(self):
        src = '''
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
print(c1())
print(c1())
print(c2())
print(c1())
'''
        assert run(src) == '1\n2\n101\n3'

    def test_anonymous_fn(self):
        src = '''
fn apply(f, x) { return f(x) }
print(apply(fn(x) { return x * x }, 7))
'''
        assert run(src) == '49'


class TestRecursion:
    def test_fibonacci(self):
        src = '''
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
print(fib(10))
'''
        assert run(src) == '55'

    def test_factorial(self):
        src = '''
fn fact(n) {
    if n <= 1 { return 1 }
    return n * fact(n - 1)
}
print(fact(7))
'''
        assert run(src) == '5040'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
