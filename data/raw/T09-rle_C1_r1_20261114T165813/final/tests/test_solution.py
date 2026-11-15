import pytest
from solution import encode, decode


@pytest.mark.parametrize("s,e", [
    ("", ""),
    ("aaa", "aaa"),
    ("aaaa", "~4~a"),
    ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"),
    ("a~b", "a~~b"),
    ("~~~", "~~~~~~"),
    ("~" * 5, "~5~~"),
    ("aaaabbbb", "~4~a~4~b"),
    ("ééééé", "~5~é"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_decode_lenient():
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~10~x") == "x" * 10


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~05~a", "~3~a", "~0~a", "~4", "~4x", "~4~", "~~~",
    "~04~a",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)


def test_roundtrip():
    for s in ["a~~~~~b", "xxxx~yyyy~~", "abc" * 10, "~a~a~a~a", "\U0001F600" * 6]:
        assert decode(encode(s)) == s
