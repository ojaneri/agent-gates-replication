import pytest

from solution import UnsafePathError, plan_extraction


# --- destination handling -------------------------------------------------

@pytest.mark.parametrize("dest", ["", None, 5, b"out"])
def test_invalid_dest_raises_value_error(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a.txt"])


def test_unsafe_error_is_value_error_subclass():
    assert issubclass(UnsafePathError, ValueError)


@pytest.mark.parametrize("dest", ["out", "out/", "out//", "out///"])
def test_trailing_slashes_on_dest_are_ignored(dest):
    assert plan_extraction(dest, ["a.txt"]) == ["out/a.txt"]


@pytest.mark.parametrize("dest", ["/", "//"])
def test_root_dest_gives_absolute_targets(dest):
    assert plan_extraction(dest, ["name"]) == ["/name"]


def test_dest_with_inner_slash_is_kept():
    assert plan_extraction("x/y/", ["a"]) == ["x/y/a"]


def test_empty_member_list_gives_empty_plan():
    assert plan_extraction("out", []) == []


# --- normalisation of valid members -------------------------------------

@pytest.mark.parametrize(
    "member, expected",
    [
        ("a.txt", "out/a.txt"),
        ("a/b/c.txt", "out/a/b/c.txt"),
        ("a//b", "out/a/b"),
        ("./a", "out/a"),
        ("a/./b", "out/a/b"),
        ("a/../b", "out/b"),
        ("a/b/../c", "out/a/c"),
        ("a/b/../../c", "out/c"),
        ("a/../a/b", "out/a/b"),
        ("..a", "out/..a"),
        ("a..", "out/a.."),
        ("...", "out/..."),
        ("a/...b/c..", "out/a/...b/c.."),
        ("a\\b", "out/a/b"),
        ("a\\..\\b", "out/b"),
        ("c", "out/c"),
        ("1:x", "out/1:x"),
        ("ab:c", "out/ab:c"),
        ("ab/c:", "out/ab/c:"),
    ],
)
def test_valid_members_are_normalised(member, expected):
    assert plan_extraction("out", [member]) == [expected]


def test_single_letter_then_colon_is_drive_prefix_not_plain_name():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a:b"])


def test_name_that_is_only_dots_and_separators_collapses_inside_dest():
    assert plan_extraction("out", ["./a/./b/."]) == ["out/a/b"]


# --- unsafe members ----------------------------------------------------

@pytest.mark.parametrize(
    "member",
    [
        "\x00",
        "a\x00b",
        "a/\x00",
        "/etc/passwd",
        "/",
        "\\win",
        "\\",
        "C:/x",
        "c:x",
        "C:\\x",
        "C:",
        "z:",
        "../x",
        "..",
        "../../x",
        "a/../../b",
        "a/../..",
        "a/b/../../../c",
        "a/..",
        ".",
        "./",
        "",
        "a/../.",
    ],
)
def test_unsafe_members_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [member])


def test_unsafe_member_anywhere_raises_and_gives_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "fine/b.txt", "../bad", "last.txt"])


def test_absolute_member_after_safe_one_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "/abs.txt"])


# --- directory entries ----------------------------------------------------

@pytest.mark.parametrize("entry", ["a/", "a/b/", "a\\", "a/b\\", "a//"])
def test_directory_entries_are_excluded(entry):
    assert plan_extraction("out", [entry]) == []


def test_directory_entries_mixed_with_files_keep_order():
    members = ["d/", "d/f.txt", "d/sub/", "d/sub/g.txt"]
    assert plan_extraction("out", members) == ["out/d/f.txt", "out/d/sub/g.txt"]


@pytest.mark.parametrize("entry", ["../", "..\\", "./", "/", "C:/", "a/../"])
def test_directory_entries_are_still_validated(entry):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [entry])


def test_directory_entry_climbing_above_dest_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a/../../d/"])


# --- duplicates ----------------------------------------------------------

@pytest.mark.parametrize(
    "members",
    [
        ["A.txt", "a.txt"],
        ["a.txt", "a.txt"],
        ["a/b", "a//b"],
        ["a/b", "a/./b"],
        ["x", "a/../x"],
        ["D/f", "d/F"],
        ["Ä.txt", "ä.txt"],
        ["MiXeD/Name", "mixed/name"],
    ],
)
def test_case_insensitive_duplicates_raise(members):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", members)


def test_same_name_as_directory_and_file_is_not_a_duplicate():
    assert plan_extraction("out", ["x", "x/"]) == ["out/x"]


def test_duplicate_directory_entries_are_not_errors():
    assert plan_extraction("out", ["d/", "d/", "D/"]) == []


def test_different_names_that_share_a_prefix_are_not_duplicates():
    assert plan_extraction("out", ["a", "ab", "a/b"]) == ["out/a", "out/ab", "out/a/b"]


# --- ordering and whole-plan results -----------------------------------

def test_result_keeps_input_order():
    members = ["b.txt", "a.txt", "c/d.txt", "a/z.txt"]
    assert plan_extraction("out", members) == [
        "out/b.txt",
        "out/a.txt",
        "out/c/d.txt",
        "out/a/z.txt",
    ]


def test_result_is_a_list_with_one_entry_per_file():
    result = plan_extraction("dest", ["1", "2", "3"])
    assert isinstance(result, list)
    assert len(result) == 3


def test_dest_root_with_nested_members():
    assert plan_extraction("/", ["a/b/../c", "d"]) == ["/a/c", "/d"]
