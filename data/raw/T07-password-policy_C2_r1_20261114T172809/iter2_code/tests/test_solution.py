import pytest

from solution import _LOWER, _UPPER, _DIGIT, _OTHER, _class_of, _contains_username, check_password

GOOD = "Tr0ub4dor&Horse"  # 16 chars, lower/upper/digit/other, no repeats


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


# --- TypeError ---

@pytest.mark.parametrize("pwd, user", [(123, "alice"), (GOOD, None), (None, None), (b"x", "a")])
def test_non_str_raises_type_error(pwd, user):
    with pytest.raises(TypeError, match="must be str"):
        check_password(pwd, user, set())


# --- LENGTH ---

def test_length_11_violates():
    assert check_password("Ab1!" * 2 + "Abc", "zz", set()) == ["LENGTH"]


def test_length_12_ok_lower_bound():
    pwd = "Ab1!Ab1!Ab1!"  # 12 chars, no repeats
    assert len(pwd) == 12
    assert check_password(pwd, "zz", set()) == []


def test_length_64_ok_upper_bound():
    pwd = ("Ab1!" * 16)  # 64 chars, no triple repeats
    assert len(pwd) == 64
    assert check_password(pwd, "zz", set()) == []


def test_length_65_violates():
    pwd = ("Ab1!" * 16) + "x"  # 65 chars
    assert len(pwd) == 65
    assert check_password(pwd, "zz", set()) == ["LENGTH"]


def test_empty_password_violates_length_and_classes():
    assert check_password("", "zz", set()) == ["LENGTH", "CLASSES"]


# --- CLASSES ---

def test_two_classes_violates():
    pwd = "abcdefghijkl"  # 12 lower only
    assert check_password(pwd, "zz", set()) == ["CLASSES"]


def test_three_classes_ok():
    assert check_password("abcdefghijk1", "zz", set()) == ["CLASSES"]  # lower + digit only
    assert check_password("abcdefghijA1", "zz", set()) == []  # lower + upper + digit


def test_lower_upper_digit_ok():
    assert check_password("abcdefgHIJ12", "zz", set()) == []


def test_lower_upper_other_ok():
    assert check_password("abcdefgHIJ!!", "zz", set()) == []


def test_digit_upper_other_ok():
    assert check_password("ABCDEFGHI12!", "zz", set()) == []


def test_non_ascii_counts_as_other():
    # lower + upper + non-ASCII 'é' => three classes
    assert check_password("abcdefgHIJé1", "zz", set()) == []


def test_non_ascii_alone_is_not_a_class_substitute():
    # lower + 'é' + 'É' (non-ASCII upper is "other" too) => only 2 classes
    assert check_password("abcdefghijkéé", "zz", set()) == ["CLASSES"]


def test_space_counts_as_other():
    assert check_password("abcdefgHIJ 1", "zz", set()) == []


def test_classes_boundaries_ascii():
    # Punctuation just outside the A-Z, a-z and 0-9 ranges counts as "other".
    assert check_password("a@bcdefgHI[12", "zz", set()) == []
    assert check_password("a`bcdefgHI{12", "zz", set()) == []
    assert check_password("a/bcdefgHI:12", "zz", set()) == []


# --- USERNAME ---

def test_username_appears_case_insensitively_violates():
    pwd = "xxALICEqw1Z!ok"  # contains 'alice' case-insensitively, no repeats
    assert check_password(pwd, "AlIcE", set()) == ["USERNAME"]


def test_username_inside_password_violates_lowercase_user():
    pwd = "Qwerty!!Alice123"
    assert check_password(pwd, "alice", set()) == ["USERNAME"]


def test_username_not_present_ok():
    assert check_password(GOOD, "bobby", set()) == []


def test_short_username_never_triggers():
    # username "ab" (2 chars) appears in password but must not trigger
    pwd = "xxabYqwERT12!!"
    assert "ab" in pwd
    assert check_password(pwd, "ab", set()) == []


def test_username_length_three_triggers():
    pwd = "qwBOBtyuERT12!!"
    assert check_password(pwd, "bob", set()) == ["USERNAME"]


def test_empty_username_never_triggers():
    assert check_password(GOOD, "", set()) == []


# --- REPEAT ---

def test_triple_repeat_violates():
    pwd = "Abcdefgh111!!xy"  # '111' is a triple
    assert check_password(pwd, "zz", set()) == ["REPEAT"]


def test_double_repeat_ok():
    pwd = "Abcdefgh11!!xyZ"
    assert check_password(pwd, "zz", set()) == []


def test_repeat_is_case_sensitive():
    pwd = "aAaBbcdefgh1!"  # 'aAa' is not a repeat
    assert check_password(pwd, "zz", set()) == []


def test_repeat_at_end_detected():
    pwd = "Abcdefghijk!!!"
    assert check_password(pwd, "zz", set()) == ["REPEAT"]


# --- BLOCKLIST ---

def test_blocklist_equality_case_insensitive_violates():
    pwd = "Password12345!"
    assert check_password(pwd, "zz", {"PASSWORD12345!"}) == ["BLOCKLIST"]


def test_blocklist_substring_is_not_violation():
    pwd = GOOD
    assert check_password(pwd, "zz", {"horse"}) == []


def test_blocklist_entry_stored_mixed_case_matches():
    pwd = GOOD
    assert check_password(pwd, "zz", {"Tr0ub4dor&horse"}) == ["BLOCKLIST"]


def test_empty_blocklist_ok():
    assert check_password(GOOD, "zz", set()) == []


# --- Ordering and multiple violations ---

def test_all_violations_in_order():
    # too short, 1 class, username 'aaa' present, triple repeat, blocklisted
    pwd = "aaaa"
    result = check_password(pwd, "aaa", {"aaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_length_before_classes():
    assert check_password("ab", "zz", set()) == ["LENGTH", "CLASSES"]


def test_order_repeat_before_blocklist():
    pwd = "Abcdefghi111!"
    assert check_password(pwd, "zz", {pwd}) == ["REPEAT", "BLOCKLIST"]


def test_order_username_before_repeat():
    pwd = "Bob111abcdEF!!"
    assert check_password(pwd, "bob", set()) == ["USERNAME", "REPEAT"]


# --- Direct tests of helpers (kill boundary and return-value mutants) ---

@pytest.mark.parametrize("char", ["a", "m", "z"])
def test_class_of_lowercase_including_ends(char):
    assert _class_of(char) == _LOWER


@pytest.mark.parametrize("char", ["A", "M", "Z"])
def test_class_of_uppercase_including_ends(char):
    assert _class_of(char) == _UPPER


@pytest.mark.parametrize("char", ["0", "5", "9"])
def test_class_of_digits_including_ends(char):
    assert _class_of(char) == _DIGIT


@pytest.mark.parametrize("char", ["@", "[", "`", "{", "/", ":", " ", "é"])
def test_class_of_other_characters(char):
    assert _class_of(char) == _OTHER


def test_contains_username_short_returns_false_exactly():
    assert _contains_username("xxabxx", "ab") is False


def test_contains_username_absent_returns_false_exactly():
    assert _contains_username("xxxxxx", "bob") is False


def test_contains_username_present_returns_true():
    assert _contains_username("xxBOBxx", "bob") is True
