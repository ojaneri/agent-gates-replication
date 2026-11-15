import pytest
from solution import check_password as cp


def test_valid():
    assert cp("Abcdefgh1jkl", "bob", set()) == []


def test_type():
    with pytest.raises(TypeError):
        cp(1, "a", set())
    with pytest.raises(TypeError):
        cp("a", None, set())


def test_length():
    assert cp("Ab1xYz", "bob", set()) == ["LENGTH"]
    assert "LENGTH" in cp("Ab1" * 30, "bob", set())
    assert cp("aB1" * 4, "bob", set()) == []
    assert cp("aB1d" * 16, "bob", set()) == []


def test_classes():
    assert cp("abcdefghijkl", "bob", set()) == ["CLASSES"]
    assert cp("abcdefgHijk!", "bob", set()) == []
    assert cp("abcdefghijé1", "bob", set()) == []


def test_username():
    assert cp("xxBOBxAbcd1k", "bob", set()) == ["USERNAME"]
    assert cp("Abcdefgh1jkl", "bo", set()) == []


def test_repeat():
    assert cp("Abcdddefgh1k", "bob", set()) == ["REPEAT"]
    assert cp("Abcdd1efgh1k", "bob", set()) == []
    assert cp("aAabcdefgh1X", "bob", set()) == []


def test_blocklist():
    assert cp("Abcdefgh1jkl", "bob", {"aBCDEFGH1JKL"}) == ["BLOCKLIST"]
    assert cp("Abcdefgh1jkl", "bob", {"abcdefgh1jklx"}) == []


def test_order():
    assert cp("aaa", "aaa", {"AAA"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
