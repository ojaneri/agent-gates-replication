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
    assert cp("Ab1xYz", "bob", set()) == ["LENGTH"]
    assert cp("Ab1" + "xYzw" * 16, "bob", set()) == ["LENGTH"]  # 67
    assert cp("Ab1" + "xYzw" * 15 + "q", "bob", set()) == []  # 64
    assert cp("Abcdefgh1jkl", "bob", set()) == []  # 12


def test_classes():
    assert cp("abcdefghijkl", "bob", set()) == ["CLASSES"]
    assert cp("abcdefgh1jkl", "bob", set()) == ["CLASSES"]
    assert cp("abcdefgh1jé!", "bob", set()) == []
    assert cp("abcdEfgh1jé!", "bob", set()) == []
    assert cp("ABCDEFGH1JéK", "bob", set()) == ["CLASSES"][:0]


def test_username():
    assert cp("Abcdefgh1jkl", "DEF", set()) == ["USERNAME"]
    assert cp("Abcdefgh1jkl", "de", set()) == []
    assert cp("Abcdefgh1jkl", "", set()) == []


def test_repeat():
    assert cp("Abcdddgh1jkl", "bob", set()) == ["REPEAT"]
    assert cp("Abcdd dgh1jkl", "bob", set()) == []
    assert cp("AbcdAaAh1jkl", "bob", set()) == []


def test_blocklist():
    assert cp("Abcdefgh1jkl", "bob", {"aBCDEFGH1JKL"}) == ["BLOCKLIST"]
    assert cp("Abcdefgh1jkl", "bob", {"Abcdefgh1jklm"}) == []


def test_order():
    r = cp("aaa", "aaa", {"AAA"})
    assert r == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
