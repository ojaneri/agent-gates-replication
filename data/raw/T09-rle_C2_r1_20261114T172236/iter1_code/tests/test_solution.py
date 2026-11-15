import pytest

from solution import decode, encode


@pytest.mark.parametrize("s,e", [
    ("", ""),
    ("a", "a"),
    ("aaa", "aaa"),
    ("aaaa", "~4~a"),
    ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"),
    ("a~b", "a~~b"),
    ("~", "~~"),
    ("~~~", "~~~~~~"),
    ("~~~~", "~4~~"),
    ("~" * 5, "~5~~"),
    ("aaabbbb", "aaa~4~b"),
    ("aabbbbbc", "aa~5~bc"),
    ("1111", "~4~1"),
    ("é" * 4, "~4~é"),
])
def test_encode_decode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_decode_lenient():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~10~x") == "x" * 10
    assert decode("~4~5") == "5555"


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~a~b", "~5", "~5x", "~5~", "~~~", "~4",
    "~05~a", "~0~a", "~3~a", "~1~a", "~~~~~", "~4~", "~~~5~",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)


def test_roundtrip():
    for s in ["abc~~~~~def", "~a~a~a~a", "xxxx~yyyy", "a" * 100 + "~" * 4]:
        assert decode(encode(s)) == s
