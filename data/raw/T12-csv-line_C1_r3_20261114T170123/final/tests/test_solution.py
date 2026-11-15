import pytest
from solution import parse_line


@pytest.mark.parametrize("line,sep,exp", [
    ("", ",", [""]),
    ("a,", ",", ["a", ""]),
    (",", ",", ["", ""]),
    (" a , b", ",", [" a ", " b"]),
    ('"a,b",c', ",", ["a,b", "c"]),
    ('"say ""hi"""', ",", ['say "hi"']),
    ('"a\nb\r",x', ",", ["a\nb\r", "x"]),
    ('""', ",", [""]),
    ('"a",', ",", ["a", ""]),
    ("a;b,c", ";", ["a", "b,c"]),
    ('a,"b"', ",", ["a", "b"]),
])
def test_ok(line, sep, exp):
    assert parse_line(line, sep) == exp


@pytest.mark.parametrize("line", ['"abc', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\rb", '"a""'])
def test_value_errors(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("args", [(1,), ("a", 1), (None, ","), (b"a",)])
def test_type_errors(args):
    with pytest.raises(TypeError):
        parse_line(*args)


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
