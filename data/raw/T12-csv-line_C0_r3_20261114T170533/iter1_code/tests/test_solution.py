import pytest
from solution import parse_line


@pytest.mark.parametrize("line,sep,exp", [
    ("", ",", [""]),
    ("a,", ",", ["a", ""]),
    (",", ",", ["", ""]),
    (" a , b", ",", [" a ", " b"]),
    ('"a,b",c', ",", ["a,b", "c"]),
    ('"say ""hi"""', ",", ['say "hi"']),
    ('""', ",", [""]),
    ('"a\nb\r",x', ",", ["a\nb\r", "x"]),
    ("a;b", ";", ["a", "b"]),
    ('"a",', ",", ["a", ""]),
    ('a,"b"', ",", ["a", "b"]),
])
def test_ok(line, sep, exp):
    assert parse_line(line, sep) == exp


@pytest.mark.parametrize("line", ['"a', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\r", '"a""'])
def test_value_errors(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_types():
    with pytest.raises(TypeError):
        parse_line(1)
    with pytest.raises(TypeError):
        parse_line("a", 1)


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
