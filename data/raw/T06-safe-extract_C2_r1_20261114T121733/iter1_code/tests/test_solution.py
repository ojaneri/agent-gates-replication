import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_order():
    assert plan_extraction("out", ["b.txt", "a/c.txt"]) == ["out/b.txt", "out/a/c.txt"]


def test_empty_members():
    assert plan_extraction("out", []) == []


@pytest.mark.parametrize("dest", ["", None, 5])
def test_bad_dest(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a"])


def test_dest_trailing_slashes():
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


def test_backslash_and_normalise():
    assert plan_extraction("o", ["a\\b", "x//y", "./z", "p/../q", "a/b/../../r"]) == [
        "o/a/b", "o/x/y", "o/z", "o/q", "o/r"]


@pytest.mark.parametrize("name", [
    "a\0b", "/a", "\\a", "C:/x", "c:x", "C:\\x", "a/../../b", "..", "../a",
    "a\\..\\..\\b", ".", "./", "a/..", "", "/", "a:",
])
def test_unsafe(name):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [name])


@pytest.mark.parametrize("name", ["..a", "a..", "...", "1:x", "ab:c"])
def test_ordinary_names(name):
    assert plan_extraction("o", [name]) == ["o/" + name]


def test_non_ascii_letter_not_drive():
    assert plan_extraction("o", ["é:x"]) == ["o/é:x"]


def test_directories_skipped_but_validated():
    assert plan_extraction("o", ["d/", "d\\", "d/f"]) == ["o/d/f"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a\\b"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a", "./a"])


def test_dir_not_duplicate():
    assert plan_extraction("o", ["a/", "a/", "A"]) == ["o/A"]


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
