import pytest
from solution import plan_extraction, UnsafePathError


def test_basic_and_dest():
    assert plan_extraction("out", ["a.txt", "b/c.txt"]) == ["out/a.txt", "out/b/c.txt"]
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


def test_bad_dest():
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_normalise():
    assert plan_extraction("o", ["a//b", "./c", "a/../d", "x\\y"]) == ["o/a/b", "o/c", "o/d", "o/x/y"]
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


@pytest.mark.parametrize("bad", ["/x", "\\x", "C:/x", "c:x", "C:\\x", "a\x00b",
                                 "a/../../b", "..", "../a", ".", "./", "a/..", "", "a/..\\.."])
def test_unsafe(bad):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", bad])


def test_dirs_skipped():
    assert plan_extraction("o", ["d/", "d\\", "d/f"]) == ["o/d/f"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "x/../a.txt"])
    assert plan_extraction("o", ["a/", "a/b"]) == ["o/a/b"]
