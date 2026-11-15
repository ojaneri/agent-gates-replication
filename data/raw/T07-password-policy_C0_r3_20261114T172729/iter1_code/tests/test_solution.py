import pytest

from solution import check_password

GOOD = "Tr0ub4dor&3xyz"  # 14 chars, lower/upper/digit/other, no repeat


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(None, "alice", set())
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())
    with pytest.raises(TypeError):
        check_password(123, "alice", set())


@pytest.mark.parametrize("length,expected", [
    (11, True), (12, False), (64, False), (65, True),
])
def test_length_bounds(length, expected):
    pw = ("Ab1!" * 20)[:length]
    # avoid REPEAT/other side effects: pattern "Ab1!" has no repeats
    result = check_password(pw, "zzzzz", set())
    assert ("LENGTH" in result) is expected


def test_classes_three_of_four_ok():
    # lower, upper, digit only -> 3 classes
    assert "CLASSES" not in check_password("abcDEF123xyz", "qqqq", set())


def test_classes_two_fails():
    assert "CLASSES" in check_password("abcdefghijklmn", "qqqq", set())
    assert "CLASSES" in check_password("ABCDEFGHIJKLMN12", "qqqq", set())


def test_non_ascii_letter_counts_as_other():
    # lower + upper + é (other) -> 3 classes
    assert "CLASSES" not in check_password("abcDEFghiJKé", "qqqq", set())


def test_space_counts_as_other():
    assert "CLASSES" not in check_password("abcDEFghi 1", "qqqq", set())


def test_username_substring_case_insensitive():
    assert "USERNAME" in check_password("xxALICE" + GOOD, "alice", set())


def test_username_short_never_triggers():
    # username "ab" (2 chars) appears in password but must not trigger
    pw = "Tr0ub4dorab&3xyz"
    assert "USERNAME" not in check_password(pw, "ab", set())


def test_username_three_chars_triggers_exact_length():
    assert "USERNAME" in check_password("Tr0ub4dorBOB&3x", "bob", set())


def test_repeat_three_in_row():
    assert "REPEAT" in check_password("Tr0uuub4dor&3x", "qqqq", set())


def test_repeat_case_sensitive():
    assert "REPEAT" not in check_password("Tr0aAab4dor&3x", "qqqq", set())


def test_repeat_two_in_row_ok():
    assert "REPEAT" not in check_password("Tr0uub4dor&3xy", "qqqq", set())


def test_blocklist_equality_case_insensitive():
    assert "BLOCKLIST" not in check_password("Password12345x", "qqqq", {"password12345"})
    assert "BLOCKLIST" in check_password("PASSWORD12345", "qqqq", {"password12345"})
    assert "BLOCKLIST" in check_password("password12345", "qqqq", {"PassWord12345"})


def test_blocklist_containment_not_violation():
    assert "BLOCKLIST" not in check_password(GOOD + "extra", "qqqq", {"tr0ub4dor"})


def test_order_of_codes():
    # length 5 (LENGTH), only lowercase (CLASSES), contains username "bobby" (USERNAME),
    # repeats "aaa" (REPEAT), equals blocklist entry (BLOCKLIST)
    pw = "aaaaa"
    result = check_password(pw, "aaaaa", {"aaaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_subset():
    result = check_password("Tr0uuub4dor&3x", "qqqq", {"tr0uuub4dor&3x"})
    assert result == ["REPEAT", "BLOCKLIST"]
