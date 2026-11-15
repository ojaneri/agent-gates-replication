import pytest

from solution import UnsafePathError, plan_extraction


def test_simple_files():
    assert plan_extraction("out", ["a.txt", "dir/b.txt"]) == ["out/a.txt", "out/dir/b.txt"]


def test_trailing_slashes_on_dest_ignored():
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]


def test_root_dest():
    assert plan_extraction("/", ["name"]) == ["/name"]


def test_empty_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_non_string_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction(None, ["a"])


def test_backslash_is_separator():
    assert plan_extraction("out", ["a\\b\\c.txt"]) == ["out/a/b/c.txt"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b", "./c", "d/./e"]) == [
        "out/a/b",
        "out/c",
        "out/d/e",
    ]


def test_dotdot_inside_destination_normalised():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]


def test_dotdot_escape_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../evil"])


def test_dotdot_climb_then_return_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/../../b"])


def test_nul_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\x00b"])


@pytest.mark.parametrize("member", ["/etc/passwd", "\\windows\\x", "\\\\server\\share"])
def test_absolute_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "z:"])
def test_drive_prefix_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", [".", "./", "a/..", "a/./..", ""])
def test_empty_after_normalisation_rejected(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_dotdot_names_are_ordinary():
    assert plan_extraction("out", ["..a", "a..", "..."]) == [
        "out/..a",
        "out/a..",
        "out/...",
    ]


def test_directory_entries_validated_but_not_returned():
    assert plan_extraction("out", ["dir/", "dir/f.txt", "other\\"]) == ["out/dir/f.txt"]


def test_directory_entry_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../dir/"])


def test_duplicate_files_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["x/a.txt", "x//a.txt"])


def test_case_insensitive_duplicates_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_directory_entries_allowed():
    assert plan_extraction("out", ["d/", "d/", "d/x"]) == ["out/d/x"]


def test_input_order_preserved():
    assert plan_extraction("out", ["z", "a", "m"]) == ["out/z", "out/a", "out/m"]


def test_unsafe_member_means_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["good.txt", "../bad"])


def test_unsafe_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)
