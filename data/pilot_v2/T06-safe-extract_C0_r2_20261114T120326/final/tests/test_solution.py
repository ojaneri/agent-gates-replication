import pytest

from solution import UnsafePathError, plan_extraction


def test_simple_file():
    assert plan_extraction("out", ["a.txt"]) == ["out/a.txt"]


def test_trailing_slash_on_dest_ignored():
    assert plan_extraction("out/", ["a.txt"]) == ["out/a.txt"]
    assert plan_extraction("out///", ["a.txt"]) == ["out/a.txt"]


def test_root_destination():
    assert plan_extraction("/", ["name"]) == ["/name"]


def test_empty_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_non_string_dest_rejected():
    with pytest.raises(ValueError):
        plan_extraction(None, ["a"])


def test_empty_members_returns_empty_list():
    assert plan_extraction("out", []) == []


def test_order_preserved():
    assert plan_extraction("d", ["b", "a", "c"]) == ["d/b", "d/a", "d/c"]


def test_empty_and_dot_segments_dropped():
    assert plan_extraction("d", ["a//b"]) == ["d/a/b"]
    assert plan_extraction("d", ["./a/./b"]) == ["d/a/b"]


def test_dotdot_inside_destination_normalised():
    assert plan_extraction("d", ["a/../b"]) == ["d/b"]


def test_backslash_is_separator():
    assert plan_extraction("d", ["a\\b\\c.txt"]) == ["d/a/b/c.txt"]


def test_names_with_dots_are_ordinary():
    assert plan_extraction("d", ["..a", "a..", "..."]) == ["d/..a", "d/a..", "d/..."]


@pytest.mark.parametrize(
    "member",
    [
        "a\x00b",
        "/etc/passwd",
        "\\windows\\x",
        "C:/x",
        "c:x",
        "C:\\x",
        "../x",
        "..",
        "a/../../b",
        "a/../../../b",
        ".",
        "./",
        "a/..",
        "",
    ],
)
def test_unsafe_members_raise(member):
    with pytest.raises(UnsafePathError):
        plan_extraction("d", [member])


def test_unsafe_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)


def test_directory_entries_validated_but_not_returned():
    assert plan_extraction("d", ["sub/", "sub/a.txt"]) == ["d/sub/a.txt"]


def test_unsafe_directory_entry_still_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["../evil/"])


def test_dot_directory_entry_raises():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["./"])


def test_duplicate_exact_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["a.txt", "a.txt"])


def test_duplicate_after_normalisation_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["a/b", "a//b"])


def test_duplicate_case_insensitive_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["A.txt", "a.txt"])


def test_same_name_in_different_dirs_is_fine():
    assert plan_extraction("d", ["x/a.txt", "y/a.txt"]) == ["d/x/a.txt", "d/y/a.txt"]


def test_no_partial_plan_on_error():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["ok.txt", "../bad"])
