import pytest

from solution import UnsafePathError, plan_extraction


# --- basic mapping -------------------------------------------------------

def test_simple_file():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_nested_file():
    assert plan_extraction("out", ["a/b/c.txt"]) == ["out/a/b/c.txt"]


def test_trailing_slashes_on_dest_are_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out///", ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]


def test_backslash_is_separator():
    assert plan_extraction("out", ["a\\b\\c.txt"]) == ["out/a/b/c.txt"]


def test_mixed_separators():
    assert plan_extraction("out", ["a/b\\c.txt"]) == ["out/a/b/c.txt"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//./b"]) == ["out/a/b"]
    assert plan_extraction("out", ["./a/./b.txt"]) == ["out/a/b.txt"]


def test_dotdot_that_stays_inside_is_normalised():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


def test_ordinary_names_with_dots_are_not_dotdot():
    assert plan_extraction("out", ["..a", "a..", "..."]) == [
        "out/..a",
        "out/a..",
        "out/...",
    ]


def test_order_is_preserved():
    assert plan_extraction("out", ["b", "a", "c/d"]) == [
        "out/b",
        "out/a",
        "out/c/d",
    ]


def test_empty_member_list():
    assert plan_extraction("out", []) == []


def test_does_not_touch_file_system():
    assert plan_extraction("/nonexistent/dest/xyz", ["f.txt"]) == [
        "/nonexistent/dest/xyz/f.txt"
    ]


# --- directory entries ---------------------------------------------------

def test_directory_entries_are_excluded():
    assert plan_extraction("out", ["d/", "d/f.txt"]) == ["out/d/f.txt"]


def test_directory_entry_with_backslash_is_excluded():
    assert plan_extraction("out", ["d\\", "d\\f.txt"]) == ["out/d/f.txt"]


def test_directory_entry_is_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../d/"])


def test_directory_entry_that_is_empty_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["./"])


# --- invalid destination -------------------------------------------------

def test_empty_dest_raises_value_error():
    with pytest.raises(ValueError):
        plan_extraction("", ["a.txt"])


def test_non_string_dest_raises_value_error():
    with pytest.raises(ValueError):
        plan_extraction(None, ["a.txt"])  # type: ignore[arg-type]


def test_unsafe_error_is_value_error_subclass():
    assert issubclass(UnsafePathError, ValueError)


# --- unsafe members: NUL, absolute, drive prefix -------------------------

@pytest.mark.parametrize("member", ["a\0b", "\0", "a.txt\0"])
def test_nul_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["/etc/passwd", "\\windows\\x", "/", "\\"])
def test_absolute_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "z:", "C:"])
def test_drive_prefix_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_colon_not_at_start_is_fine():
    assert plan_extraction("out", ["a/b:c"]) == ["out/a/b:c"]
    assert plan_extraction("out", ["ab:c"]) == ["out/ab:c"]


def test_letter_colon_at_start_is_drive_prefix_even_with_more_text():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a:b"])


# --- unsafe members: traversal -------------------------------------------

@pytest.mark.parametrize(
    "member",
    ["../x", "..\\x", "a/../../b", "a/../..", "a/../../../b", "..", "../"],
)
def test_climbing_above_dest_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_climb_then_descend_is_still_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/../../b"])


# --- unsafe members: empty after normalisation ---------------------------

@pytest.mark.parametrize("member", [".", "./", "a/..", "", "//", "./.", "a/./.."])
def test_empty_after_normalisation_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


# --- duplicates ----------------------------------------------------------

def test_exact_duplicate_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a.txt", "a.txt"])


def test_case_insensitive_duplicate_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b", "a\\b"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/../b", "b"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["x//y", "X/./Y"])


def test_directory_entry_does_not_collide_with_file():
    assert plan_extraction("out", ["d/", "d"]) == ["out/d"]


# --- no partial plan -----------------------------------------------------

def test_one_unsafe_member_rejects_whole_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "../bad", "also-ok.txt"])


def test_unsafe_member_after_duplicate_still_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a", "a", "../x"])
