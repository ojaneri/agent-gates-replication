import pytest
from solution import check_password as cp


def test_valid():
    assert cp("Abcdefgh1jkl", "bob", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        cp(1, "a", set())
    with pytest.raises(TypeError):
        cp("a", None, set())


def test_length():
    assert cp("Ab1xyzuvwqp", "bob", set()) == ["LENGTH"]
    assert cp("Ab1" + "xy" * 31, "bob", set()) == ["LENGTH"]
    assert cp("Ab1" + "xy" * 30 + "z", "bob", set()) == []


def test_classes():
    assert cp("abcdefghijkl", "bob", set()) == ["CLASSES"]
    assert cp("abcdefgHijk!", "bob", set()) == []
    assert cp("abcdefgéijk1", "bob", set()) == []


def test_username():
    assert cp("xxBOBxAbcdef1", "bob", set()) == ["USERNAME"]
    assert cp("Abcdefgh1jbo", "bo", set()) == []


def test_repeat():
    assert cp("Abcdefgh1jkkk", "bob", set()) == ["REPEAT"]
    assert cp("aAaBcdefgh12", "bob", set()) == []


def test_blocklist():
    assert cp("Abcdefgh1jkl", "bob", {"ABCDEFGH1JKL"}) == ["BLOCKLIST"]
    assert cp("Abcdefgh1jkl", "bob", {"abcdefgh1jkl2"}) == []


def test_order():
    assert cp("aaa", "aaa", {"aaa"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
