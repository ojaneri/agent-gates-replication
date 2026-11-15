import pytest

from solution import parse_line


# --- basic splitting -------------------------------------------------------

def test_empty_line_gives_one_empty_field():
    assert parse_line("") == [""]


def test_single_field():
    assert parse_line("abc") == ["abc"]


def test_simple_split():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_trailing_separator_gives_empty_last_field():
    assert parse_line("a,") == ["a", ""]


def test_leading_separator_gives_empty_first_field():
    assert parse_line(",a") == ["", "a"]


def test_only_separator_gives_two_empty_fields():
    assert parse_line(",") == ["", ""]


def test_two_separators_give_three_empty_fields():
    assert parse_line(",,") == ["", "", ""]


def test_empty_middle_field():
    assert parse_line("a,,b") == ["a", "", "b"]


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", ",")


def test_custom_separator():
    assert parse_line("a;b;c", ";") == ["a", "b", "c"]


def test_custom_separator_does_not_split_on_comma():
    assert parse_line("a,b;c", ";") == ["a,b", "c"]


def test_multi_char_content_with_tab_separator():
    assert parse_line("one\ttwo\tthree", "\t") == ["one", "two", "three"]


def test_space_separator():
    assert parse_line("a b", " ") == ["a", "b"]


def test_separator_that_is_a_letter():
    assert parse_line("xaxbx", "x") == ["", "a", "b", ""]


# --- whitespace is kept -----------------------------------------------------

def test_whitespace_is_not_trimmed():
    assert parse_line(" a , b") == [" a ", " b"]


def test_whitespace_only_field_is_kept():
    assert parse_line("   ") == ["   "]


def test_tab_inside_field_is_kept():
    assert parse_line("a\tb,c") == ["a\tb", "c"]


# --- quoted fields ----------------------------------------------------------

def test_quoted_field_with_separator():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_becomes_one_quote():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_empty_quoted_field():
    assert parse_line('""') == [""]


def test_empty_quoted_fields_around_separator():
    assert parse_line('"",""') == ["", ""]


def test_quoted_field_followed_by_empty_field():
    assert parse_line('"a",') == ["a", ""]


def test_quoted_field_keeps_whitespace_inside():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_quoted_field_keeps_newline_inside():
    assert parse_line('"a\nb",c') == ["a\nb", "c"]


def test_quoted_field_keeps_carriage_return_inside():
    assert parse_line('"a\rb"') == ["a\rb"]


def test_quoted_field_keeps_crlf_inside():
    assert parse_line('"a\r\nb"') == ["a\r\nb"]


def test_quoted_field_with_custom_separator_inside():
    assert parse_line('"a;b";c', ";") == ["a;b", "c"]


def test_quoted_field_with_comma_when_sep_is_semicolon():
    assert parse_line('"a,b";c', ";") == ["a,b", "c"]


def test_only_doubled_quotes():
    assert parse_line('""""') == ['"']


def test_three_doubled_quotes_inside():
    assert parse_line('""""""""') == ['"""']


def test_quoted_field_then_quoted_field():
    assert parse_line('"a","b"') == ["a", "b"]


def test_mixed_quoted_and_plain_fields():
    assert parse_line('x,"y,z",w') == ["x", "y,z", "w"]


def test_quoted_field_ending_at_end_of_line_with_doubled_quote_before_it():
    assert parse_line('"a"""') == ['a"']


def test_quote_char_as_sep_is_not_allowed_even_in_quoted_context():
    with pytest.raises(ValueError):
        parse_line('"a"', '"')


def test_quoted_field_then_separator_then_plain_field_with_space():
    assert parse_line('"a", b') == ["a", " b"]


# --- errors: type ----------------------------------------------------------

def test_line_must_be_str():
    with pytest.raises(TypeError):
        parse_line(123)


def test_line_none_is_type_error():
    with pytest.raises(TypeError):
        parse_line(None)


def test_line_bytes_is_type_error():
    with pytest.raises(TypeError):
        parse_line(b"a,b")


def test_sep_must_be_str():
    with pytest.raises(TypeError):
        parse_line("a,b", 1)


def test_sep_none_is_type_error():
    with pytest.raises(TypeError):
        parse_line("a,b", None)


def test_sep_bytes_is_type_error():
    with pytest.raises(TypeError):
        parse_line("a,b", b",")


# --- errors: sep value -----------------------------------------------------

def test_empty_sep_is_value_error():
    with pytest.raises(ValueError):
        parse_line("a,b", "")


def test_multi_char_sep_is_value_error():
    with pytest.raises(ValueError):
        parse_line("a,b", ",,")


def test_sep_double_quote_is_value_error():
    with pytest.raises(ValueError):
        parse_line("a,b", '"')


def test_sep_cr_is_value_error():
    with pytest.raises(ValueError):
        parse_line("a\rb", "\r")


def test_sep_lf_is_value_error():
    with pytest.raises(ValueError):
        parse_line("a\nb", "\n")


# --- errors: quoting -------------------------------------------------------

def test_unclosed_quoted_field():
    with pytest.raises(ValueError):
        parse_line('"abc')


def test_lone_opening_quote():
    with pytest.raises(ValueError):
        parse_line('"')


def test_unclosed_quote_after_doubled_quote():
    with pytest.raises(ValueError):
        parse_line('"a""')


def test_unclosed_quoted_field_after_separator():
    with pytest.raises(ValueError):
        parse_line('a,"b,c')


def test_char_after_closing_quote_is_error():
    with pytest.raises(ValueError):
        parse_line('"a"b')


def test_space_after_closing_quote_is_error():
    with pytest.raises(ValueError):
        parse_line('"a" ,b')


def test_text_after_closing_quote_without_separator_is_error():
    with pytest.raises(ValueError):
        parse_line('"a"x"')


def test_quote_inside_plain_field_is_error():
    with pytest.raises(ValueError):
        parse_line('a"b')


def test_quote_inside_plain_field_after_separator_is_error():
    with pytest.raises(ValueError):
        parse_line('x,a"b')


def test_quote_at_end_of_plain_field_is_error():
    with pytest.raises(ValueError):
        parse_line('a"')


# --- errors: CR / LF outside quotes ---------------------------------------

def test_lf_outside_quotes_is_error():
    with pytest.raises(ValueError):
        parse_line("a\nb")


def test_cr_outside_quotes_is_error():
    with pytest.raises(ValueError):
        parse_line("a\rb")


def test_crlf_outside_quotes_is_error():
    with pytest.raises(ValueError):
        parse_line("a\r\nb")


def test_lf_after_separator_outside_quotes_is_error():
    with pytest.raises(ValueError):
        parse_line("a,\nb")


def test_lf_after_closing_quote_is_error():
    with pytest.raises(ValueError):
        parse_line('"a"\n')
