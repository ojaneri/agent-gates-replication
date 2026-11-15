import pytest

from solution import plan_extraction, UnsafePathError


def test_simple():
    assert plan_extraction("out", ["a.txt", "dir/b.txt"]) == ["out/a.txt", "out/dir/b.txt"]


def test_order_preserved():
    assert plan_extraction("out", ["b", "a"]) == ["out/b", "out/a"]


def test_dest_trailing_slash_and_root():
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


def test_empty_dest():
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_dot_and_empty_segments_dropped():
    assert plan_extraction("out", ["./a//b/./c"]) == ["out/a/b/c"]


def test_inner_parent_segments_are_resolved():
    assert plan_extraction("out", ["a/../b"]) == ["out/b"]
    assert plan_extraction("out", ["a/b/../../c"]) == ["out/c"]


@pytest.mark.parametrize("m", ["../a", "a/../../b", "..", "a/b/../../../c"])
def test_escape_rejected(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [m])


@pytest.mark.parametrize("m", [".", "./", "a/..", "//", ""])
def test_empty_after_normalisation_rejected(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [m])


def test_backslash_is_a_separator():
    assert plan_extraction("out", ["dir\\file.txt"]) == ["out/dir/file.txt"]


@pytest.mark.parametrize("m", ["..\\evil.exe", "a\\..\\..\\b", "\\abs", "\\\\server\\share"])
def test_backslash_attacks_rejected(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [m])


@pytest.mark.parametrize("m", ["/etc/passwd", "C:/x", "c:x", "C:\\Windows\\x", "z:"])
def test_absolute_and_drive_rejected(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("out", [m])


def test_nul_rejected():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a\x00.txt"])


def test_dotted_names_are_ordinary():
    assert plan_extraction("out", ["..a", "a..", "...", ".hidden"]) == ["out/..a", "out/a..", "out/...", "out/.hidden"]


def test_directory_entries_skipped_but_validated():
    assert plan_extraction("out", ["dir/", "dir/a"]) == ["out/dir/a"]
    assert plan_extraction("out", ["dir\\", "dir\\a"]) == ["out/dir/a"]
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["../", "a"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["./"])


def test_directory_entry_and_file_with_same_name():
    assert plan_extraction("out", ["dir/", "dir"]) == ["out/dir"]


def test_duplicates_rejected_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["a", "./a"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["x/y", "x\\y"])


def test_unsafe_error_is_value_error():
    assert issubclass(UnsafePathError, ValueError)


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("out", ["ok.txt", "../bad"])
