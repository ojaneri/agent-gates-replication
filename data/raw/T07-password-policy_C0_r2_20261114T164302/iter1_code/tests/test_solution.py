import pytest

from solution import check_password


GOOD = "Tr0ub4dor&3xyz"  # 15 chars, lower/upper/digit/other, no repeats


def test_valid_password_gives_empty_list():
    assert check_password(GOOD, "alice", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(None, "alice", set())
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())
    with pytest.raises(TypeError):
        check_password(123456789012, "alice", set())


def test_length_boundaries():
    base12 = "Ab1!Ab1!Ab1!"       # 12 chars, no repeats
    assert len(base12) == 12
    assert "LENGTH" not in check_password(base12, "zzz", set())
    assert "LENGTH" in check_password(base12[:-1], "zzz", set())  # 11

    base64 = "Ab1!" * 16          # 64 chars
    assert len(base64) == 64
    assert "LENGTH" not in check_password(base64, "zzz", set())
    assert "LENGTH" in check_password(base64 + "A", "zzz", set())  # 65


def test_classes_need_three_of_four():
    # lowercase + digits only -> 2 classes
    assert "CLASSES" in check_password("abcdefgh1234", "zzz", set())
    # lowercase + uppercase + digits -> 3 classes
    assert "CLASSES" not in check_password("abcdefGH1234", "zzz", set())
    # lowercase + uppercase + other -> 3 classes
    assert "CLASSES" not in check_password("abcdefGH!!ij", "zzz", set())
    # all four classes
    assert "CLASSES" not in check_password("aB3!aB3!aB3!", "zzz", set())


def test_non_ascii_letters_count_as_other():
    # lowercase + uppercase + é (other) -> 3 classes: fine
    assert "CLASSES" not in check_password("abcdefGHéijkl", "zzz", set())
    # lowercase + é only -> 2 classes: violated
    assert "CLASSES" in check_password("abcdéfghijklm", "zzz", set())


def test_space_counts_as_other():
    assert "CLASSES" not in check_password("abcdefGH ijkl", "zzz", set())


def test_username_substring_case_insensitive():
    pw = "Xq7-alice-Zw9!"
    assert "USERNAME" in check_password(pw, "ALICE", set())
    assert "USERNAME" in check_password(pw, "alice", set())
    assert "USERNAME" not in check_password(pw, "bobby", set())


def test_short_username_never_triggers():
    pw = "Xq7-ab-Zw9!kk"
    assert "USERNAME" not in check_password(pw, "ab", set())
    assert "USERNAME" not in check_password(pw, "", set())


def test_username_exactly_three_triggers():
    pw = "Xq7-abc-Zw9!kk"
    assert "USERNAME" in check_password(pw, "abc", set())


def test_repeat_three_in_a_row():
    assert "REPEAT" in check_password("Xq7aaa-Zw9!kk", "zzz", set())
    assert "REPEAT" not in check_password("Xq7aa-Zw9!kkB", "zzz", set())


def test_repeat_is_case_sensitive():
    assert "REPEAT" not in check_password("Xq7aAa-Zw9!kk", "zzz", set())


def test_repeat_non_adjacent_not_violation():
    assert "REPEAT" not in check_password("Xq7a-aZ-w9!kB", "zzz", set())


def test_blocklist_equality_after_lower():
    assert "BLOCKLIST" in check_password("password123!", "zzz", {"Password123!"})
    assert "BLOCKLIST" in check_password("PASSWORD123!", "zzz", {"password123!"})


def test_blocklist_containment_is_not_violation():
    assert "BLOCKLIST" not in check_password("MyPassword123!x", "zzz", {"password"})


def test_order_of_all_codes():
    result = check_password("aaa", "aaa", {"aaa"})
    assert result == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]


def test_order_subset_preserved():
    pw = "abcdefghijkl"  # length ok, one class
    assert check_password(pw, "zzz", {"abcdefghijkl"}) == ["CLASSES", "BLOCKLIST"]
