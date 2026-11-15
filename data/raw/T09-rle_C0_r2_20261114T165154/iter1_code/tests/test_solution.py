import random

import pytest

from solution import decode, encode


# ---------- encode ----------

def test_encode_empty():
    assert encode("") == ""


def test_encode_short_runs_unchanged():
    assert encode("aaa") == "aaa"
    assert encode("abc") == "abc"


def test_encode_run_of_four_and_five():
    assert encode("aaaa") == "~4~a"
    assert encode("aaaaa") == "~5~a"


def test_encode_run_of_twelve_is_single_run():
    assert encode("a" * 12) == "~12~a"


def test_encode_tilde_escaped():
    assert encode("~") == "~~"
    assert encode("a~b") == "a~~b"


def test_encode_run_of_tildes():
    assert encode("~" * 5) == "~5~~"


def test_encode_short_tilde_run_escaped_each():
    assert encode("~~~") == "~~~~~~"


def test_encode_mixed():
    assert encode("aaaa~~bbbbbbc") == "~4~a~~~~~6~bc"


def test_encode_unicode():
    assert encode("ééééé") == "~5~é"
    assert encode("日日日日") == "~4~日"


def test_encode_runs_are_maximal():
    assert encode("aaaabbbb") == "~4~a~4~b"


# ---------- decode ----------

def test_decode_empty():
    assert decode("") == ""


def test_decode_plain():
    assert decode("abc") == "abc"
    assert decode("aaa") == "aaa"


def test_decode_escaped_tilde():
    assert decode("~~") == "~"
    assert decode("a~~b") == "a~b"


def test_decode_runs():
    assert decode("~5~a") == "aaaaa"
    assert decode("~12~a") == "a" * 12
    assert decode("~5~~") == "~" * 5


def test_decode_accepts_non_canonical_forms():
    assert decode("aaaa") == "aaaa"
    assert decode("~4~a~4~a") == "a" * 8


def test_decode_run_followed_by_escaped_tilde():
    assert decode("~4~a~~") == "aaaa~"


def test_decode_digit_character_as_payload():
    # The payload character may itself be a digit or a tilde.
    assert decode("~4~1") == "1111"


@pytest.mark.parametrize(
    "bad",
    [
        "~",            # tilde at end
        "a~",           # tilde at end
        "~x",           # tilde followed by non-tilde, non-digit
        "~a~b",         # same
        "~05~a",        # leading zero
        "~00004~a",     # leading zeros
        "~0~a",         # zero count
        "~3~a",         # count below 4
        "~1~a",         # count below 4
        "~5a",          # count not followed by ~
        "~5",           # count at end, no ~
        "~5~",          # missing character
        "~12",          # no closing ~ and no char
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


# ---------- round trip ----------

ALPHABET = list("ab~0123 é日")


def test_round_trip_examples():
    samples = [
        "",
        "a",
        "~",
        "~~~~",
        "aaaa~~bbbbbbc",
        "~" * 4 + "x" * 3,
        "123444444444",
        "é" * 7 + "~",
    ]
    for s in samples:
        assert decode(encode(s)) == s


def test_round_trip_random():
    rng = random.Random(12345)
    for _ in range(2000):
        length = rng.randint(0, 60)
        s = "".join(rng.choice(ALPHABET) for _ in range(length))
        assert decode(encode(s)) == s


def test_round_trip_long_runs():
    rng = random.Random(7)
    for _ in range(200):
        parts = []
        for _ in range(rng.randint(1, 6)):
            parts.append(rng.choice(ALPHABET) * rng.randint(1, 30))
        s = "".join(parts)
        assert decode(encode(s)) == s
