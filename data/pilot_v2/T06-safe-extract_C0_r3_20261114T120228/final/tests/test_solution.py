import pytest

from solution import UnsafePathError, plan_extraction


# --- dest handling -------------------------------------------------------

def test_basic_join():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_trailing_slashes_on_dest_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out///", ["a.txt"]) == ["out/a.txt"]


def test_root_dest():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]


@pytest.mark.parametrize("dest", ["", None, 5])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_unsafe_path_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)


# --- normalisation -------------------------------------------------------

def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b"]) == ["out/a/b"]
    assert plan_extraction("out", ["./a/./b"]) == ["out/a/b"]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]


def test_backslash_is_separator():
    assert plan_extraction("out", ["dir\\file.txt"]) == ["out/dir/file.txt"]


def test_mixed_separators():
    assert plan_extraction("out", ["a\\b/c"]) == ["out/a/b/c"]


def test_dotdot_inside_dest_is_fine():
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


def test_names_that_look_like_dotdot_are_ordinary():
    assert plan_extraction("out", ["..a", "a..", "..."]) == [
        "out/..a",
        "out/a..",
        "out/...",
    ]


# --- unsafe members ------------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "a/../../b",
        "a/../../../b",
        "..",
        "a\\..\\..\\b",
        "a/../../b/",  # climbing directory entry is still unsafe
    ],
)
def test_climbing_above_dest_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize(
    "member",
    ["/etc/passwd", "\\windows\\x", "/", "\\"],
)
def test_absolute_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "Z:"])
def test_drive_prefix_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_single_letter_colon_is_drive_prefix_even_mid_name():
    # Spec: a letter followed by ":" at the start is a drive prefix.
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a:b"])


def test_colon_after_longer_name_is_ordinary():
    assert plan_extraction("out", ["ab:c", "dir/x:y"]) == ["out/ab:c", "out/dir/x:y"]


@pytest.mark.parametrize("member", ["a\0b", "\0", "x/\0"])
def test_nul_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", [".", "./", "a/..", "a/../", ""])
def test_empty_after_normalisation_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


# --- directory entries ---------------------------------------------------

def test_directory_entries_not_in_result():
    assert plan_extraction("out", ["dir/", "dir/a.txt", "dir\\sub\\"]) == [
        "out/dir/a.txt",
    ]


def test_directory_entry_is_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../evil/"])


def test_only_directories_gives_empty_plan():
    assert plan_extraction("out", ["a/", "a/b/"]) == []


# --- duplicates ----------------------------------------------------------

def test_duplicate_after_normalisation_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b.txt", "a//b.txt"])


def test_duplicate_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_across_separators():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["d/x", "d\\x"])


def test_distinct_names_are_not_duplicates():
    assert plan_extraction("out", ["a.txt", "a.txt.bak"]) == [
        "out/a.txt",
        "out/a.txt.bak",
    ]


# --- ordering and atomicity ----------------------------------------------

def test_preserves_input_order():
    members = ["z.txt", "a.txt", "m/n.txt"]
    assert plan_extraction("out", members) == ["out/z.txt", "out/a.txt", "out/m/n.txt"]


def test_empty_members_list():
    assert plan_extraction("out", []) == []


def test_any_unsafe_member_raises_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["good.txt", "../bad.txt", "also-good.txt"])


def test_does_not_touch_filesystem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan_extraction("out", ["a/b.txt"])
    assert list(tmp_path.iterdir()) == []
