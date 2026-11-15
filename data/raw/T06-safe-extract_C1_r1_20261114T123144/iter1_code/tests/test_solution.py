import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_dest_variants():
    assert plan_extraction("out", ["a.txt", "b/c.txt"]) == ["out/a.txt", "out/b/c.txt"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


@pytest.mark.parametrize("dest", ["", None, 5])
def test_bad_dest(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["a"])


def test_normalisation():
    assert plan_extraction("d", ["a//b", "./c", "x/../y", "e\\f\\..\\g", "..a", "a..", "..."]) == [
        "d/a/b", "d/c", "d/y", "d/e/g", "d/..a", "d/a..", "d/..."]


@pytest.mark.parametrize("m", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../a", "a/../../b",
    ".", "./", "a/..", "", "a/..\\..",
])
def test_unsafe(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("d", [m])


def test_directories_skipped():
    assert plan_extraction("d", ["a/", "a/b", "c\\"]) == ["d/a/b"]


def test_dir_still_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["../x/"])


def test_duplicates_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["A.txt", "x", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["a/b", "a\\b"])


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["ok", "../bad"])


def test_digit_colon_not_drive():
    assert plan_extraction("d", ["1:x"]) == ["d/1:x"]
