import pytest

from solution import check_password

GOOD = "Abcdefgh1jkl"


def test_valid():
    assert check_password(GOOD, "bob", set()) == []


def test_type_errors():
    with pytest.raises(TypeError):
        check_password(1, "bob", set())
    with pytest.raises(TypeError):
        check_password(GOOD, None, set())


def test_length_bounds():
    assert check_password("Abcdefgh1jk", "zzz", set()) == ["LENGTH"]
    assert check_password("Abcdefgh1jkl", "zzz", set()) == []
    p64 = ("Abcdefgh1j" * 7)[:64]
    assert check_password(p64, "zzz", set()) == []
    assert check_password(p64 + "k", "zzz", set()) == ["LENGTH"]


def test_classes():
    assert check_password("abcdefghijkl", "zzz", set()) == ["CLASSES"]
    assert check_password("abcdefgh1jkl", "zzz", set()) == ["CLASSES"]
    assert check_password("abcdefgh1jk!", "zzz", set()) == []
    assert check_password("ABCDEFGH1JK!", "zzz", set()) == []
    assert check_password("abcdefghijkéA", "zzz", set()) == []
    assert check_password("abcdefghijkA1", "zzz", set()) == []
    assert check_password("ABCDEFGHIJKL ", "zzz", set()) == ["CLASSES"]
    assert check_password("abcdefg hijk1", "zzz", set()) == []
    assert check_password("@[`{abcdefgh", "zzz", set()) == ["CLASSES"]
    assert check_password("/:AZaz09/:AZ", "zzz", set()) == []


def test_username():
    assert check_password("xxBOBxxAb1cd", "bob", set()) == ["USERNAME"]
    assert check_password("xxbobxxAb1cd", "BOB", set()) == ["USERNAME"]
    assert check_password("xxboxyxAb1cd", "bo", set()) == []
    assert check_password("xxboxyxAb1cd", "", set()) == []
    assert check_password("xxbxoxbAb1cd", "bob", set()) == []


def test_repeat():
    assert check_password("Abcdefgh1jkk", "zzz", set()) == []
    assert check_password("Abcdefgh1kkk", "zzz", set()) == ["REPEAT"]
    assert check_password("Abcdefgh1jjj", "zzz", set()) == ["REPEAT"]
    assert check_password("aaaBcdefgh1j", "zzz", set()) == ["REPEAT"]
    assert check_password("aAaBcdefgh1j", "zzz", set()) == []
    assert check_password("aabaBcdefgh1", "zzz", set()) == []


def test_blocklist():
    assert check_password(GOOD, "zzz", {GOOD.upper()}) == ["BLOCKLIST"]
    assert check_password(GOOD, "zzz", {"x", GOOD.lower()}) == ["BLOCKLIST"]
    assert check_password(GOOD, "zzz", {"Abcdefgh1"}) == []


def test_order_all():
    assert check_password("aaa", "aaa", {"AAA"}) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
        "REPEAT",
        "BLOCKLIST",
    ]
