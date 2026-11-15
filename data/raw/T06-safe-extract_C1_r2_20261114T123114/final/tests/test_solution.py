import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_paths():
    assert plan_extraction("out", ["a.txt", "dir/b.txt"]) == [
        "out/a.txt",
        "out/dir/b.txt",
    ]


def test_empty_member_list():
    assert plan_extraction("out", []) == []


def test_input_order_preserved():
    assert plan_extraction("out", ["z", "a", "m/n"]) == ["out/z", "out/a", "out/m/n"]


@pytest.mark.parametrize("dest", ["out/", "out//", "out///"])
def test_trailing_slashes_on_dest_are_ignored(dest):
    assert plan_extraction(dest, ["a"]) == ["out/a"]


def test_root_destination():
    assert plan_extraction("/", ["name"]) == ["/name"]
    assert plan_extraction("//", ["name"]) == ["/name"]


@pytest.mark.parametrize("dest", ["", None, 3, b"out"])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a"])


def test_backslash_is_separator():
    assert plan_extraction("out", ["a\\b\\c.txt"]) == ["out/a/b/c.txt"]


def test_mixed_separators():
    assert plan_extraction("out", ["a/b\\c"]) == ["out/a/b/c"]


def test_empty_segments_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b", "./c", "d/./e"]) == [
        "out/a/b",
        "out/c",
        "out/d/e",
    ]


def test_dotdot_that_stays_inside_is_resolved():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]
    assert plan_extraction("out", ["a/b/../c"]) == ["out/a/c"]


@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "..",
        "a/../../b",
        "a/../..",
        "..\\x",
        "a\\..\\..\\b",
        "a/../../../b",
    ],
)
def test_climbing_above_destination_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize(
    "member",
    ["/etc/passwd", "\\evil", "C:/x", "c:x", "C:\\x", "z:", "a:b"],
)
def test_absolute_or_drive_prefixed_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_nul_character_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\x00b"])


@pytest.mark.parametrize("member", [".", "./", "a/..", "a/../", "", "\\.\\"])
def test_empty_after_normalisation_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_ordinary_names_with_dots_are_safe():
    assert plan_extraction("out", ["..a", "a..", "...", "a...b"]) == [
        "out/..a",
        "out/a..",
        "out/...",
        "out/a...b",
    ]


def test_directory_entries_validated_but_excluded():
    assert plan_extraction("out", ["dir/", "dir/file", "d2\\"]) == ["out/dir/file"]


def test_unsafe_directory_entry_still_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../evil/"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["/abs/"])


def test_directory_entry_with_same_name_as_file_is_not_a_duplicate():
    assert plan_extraction("out", ["a", "a/"]) == ["out/a"]


def test_case_insensitive_duplicate_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a//b", "a/b"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/./b", "A\\B"])


def test_same_name_in_different_directories_is_fine():
    assert plan_extraction("out", ["x/a", "y/a"]) == ["out/x/a", "out/y/a"]


def test_unsafe_member_anywhere_yields_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "fine/too.txt", "../bad"])


def test_unsafe_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)
    with pytest.raises(ValueError):
        plan_extraction("out", ["../bad"])
