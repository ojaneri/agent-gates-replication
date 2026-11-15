import pytest

from solution import parse_line


@pytest.mark.parametrize("line,sep,expected", [
    ("a,b,c", ",", ["a", "b", "c"]),
    ("", ",", [""]),
    ("a", ",", ["a"]),
    ("a,", ",", ["a", ""]),
    (",", ",", ["", ""]),
    (",,", ",", ["", "", ""]),
    (",a", ",", ["", "a"]),
    (" a , b ", ",", [" a ", " b "]),
    ('"a,b",c', ",", ["a,b", "c"]),
    ('"say ""hi"""', ",", ['say "hi"']),
    ('""', ",", [""]),
    ('"",""', ",", ["", ""]),
    ('""""', ",", ['"']),
    ('a,""', ",", ["a", ""]),
    ('"x\ny",z', ",", ["x\ny", "z"]),
    ('"x\r\ny"', ",", ["x\r\ny"]),
    ('" a "', ",", [" a "]),
    ("a;b,c", ";", ["a", "b,c"]),
    ("a\tb", "\t", ["a", "b"]),
    ('"a;b";c', ";", ["a;b", "c"]),
    ("é,ü", ",", ["é", "ü"]),
    ("abc", "b", ["a", "c"]),
])
def test_parse(line, sep, expected):
    assert parse_line(line, sep) == expected


def test_default_separator():
    assert parse_line("x,y") == ["x", "y"]


@pytest.mark.parametrize("line,sep", [
    ('a"b', ","), ('a,b"', ","), ('"abc', ","), ('"a""', ","), ('"', ","), ('"a"b', ","), ('"a" ,b', ","),
    ("a\nb", ","), ("a\rb", ","), ("a,\n", ","),
    ("a", ""), ("a", ";;"), ("a", '"'), ("a", "\n"), ("a", "\r"),
])
def test_value_errors(line, sep):
    with pytest.raises(ValueError):
        parse_line(line, sep)


@pytest.mark.parametrize("line,sep", [(None, ","), (b"a,b", ","), (["a", "b"], ","), ("a", None), ("a", 44)])
def test_type_errors(line, sep):
    with pytest.raises(TypeError):
        parse_line(line, sep)
