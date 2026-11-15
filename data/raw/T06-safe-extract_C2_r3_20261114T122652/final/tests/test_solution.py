import pytest

from solution import UnsafePathError, plan_extraction


# --- destination handling -------------------------------------------------

def test_basic_file():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_trailing_slashes_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out//", ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]
    assert plan_extraction("///", ["a.txt"]) == ["/a.txt"]


def test_leading_slash_in_dest_kept():
    assert plan_extraction("/tmp/out", ["x"]) == ["/tmp/out/x"]


@pytest.mark.parametrize("bad", ["", None, 5])
def test_invalid_dest_raises_value_error(bad):
    with pytest.raises(ValueError):
        plan_extraction(bad, ["a"])


def test_empty_member_list():
    assert plan_extraction("out", []) == []


def test_order_preserved():
    assert plan_extraction("out", ["b", "a", "c/d"]) == ["out/b", "out/a", "out/c/d"]


def test_nested_path():
    assert plan_extraction("out", ["a/b/c.txt"]) == ["out/a/b/c.txt"]


# --- separators and normalisation ----------------------------------------

def test_backslash_is_separator():
    assert plan_extraction("out", ["a\\b.txt"]) == ["out/a/b.txt"]


def test_backslash_dotdot_normalised():
    assert plan_extraction("out", ["a\\..\\b"]) == ["out/b"]


def test_empty_segments_dropped():
    assert plan_extraction("out", ["a//b"]) == ["out/a/b"]


def test_dot_segments_dropped():
    assert plan_extraction("out", ["./a/./b"]) == ["out/a/b"]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]


def test_dotdot_then_back_down_is_safe():
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


def test_ordinary_names_with_dots():
    assert plan_extraction("out", ["..a", "a..", "..."]) == ["out/..a", "out/a..", "out/..."]


def test_drive_like_name_without_letter_is_ordinary():
    assert plan_extraction("out", ["1:x"]) == ["out/1:x"]


# --- unsafe members -------------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "a/../../b",
        "a/../../../b",
        "..",
        "../",
    ],
)
def test_climbing_above_destination_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["/etc/passwd", "\\windows", "/"])
def test_absolute_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "C:", "z:/a/b"])
def test_drive_prefix_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_nul_character_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\x00b"])


@pytest.mark.parametrize("member", ["", ".", "./", "a/..", "a/../"])
def test_empty_after_normalisation_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_unsafe_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)
    with pytest.raises(ValueError):
        plan_extraction("out", ["../x"])


def test_no_partial_plan_on_unsafe_member():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "../bad", "ok2.txt"])


def test_unsafe_directory_entry_is_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../escape/"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["/abs/"])


# --- directory entries ----------------------------------------------------

def test_directory_entries_excluded():
    assert plan_extraction("out", ["a/", "b/c.txt"]) == ["out/b/c.txt"]


def test_backslash_directory_entry_excluded():
    assert plan_extraction("out", ["a\\", "b"]) == ["out/b"]


def test_only_directories_gives_empty_plan():
    assert plan_extraction("out", ["a/", "a/b/", "a/./"]) == []


def test_directory_entries_do_not_count_as_duplicates():
    assert plan_extraction("out", ["a/", "A/"]) == []


def test_directory_then_file_with_same_name_allowed():
    assert plan_extraction("out", ["a/", "a"]) == ["out/a"]


# --- duplicates -----------------------------------------------------------

def test_case_insensitive_duplicate_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a", "./a"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["x/../a", "a"])


def test_duplicate_across_separators_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\\b", "A/B"])


def test_distinct_names_are_not_duplicates():
    assert plan_extraction("out", ["a", "ab", "a/b"]) == ["out/a", "out/ab", "out/a/b"]
