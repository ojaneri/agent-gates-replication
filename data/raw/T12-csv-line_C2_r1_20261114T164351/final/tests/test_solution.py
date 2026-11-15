import pytest

from solution import parse_line


@pytest.mark.parametrize(
    "line,expected",
    [
        ("", [""]),
        ("a,", ["a", ""]),
        (",", ["", ""]),
        ("a,b,c", ["a", "b", "c"]),
        (" a , b", [" a ", " b"]),
        ('"a,b",c', ["a,b", "c"]),
        ('"say ""hi"""', ['say "hi"']),
        ('"a\r\nb",c', ["a\r\nb", "c"]),
        ('"",x', ["", "x"]),
        ('x,""', ["x", ""]),
        ('"a",', ["a", ""]),
        ('"a"', ["a"]),
        ('"a",""', ["a", ""]),
        ('"a","b"', ["a", "b"]),
    ],
)
def test_valid(line, expected):
    assert parse_line(line) == expected


def test_custom_sep():
    assert parse_line("a;b,c", ";") == ["a", "b,c"]
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


@pytest.mark.parametrize(
    "line",
    ['"abc', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\rb", 'x,"a"b', '"a""', 'a,b"'],
)
def test_bad_lines(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_type_errors():
    with pytest.raises(TypeError):
        parse_line(None)
    with pytest.raises(TypeError):
        parse_line("a", 1)
    with pytest.raises(TypeError):
        parse_line(b"a")


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
