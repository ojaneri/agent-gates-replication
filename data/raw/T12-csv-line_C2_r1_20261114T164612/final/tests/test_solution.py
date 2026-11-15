import pytest

from solution import parse_line


# --- basic splitting -------------------------------------------------------

def test_simple_fields():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_single_field_no_separator():
    assert parse_line("abc") == ["abc"]


def test_empty_line_gives_one_empty_field():
    assert parse_line("") == [""]


def test_trailing_separator_gives_empty_last_field():
    assert parse_line("a,") == ["a", ""]


def test_only_separator_gives_two_empty_fields():
    assert parse_line(",") == ["", ""]


def test_two_separators_give_three_empty_fields():
    assert parse_line(",,") == ["", "", ""]


def test_leading_separator_gives_empty_first_field():
    assert parse_line(",a") == ["", "a"]


def test_whitespace_is_kept():
    assert parse_line(" a , b") == [" a ", " b"]


def test_whitespace_only_field_is_kept():
    assert parse_line(" , ") == [" ", " "]


def test_default_separator_is_comma():
    assert parse_line("x,y") == parse_line("x,y", ",") == ["x", "y"]


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]


def test_comma_is_ordinary_with_other_separator():
    assert parse_line("a,b", sep=";") == ["a,b"]


def test_space_separator():
    assert parse_line("a b", sep=" ") == ["a", "b"]


def test_tab_separator():
    assert parse_line("a\tb", sep="\t") == ["a", "b"]


def test_result_is_a_list_of_str():
    result = parse_line("a,b")
    assert isinstance(result, list)
    assert all(isinstance(f, str) for f in result)


# --- quoted fields ---------------------------------------------------------

def test_quoted_field_with_separator_inside():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_quoted_field_strips_quotes():
    assert parse_line('"abc"') == ["abc"]


def test_doubled_quote_inside_quoted_field():
    assert parse_line('"say ""hi"""') == ['say "hi"']


def test_empty_quoted_field():
    assert parse_line('""') == [""]


def test_empty_quoted_field_then_field():
    assert parse_line('"",x') == ["", "x"]


def test_quoted_field_then_trailing_separator():
    assert parse_line('"a",') == ["a", ""]


def test_quoted_field_in_the_middle():
    assert parse_line('a,"b,c",d') == ["a", "b,c", "d"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_quoted_field_keeps_newline():
    assert parse_line('"a\nb",c') == ["a\nb", "c"]


def test_quoted_field_keeps_carriage_return():
    assert parse_line('"a\rb"') == ["a\rb"]


def test_quoted_field_with_custom_separator_inside():
    assert parse_line('"a,b";c', sep=";") == ["a,b", "c"]


def test_doubled_quote_as_whole_value():
    assert parse_line('""""') == ['"']


def test_doubled_quote_then_separator():
    assert parse_line('"x""",y') == ['x"', "y"]


def test_quoted_field_containing_only_separator():
    assert parse_line('","') == [","]


# --- errors ----------------------------------------------------------------

@pytest.mark.parametrize("line", [
    '"abc',          # unclosed quote
    '"a""',          # doubled quote leaves field unclosed
    '"""',           # opening quote, doubled quote, no closing quote
    'a,"b',          # unclosed quote after a separator
])
def test_unclosed_quote_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", [
    '"a"b',          # character right after closing quote
    '"a" ,b',        # space after closing quote
    'a,"b"c,d',      # junk after closing quote mid-line
    '"a"""b"',       # closing quote followed by non-separator
])
def test_character_after_closing_quote_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", [
    'a"b',           # quote inside unquoted field
    'a,b"',          # trailing quote in unquoted field
    '"a",b"c',       # quote inside a later unquoted field
])
def test_quote_inside_unquoted_field_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ["a\nb", "a\rb", "a,b\n", "a\r\nb"])
def test_line_break_outside_quotes_raises(line):
    with pytest.raises(ValueError):
        parse_line(line)


# --- argument validation ---------------------------------------------------

@pytest.mark.parametrize("line", [None, 1, b"a,b", ["a"]])
def test_line_must_be_str(line):
    with pytest.raises(TypeError):
        parse_line(line)


@pytest.mark.parametrize("sep", [None, 1, b",", [","]])
def test_sep_must_be_str(sep):
    with pytest.raises(TypeError):
        parse_line("a,b", sep)


@pytest.mark.parametrize("sep", ["", "ab", ",,", "  "])
def test_sep_must_be_one_character(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep)


@pytest.mark.parametrize("sep", ['"', "\r", "\n"])
def test_sep_must_not_be_quote_or_line_break(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep)


def test_type_error_checked_before_value_error():
    with pytest.raises(TypeError):
        parse_line(5, "")
