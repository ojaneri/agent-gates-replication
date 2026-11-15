import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_dest_slash():
    assert plan_extraction("out/", ["a.txt", "b/c.txt"]) == ["out/a.txt", "out/b/c.txt"]
    assert plan_extraction("/", ["x"]) == ["/x"]


def test_bad_dest():
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_normalise():
    assert plan_extraction("o", ["a//b", "./c", "a/../d", "e\\f"]) == [
        "o/a/b", "o/c", "o/d", "o/e/f"]


@pytest.mark.parametrize("name", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../x", "a/../../b",
    ".", "./", "a/..", "", "a\\..\\..\\b",
])
def test_unsafe(name):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [name])


def test_dotdot_like_names():
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


def test_directory_entries():
    assert plan_extraction("o", ["d/", "d/f", "e\\"]) == ["o/d/f"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_collisions():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a//B"])
    assert plan_extraction("o", ["a/", "A/"]) == []


def test_no_partial():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
