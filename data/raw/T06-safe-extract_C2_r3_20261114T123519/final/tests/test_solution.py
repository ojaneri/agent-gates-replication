import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_order():
    assert plan_extraction("out", ["b.txt", "a/c.txt"]) == ["out/b.txt", "out/a/c.txt"]


def test_empty_members():
    assert plan_extraction("out", []) == []


@pytest.mark.parametrize("d", ["", None, 5])
def test_bad_dest(d):
    with pytest.raises(ValueError):
        plan_extraction(d, ["a"])


def test_dest_trailing_slashes():
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


def test_separators_and_normalisation():
    assert plan_extraction("o", ["a//b", "./c", "d\\e", "f/../g", "h/./i"]) == [
        "o/a/b", "o/c", "o/d/e", "o/g", "o/h/i"]


@pytest.mark.parametrize("m", [
    "a\0b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "..", "../a", "a/../../b",
    "a\\..\\..\\b", ".", "./", "a/..", "", "//", "z:",
])
def test_unsafe(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [m])


@pytest.mark.parametrize("m", ["..a", "a..", "...", "1:x", "ab:c", "é:x"])
def test_ordinary_names(m):
    assert plan_extraction("o", [m]) == ["o/" + m]


def test_directory_entries_skipped():
    assert plan_extraction("o", ["d/", "d\\", "d/f"]) == ["o/d/f"]


def test_dir_entry_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a\\b"])


def test_dir_not_duplicate():
    assert plan_extraction("o", ["a/", "a/"]) == []
    assert plan_extraction("o", ["A/", "a"]) == ["o/a"]


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
