import pytest

from solution import check_password

# A password that satisfies every rule for the username "alice" and an empty blocklist.
GOOD = "Tr0ub4dor&3xyz"


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


# --- TypeError -------------------------------------------------------------

@pytest.mark.parametrize(
    "password,username",
    [(123456789012, "alice"), (None, "alice"), (GOOD, None), (b"bytes-pass!", "alice")],
)
def test_non_str_raises_type_error(password, username):
    with pytest.raises(TypeError):
        check_password(password, username, set())


# --- LENGTH ----------------------------------------------------------------

def test_length_11_violates():
    pw = "Ab1!defghij"  # 11 chars
    assert len(pw) == 11
    assert "LENGTH" in check_password(pw, "zzz", set())


def test_length_12_ok():
    pw = "Ab1!defghijk"  # 12 chars
    assert len(pw) == 12
    assert check_password(pw, "zzz", set()) == []


def test_length_64_ok():
    pw = ("Ab1!" * 16)  # 64 chars
    assert len(pw) == 64
    assert check_password(pw, "zzz", set()) == []


def test_length_65_violates():
    pw = ("Ab1!" * 16) + "x"  # 65 chars, no REPEAT
    assert len(pw) == 65
    assert check_password(pw, "zzz", set()) == ["LENGTH"]


def test_empty_password_violates_length_and_classes():
    assert check_password("", "alice", set()) == ["LENGTH", "CLASSES"]


# --- CLASSES ---------------------------------------------------------------

def test_two_classes_violates():
    # lowercase + digits only, 12+ chars, no repeats
    pw = "abc123def456"
    assert check_password(pw, "zzz", set()) == ["CLASSES"]


def test_three_classes_ok_lower_upper_digit():
    pw = "abcDEF123xyz"
    assert check_password(pw, "zzz", set()) == []


def test_three_classes_ok_lower_upper_other():
    pw = "abcDEF!@#xyz"
    assert check_password(pw, "zzz", set()) == []


def test_three_classes_ok_lower_digit_other():
    pw = "abc123!@#xyz"
    assert check_password(pw, "zzz", set()) == []


def test_three_classes_ok_upper_digit_other():
    pw = "ABC123!@#XYZ"
    assert check_password(pw, "zzz", set()) == []


def test_all_four_classes_ok():
    pw = "aB3!aB3!aB3!"
    assert check_password(pw, "zzz", set()) == []


def test_non_ascii_letter_counts_as_other():
    # lowercase, uppercase, and 'é' (other) -> 3 classes
    pw = "abcDEFéxyzuv"
    assert len(pw) == 12
    assert check_password(pw, "zzz", set()) == []


def test_only_non_ascii_is_one_class():
    pw = "éèêëàáâãäåæç"  # 12 chars, all 'other' -> 1 class
    assert check_password(pw, "zzz", set()) == ["CLASSES"]


def test_space_counts_as_other():
    pw = "abcDEF 123xyz"
    assert check_password(pw, "zzz", set()) == []


# --- USERNAME --------------------------------------------------------------

def test_username_inside_password_violates_case_insensitive():
    pw = "xxALICE-pass9Q"  # contains 'alice' ignoring case
    assert "USERNAME" in check_password(pw, "Alice", set())


def test_username_exact_match_inside_violates():
    pw = "Tr0ub4dor&bob3xyz"
    assert check_password(pw, "bob", set()) == ["USERNAME"]


def test_username_not_inside_ok():
    assert check_password(GOOD, "carol", set()) == []


def test_username_length_2_never_triggers():
    # "Tr" appears in the password but username is only 2 chars
    assert check_password(GOOD, "Tr", set()) == []


def test_username_length_3_triggers():
    pw = "Xyz-Tr0ub4dor9!"
    assert check_password(pw, "XYZ", set()) == ["USERNAME"]


def test_empty_username_never_triggers():
    assert check_password(GOOD, "", set()) == []


# --- REPEAT ----------------------------------------------------------------

def test_three_in_a_row_violates():
    pw = "Abcdefg111hijk"  # '111' -> REPEAT
    assert check_password(pw, "zzz", set()) == ["REPEAT"]


def test_two_in_a_row_ok():
    pw = "Abcdefg11hijk!"
    assert check_password(pw, "zzz", set()) == []


def test_repeat_case_sensitive_aAa_not_repeat():
    pw = "aAabcdefghiJk1!"  # 'aAa' not a repeat
    assert check_password(pw, "zzz", set()) == []


def test_repeat_at_end_detected():
    pw = "Abcdefghijk!!!"
    assert check_password(pw, "zzz", set()) == ["REPEAT"]


def test_repeat_at_start_detected():
    pw = "!!!Abcdefghijk1"
    assert check_password(pw, "zzz", set()) == ["REPEAT"]


def test_repeat_with_case_run_is_case_sensitive():
    # 'AAA' is a real repeat
    pw = "xyzAAAbcdefg1"
    assert check_password(pw, "zzz", set()) == ["REPEAT"]


# --- BLOCKLIST -------------------------------------------------------------

def test_blocklist_equality_violates_case_insensitive():
    pw = "Password12345!"
    assert check_password(pw, "zzz", {"PASSWORD12345!"}) == ["BLOCKLIST"]


def test_blocklist_entry_lowercase_matches_mixed_password():
    pw = "SecretPhrase01!"
    assert check_password(pw, "zzz", {"secretphrase01!"}) == ["BLOCKLIST"]


def test_blocklist_substring_is_not_violation():
    pw = "xxPassword12345!"
    assert check_password(pw, "zzz", {"password12345!"}) == []


def test_blocklist_empty_set_ok():
    assert check_password(GOOD, "zzz", set()) == []


# --- Ordering and combinations --------------------------------------------

def test_all_violations_reported_in_order():
    # short (LENGTH), only lowercase (CLASSES), contains username 'bob' (USERNAME),
    # 'aaa' (REPEAT), equal to blocklist entry (BLOCKLIST)
    pw = "bobaaa"
    result = check_password(pw, "bob", {"bobaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_is_length_before_classes():
    assert check_password("aa", "zzz", set()) == ["LENGTH", "CLASSES"]


def test_order_repeat_before_blocklist():
    pw = "Aaaaaaaaaaa1"  # 12 chars, 3 classes, repeats, equals blocklist entry
    result = check_password(pw, "zzz", {"aaaaaaaaaaa1"})
    assert result == ["REPEAT", "BLOCKLIST"]


def test_username_and_blocklist_together():
    pw = "Tr0ub4dor&3xyz"
    result = check_password(pw, "Tr0", {"tr0ub4dor&3xyz"})
    assert result == ["USERNAME", "BLOCKLIST"]
