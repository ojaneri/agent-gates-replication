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


@pytest.mark.parametrize("m", ["a\0b", "/x", "\\x", "C:/x", "c:x", "C:\\x",
                               "a/../../b", "..", "../a", ".", "./", "a/..", ""])
def test_unsafe(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [m])


def test_dotdot_names_ok():
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


def test_directories_skipped():
    assert plan_extraction("o", ["d/", "d/f", "e\\"]) == ["o/d/f"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a/x/../B"])


def test_no_partial():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
