import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.lexer  import Lexer, TT
from src.errors import LexError
import pytest


def tok_types(source):
    return [t.type for t in Lexer(source).tokenize() if t.type != TT.EOF]

def tok_values(source):
    return [(t.type, t.value) for t in Lexer(source).tokenize() if t.type != TT.EOF]


class TestNumbers:
    def test_integer(self):
        toks = [t for t in Lexer("42").tokenize() if t.type == TT.NUMBER]
        assert toks[0].value == 42.0

    def test_float(self):
        toks = [t for t in Lexer("3.14").tokenize() if t.type == TT.NUMBER]
        assert abs(toks[0].value - 3.14) < 1e-9

    def test_multiple(self):
        vals = [t.value for t in Lexer("1 2 3").tokenize() if t.type == TT.NUMBER]
        assert vals == [1.0, 2.0, 3.0]


class TestStrings:
    def test_double_quote(self):
        toks = [t for t in Lexer('"hello"').tokenize() if t.type == TT.STRING]
        assert toks[0].value == 'hello'

    def test_single_quote(self):
        toks = [t for t in Lexer("'world'").tokenize() if t.type == TT.STRING]
        assert toks[0].value == 'world'

    def test_unterminated(self):
        with pytest.raises(LexError):
            Lexer('"oops').tokenize()


class TestKeywords:
    def test_all_keywords(self):
        src   = 'let fn if elif else while return true false nil and or not print'
        types = tok_types(src)
        assert TT.LET    in types
        assert TT.FN     in types
        assert TT.IF     in types
        assert TT.ELIF   in types
        assert TT.ELSE   in types
        assert TT.WHILE  in types
        assert TT.RETURN in types
        assert TT.TRUE   in types
        assert TT.FALSE  in types
        assert TT.NIL    in types
        assert TT.AND    in types
        assert TT.OR     in types
        assert TT.NOT    in types
        assert TT.PRINT  in types


class TestOperators:
    def test_two_char_ops(self):
        types = tok_types('== != <= >=')
        assert types == [TT.EQEQ, TT.BANGEQ, TT.LTEQ, TT.GTEQ]

    def test_single_char_ops(self):
        types = tok_types('+ - * / %')
        assert types == [TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH, TT.PERCENT]

    def test_bad_bang(self):
        with pytest.raises(LexError):
            Lexer('!').tokenize()


class TestComments:
    def test_comment_ignored(self):
        types = tok_types('42 # ignored\n99')
        nums = [t for t in Lexer('42 # ignored\n99').tokenize() if t.type == TT.NUMBER]
        assert len(nums) == 2
        assert nums[0].value == 42.0
        assert nums[1].value == 99.0


class TestNewlines:
    def test_newline_emitted(self):
        types = tok_types('a\nb')
        assert TT.NEWLINE in types

    def test_newline_suppressed_after_lbrace(self):
        types = tok_types('{\n')
        assert TT.NEWLINE not in types


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
