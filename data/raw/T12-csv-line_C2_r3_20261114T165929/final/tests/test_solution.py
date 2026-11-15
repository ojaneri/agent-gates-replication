import pytest

from solution import parse_line


# --- basic splitting -------------------------------------------------------

@pytest.mark.parametrize(
    "line, expected",
    [
        ("", [""]),
        ("a", ["a"]),
        ("a,b", ["a", "b"]),
        ("a,b,c", ["a", "b", "c"]),
        ("a,", ["a", ""]),
        (",a", ["", "a"]),
        (",", ["", ""]),
        (",,", ["", "", ""]),
        ("a,,b", ["a", "", "b"]),
    ],
)
def test_default_separator_counts(line, expected):
    assert parse_line(line) == expected


def test_k_separators_give_k_plus_one_fields():
    for k in range(10):
        assert len(parse_line("," * k)) == k + 1


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]


def test_custom_separator_does_not_split_on_comma():
    assert parse_line("a,b;c", sep=";") == ["a,b", "c"]


def test_tab_separator():
    assert parse_line("x\ty", sep="\t") == ["x", "y"]


def test_whitespace_is_kept():
    assert parse_line(" a , b") == [" a ", " b"]


def test_whitespace_only_field_kept():
    assert parse_line("   ") == ["   "]


def test_space_separator_keeps_empty_fields():
    assert parse_line("a  b", sep=" ") == ["a", "", "b"]


# --- quoted fields ---------------------------------------------------------

def test_quoted_field_with_separator():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_becomes_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_empty_quoted_field():
    assert parse_line('""') == [""]


def test_empty_quoted_field_then_separator():
    assert parse_line('"",x') == ["", "x"]


def test_quoted_field_at_end_followed_by_separator():
    assert parse_line('a,"b",') == ["a", "b", ""]


def test_quoted_field_ending_in_doubled_quote():
    assert parse_line('"a"""') == ['a"']


def test_quoted_field_with_only_doubled_quote():
    assert parse_line('""""') == ['"']


def test_quoted_field_with_two_doubled_quotes():
    assert parse_line('""""""') == ['""']


def test_quoted_field_keeps_newline_and_cr():
    assert parse_line('"a\nb\rc",d') == ["a\nb\rc", "d"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a "," b "') == [" a ", " b "]


def test_quoted_field_with_custom_separator():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


def test_comma_inside_quotes_is_not_separator_for_semicolon_sep():
    assert parse_line('"a,b";c', sep=";") == ["a,b", "c"]


def test_quoted_then_quoted():
    assert parse_line('"a","b"') == ["a", "b"]


def test_quoted_field_with_single_quote_char_inside():
    assert parse_line("\"it's\"") == ["it's"]


def test_quoted_field_with_separator_at_end_inside_quotes():
    assert parse_line('"a,"') == ["a,"]


# --- errors: type and separator --------------------------------------------

def test_line_must_be_str():
    with pytest.raises(TypeError):
        parse_line(None)


def test_line_bytes_rejected():
    with pytest.raises(TypeError):
        parse_line(b"a,b")


def test_sep_must_be_str():
    with pytest.raises(TypeError):
        parse_line("a,b", sep=1)


def test_sep_none_rejected():
    with pytest.raises(TypeError):
        parse_line("a,b", sep=None)


@pytest.mark.parametrize("sep", ["", ";;", "ab"])
def test_sep_must_be_one_character(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


@pytest.mark.parametrize("sep", ['"', "\r", "\n"])
def test_sep_forbidden_characters(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


# --- errors: quoting -------------------------------------------------------

@pytest.mark.parametrize("line", ['"abc', '"', '"a""', '"a,b'])
def test_unclosed_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['"a"b', '"a" ,b', '"a"x,b', '"a" "b"'])
def test_character_after_closing_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_quote_inside_unquoted_field():
    with pytest.raises(ValueError):
        parse_line('a"b')


def test_quote_inside_unquoted_field_later_in_line():
    with pytest.raises(ValueError):
        parse_line('x,a"b,c')


def test_quote_after_text_in_second_field():
    with pytest.raises(ValueError):
        parse_line('a,b"')


# --- errors: line breaks outside quotes ------------------------------------

@pytest.mark.parametrize("line", ["a\nb", "a\rb", "\n", "\r", "a,b\n", "a\r"])
def test_newline_outside_quotes(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_newline_after_quoted_field_is_error():
    with pytest.raises(ValueError):
        parse_line('"a"\n')


def test_newline_in_unquoted_field_with_custom_sep():
    with pytest.raises(ValueError):
        parse_line("a\nb", sep=";")
