import pytest

from solution import check_password

GOOD = "Abcdefgh1jkl"


def test_valid():
    assert check_password(GOOD, "bob", set()) == []


def test_type_errors():
    with pytest.raises(TypeError, match="must be str"):
        check_password(1, "bob", set())
    with pytest.raises(TypeError, match="must be str"):
        check_password(GOOD, None, set())


def test_length_bounds():
    assert "LENGTH" in check_password("Abcdefgh1jk", "bob", set())
    assert "LENGTH" not in check_password("Abcdefgh1jkl", "bob", set())
    p64 = ("Ab1" * 22)[:64]
    p64 = "Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9St0Uv1Wx2Yz3Ab4Cd5Ef6Gh7Ij8Kl9Mn0Op1Q"[:64]
    assert len(p64) == 64
    assert "LENGTH" not in check_password(p64, "bob", set())
    assert "LENGTH" in check_password(p64 + "x", "bob", set())


def test_classes():
    assert check_password("abcdefghijkl", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefghijKL", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefghij12", "bob", set()) == ["CLASSES"]
    assert check_password("abcdefghijK1", "bob", set()) == []
    assert check_password("abcdefghijé!", "bob", set()) == ["CLASSES"]
    assert check_password("azAZ09azAZ09", "bob", set()) == []
    assert check_password("abcdefghiJé!", "bob", set()) == []
    assert check_password("ABCDEFGHIJ1 ", "bob", set()) == []
    assert check_password("abcdefghij1é", "bob", set()) == []
    assert check_password("abcdefghijé1", "bob", set()) == []
    assert check_password("ABCDEFGHIJ1é", "bob", set()) == []
    assert check_password("abcdefghi{}1", "bob", set()) == []
    assert check_password("abcdefghi@Z0", "bob", set()) == []
    assert check_password("abcdefghi`Z9", "bob", set()) == []
    assert check_password("abcdefghi[Z/", "bob", set()) == []
    assert check_password("abcdefghi:Z!", "bob", set()) == []


def test_username():
    assert check_password("xxBobxAbcdef1", "bob", set()) == ["USERNAME"]
    assert check_password("xxBOBxAbcdef1", "Bob", set()) == ["USERNAME"]
    assert check_password("xxbxAbcdef1xx", "b", set()) == []
    assert check_password("xxboxAbcdef1xx", "bo", set()) == []
    assert check_password("xxbobAbcdef1xx", "bob", set()) == ["USERNAME"]


def test_repeat():
    assert check_password("Abcdddefgh1j", "bob", set()) == ["REPEAT"]
    assert check_password("Abcddefgh1jk", "bob", set()) == []
    assert check_password("AAAbcdefgh1j", "bob", set()) == ["REPEAT"]
    assert check_password("Abcdefgh1jaa", "bob", set()) == []
    assert check_password("Abcdefgh1AAA", "bob", set()) == ["REPEAT"]
    assert check_password("aAabcdefgh1B", "bob", set()) == []


def test_blocklist():
    assert check_password(GOOD, "bob", {GOOD.upper()}) == ["BLOCKLIST"]
    assert check_password(GOOD, "bob", {"x", GOOD}) == ["BLOCKLIST"]
    assert check_password(GOOD, "bob", {GOOD + "x", "Abc"}) == []


def test_order():
    assert check_password("aaa", "aaa", {"aaa"}) == [
        "LENGTH",
        "CLASSES",
        "USERNAME",
        "REPEAT",
        "BLOCKLIST",
    ]
