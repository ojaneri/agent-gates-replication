import pytest

from solution import decode, encode


@pytest.mark.parametrize("s,e", [
    ("", ""),
    ("aaa", "aaa"),
    ("aaaa", "~4~a"),
    ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"),
    ("a~b", "a~~b"),
    ("~~~", "~~~~~~"),
    ("~" * 5, "~5~~"),
    ("aaaabbb", "~4~abbb"),
    ("é" * 4 + "x", "~4~éx"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_decode_lenient():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~10~~") == "~" * 10


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~~~", "~4", "~4x", "~4~", "~04~a", "~3~a", "~0~a",
    "~1~a", "~12",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)


def test_roundtrip():
    import itertools
    for n in range(0, 7):
        for tup in itertools.product("a~1", repeat=n):
            s = "".join(tup)
            assert decode(encode(s)) == s
    s = "a" * 7 + "~" * 6 + "b" + "1" * 4
    assert decode(encode(s)) == s
