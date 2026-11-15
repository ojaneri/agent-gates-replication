import pytest

from solution import UnsafePathError, plan_extraction


# --- dest handling -------------------------------------------------------

@pytest.mark.parametrize("dest", ["", None, 5])
def test_dest_must_be_non_empty_string(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_basic_paths():
    assert plan_extraction("out", ["a.txt", "d/b.txt"]) == ["out/a.txt", "out/d/b.txt"]


def test_trailing_slashes_on_dest_are_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out//", ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["a.txt", "d/b.txt"]) == ["/a.txt", "/d/b.txt"]


def test_error_subclass_of_value_error():
    assert issubclass(UnsafePathError, ValueError)


# --- separators and normalisation ----------------------------------------

def test_backslash_is_separator():
    assert plan_extraction("out", ["d\\b.txt"]) == ["out/d/b.txt"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b", "./c/./d"]) == ["out/a/b", "out/c/d"]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]


def test_dotdot_that_climbs_down_again_is_fine():
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


def test_names_with_dots_are_ordinary():
    assert plan_extraction("out", ["..a", "a..", "..."]) == ["out/..a", "out/a..", "out/..."]


def test_order_of_input_preserved():
    assert plan_extraction("out", ["z.txt", "a.txt", "m/n.txt"]) == [
        "out/z.txt",
        "out/a.txt",
        "out/m/n.txt",
    ]


# --- unsafe members -------------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "a/../../b",
        "a/../..",
        "/etc/passwd",
        "\\x",
        "C:/x",
        "c:x",
        "C:\\x",
        "a\x00b",
        ".",
        "./",
        "a/..",
        "",
    ],
)
def test_unsafe_members_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_unsafe_directory_entry_still_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../dir/"])


def test_no_partial_plan_when_one_member_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "../bad.txt"])


# --- directory entries ----------------------------------------------------

def test_directory_entries_excluded_from_result():
    assert plan_extraction("out", ["d/", "d/f.txt", "e\\"]) == ["out/d/f.txt"]


# --- duplicates -----------------------------------------------------------

def test_case_insensitive_duplicate_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/x", "A\\X"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/./x", "a//x"])


def test_duplicate_directory_entries_are_not_file_duplicates():
    assert plan_extraction("out", ["d/", "d/"]) == []
