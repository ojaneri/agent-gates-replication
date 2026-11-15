import pytest
from solution import plan_extraction, UnsafePathError


def test_basic_and_order():
    assert plan_extraction("out", ["b.txt", "a/c.txt"]) == ["out/b.txt", "out/a/c.txt"]


def test_dest_handling():
    assert plan_extraction("out/", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]
    for bad in ("", None):
        with pytest.raises(ValueError):
            plan_extraction(bad, ["a"])


def test_normalisation():
    assert plan_extraction("o", ["a//b", "./c", "d/../e", "f\\g"]) == ["o/a/b", "o/c", "o/e", "o/f/g"]
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


@pytest.mark.parametrize("bad", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../a", "a/../../b",
    "a\\..\\..\\b", ".", "./", "a/..", "",
])
def test_unsafe(bad):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [bad])


def test_directories_skipped_but_validated():
    assert plan_extraction("o", ["d/", "d/f", "e\\"]) == ["o/d/f"]
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "x/../a.txt"])
    assert plan_extraction("o", ["d/", "d", ]) == ["o/d"]


def test_no_partial():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
