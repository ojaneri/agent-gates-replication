import pytest
from solution import plan_extraction, UnsafePathError


def test_basic():
    assert plan_extraction("out", ["a.txt", "d/b.txt"]) == ["out/a.txt", "out/d/b.txt"]


def test_dest():
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]
    with pytest.raises(ValueError):
        plan_extraction("", ["a"])


def test_normalise():
    assert plan_extraction("o", ["a//b", "./c", "x/../y", "d\\e"]) == ["o/a/b", "o/c", "o/y", "o/d/e"]


def test_dir_entries_skipped():
    assert plan_extraction("o", ["d/", "d\\", "d/f"]) == ["o/d/f"]


@pytest.mark.parametrize("bad", ["/x", "\\x", "C:/x", "c:x", "C:\\x", "a/../../b", "..", "a\0b",
                                 ".", "./", "a/..", "../"])
def test_unsafe(bad):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [bad])


def test_dotdot_names_ok():
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a//B"])


def test_dir_not_duplicate():
    assert plan_extraction("o", ["a/", "A"]) == ["o/A"]


def test_no_partial():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
