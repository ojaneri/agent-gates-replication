import pytest

from solution import parse_line


# Basic splitting

@pytest.mark.parametrize(
    "line, expected",
    [
        ("", [""]),
        ("a", ["a"]),
        ("a,b,c", ["a", "b", "c"]),
        ("a,", ["a", ""]),
        (",", ["", ""]),
        (",,", ["", "", ""]),
        (",a", ["", "a"]),
    ],
)
def test_empty_and_basic_splitting(line, expected):
    assert parse_line(line) == expected


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]
    assert parse_line("a,b", sep=";") == ["a,b"]
    assert parse_line("a\tb", sep="\t") == ["a", "b"]


def test_whitespace_is_preserved():
    assert parse_line(" a , b") == [" a ", " b"]
    assert parse_line("  ") == ["  "]
    assert parse_line(" ,") == [" ", ""]


# Quoted fields

def test_quoted_field_with_separator():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quotes_become_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_quoted_empty_field():
    assert parse_line('""') == [""]
    assert parse_line('"",x') == ["", "x"]
    assert parse_line('x,""') == ["x", ""]


def test_quote_only_field():
    assert parse_line('""""') == ['"']


def test_newlines_and_carriage_returns_inside_quotes():
    assert parse_line('"a\nb",c') == ["a\nb", "c"]
    assert parse_line('"a\rb"') == ["a\rb"]


def test_quoted_field_with_custom_separator():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]
    assert parse_line('"a,b";c', sep=";") == ["a,b", "c"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_quoted_field_at_end_after_separator():
    assert parse_line('a,"b"') == ["a", "b"]


# Type errors

@pytest.mark.parametrize("line", [None, 1, b"a,b", ["a"]])
def test_line_must_be_str(line):
    with pytest.raises(TypeError):
        parse_line(line)


@pytest.mark.parametrize("sep", [None, 1, b","])
def test_sep_must_be_str(sep):
    with pytest.raises(TypeError):
        parse_line("a,b", sep=sep)


# Separator validation

@pytest.mark.parametrize("sep", ["", ",,", ";;", "ab"])
def test_sep_must_be_exactly_one_character(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


@pytest.mark.parametrize("sep", ['"', "\r", "\n"])
def test_sep_cannot_be_quote_or_line_break(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


# Quoting errors

def test_unclosed_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"abc')
    with pytest.raises(ValueError):
        parse_line('a,"b,c')
    with pytest.raises(ValueError):
        parse_line('"')


def test_unclosed_quote_with_doubled_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"a""')


def test_text_after_closing_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"a"b')
    with pytest.raises(ValueError):
        parse_line('"a" ,b')
    with pytest.raises(ValueError):
        parse_line('"a" ')


def test_doubled_quote_inside_quoted_field_is_valid():
    # "" inside a quoted field is an escaped quote, not a closing quote.
    assert parse_line('"a""b"') == ['a"b']


def test_quote_inside_unquoted_field_raises():
    with pytest.raises(ValueError):
        parse_line('a"b')
    with pytest.raises(ValueError):
        parse_line('a,b"c,d')


# Line break errors

@pytest.mark.parametrize("line", ["a\nb", "a\rb", "a,b\n", "\r", "a,\nb"])
def test_line_break_outside_quotes_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)
