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
    ('"a",', ["a", ""]),
    ('"",x', ["", "x"]),
    ('"a\r\nb"', ["a\r\nb"]),
    ('"a"', ["a"]),
    ('"""",b', ['"', "b"]),
])
def test_ok(line, expected):
    assert parse_line(line) == expected


def test_custom_sep():
    assert parse_line("a;b,c", ";") == ["a", "b,c"]
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


@pytest.mark.parametrize("line", [
    '"abc', '"', '"a""', '"a"b', '"a" ,b', 'a"b', "a\nb", "a\rb", '"a"\n',
])
def test_value_errors(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line,sep", [(1, ","), ("a", 1), (None, ","), (b"a", ",")])
def test_type_errors(line, sep):
    with pytest.raises(TypeError):
        parse_line(line, sep)


@pytest.mark.parametrize("sep", ["", ",,", '"', "\r", "\n"])
def test_bad_sep(sep):
    with pytest.raises(ValueError):
        parse_line("a", sep)
