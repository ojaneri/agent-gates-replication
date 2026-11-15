import pytest

from solution import check_password

GOOD = "Tr0ub4dor&3xyz"  # 14 chars, all 4 classes, no triple repeats


def test_valid_password_has_no_violations():
    assert check_password(GOOD, "alice", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(123, "alice", set())
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())


def test_non_str_username_short_list_still_raises():
    # len(["x"]) is 1, so a lenient check would silently accept this
    with pytest.raises(TypeError):
        check_password(GOOD, ["x"], set())


def test_non_str_password_with_str_username_raises():
    with pytest.raises(TypeError):
        check_password(["x" * 12], "alice", set())


# LENGTH
def test_length_lower_boundary():
    assert "LENGTH" in check_password("Abcdefghij1"[:11], "zz", set())  # 11
    assert "LENGTH" not in check_password("Abcdefghij1x", "zz", set())  # 12


def test_length_upper_boundary():
    assert "LENGTH" not in check_password("Ab1" + "x" * 61, "zz", set())  # 64
    assert "LENGTH" in check_password("Ab1" + "x" * 62, "zz", set())  # 65


# CLASSES
def test_three_classes_passes():
    assert "CLASSES" not in check_password("abcdefghijK1", "zz", set())  # lower, upper, digit
    assert "CLASSES" not in check_password("abcdefgh1 K", "zz", set())  # + space (other)


def test_two_classes_violates():
    assert "CLASSES" in check_password("abcdefghijkl", "zz", set())  # only lower
    assert "CLASSES" in check_password("abcdefghijk1", "zz", set())  # lower + digit
    assert "CLASSES" in check_password("abcdefghijk!", "zz", set())  # lower + other
    assert "CLASSES" in check_password("ABCDEFGHIJK1", "zz", set())  # upper + digit


def test_other_class_includes_non_ascii_and_punctuation():
    assert "CLASSES" not in check_password("abcdefghijKé", "zz", set())  # lower, upper, é
    assert "CLASSES" not in check_password("abcdefghijK ", "zz", set())  # lower, upper, space


@pytest.mark.parametrize(
    "endpoint, twin, third",
    [
        ("a", "b", "B"),  # lowercase bounds: a, z
        ("z", "y", "B"),
        ("A", "B", "b"),  # uppercase bounds: A, Z
        ("Z", "Y", "b"),
        ("0", "5", "B"),  # digit bounds: 0, 9
        ("9", "8", "B"),
    ],
)
def test_class_bounds_are_inclusive(endpoint, twin, third):
    # Only two classes really present; treating the endpoint as "other" would wrongly give three.
    assert "CLASSES" in check_password(endpoint + twin + third, "zz", set())


def test_non_ascii_letter_is_not_lowercase():
    # "é" counts as other, not lowercase: lower + other = 2 classes
    assert "CLASSES" in check_password("abcdefghijkél", "zz", set())


# USERNAME
def test_username_inside_password_violates():
    assert "USERNAME" in check_password("Xq7alice" + "Zz9pad", "alice", set())


def test_username_match_is_case_insensitive():
    assert "USERNAME" in check_password("Xq7ALICE" + "Zz9pad", "alice", set())


def test_short_username_never_triggers():
    assert "USERNAME" not in check_password("Xq7ab" + "Zz9padab", "ab", set())


def test_username_of_length_three_triggers():
    assert "USERNAME" in check_password("Xq7bob" + "Zz9pad", "bob", set())


def test_username_absent_does_not_trigger():
    assert "USERNAME" not in check_password(GOOD, "carol", set())


# REPEAT
def test_three_in_a_row_violates():
    assert "REPEAT" in check_password("Abcdefghi111", "zz", set())


def test_two_in_a_row_is_fine():
    assert "REPEAT" not in check_password("Abcdefgh1122", "zz", set())


def test_repeat_is_case_sensitive():
    assert "REPEAT" not in check_password("aAaBbcdef1X!", "zz", set())


def test_repeat_run_not_at_start():
    assert "REPEAT" in check_password("Abcdefgh!xxx", "zz", set())


def test_repeat_run_resets_correctly():
    assert "REPEAT" not in check_password("aabbcdefgh1X", "zz", set())


# BLOCKLIST
def test_blocklist_equality_violates_case_insensitively():
    assert "BLOCKLIST" in check_password(GOOD, "zz", {GOOD.upper()})


def test_blocklist_substring_is_not_violation():
    assert "BLOCKLIST" not in check_password(GOOD, "zz", {"tr0ub"})


def test_blocklist_entry_uppercase_matches():
    assert "BLOCKLIST" in check_password(GOOD.lower(), "zz", {GOOD})


# ORDER and combinations
def test_all_violations_in_documented_order():
    pw = "aliceaaa"  # 8 chars, 1 class, contains "alice", has "aaa"
    result = check_password(pw, "alice", {pw})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_subset_preserved():
    assert check_password("aaa", "zz", {"aaa"}) == ["LENGTH", "CLASSES", "REPEAT", "BLOCKLIST"]
