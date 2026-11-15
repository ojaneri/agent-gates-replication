import pytest

from solution import UnsafePathError, plan_extraction


def test_unsafe_path_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)


def test_basic_file():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_nested_file_keeps_order():
    assert plan_extraction("out", ["z.txt", "d/a.txt", "b.txt"]) == [
        "out/z.txt",
        "out/d/a.txt",
        "out/b.txt",
    ]


def test_empty_members_list():
    assert plan_extraction("out", []) == []


@pytest.mark.parametrize("dest", ["out/", "out//", "out///"])
def test_trailing_slashes_ignored(dest):
    assert plan_extraction(dest, ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]
    assert plan_extraction("//", ["a/b"]) == ["/a/b"]


@pytest.mark.parametrize("dest", ["", None, 5])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_backslash_is_separator():
    assert plan_extraction("out", ["dir\\a.txt"]) == ["out/dir/a.txt"]
    assert plan_extraction("out", ["dir\\sub/a.txt"]) == ["out/dir/sub/a.txt"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b"]) == ["out/a/b"]
    assert plan_extraction("out", ["./a/./b"]) == ["out/a/b"]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]
    assert plan_extraction("out", ["a/b/../c"]) == ["out/a/c"]


def test_dotdot_like_names_are_ordinary():
    assert plan_extraction("out", ["..a", "a..", "..."]) == [
        "out/..a",
        "out/a..",
        "out/...",
    ]


@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "a/../../b",
        "a/../../../b",
        "/etc/passwd",
        "\\windows\\x",
        "C:/x",
        "c:x",
        "C:\\x",
        "a\x00b",
        "\x00",
        ".",
        "./",
        "a/..",
        "",
        "/",
        "\\",
    ],
)
def test_unsafe_members_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_drive_letter_only_in_first_position_is_not_a_prefix():
    # "a:" in the middle is an ordinary segment name; only a leading prefix is refused.
    assert plan_extraction("out", ["dir/c:x"]) == ["out/dir/c:x"]


def test_directory_entries_excluded_but_validated():
    assert plan_extraction("out", ["d/", "d/a.txt"]) == ["out/d/a.txt"]
    assert plan_extraction("out", ["d\\"]) == []
    assert plan_extraction("out", ["d/", "e/"]) == []


@pytest.mark.parametrize("member", ["../", "a/../../", "/dir/", "C:/dir/"])
def test_unsafe_directory_entries_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_case_insensitive_duplicate_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b", "a//b"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b", "a\\b"])


def test_directory_and_file_with_same_name_not_a_duplicate():
    assert plan_extraction("out", ["a", "a/"]) == ["out/a"]


def test_no_partial_plan_on_unsafe_member():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "../bad.txt", "also_ok.txt"])
