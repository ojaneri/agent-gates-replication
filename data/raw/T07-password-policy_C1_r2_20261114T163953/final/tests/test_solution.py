import pytest

from solution import check_password

GOOD = "Tr0ub4dor&3xyz"  # 14 chars, all 4 classes, no triple repeat, no username
EMPTY: set[str] = set()


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", EMPTY) == []


# ---- TypeError ----

def test_non_str_password_raises():
    with pytest.raises(TypeError):
        check_password(None, "alice", EMPTY)  # type: ignore[arg-type]


def test_non_str_username_raises():
    with pytest.raises(TypeError):
        check_password(GOOD, None, EMPTY)  # type: ignore[arg-type]


def test_bytes_password_raises():
    with pytest.raises(TypeError):
        check_password(b"Tr0ub4dor&3xyz", "alice", EMPTY)  # type: ignore[arg-type]


# ---- LENGTH ----

def test_length_11_violates():
    assert check_password("Ab1!Ab1!Ab1", "zzz", EMPTY) == ["LENGTH"]


def test_length_12_ok():
    assert check_password("Ab1!Ab1!Ab1!", "zzz", EMPTY) == []


def test_length_64_ok():
    pw = "Ab1!" * 16  # 64 chars
    assert len(pw) == 64
    assert check_password(pw, "zzz", EMPTY) == []


def test_length_65_violates():
    pw = ("Ab1!" * 16) + "x"  # 65 chars
    assert check_password(pw, "zzz", EMPTY) == ["LENGTH"]


# ---- CLASSES ----

def test_two_classes_violates():
    # lowercase + digit only, 12 chars, no repeats
    assert check_password("abcdefgh1234", "zzz", EMPTY) == ["CLASSES"]


def test_three_classes_lower_upper_digit():
    assert check_password("abcDEF123456", "zzz", EMPTY) == []


def test_three_classes_lower_upper_other():
    assert check_password("abcDEFghijk!", "zzz", EMPTY) == []


def test_three_classes_lower_digit_other():
    assert check_password("abcdefg12345!", "zzz", EMPTY) == []


def test_three_classes_upper_digit_other():
    assert check_password("ABCDEFG12345!", "zzz", EMPTY) == []


def test_space_counts_as_other():
    # lower + upper + space
    assert check_password("abcdefGHIJKL ", "zzz", EMPTY) == []


def test_non_ascii_counts_as_other():
    # lower + upper + é (other); exactly 3 classes
    assert check_password("abcdefGHIJKLé", "zzz", EMPTY) == []


def test_non_ascii_lowercase_is_not_ascii_lower():
    # upper + digit + é (other): é is not in a-z, so 3 classes -> ok
    assert check_password("ABCDEFGHIJKL1234é", "zzz", EMPTY) == []


def test_non_ascii_lowercase_alone_does_not_count_as_lower():
    # 14 distinct non-ASCII letters: only the "other" class is present
    assert check_password("éàçñöüáíóúäëÿõ", "zzz", EMPTY) == ["CLASSES"]


def test_only_upper_and_other_violates():
    # distinct symbols so no REPEAT
    assert check_password("ABCDEFGHIJKL!_?#", "zzz", EMPTY) == ["CLASSES"]


def test_only_digit_and_other_violates():
    assert check_password("123456789012!!", "zzz", EMPTY) == ["CLASSES"]


# ---- USERNAME ----

def test_username_inside_password_violates():
    assert "USERNAME" in check_password("PrefixAlice123!", "alice", EMPTY)


def test_username_match_is_case_insensitive():
    assert "USERNAME" in check_password("pfxALICE123!!", "Alice", EMPTY)


def test_username_shorter_than_3_never_triggers():
    # "ab" is inside the password, but the username has only 2 characters
    assert "USERNAME" not in check_password("Ab1!xxAbxx12", "Ab", EMPTY)


def test_username_exactly_3_triggers():
    assert "USERNAME" in check_password("Abc1!abcXYZ9", "abc", EMPTY)


def test_username_not_present_no_violation():
    assert "USERNAME" not in check_password(GOOD, "zed", EMPTY)


# ---- REPEAT ----

def test_triple_repeat_violates():
    assert check_password("Abc1!xxxDEFG9", "zzz", EMPTY) == ["REPEAT"]


def test_double_repeat_ok():
    assert check_password("Abc1!xxDEFG9h", "zzz", EMPTY) == []


def test_case_sensitive_aAa_not_repeat():
    assert "REPEAT" not in check_password("Abc1!aAaDEFG9h", "zzz", EMPTY)


def test_repeat_at_end_detected():
    assert "REPEAT" in check_password("Abc1!DEFG9hhh", "zzz", EMPTY)


def test_repeat_at_start_detected():
    assert "REPEAT" in check_password("!!!Abc1DEFG9hi", "zzz", EMPTY)


def test_repeat_of_non_letters_detected():
    assert "REPEAT" in check_password("Abc1DEFG9!!!h", "zzz", EMPTY)


# ---- BLOCKLIST ----

def test_blocklist_equality_violates():
    assert check_password("Password123!", "zzz", {"password123!"}) == ["BLOCKLIST"]


def test_blocklist_entry_is_lowercased_before_compare():
    assert check_password("Password123!", "zzz", {"PASSWORD123!"}) == ["BLOCKLIST"]


def test_blocklist_substring_not_violation():
    assert check_password(GOOD, "zzz", {"tr0ub"}) == []


def test_blocklist_empty_set_ok():
    assert check_password(GOOD, "zzz", set()) == []


# ---- Ordering and combinations ----

def test_all_violations_in_order():
    # too short, 1 class, username "bob" inside, "aaa" repeat, blocklisted
    result = check_password("bobaaa", "bob", {"bobaaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_independent_of_blocklist_size():
    result = check_password("bobaaa", "bob", {"bobaaa", "other", "more"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_length_and_repeat_only():
    # 11 chars, 4 classes, "zzz" repeat; username "qqq" absent
    assert check_password("Aaa1!zzz!9Q", "qqq", EMPTY) == ["LENGTH", "REPEAT"]


def test_classes_and_username_and_length():
    # "alicealice": 10 chars, lowercase only, username inside, no triple repeat
    assert check_password("alicealice", "alice", EMPTY) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
    ]
