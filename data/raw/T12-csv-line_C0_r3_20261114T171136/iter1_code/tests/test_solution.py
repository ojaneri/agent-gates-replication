import pytest

from solution import parse_line


@pytest.mark.parametrize(
    "line, expected",
    [
        ("", [""]),
        ("a", ["a"]),
        ("a,", ["a", ""]),
        (",", ["", ""]),
        (",,", ["", "", ""]),
        ("a,b,c", ["a", "b", "c"]),
        (" a , b", [" a ", " b"]),
        ("   ", ["   "]),
    ],
)
def test_unquoted_fields(line, expected):
    assert parse_line(line) == expected


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]
    assert parse_line("a,b;c", sep=";") == ["a,b", "c"]
    assert parse_line("a|", sep="|") == ["a", ""]


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", sep=",")


def test_quoted_field_with_separator():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_inside_quoted_field():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_quoted_empty_field():
    assert parse_line('"",x') == ["", "x"]
    assert parse_line('""') == [""]


def test_quoted_field_with_newlines_and_cr():
    assert parse_line('"a\nb","c\rd"') == ["a\nb", "c\rd"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_quoted_field_with_custom_separator_inside():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


def test_trailing_separator_after_quoted_field():
    assert parse_line('"a",') == ["a", ""]


def test_mixed_quoted_and_unquoted():
    assert parse_line('x,"y,z",w') == ["x", "y,z", "w"]


# Type errors

@pytest.mark.parametrize("line", [None, 1, b"a,b", ["a"]])
def test_line_must_be_str(line):
    with pytest.raises(TypeError):
        parse_line(line)


@pytest.mark.parametrize("sep", [None, 1, b","])
def test_sep_must_be_str(sep):
    with pytest.raises(TypeError):
        parse_line("a,b", sep=sep)


# Separator value errors

@pytest.mark.parametrize("sep", ["", ",,", "ab"])
def test_sep_must_be_one_character(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


@pytest.mark.parametrize("sep", ['"', "\r", "\n"])
def test_sep_cannot_be_quote_or_newline(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


# Field errors

@pytest.mark.parametrize(
    "line",
    [
        '"abc',
        '"',
        '"a""',
        '"a,b',
    ],
)
def test_unclosed_quoted_field(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize('line', ['"a"b', '"a" ,b', '"a"x,b', '"a" '])
def test_char_after_closing_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['a"b', '"a"b"c', 'x,a"b'])
def test_quote_inside_unquoted_field(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ["a\nb", "a\rb", "a,b\n", "\r"])
def test_newline_outside_quotes(line):
    with pytest.raises(ValueError):
        parse_line(line)
