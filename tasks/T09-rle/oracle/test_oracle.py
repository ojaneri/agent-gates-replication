import pytest

from solution import encode, decode


@pytest.mark.parametrize("s,e", [
    ("", ""), ("a", "a"), ("aaa", "aaa"), ("aaaa", "~4~a"), ("aaaaa", "~5~a"),
    ("a" * 12, "~12~a"), ("abbbbc", "a~4~bc"), ("~", "~~"), ("a~b", "a~~b"),
    ("~~~", "~~~~~~"), ("~~~~~", "~5~~"), ("ééééé", "~5~é"), ("1111", "~4~1"),
    ("aaaabbbb", "~4~a~4~b"), ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                "~100~a"),
])
def test_encode(s, e):
    assert encode(s) == e


@pytest.mark.parametrize("s", ["", "abc", "aaaa", "~~~~~~~~~", "a~4~b", "112222333334", "x" * 37 + "~" + "y" * 3,
                               "~1~", "ab~~cd~~~~e", "ééééé é"])
def test_round_trip(s):
    assert decode(encode(s)) == s


def test_decode_accepts_non_canonical():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8


def test_decode_runs_and_escapes():
    assert decode("~4~~") == "~~~~"
    assert decode("~~5") == "~5"
    assert decode("~10~z1") == "z" * 10 + "1"
    assert decode("~9~a") == "a" * 9
    assert decode("~90~b") == "b" * 90


@pytest.mark.parametrize("t", ["~", "a~", "~a", "~4", "~4~", "~04~a", "~3~a", "~0~a", "~4a", "~ 4~a", "~-4~a"])
def test_decode_errors(t):
    with pytest.raises(ValueError):
        decode(t)
