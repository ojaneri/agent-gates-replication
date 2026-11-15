import pytest
from solution import plan_extraction, UnsafePathError


def test_basic():
    assert plan_extraction("out", ["a.txt", "d/b.txt"]) == ["out/a.txt", "out/d/b.txt"]


def test_dest():
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]
    for bad in ("", None):
        with pytest.raises(ValueError):
            plan_extraction(bad, [])


def test_normalise():
    assert plan_extraction("o", ["a//b", "./c", "a/../d", "e\\f"]) == ["o/a/b", "o/c", "o/d", "o/e/f"]
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


@pytest.mark.parametrize("bad", [
    "a\0b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../x", "a/../../b",
    ".", "./", "a/..", "a/../", "", "..\\x",
])
def test_unsafe(bad):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [bad])


def test_directories_skipped():
    assert plan_extraction("o", ["d/", "d/f", "e\\"]) == ["o/d/f"]


def test_dir_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_collisions():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a\\b"])


def test_no_partial():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
