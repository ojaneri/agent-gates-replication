import pytest

from solution import check_password

GOOD = "Tr0ub4dor&3xyz"  # 14 chars, 4 classes, no triple repeat
USER = "alice"
EMPTY_BL: set[str] = set()


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, USER, EMPTY_BL) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(None, USER, EMPTY_BL)
    with pytest.raises(TypeError):
        check_password(GOOD, None, EMPTY_BL)
    with pytest.raises(TypeError):
        check_password(123, USER, EMPTY_BL)
    with pytest.raises(TypeError):
        check_password(GOOD, b"alice", EMPTY_BL)


# LENGTH: 12..64 inclusive, built from a 4-class base with no triple repeats
def _pw(n: int) -> str:
    base = "Aa1!"
    return (base * (n // 4 + 1))[:n]


def test_length_lower_boundary():
    assert len(_pw(11)) == 11
    assert check_password(_pw(11), USER, EMPTY_BL) == ["LENGTH"]
    assert len(_pw(12)) == 12
    assert check_password(_pw(12), USER, EMPTY_BL) == []


def test_length_upper_boundary():
    assert len(_pw(64)) == 64
    assert check_password(_pw(64), USER, EMPTY_BL) == []
    assert len(_pw(65)) == 65
    assert check_password(_pw(65), USER, EMPTY_BL) == ["LENGTH"]


def test_length_empty_password():
    assert "LENGTH" in check_password("", USER, EMPTY_BL)


# CLASSES
def test_two_classes_fails():
    assert check_password("abcdefghijkl", USER, EMPTY_BL) == ["CLASSES"]


def test_three_classes_passes():
    assert check_password("abcdefghijA1", USER, EMPTY_BL) == []  # lower, upper, digit


def test_other_class_counts_including_non_ascii():
    assert check_password("abcdefghijK é", USER, EMPTY_BL) == []  # lower, upper, space
    assert check_password("ABCDEFGHIJ1é", USER, EMPTY_BL) == []  # upper, digit, non-ASCII
    assert check_password("ABCDEFGHIJKLM ", USER, EMPTY_BL) == ["CLASSES"]  # upper + space only


# USERNAME
def test_username_inside_password_case_insensitive():
    pw = "xxALICE1!xyzabcdef"
    assert "USERNAME" in check_password(pw, "AlIcE", EMPTY_BL)


def test_username_shorter_than_three_never_triggers():
    pw = "ab" + "Cd1!efghijk"
    assert "USERNAME" not in check_password(pw, "ab", EMPTY_BL)
    assert "USERNAME" not in check_password(pw, "", EMPTY_BL)


def test_username_three_chars_triggers():
    pw = "Xyz1!" + "AbAbAbAb" + "q"
    assert "USERNAME" in check_password(pw, "XYZ", EMPTY_BL)


def test_username_absent_does_not_trigger():
    assert "USERNAME" not in check_password(GOOD, "bobby", EMPTY_BL)


# REPEAT
def test_triple_repeat_violates():
    assert check_password("Abc1!defgh000", USER, EMPTY_BL) == ["REPEAT"]


def test_double_repeat_ok():
    assert check_password("Abc1!defgh00x", USER, EMPTY_BL) == []


def test_repeat_is_case_sensitive():
    assert check_password("aAaBcd1!efgh", USER, EMPTY_BL) == []


# BLOCKLIST
def test_blocklist_equality_case_insensitive():
    assert check_password(GOOD, USER, {"TR0UB4DOR&3XYZ"}) == ["BLOCKLIST"]


def test_blocklist_containment_is_not_violation():
    assert check_password(GOOD, USER, {"tr0ub4"}) == []


# ORDER
def test_multiple_violations_in_rule_order():
    pw = "alice000"  # short, two classes, contains username, triple repeat, blocklisted
    assert check_password(pw, "alice", {"ALICE000"}) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
        "REPEAT",
        "BLOCKLIST",
    ]


def test_all_violations_in_order_on_long_password():
    pw = "aaaa" + "b" * 70  # too long, lower only, username, repeat, blocklisted
    assert check_password(pw, "aaaa", {pw.upper()}) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
        "REPEAT",
        "BLOCKLIST",
    ]
