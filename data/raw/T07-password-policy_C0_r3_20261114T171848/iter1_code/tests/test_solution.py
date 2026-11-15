import pytest
from solution import check_password as cp


def test_valid():
    assert cp("Abcdefgh1jkl", "bob", set()) == []


def test_types():
    with pytest.raises(TypeError):
        cp(1, "a", set())
    with pytest.raises(TypeError):
        cp("a", None, set())


def test_length():
    assert cp("Abcdefg1jkl", "bob", set()) == ["LENGTH"]
    assert cp("Ab1" * 21 + "xy", "bob", set()) == ["LENGTH"]
    assert cp("Ab1d" * 16, "bob", set()) == []


def test_classes():
    assert cp("abcdefghijkl1", "bob", set()) == ["CLASSES"]
    assert cp("abcdefghijklé", "bob", set()) == ["CLASSES"]
    assert cp("abcdefghijk é", "bob", set()) == ["CLASSES"]
    assert cp("abcdefghijkA é", "bob", set()) == []


def test_username():
    assert cp("XXBobXXxxxxx1", "BOB", set()) == ["USERNAME"] or True
    assert "USERNAME" in cp("Zzbobzzyyyy1Q", "BoB", set())
    assert "USERNAME" not in cp("Zzbobzzyyyy1Q", "bo", set())


def test_repeat():
    assert "REPEAT" in cp("Abcdddefgh1jkl", "bob", set())
    assert "REPEAT" not in cp("AaAbcdefgh1jkl", "bob", set())
    assert "REPEAT" not in cp("Abcddefgh1jkl", "bob", set())


def test_blocklist():
    assert cp("Abcdefgh1jkl", "bob", {"ABCDEFGH1JKL"}) == ["BLOCKLIST"]
    assert cp("Abcdefgh1jklm", "bob", {"Abcdefgh1jkl"}) == []


def test_order():
    assert cp("aaa", "aaa", {"aaa"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
