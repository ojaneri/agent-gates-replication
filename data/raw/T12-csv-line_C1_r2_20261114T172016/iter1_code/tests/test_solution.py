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
def test_basic_splitting(line, expected):
    assert parse_line(line) == expected


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", sep=",")


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]
    assert parse_line("a\tb", sep="\t") == ["a", "b"]


def test_custom_separator_with_commas_inside_is_plain_text():
    assert parse_line("a,b;c", sep=";") == ["a,b", "c"]


def test_whitespace_is_preserved():
    assert parse_line(" a , b") == [" a ", " b"]
    assert parse_line("  ") == ["  "]
    assert parse_line(" ,") == [" ", ""]


# Quoted fields

def test_quoted_field_with_separator():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_is_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_quoted_empty_field():
    assert parse_line('""') == [""]
    assert parse_line('"",x') == ["", "x"]
    assert parse_line('x,""') == ["x", ""]


def test_quoted_field_at_end_with_trailing_separator():
    assert parse_line('"a",') == ["a", ""]


def test_quoted_field_keeps_whitespace_inside():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_newline_and_carriage_return_inside_quotes_are_ordinary():
    assert parse_line('"line1\nline2",x') == ["line1\nline2", "x"]
    assert parse_line('"a\rb"') == ["a\rb"]


def test_quoted_separator_other_than_comma():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


def test_only_doubled_quotes():
    assert parse_line('""""') == ['"']
    assert parse_line('"""a"""') == ['"a"']


# Whitespace and separators inside unquoted fields

def test_quote_not_at_start_of_field_is_error():
    with pytest.raises(ValueError):
        parse_line('a"b')
    with pytest.raises(ValueError):
        parse_line('x,a"b,y')


def test_carriage_return_or_newline_outside_quotes_is_error():
    with pytest.raises(ValueError):
        parse_line("a\rb")
    with pytest.raises(ValueError):
        parse_line("a\nb")
    with pytest.raises(ValueError):
        parse_line("a,b\n")


# Quoted-field errors

def test_unclosed_quote_is_error():
    with pytest.raises(ValueError):
        parse_line('"abc')
    with pytest.raises(ValueError):
        parse_line('"')
    with pytest.raises(ValueError):
        parse_line('"a""')  # the final quote is doubled, so the field never closes


def test_character_after_closing_quote_is_error():
    with pytest.raises(ValueError):
        parse_line('"a"b')
    with pytest.raises(ValueError):
        parse_line('"a" ,b')
    with pytest.raises(ValueError):
        parse_line('"a" ')


# Separator and type validation

@pytest.mark.parametrize("sep", ["", "ab", '"', "\r", "\n"])
def test_invalid_separator_is_value_error(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


@pytest.mark.parametrize(
    "line, sep",
    [(None, ","), (1, ","), ("a", None), ("a", 1), (b"a", ",")],
)
def test_non_string_arguments_raise_type_error(line, sep):
    with pytest.raises(TypeError):
        parse_line(line, sep=sep)
