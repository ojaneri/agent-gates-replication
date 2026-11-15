import pytest

from solution import parse_line


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
        (" a , b", [" a ", " b"]),
        ("a;b", ["a;b"]),
    ],
)
def test_unquoted_fields(line, expected):
    assert parse_line(line) == expected


def test_custom_separator():
    assert parse_line("a;b;c", sep=";") == ["a", "b", "c"]
    assert parse_line("a,b", sep=";") == ["a,b"]
    assert parse_line("a\tb", sep="\t") == ["a", "b"]
    assert parse_line(" ", sep=" ") == ["", ""]


def test_quoted_fields():
    assert parse_line('"a,b",c') == ["a,b", "c"]
    assert parse_line('"say ""hi"""') == ['say "hi"']
    assert parse_line('""') == [""]
    assert parse_line('"",""') == ["", ""]
    assert parse_line('"a"') == ["a"]
    assert parse_line('x,"a"') == ["x", "a"]


def test_quoted_field_allows_newlines_and_cr():
    assert parse_line('"a\nb",c') == ["a\nb", "c"]
    assert parse_line('"a\rb"') == ["a\rb"]


def test_quoted_field_keeps_whitespace():
    assert parse_line('" a ",b') == [" a ", "b"]


def test_doubled_quote_at_end_of_quoted_field():
    assert parse_line('"a"""') == ['a"']


def test_quoted_field_with_custom_separator():
    assert parse_line('"a;b";c', sep=";") == ["a;b", "c"]


@pytest.mark.parametrize("line", ['"abc', '"a""', '"', '"a,b'])
def test_unterminated_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['"a"b', '"a" ,b', '"a"\r', '"a"x,"b"'])
def test_junk_after_closing_quote(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ['a"b', 'a,b"', '"a",b"c'])
def test_quote_inside_unquoted_field(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("line", ["a\rb", "a\nb", "a,b\n", "\r"])
def test_cr_or_lf_outside_quotes(line):
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize("sep", ["", "ab", '"', "\r", "\n"])
def test_invalid_separator_value(sep):
    with pytest.raises(ValueError):
        parse_line("a,b", sep=sep)


@pytest.mark.parametrize(
    "line, sep",
    [(None, ","), (1, ","), (b"a,b", ","), ("a,b", None), ("a,b", 1)],
)
def test_wrong_types(line, sep):
    with pytest.raises(TypeError):
        parse_line(line, sep)


def test_default_separator_is_comma():
    assert parse_line("x,y") == ["x", "y"]
