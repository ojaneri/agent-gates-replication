import pytest

from solution import UnsafePathError, plan_extraction


def test_basic_and_order():
    assert plan_extraction("out", ["b.txt", "a/c.txt"]) == ["out/b.txt", "out/a/c.txt"]


def test_empty_members():
    assert plan_extraction("out", []) == []


def test_dest_trailing_slash_and_root():
    assert plan_extraction("out//", ["x"]) == ["out/x"]
    assert plan_extraction("/", ["x"]) == ["/x"]


@pytest.mark.parametrize("dest", ["", None])
def test_bad_dest(dest):
    with pytest.raises(ValueError):
        plan_extraction(dest, ["x"])


def test_normalisation():
    assert plan_extraction("o", ["a//b", "./c", "d/../e", "f\\g"]) == [
        "o/a/b", "o/c", "o/e", "o/f/g"]


def test_dotted_names_ordinary():
    assert plan_extraction("o", ["..a", "a..", "..."]) == ["o/..a", "o/a..", "o/..."]


@pytest.mark.parametrize("bad", [
    "a\x00b", "/x", "\\x", "C:/x", "c:x", "C:\\x", "..", "../x", "a/../../b",
    "..\\x", ".", "./", "a/..", "", "a/../",
])
def test_unsafe(bad):
    with pytest.raises(UnsafePathError):
        plan_extraction("o", [bad])


def test_colon_not_drive():
    assert plan_extraction("o", ["1:x", "ab:"]) == ["o/1:x", "o/ab:"]
    assert plan_extraction("o", ["a"]) == ["o/a"]


def test_directories_skipped():
    assert plan_extraction("o", ["d/", "e\\", "d/f"]) == ["o/d/f"]


def test_directory_validated():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["../d/"])


def test_duplicates_case_insensitive():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["A.txt", "a.txt"])
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["a/b", "a\\./b"])


def test_dir_and_file_same_name_ok():
    assert plan_extraction("o", ["a/", "a"]) == ["o/a"]


def test_no_partial_plan():
    with pytest.raises(UnsafePathError):
        plan_extraction("o", ["ok", "../bad"])
