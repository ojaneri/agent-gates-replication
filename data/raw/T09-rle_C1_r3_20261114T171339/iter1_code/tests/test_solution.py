import pytest
from solution import encode, decode


@pytest.mark.parametrize("s,e", [
    ("", ""),
    ("aaa", "aaa"),
    ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"),
    ("~~~~~", "~5~~"),
    ("a~b", "a~~b"),
    ("~~", "~~~~"),
    ("aaaabbb", "~4~abbb"),
])
def test_encode(s, e):
    assert encode(s) == e
    assert decode(e) == s


def test_roundtrip():
    for s in ["x~~~~y", "ééééé~", "a" * 100 + "~" * 4, "abc"]:
        assert decode(encode(s)) == s


def test_decode_lenient():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8


@pytest.mark.parametrize("t", [
    "~", "a~", "~x", "~05~a", "~0~a", "~3~a", "~5a", "~5", "~5~", "~4",
])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)
