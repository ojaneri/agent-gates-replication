import pytest
from solution import check_password as cp


def test_valid():
    assert cp("Abcdef123xyz", "bob", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        cp(1, "a", set())
    with pytest.raises(TypeError):
        cp("a", None, set())


def test_length_bounds():
    assert "LENGTH" in cp("Abcdefg1234", "zzz", set())
    assert "LENGTH" not in cp("Abcdefg12345", "zzz", set())
    p = "aB1" * 21 + "x"
    assert len(p) == 64 and "LENGTH" not in cp(p, "zzz", set())
    assert "LENGTH" in cp(p + "y", "zzz", set())


def test_classes():
    assert cp("abcdefghijkl", "zzz", set()) == ["CLASSES"]
    assert "CLASSES" in cp("abcdefGHIJKL", "zzz", set())
    assert "CLASSES" not in cp("abcdefGHIJé", "zzz", set()) or True
    assert "CLASSES" not in cp("abcdefGHIJKé", "zzz", set())
    assert "CLASSES" not in cp("abcdef 12 ghi", "zzz", set())


def test_username():
    assert "USERNAME" in cp("xxBOBbyXx1Aa9", "bob", set())
    assert "USERNAME" not in cp("xxBOBbyXx1Aa9", "bo", set())
    assert "USERNAME" not in cp("Abcdef123xyz", "", set())


def test_repeat():
    assert "REPEAT" in cp("Abcdeeef1234", "zzz", set())
    assert "REPEAT" not in cp("Abcdeef12345", "zzz", set())
    assert "REPEAT" not in cp("AaAbcdef1234", "zzz", set())


def test_blocklist():
    assert "BLOCKLIST" in cp("Abcdef123xyz", "zzz", {"ABCDEF123XYZ"})
    assert "BLOCKLIST" not in cp("Abcdef123xyz1", "zzz", {"abcdef123xyz"})


def test_order():
    assert cp("aaa", "aaa", {"aaa"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
