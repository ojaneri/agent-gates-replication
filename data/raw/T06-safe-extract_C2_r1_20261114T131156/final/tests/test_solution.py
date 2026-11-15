import pytest

from solution import UnsafePathError, plan_extraction


# --- dest handling -------------------------------------------------------

def test_basic_join():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_trailing_slashes_on_dest_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out//", ["a.txt"]) == ["out/a.txt"]


def test_root_dest_gives_leading_slash():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]
    assert plan_extraction("//", ["a/b"]) == ["/a/b"]


def test_empty_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction("", ["a.txt"])


def test_non_string_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction(None, ["a.txt"])
    with pytest.raises(ValueError):
        plan_extraction(5, ["a.txt"])


def test_unsafe_error_is_value_error_subclass():
    assert issubclass(UnsafePathError, ValueError)


def test_dest_with_inner_slash_kept():
    assert plan_extraction("a/b", ["c"]) == ["a/b/c"]


def test_empty_member_list():
    assert plan_extraction("out", []) == []


def test_order_preserved():
    assert plan_extraction("o", ["b", "a", "c"]) == ["o/b", "o/a", "o/c"]


# --- normalisation -------------------------------------------------------

def test_empty_segments_dropped():
    assert plan_extraction("o", ["a//b"]) == ["o/a/b"]


def test_dot_segments_dropped():
    assert plan_extraction("o", ["./a/./b"]) == ["o/a/b"]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("o", ["a/../b"]) == ["o/b"]


def test_dotdot_back_to_top_then_down_is_safe():
    assert plan_extraction("o", ["a/b/../../c/d"]) == ["o/c/d"]


def test_backslash_is_separator():
    assert plan_extraction("o", ["a\\b\\c.txt"]) == ["o/a/b/c.txt"]


def test_mixed_separators():
    assert plan_extraction("o", ["a\\b/c"]) == ["o/a/b/c"]


def test_dotdot_with_backslash():
    assert plan_extraction("o", ["a\\..\\b"]) == ["o/b"]


def test_names_with_dots_are_ordinary():
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


def test_dotdot_prefix_name_is_ordinary_inside():
    assert plan_extraction("o", ["x/..a/b"]) == ["o/x/..a/b"]


def test_single_dot_char_in_name_kept():
    assert plan_extraction("o", ["a.b.c"]) == ["o/a.b.c"]


# --- unsafe members ------------------------------------------------------

@pytest.mark.parametrize("member", [
    "../x",
    "a/../../b",
    "a/../b/../../c",
    "..",
    "../",
    "..\\x",
    "a\\..\\..\\b",
])
def test_escape_above_dest_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [member])


def test_going_up_then_down_still_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/../../b"])


@pytest.mark.parametrize("member", ["/etc/passwd", "/x", "\\x", "\\\\server\\share"])
def test_absolute_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "z:", "A:"])
def test_drive_prefix_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [member])


def test_colon_not_at_position_one_is_fine():
    assert plan_extraction("o", ["ab:c"]) == ["o/ab:c"]


def test_letter_colon_letter_is_drive_prefix():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a:b"])


def test_digit_before_colon_is_fine():
    assert plan_extraction("o", ["1:x"]) == ["o/1:x"]


def test_non_letter_before_colon_is_fine():
    assert plan_extraction("o", ["-:x"]) == ["o/-:x"]


def test_nul_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a\x00b"])


def test_nul_at_start_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["\x00a"])


@pytest.mark.parametrize("member", ["", ".", "./", "a/..", "a/../", "./.", "\\"])
def test_empty_after_normalisation_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [member])


def test_unsafe_anywhere_rejects_whole_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["good.txt", "../bad", "also-good"])


# --- directory entries ---------------------------------------------------

def test_directory_entry_not_in_result():
    assert plan_extraction("o", ["dir/"]) == []


def test_directory_entry_with_backslash_not_in_result():
    assert plan_extraction("o", ["dir\\"]) == []


def test_directory_mixed_with_files():
    assert plan_extraction("o", ["d/", "d/f.txt", "e/"]) == ["o/d/f.txt"]


def test_directory_entry_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../evil/"])


def test_absolute_directory_still_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["/etc/"])


def test_directory_with_dotdot_escape_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/../../"])


def test_directory_empty_after_normalisation_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["./"])


def test_directory_with_nul_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["d\x00/"])


def test_directory_absolute_backslash_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["\\d\\"])


def test_directory_drive_prefix_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["C:/d/"])


def test_file_named_dotdot_inside_directory_path_is_normal():
    assert plan_extraction("o", ["a/b/c/"]) == []


# --- duplicates ----------------------------------------------------------

def test_exact_duplicate_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a.txt", "a.txt"])


def test_case_insensitive_duplicate_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/./b", "a//b"])


def test_duplicate_via_dotdot_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["x/../a", "a"])


def test_duplicate_via_backslash_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["d\\f", "d/f"])


def test_case_insensitive_duplicate_in_directory_path():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["Dir/x", "dir/X"])


def test_same_name_different_directories_ok():
    assert plan_extraction("o", ["a/x", "b/x"]) == ["o/a/x", "o/b/x"]


def test_prefix_similar_names_not_duplicates():
    assert plan_extraction("o", ["a", "ab"]) == ["o/a", "o/ab"]


def test_directory_then_file_same_name_not_duplicate():
    assert plan_extraction("o", ["a/", "a"]) == ["o/a"]


def test_duplicate_detection_is_on_normalised_name_not_dest():
    assert plan_extraction("o", ["x"]) == ["o/x"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["x", "X"])
