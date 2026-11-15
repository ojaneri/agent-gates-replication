import pytest

from solution import check_password

GOOD = "Tr0ub4dor&3xyz"  # 14 chars, lower/upper/digit/other


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(123, "alice", set())
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())
    with pytest.raises(TypeError):
        check_password(b"bytes-password!", "alice", set())


@pytest.mark.parametrize("length", [12, 64])
def test_length_bounds_allowed(length):
    pw = ("Aa1!" * 16)[:length]
    assert "LENGTH" not in check_password(pw, "zzz", set())


@pytest.mark.parametrize("length", [0, 11, 65, 100])
def test_length_out_of_bounds(length):
    pw = ("Aa1!" * 30)[:length]
    assert "LENGTH" in check_password(pw, "zzz", set())


def test_classes_three_is_enough():
    # lower, upper, digit only -> 3 classes
    assert "CLASSES" not in check_password("abcDEF123xyz", "zzz", set())


def test_classes_two_is_violation():
    # lower + upper only
    assert "CLASSES" in check_password("abcdefGHIJKLM", "zzz", set())


def test_classes_other_counts_for_space_punct_and_non_ascii():
    # lower, upper, other (space) -> 3 classes
    assert "CLASSES" not in check_password("abcDEF ghijk", "zzz", set())
    # digit + other + lower -> 3 classes, non-ascii é counts as other
    assert "CLASSES" not in check_password("1234é5678abc", "zzz", set())
    # only digits and punctuation -> 2 classes
    assert "CLASSES" in check_password("1234!@#$%^&*()", "zzz", set())


def test_username_substring_case_insensitive():
    pw = "Xx-ALICE-yy-9876"
    assert "USERNAME" in check_password(pw, "alice", set())


def test_username_short_never_triggers():
    pw = "Xx-ab-yy-98765"
    assert "USERNAME" not in check_password(pw, "ab", set())


def test_username_absent_not_violated():
    assert "USERNAME" not in check_password(GOOD, "bobby", set())


def test_repeat_three_in_a_row_violates():
    assert "REPEAT" in check_password("Abcdefgh111ijk", "zzz", set())


def test_repeat_two_in_a_row_ok():
    assert "REPEAT" not in check_password("Abcdefgh11ijkL", "zzz", set())


def test_repeat_is_case_sensitive():
    assert "REPEAT" not in check_password("aAaBcDeFgHiJ1", "zzz", set())


def test_blocklist_equality_case_insensitive():
    pw = "Password12345"
    assert "BLOCKLIST" in check_password(pw, "zzz", {"PASSWORD12345"})


def test_blocklist_containment_is_not_violation():
    pw = "xxPassword12345yy"
    assert "BLOCKLIST" not in check_password(pw, "zzz", {"password12345"})


def test_rules_reported_in_order():
    # too short, only 1 class, username present, repeats, blocklisted
    pw = "aaaa"
    result = check_password(pw, "aaa", {"aaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_multiple_violations_subset_order():
    result = check_password("abcdefghijkl", "zzz", set())
    assert result == ["CLASSES"]
