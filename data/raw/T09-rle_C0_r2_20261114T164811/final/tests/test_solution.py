import pytest
from solution import encode, decode


@pytest.mark.parametrize("s,e", [
    ("", ""),
    ("aaa", "aaa"),
    ("aaaa", "~4~a"),
    ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"),
    ("a~b", "a~~b"),
    ("~", "~~"),
    ("~~~", "~~~~~~"),
    ("~" * 5, "~5~~"),
    ("aaaabbbb", "~4~a~4~b"),
    ("é" * 4, "~4~é"),
    ("1111", "~4~1"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_roundtrip():
    for s in ["abc~~~~~~x", "zzzz~zzzz", "~a~a~a~a", "\n\n\n\n\n"]:
        assert decode(encode(s)) == s


def test_decode_lenient():
    assert decode("~2~~".replace("2", "4")) == "~~~~"
    assert decode("~4~a~4~a") == "a" * 8


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~05~a", "~3~a", "~0~a", "~4", "~4x", "~4~", "~4a~a", "~~~",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)
