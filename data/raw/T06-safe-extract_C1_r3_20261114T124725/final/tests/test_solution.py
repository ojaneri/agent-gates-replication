import pytest

from solution import UnsafePathError, plan_extraction


# --- dest handling -------------------------------------------------------

@pytest.mark.parametrize("dest", ["", None, 3])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_trailing_slashes_on_dest_are_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out///", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_root_dest_gives_absolute_targets():
    assert plan_extraction("/", ["a.txt", "d/b.txt"]) == ["/a.txt", "/d/b.txt"]


# --- basic planning ------------------------------------------------------

def test_empty_member_list_gives_empty_plan():
    assert plan_extraction("out", []) == []


def test_input_order_is_preserved():
    assert plan_extraction("out", ["z", "a", "m/n"]) == ["out/z", "out/a", "out/m/n"]


def test_backslash_is_a_separator():
    assert plan_extraction("out", ["dir\\file.txt"]) == ["out/dir/file.txt"]


def test_empty_and_dot_segments_are_dropped():
    assert plan_extraction("out", ["a//b", "./c", "d/./e", "f/."]) == [
        "out/a/b",
        "out/c",
        "out/d/e",
        "out/f",
    ]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


def test_names_with_dots_are_ordinary():
    names = ["..a", "a..", "...", "x/..y/z..", ".hidden"]
    assert plan_extraction("out", names) == [
        "out/..a",
        "out/a..",
        "out/...",
        "out/x/..y/z..",
        "out/.hidden",
    ]


# --- directory entries ---------------------------------------------------

def test_directory_entries_are_validated_but_not_returned():
    assert plan_extraction("out", ["d/", "d/f.txt", "e\\"]) == ["out/d/f.txt"]


def test_unsafe_directory_entry_still_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../", "ok.txt"])


def test_only_directory_entries_gives_empty_plan():
    assert plan_extraction("out", ["d/", "e/"]) == []


# --- unsafe members ------------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "a\x00b",
        "/etc/passwd",
        "\\windows\\x",
        "C:/x",
        "c:x",
        "C:\\x",
        "../escape",
        "a/../../b",
        "a/../../../b",
        "..",
        "../..",
        ".",
        "./",
        "a/..",
        "",
    ],
)
def test_unsafe_members_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", member])


def test_unsafe_error_is_a_value_error():
    assert issubclass(UnsafePathError, ValueError)
    with pytest.raises(ValueError):
        plan_extraction("out", ["../x"])


def test_drive_prefix_requires_ascii_letter_and_colon_second():
    # "1:" is not a drive prefix, so it is an ordinary name.
    assert plan_extraction("out", ["1:x"]) == ["out/1:x"]
    # A bare single letter has no colon, so it is an ordinary name.
    assert plan_extraction("out", ["c"]) == ["out/c"]
    # Colon after a leading letter is a drive prefix only at position 1.
    assert plan_extraction("out", ["ab:c"]) == ["out/ab:c"]


def test_colon_in_later_segment_is_not_a_drive():
    assert plan_extraction("out", ["d/C:x"]) == ["out/d/C:x"]


def test_no_partial_plan_on_unsafe_member():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["good.txt", "../bad.txt", "other.txt"])


# --- duplicates ----------------------------------------------------------

def test_duplicate_file_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a.txt", "a.txt"])


def test_duplicate_after_normalisation_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b.txt", "a//./b.txt"])


def test_duplicate_is_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["Dir\\File", "dir/file"])


def test_non_duplicate_similar_names_are_fine():
    assert plan_extraction("out", ["a.txt", "a.txt.bak", "ab.txt"]) == [
        "out/a.txt",
        "out/a.txt.bak",
        "out/ab.txt",
    ]


def test_directory_entry_does_not_count_as_duplicate():
    assert plan_extraction("out", ["a/", "a"]) == ["out/a"]
