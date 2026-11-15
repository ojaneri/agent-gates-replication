import random

import pytest

from solution import decode, encode


@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("a", "a"),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("~", "~~"),
        ("~~~", "~~~~~~"),
        ("~~~~~", "~5~~"),
        ("~~~~", "~4~~"),
        ("a~b", "a~~b"),
        ("abc", "abc"),
        ("aab", "aab"),
        ("1111", "~4~1"),
        ("ab" + "x" * 4 + "cd", "ab~4~xcd"),
        ("é" * 6, "~6~é"),
        ("\U0001F600" * 4, "~4~\U0001F600"),
        ("a\nnn\n", "a\nnn\n"),
        ("aaaa~~~~", "~4~a~4~~"),
    ],
)
def test_encode_and_decode_examples(plain, encoded):
    assert encode(plain) == encoded
    assert decode(encoded) == plain


def test_encode_empty():
    assert encode("") == ""


def test_decode_empty():
    assert decode("") == ""


def test_decode_accepts_unproduced_forms():
    # Plain run of four, and two runs of the same character in a row.
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8
    assert decode("~4~a~5~a") == "a" * 9


def test_decode_plain_chars_and_escapes():
    assert decode("a~~b") == "a~b"
    assert decode("~~") == "~"
    assert decode("~~~~") == "~~"


def test_decode_run_of_digits_and_tilde():
    assert decode("~4~1") == "1111"
    assert decode("~10~z") == "z" * 10
    assert decode("~4~~") == "~~~~"
    assert decode("~4~~~~") == "~" * 5  # run of four '~', then escaped '~'


@pytest.mark.parametrize(
    "bad",
    [
        "~",  # tilde at end
        "a~",  # tilde at end after text
        "~a",  # neither tilde nor digit
        "~x~",  # neither tilde nor digit
        "~ ",  # space after tilde
        "~04~a",  # leading zero
        "~0~a",  # leading zero (and below 4)
        "~00~a",  # leading zeros
        "~3~a",  # count below 4
        "~1~a",  # count below 4
        "~5",  # count at end of text, not followed by tilde
        "~5a",  # count not followed by tilde
        "~12",  # count at end of text
        "~5~",  # missing character after second tilde
        "~~~",  # escaped tilde then lone tilde at end
        "x~4~",  # missing character after count
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


def _random_string(rng: random.Random, length: int) -> str:
    alphabet = "ab~0123456789 \n"
    out = []
    while len(out) < length:
        c = rng.choice(alphabet)
        out.extend([c] * rng.randint(1, 12))
    return "".join(out[:length])


def test_round_trip_random_strings():
    rng = random.Random(12345)
    for _ in range(500):
        s = _random_string(rng, rng.randint(0, 60))
        assert decode(encode(s)) == s


def test_maximal_runs():
    assert encode("a" * 12) == "~12~a"
    assert encode("a" * 4 + "b" * 4) == "~4~a~4~b"
