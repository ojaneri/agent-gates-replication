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
        ('"a\nb\r",x', ["a\nb\r", "x"]),
        ('""', [""]),
        ('"",""', ["", ""]),
        ('a,"b"', ["a", "b"]),
        ('"a",', ["a", ""]),
        ('"""",x', ['"', "x"]),
    ],
)
def test_ok(line, expected):
    assert parse_line(line) == expected


def test_custom_sep():
    assert parse_line("a;b,c", ";") == ["a", "b,c"]
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


@pytest.mark.parametrize(
    "line", ['"abc', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\rb", '"a""', '"']
)
def test_bad_lines(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("args", [(1,), (None,), ("a", 1), ("a", None), (b"a",)])
def test_type_errors(args):
    with pytest.raises(TypeError):
        parse_line(*args)


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
