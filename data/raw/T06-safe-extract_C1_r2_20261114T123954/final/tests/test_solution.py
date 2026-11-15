import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_dest_forms():
    assert plan_extraction("out", ["a.txt", "b/c.txt"]) == ["out/a.txt", "out/b/c.txt"]
    assert plan_extraction("out//", ["a"]) == ["out/a"]
    assert plan_extraction("/", ["a"]) == ["/a"]


@pytest.mark.parametrize("dest", ["", None, 5])
def test_bad_dest(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, [])


def test_normalisation():
    assert plan_extraction("d", ["a//b", "./c", "x/../y", "a\\z\\w"]) == [
        "d/a/b", "d/c", "d/y", "d/a/z/w"]
    assert plan_extraction("d", ["..a", "a..", "..."]) == ["d/..a", "d/a..", "d/..."]


@pytest.mark.parametrize("m", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "../a", "a/../../b",
    "a\\..\\..\\b", ".", "./", "a/..", "", "a/../",
])
def test_unsafe(m):
    with pytest.raises(UnsafePathError):
        plan_extraction("d", [m])


def test_directories_skipped():
    assert plan_extraction("d", ["a/", "a/b", "c\\"]) == ["d/a/b"]


def test_duplicates():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["A.txt", "x", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["a/b", "a\\.\\B"])


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("d", ["ok", "../bad"])


def test_dir_and_file_same_name_ok():
    assert plan_extraction("d", ["a/", "a/b"]) == ["d/a/b"]
