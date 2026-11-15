import pytest

from solution import parse_line


# --- Basic splitting -------------------------------------------------------

def test_empty_line_gives_one_empty_field():
    assert parse_line("") == [""]


def test_simple_fields():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_single_field_no_separator():
    assert parse_line("abc") == ["abc"]


def test_trailing_separator_gives_empty_field():
    assert parse_line("a,") == ["a", ""]


def test_only_separator_gives_two_empty_fields():
    assert parse_line(",") == ["", ""]


def test_leading_separator():
    assert parse_line(",a") == ["", "a"]


def test_consecutive_separators():
    assert parse_line("a,,b") == ["a", "", "b"]


def test_k_separators_give_k_plus_one_fields():
    assert parse_line(",,,") == ["", "", "", ""]


def test_whitespace_is_not_trimmed():
    assert parse_line(" a , b") == [" a ", " b"]


def test_whitespace_only_field_kept():
    assert parse_line("  ,\t") == ["  ", "\t"]


# --- Custom separators -----------------------------------------------------

def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]


def test_tab_separator():
    assert parse_line("a\tb", sep="\t") == ["a", "b"]


def test_space_separator_keeps_empty_fields():
    assert parse_line("a  b", sep=" ") == ["a", "", "b"]


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", sep=",")


def test_comma_is_ordinary_when_sep_is_semicolon():
    assert parse_line("a,b;c", sep=";") == ["a,b", "c"]


# --- Quoted fields ---------------------------------------------------------

def test_quoted_field_with_separator_inside():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_quoted_field_quotes_removed():
    assert parse_line('"abc"') == ["abc"]


def test_doubled_quote_becomes_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_empty_quoted_field():
    assert parse_line('""') == [""]


def test_empty_quoted_fields_around_separator():
    assert parse_line('"",""') == ["", ""]


def test_quoted_field_then_empty_trailing_field():
    assert parse_line('"a",') == ["a", ""]


def test_quoted_whitespace_preserved():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_cr_and_lf_inside_quotes_are_ordinary():
    assert parse_line('"a\r\nb",c') == ["a\r\nb", "c"]


def test_quoted_field_with_custom_separator_inside():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


def test_quoted_field_contains_only_doubled_quote():
    assert parse_line('""""') == ['"']


# --- Errors: separator argument --------------------------------------------

def test_line_must_be_str():
    with pytest.raises(TypeError):
        parse_line(123)


def test_line_none_raises_type_error():
    with pytest.raises(TypeError):
        parse_line(None)


def test_line_bytes_raises_type_error():
    with pytest.raises(TypeError):
        parse_line(b"a,b")


def test_sep_must_be_str():
    with pytest.raises(TypeError):
        parse_line("a,b", sep=1)


def test_sep_none_raises_type_error():
    with pytest.raises(TypeError):
        parse_line("a,b", sep=None)


def test_sep_empty_string_raises_value_error():
    with pytest.raises(ValueError):
        parse_line("a,b", sep="")


def test_sep_multi_character_raises_value_error():
    with pytest.raises(ValueError):
        parse_line("a,b", sep=", ")


@pytest.mark.parametrize("bad", ['"', "\r", "\n"])
def test_sep_forbidden_characters_raise_value_error(bad):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=bad)


# --- Errors: malformed quoting ---------------------------------------------

def test_unclosed_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"abc')


def test_unclosed_quote_with_separator_inside_raises():
    with pytest.raises(ValueError):
        parse_line('"a,b')


def test_lone_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"')


def test_quote_then_doubled_quote_unclosed_raises():
    # '"a""' : the "" is an escaped quote, so the field never closes.
    with pytest.raises(ValueError):
        parse_line('"a""')


def test_text_after_closing_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"a"b')


def test_space_after_closing_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"a" ,b')


def test_quote_before_custom_sep_mismatch_raises():
    with pytest.raises(ValueError):
        parse_line('"a",b', sep=";")


def test_quote_inside_unquoted_field_raises():
    with pytest.raises(ValueError):
        parse_line('a"b')


def test_quote_inside_unquoted_field_after_sep_raises():
    with pytest.raises(ValueError):
        parse_line('x,a"b')


def test_quote_at_end_of_unquoted_field_raises():
    with pytest.raises(ValueError):
        parse_line('a"')


@pytest.mark.parametrize("line", ["a\rb", "a\nb", "a,b\r", "a\n", "\r"])
def test_cr_or_lf_outside_quotes_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)


def test_cr_after_closing_quote_raises():
    with pytest.raises(ValueError):
        parse_line('"a"\r')
