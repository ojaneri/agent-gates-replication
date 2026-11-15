import pytest

from solution import parse_line


# --- basic splitting -------------------------------------------------------

@pytest.mark.parametrize(
    "line, expected",
    [
        ("", [""]),
        ("a", ["a"]),
        ("a,b", ["a", "b"]),
        ("a,", ["a", ""]),
        (",", ["", ""]),
        (",,", ["", "", ""]),
        (",a", ["", "a"]),
        ("a,b,c", ["a", "b", "c"]),
    ],
)
def test_basic_splitting(line, expected):
    assert parse_line(line) == expected


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", ",")


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]
    assert parse_line("a;;b", sep=";") == ["a", "", "b"]


def test_comma_is_plain_text_with_other_separator():
    assert parse_line("a,b;c", sep=";") == ["a,b", "c"]


def test_whitespace_is_preserved():
    assert parse_line(" a , b") == [" a ", " b"]
    assert parse_line("  ") == ["  "]
    assert parse_line(" ,") == [" ", ""]


def test_tab_separator():
    assert parse_line("a\tb", sep="\t") == ["a", "b"]


# --- quoted fields ---------------------------------------------------------

def test_quoted_field_with_separator_inside():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_becomes_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_empty_quoted_field():
    assert parse_line('"",x') == ["", "x"]
    assert parse_line('""') == [""]


def test_quoted_field_with_only_doubled_quote():
    assert parse_line('""""') == ['"']


def test_quoted_field_keeps_cr_and_lf():
    assert parse_line('"a\r\nb",c') == ["a\r\nb", "c"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_quoted_field_at_end_of_line_with_trailing_separator():
    assert parse_line('"a",') == ["a", ""]


def test_quoted_field_with_custom_separator():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


def test_quote_inside_quoted_field_with_comma_not_separator():
    # A comma is only special outside quotes.
    assert parse_line('"x,"",y"') == ['x,",y']


# --- errors ----------------------------------------------------------------

@pytest.mark.parametrize("line", [None, 1, b"a,b", ["a"]])
def test_line_must_be_str(line):
    with pytest.raises(TypeError):
        parse_line(line)


@pytest.mark.parametrize("sep", [None, 1, b","])
def test_sep_must_be_str(sep):
    with pytest.raises(TypeError):
        parse_line("a,b", sep)


@pytest.mark.parametrize("sep", ["", ",,", ";;", "ab"])
def test_sep_must_be_one_character(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep)


@pytest.mark.parametrize("sep", ['"', "\r", "\n"])
def test_sep_cannot_be_quote_or_newline(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep)


@pytest.mark.parametrize(
    "line",
    [
        '"abc',          # no closing quote
        '"',             # lone opening quote
        '"a""',          # doubled quote at end, still unclosed
        '"a,b',          # unclosed with separator inside
        'x,"abc',        # unclosed quoted field after a separator
    ],
)
def test_unclosed_quoted_field(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['"a"b', '"a" ,b', '"a"x"', '"a" '])
def test_character_after_closing_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['a"b', 'a,b"c', '"a"b"', 'ab"'])
def test_quote_inside_unquoted_field(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ["a\rb", "a\nb", "a,b\n", "a\r,b", "\n"])
def test_cr_or_lf_outside_quotes(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_custom_separator_quoted_field_then_separator():
    assert parse_line('"a";b', sep=";") == ["a", "b"]


def test_custom_separator_quote_after_closing_error():
    with pytest.raises(ValueError):
        parse_line('"a",b', sep=";")


def test_custom_separator_unquoted_quote_error():
    with pytest.raises(ValueError):
        parse_line('a;b"', sep=";")
