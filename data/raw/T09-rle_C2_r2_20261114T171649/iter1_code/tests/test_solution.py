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
    ("~" * 5, "~5~~"),
    ("aaaabbbbb", "~4~a~5~b"),
    ("xaaaay", "x~4~ay"),
    ("1111", "~4~1"),
])
def test_encode_decode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_decode_non_canonical():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~10~é") == "é" * 10
    assert decode("~4~~") == "~~~~"


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~a~b", "~04~a", "~0~a", "~3~a", "~1~a", "~4", "~4a",
    "~4~", "~~~", "~12", "~4x~a", "~²~a",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)


def test_roundtrip():
    for s in ["", "abc", "~~~~~~~a~~", "zzzzzzz~zzzz~~~~", "日日日日日x"]:
        assert decode(encode(s)) == s
