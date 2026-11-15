import pytest

from solution import check_password

GOOD = "Correct-Horse7"   # 14 chars, lower, upper, digit, other


def test_valid_password():
    assert check_password(GOOD, "alice", set()) == []


@pytest.mark.parametrize("pw,ok", [("Abcdefgh1-x", False), ("Abcdefgh1-xy", True),
                                   ("Ab1-" + "x" * 60, True), ("Ab1-" + "x" * 61, False)])
def test_length_bounds(pw, ok):
    pw = pw.replace("xxx", "xyx")  # avoid repeats
    assert ("LENGTH" not in check_password(pw, "zz", set())) is ok


def test_length_exact_64_and_65():
    base = "Ab1-" + "xy" * 30          # 64 chars, no repeats
    assert len(base) == 64 and check_password(base, "zz", set()) == []
    assert check_password(base + "z", "zz", set()) == ["LENGTH"]


def test_three_classes_enough():
    assert check_password("abcdefghijk1-", "zz", set()) == []      # lower, digit, other
    assert check_password("ABCDEFGHIJK1z", "zz", set()) == []      # upper, digit, lower


@pytest.mark.parametrize("pw", ["BCDEFGHIJK-a", "BCDEFGHIJK-z", "bcdefghijk-A", "bcdefghijk-Z",
                                "BCDEFGHIJK-0", "BCDEFGHIJK-9"])
def test_class_boundary_characters(pw):
    # the last character is the only member of its class
    assert check_password(pw, "zz", set()) == []


def test_repeat_at_the_end():
    assert check_password("Correct-Hor777", "zz", set()) == ["REPEAT"]


def test_two_classes_violate():
    assert check_password("abcdefghijkl1", "zz", set()) == ["CLASSES"]
    assert check_password("abcdefghijklm", "zz", set()) == ["CLASSES"]


def test_non_ascii_letter_counts_as_other():
    # lower ASCII + digit + 'é' (other) -> 3 classes
    assert check_password("abcdefghijk1é", "zz", set()) == []
    # only lower ASCII and 'é' -> 2 classes
    assert check_password("abcdefghijklé", "zz", set()) == ["CLASSES"]


def test_space_counts_as_other():
    assert check_password("abcdefgh ijk1", "zz", set()) == []


def test_username_case_insensitive():
    assert check_password("xxAlIcExx-Y1z", "alice", set()) == ["USERNAME"]


def test_short_username_ignored():
    assert check_password("Correct-Ho7se", "Ho", set()) == []


def test_username_of_exactly_three():
    assert check_password("Correct-Bob7x", "bob", set()) == ["USERNAME"]


def test_repeat_three():
    assert check_password("Corrrect-Hor7", "zz", set()) == ["REPEAT"]


def test_two_in_a_row_is_fine():
    assert check_password("Corrappend-H7", "zz", set()) == []


def test_repeat_is_case_sensitive():
    assert check_password("CoaAarect-Hr7", "zz", set()) == []


def test_repeat_of_other_characters():
    assert check_password("Correct---Ho7", "zz", set()) == ["REPEAT"]


def test_blocklist_equality_case_insensitive():
    assert check_password("Password-1234", "zz", {"PASSWORD-1234"}) == ["BLOCKLIST"]


def test_blocklist_substring_not_a_violation():
    assert check_password("Password-12345", "zz", {"password"}) == []


def test_order_of_all_violations():
    # short, one class, contains username, repeat, blocklisted
    assert check_password("aaabob", "bob", {"AAABOB"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_empty_password():
    assert check_password("", "bob", set()) == ["LENGTH", "CLASSES"]


@pytest.mark.parametrize("pw,user", [(None, "a"), ("abc", None), (123, "a"), (b"bytes", "a"),
                                     (["Correct-Horse7"], "alice"), ("Correct-Horse7", ["alice"])])
def test_type_errors(pw, user):
    with pytest.raises(TypeError):
        check_password(pw, user, set())
