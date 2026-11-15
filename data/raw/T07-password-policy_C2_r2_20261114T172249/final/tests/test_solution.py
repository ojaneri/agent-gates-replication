import pytest

from solution import _has_three_classes, _has_triple_repeat, check_password

GOOD = "Abcdefghij1!"  # 12 chars, lower, upper, digit, other; no repeat


@pytest.mark.parametrize("ch", ["a", "z", "m"])
def test_lower_boundary_chars_are_lower(ch):
    # Only True if ch counts as lowercase (otherwise just upper + digit = 2 classes)
    assert _has_three_classes(ch + "A0") is True


@pytest.mark.parametrize("ch", ["A", "Z", "M"])
def test_upper_boundary_chars_are_upper(ch):
    # Only True if ch counts as uppercase (otherwise just lower + digit = 2 classes)
    assert _has_three_classes("a" + ch + "0") is True


@pytest.mark.parametrize("ch", ["0", "9", "5"])
def test_digit_boundary_chars_are_digits(ch):
    assert _has_three_classes("a" + "A" + ch) is True


@pytest.mark.parametrize("ch", ["@", "[", "`", "{", "/", ":", " ", "é"])
def test_other_boundary_chars_count_as_other(ch):
    assert _has_three_classes("a" + "A" + ch) is True
    assert _has_three_classes("aA" + ch) is True


@pytest.mark.parametrize("ch", ["@", "[", "`", "{", "/", ":"])
def test_other_boundary_alone_is_one_class(ch):
    assert _has_three_classes("a" + ch * 2) is False


def test_two_classes_not_enough():
    assert _has_three_classes("aaaa0000") is False
    assert _has_three_classes("AAAA0000") is False


def test_triple_repeat_helper_false_when_none():
    assert _has_triple_repeat("abcabc") is False
    assert _has_triple_repeat("ab") is False
    assert _has_triple_repeat("") is False


def test_triple_repeat_helper_true_when_present():
    assert _has_triple_repeat("xaaay") is True


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


def test_type_error_on_non_str_password():
    with pytest.raises(TypeError):
        check_password(123, "alice", set())


def test_type_error_on_non_str_username():
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())


def test_length_min_boundary_ok():
    assert "LENGTH" not in check_password("Abcdefghi1!x", "zz", set())  # 12 chars


def test_length_too_short():
    assert check_password("Abcdefghi1!", "zz", set()) == ["LENGTH"]  # 11 chars


def test_length_max_boundary_ok():
    pw = ("Abcdefghi1!" * 6)[:64]
    assert len(pw) == 64
    assert "LENGTH" not in check_password(pw, "zz", set())


def test_length_too_long():
    pw = ("Abcdefghi1!" * 6)[:64] + "x"
    assert check_password(pw, "zz", set()) == ["LENGTH"]


def test_classes_three_is_ok():
    # lower, upper, digit only: 3 classes
    assert "CLASSES" not in check_password("Abcdefghij12", "zz", set())


def test_classes_two_is_violation():
    assert check_password("abcdefghijkl", "zz", set()) == ["CLASSES"]


def test_classes_other_counts_as_class():
    # lower, upper, other
    assert "CLASSES" not in check_password("abcdefghijK ", "zz", set())


def test_classes_digit_and_other_only():
    assert check_password("123456789012!", "zz", set()) == ["CLASSES"]


def test_classes_non_ascii_is_other():
    # lower, upper, non-ascii letter -> 3 classes
    assert "CLASSES" not in check_password("abcdefghijKé", "zz", set())


def test_classes_non_ascii_alone_not_enough():
    assert check_password("éaéaéaéaéaéa", "zz", set()) == ["CLASSES"]


def test_username_inside_password_violates():
    pw = "Xyzalice12345!"
    assert check_password(pw, "alice", set()) == ["USERNAME"]


def test_username_match_is_case_insensitive():
    pw = "XyzALICE12345!"
    assert check_password(pw, "alice", set()) == ["USERNAME"]


def test_username_short_never_triggers():
    pw = "Abcdefghij1!ab"
    assert "USERNAME" not in check_password(pw, "ab", set())


def test_username_length_three_triggers():
    pw = "Abcdefghij1!abc"
    assert "USERNAME" in check_password(pw, "abc", set())


def test_username_absent_ok():
    assert "USERNAME" not in check_password(GOOD, "bobby", set())


def test_repeat_three_in_row_violates():
    pw = "Abcdeeefghi1!"
    assert check_password(pw, "zz", set()) == ["REPEAT"]


def test_repeat_at_end_violates():
    pw = "Abcdefghi1!!!"
    assert check_password(pw, "zz", set()) == ["REPEAT"]


def test_repeat_two_in_row_ok():
    pw = "Abcdeefghi1!"
    assert "REPEAT" not in check_password(pw, "zz", set())


def test_repeat_is_case_sensitive():
    pw = "Abcdefghi1aAa"
    assert "REPEAT" not in check_password(pw, "zz", set())


def test_repeat_non_adjacent_ok():
    pw = "Abcdaefgaaxhi1!"
    assert "REPEAT" not in check_password(pw, "zz", set())


def test_blocklist_exact_match_violates():
    assert check_password(GOOD, "zz", {GOOD.lower()}) == ["BLOCKLIST"]


def test_blocklist_case_insensitive_entry_and_password():
    assert check_password(GOOD, "zz", {GOOD.upper()}) == ["BLOCKLIST"]


def test_blocklist_substring_is_not_violation():
    assert "BLOCKLIST" not in check_password(GOOD, "zz", {"abcdef"})


def test_blocklist_not_present_ok():
    assert "BLOCKLIST" not in check_password(GOOD, "zz", {"other"})


def test_multiple_violations_in_order():
    # too short, 1 class, username inside, repeat, blocklisted
    result = check_password("aaaa", "aaa", {"aaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_of_codes_for_partial_violations():
    # 12 chars, only lower -> CLASSES; contains "bob" -> USERNAME; no triple repeat
    assert check_password("bobbobbobbob", "bob", set()) == ["CLASSES", "USERNAME"]
