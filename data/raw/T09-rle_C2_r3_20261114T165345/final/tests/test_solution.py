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
    ("aaaabbbbb", "~4~a~5~b"),
    ("a" * 9 + "b", "~9~ab"),
    ("é" * 4 + "x", "~4~éx"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_decode_lenient():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~10~x") == "x" * 10
    assert decode("~4~~") == "~~~~"
    assert decode("~4~1") == "1111"


@pytest.mark.parametrize("t", [
    "~", "a~", "~a", "~x~a", "~04~a", "~0~a", "~3~a", "~1~a", "~4", "~4a",
    "~4~", "x~12", "~~~", "~ 4~a", "~-4~a", "~4a~a",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)


def test_roundtrip():
    for s in ["", "~", "a~~~~~b", "abcabc", "zzzz~zzzz", "~~~~~~~~~~~~", "a" * 100]:
        assert decode(encode(s)) == s
