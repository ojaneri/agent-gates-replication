import pytest
from solution import parse_line


@pytest.mark.parametrize("line,expected", [
    ("", [""]),
    ("a,", ["a", ""]),
    (",", ["", ""]),
    ("a,b,c", ["a", "b", "c"]),
    (" a , b", [" a ", " b"]),
    ('"a,b",c', ["a,b", "c"]),
    ('"say ""hi"""', ['say "hi"']),
    ('"a\r\nb",c', ["a\r\nb", "c"]),
    ('""', [""]),
    ('"",x', ["", "x"]),
    ('a,"b"', ["a", "b"]),
    ('"a",', ["a", ""]),
])
def test_ok(line, expected):
    assert parse_line(line) == expected


def test_custom_sep():
    assert parse_line("a;b,c", ";") == ["a", "b,c"]
    assert parse_line('"a;b";c', ";") == ["a;b", "c"]


@pytest.mark.parametrize("line", [
    '"abc', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\rb", '"a""',
])
def test_value_errors(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_type_errors():
    with pytest.raises(TypeError):
        parse_line(1)
    with pytest.raises(TypeError):
        parse_line("a", 1)
    with pytest.raises(TypeError):
        parse_line(b"a")


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
