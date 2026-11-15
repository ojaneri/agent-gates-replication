import pytest
from solution import check_password as cp


def test_valid():
    assert cp("Abcdefg1hijk", "bob", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        cp(1, "a", set())
    with pytest.raises(TypeError):
        cp("a", None, set())


def test_length_bounds():
    assert "LENGTH" in cp("Abcdefg1hij", "bob", set())
    assert "LENGTH" not in cp("Abcdefg1hijk", "bob", set())
    assert "LENGTH" not in cp("Ab1" * 21 + "c", "bob", set())  # 64
    assert "LENGTH" in cp("Ab1" * 21 + "cd", "bob", set())  # 65


def test_classes():
    assert "CLASSES" in cp("abcdefghijklm", "bob", set())
    assert "CLASSES" in cp("abcdefGHIJKLM", "bob", set())
    assert "CLASSES" not in cp("abcdefGHIJ12", "bob", set())
    assert "CLASSES" not in cp("abcdefGHIJé ", "bob", set())


def test_username():
    assert "USERNAME" in cp("xxBOBbyxAb1xyz", "bobby", set())
    assert "USERNAME" not in cp("Abcdefg1hijk", "ab", set())
    assert "USERNAME" not in cp("Abcdefg1hijk", "", set())


def test_repeat():
    assert "REPEAT" in cp("Abcdefg1hiiik", "bob", set())
    assert "REPEAT" not in cp("Abcdefg1hiiAk".replace("iiA", "iAi"), "bob", set())
    assert "REPEAT" not in cp("aAaBcdefg1hijk", "bob", set())


def test_blocklist():
    assert "BLOCKLIST" in cp("Abcdefg1hijk", "bob", {"ABCDEFG1HIJK"})
    assert "BLOCKLIST" not in cp("Abcdefg1hijkx", "bob", {"abcdefg1hijk"})


def test_order():
    assert cp("aaa", "aaa", {"aaa"}) == ["LENGTH", "CLASSES", "USERNAME", "REPEAT", "BLOCKLIST"]
