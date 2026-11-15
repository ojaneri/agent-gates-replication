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
    assert "LENGTH" in check_password("Abcdefgh1jk", "bob", set())
    assert "LENGTH" not in check_password("Abcdefgh1jkl", "bob", set())
    p64 = ("Ab1" + "xyz") * 10 + "Ab1x"
    assert len(p64) == 64
    assert "LENGTH" not in check_password(p64, "bob", set())
    assert "LENGTH" in check_password(p64 + "q", "bob", set())


def test_classes():
    assert check_password("abcdefghijkl", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefgh1jkl", "bob", set()) == ["CLASSES"]
    assert check_password("ABCDEFGH1JKL", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefgh1jkl1", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefghijk!", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefghi1k!", "bob", set()) == []
    assert check_password("abcdefghiAk!", "bob", set()) == []
    assert check_password("abcdefghAAk1", "bob", set()) == []
    assert check_password("abcdefghi1ké", "bob", set()) == []
    assert check_password("ABCDEFGHI1k ", "bob", set()) == []
    # boundary chars are not letters/digits
    assert check_password("abcdefghij`{", "bob", set()) == ["CLASSES"]
    assert check_password("ABCDEFGHI@[A", "bob", set()) == ["CLASSES"]
    assert check_password("0123456789/:", "bob", set()) == ["CLASSES"]
    assert check_password("ABCDEFGHIJK@", "bob", set()) == ["CLASSES"]


def test_username():
    assert check_password("xxBOBxxAbc1x", "bob", set()) == ["USERNAME"]
    assert check_password("xxbobxxAbc1x", "BOB", set()) == ["USERNAME"]
    assert check_password("xxbbxxAbc1xy", "bb", set()) == []
    assert check_password("xxbbxxAbc1xy", "", set()) == []


def test_repeat():
    assert check_password("Abcdefgh1jjj", "bob", set()) == ["REPEAT"]
    assert check_password("Abcdefgh1jj1", "bob", set()) == []
    assert check_password("Abcdefgh1aAa", "bob", set()) == []
    assert check_password("aaabcdefgH1k", "bob", set()) == ["REPEAT"]


def test_blocklist():
    assert check_password(GOOD, "bob", {GOOD.upper()}) == ["BLOCKLIST"]
    assert check_password(GOOD, "bob", {GOOD.lower()}) == ["BLOCKLIST"]
    assert check_password(GOOD, "bob", {"Abcdefgh1"}) == []


def test_order():
    assert check_password("aaa", "aaa", {"aaa"}) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
        "REPEAT",
        "BLOCKLIST",
    ]
