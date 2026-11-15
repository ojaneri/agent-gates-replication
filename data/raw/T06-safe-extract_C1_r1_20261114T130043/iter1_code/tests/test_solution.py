import pytest

from solution import UnsafePathError, plan_extraction


# --- basic behaviour -------------------------------------------------------

def test_simple_files_in_order():
    assert plan_extraction("out", ["b.txt", "a.txt"]) == ["out/b.txt", "out/a.txt"]


def test_nested_path_kept():
    assert plan_extraction("out", ["d/e/f.txt"]) == ["out/d/e/f.txt"]


def test_empty_member_list_gives_empty_plan():
    assert plan_extraction("out", []) == []


def test_trailing_slashes_on_dest_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out//", ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["a.txt"]) == ["/a.txt"]


def test_nested_destination_kept_verbatim():
    assert plan_extraction("x/y", ["a"]) == ["x/y/a"]


# --- dest validation -------------------------------------------------------

@pytest.mark.parametrize("dest", ["", None, 3])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_unsafe_error_is_value_error_subclass():
    assert issubclass(UnsafePathError, ValueError)


# --- normalisation ---------------------------------------------------------

def test_backslash_is_separator():
    assert plan_extraction("out", ["a\\b\\c.txt"]) == ["out/a/b/c.txt"]


def test_mixed_separators():
    assert plan_extraction("out", ["a/b\\c"]) == ["out/a/b/c"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("out", ["a//b", "./c", "d/./e"]) == [
        "out/a/b",
        "out/c",
        "out/d/e",
    ]


def test_dotdot_removes_previous_segment():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]


def test_dotdot_back_within_destination_is_safe():
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


# --- ordinary names that merely look like dots -----------------------------

@pytest.mark.parametrize("name", ["..a", "a..", "...", "a...b"])
def test_names_with_extra_dots_are_ordinary(name):
    assert plan_extraction("out", [name]) == [f"out/{name}"]


def test_dotdot_names_inside_segment_not_treated_as_parent():
    assert plan_extraction("out", ["..a/b"]) == ["out/..a/b"]


# --- unsafe members --------------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "../x",
        "a/../../b",
        "a/../../../b",
        "..",
        "../",
        "..\\x",
    ],
)
def test_escape_above_destination_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["/etc/passwd", "\\windows\\x", "/", "\\"])
def test_absolute_members_are_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


@pytest.mark.parametrize("member", ["C:/x", "c:x", "C:\\x", "Z:"])
def test_drive_prefix_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_colon_not_right_after_first_letter_is_ordinary():
    assert plan_extraction("out", ["ab:c"]) == ["out/ab:c"]


def test_digit_before_colon_is_not_drive():
    assert plan_extraction("out", ["1:x"]) == ["out/1:x"]


def test_nul_character_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\x00b"])


@pytest.mark.parametrize("member", ["", ".", "./", "a/..", "a/../.", "//"])
def test_empty_after_normalisation_is_unsafe(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_unsafe_member_means_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["good.txt", "../bad.txt", "also-good.txt"])


# --- directory entries -----------------------------------------------------

def test_directory_entries_excluded_from_result():
    assert plan_extraction("out", ["d/", "d/f.txt", "e\\"]) == ["out/d/f.txt"]


def test_directory_entry_is_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../dir/"])


def test_directory_entry_that_normalises_empty_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["./"])


def test_directory_entry_does_not_collide_with_file():
    assert plan_extraction("out", ["a/", "a"]) == ["out/a"]


# --- duplicates ------------------------------------------------------------

def test_case_insensitive_duplicate_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])


def test_duplicate_after_normalisation_is_unsafe():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b.txt", "a//b.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/b.txt", "a\\b.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["x/../a.txt", "a.txt"])


def test_same_name_in_different_directories_is_fine():
    assert plan_extraction("out", ["a/x.txt", "b/x.txt"]) == [
        "out/a/x.txt",
        "out/b/x.txt",
    ]
