import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_order():
    assert plan_extraction("out", ["b.txt", "a/c.txt"]) == ["out/b.txt", "out/a/c.txt"]


def test_dest_trailing_and_root():
    assert plan_extraction("out/", ["x"]) == ["out/x"]
    assert plan_extraction("/", ["x"]) == ["/x"]


@pytest.mark.parametrize("d", ["", None, 5])
def test_bad_dest(d):
    with pytest.raises(ValueError):
        plan_extraction(d, [])


def test_normalisation():
    assert plan_extraction("o", ["a//b", "./c", "a/../d", "e\\f", "..a", "a..", "..."]) == [
        "o/a/b", "o/c", "o/d", "o/e/f", "o/..a", "o/a..", "o/..."]


@pytest.mark.parametrize("m", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../x", "a/../../b",
    ".", "./", "a/..", "", "a/..\\..",
])
def test_unsafe(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [m])


def test_directories_skipped():
    assert plan_extraction("o", ["d/", "d\\", "d/f"]) == ["o/d/f"]


def test_directory_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a\\b"])


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])


def test_non_letter_colon_ok():
    assert plan_extraction("o", ["1:x"]) == ["o/1:x"]
