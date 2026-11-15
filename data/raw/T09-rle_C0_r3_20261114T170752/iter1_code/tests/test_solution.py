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
    ("1111", "~4~1"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_roundtrip():
    for s in ["x~~~~y", "ééééé", "😀" * 7, "ab" * 5, "~a~~a" * 3, "9" * 30]:
        assert decode(encode(s)) == s


def test_decode_lenient():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~4~~") == "~~~~"
    assert decode("~10~0") == "0" * 10


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~5", "~5x", "~5~", "~05~a", "~3~a", "~0~a", "~1~a", "~~~",
    "~4", "~-4~a",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)
