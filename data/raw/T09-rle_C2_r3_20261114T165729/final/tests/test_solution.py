import random

import pytest

from solution import decode, encode


@pytest.mark.parametrize(
    "plain, expected",
    [
        ("", ""),
        ("a", "a"),
        ("aa", "aa"),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("a" * 12, "~12~a"),
        ("12", "12"),
        ("1111", "~4~1"),
        ("aaaa1", "~4~a1"),
        ("aaaabbbb", "~4~a~4~b"),
        ("aaaaaaaa1", "~8~a1"),
        ("aaabbbbcc", "aaa~4~bcc"),
        ("~", "~~"),
        ("~~", "~~~~"),
        ("~~~", "~~~~~~"),
        ("~~~~", "~4~~"),
        ("~~~~~", "~5~~"),
        ("a~b", "a~~b"),
        ("aa~~~~aa", "aa~4~~aa"),
        ("x~4~", "x~~4~~"),
        ("é" * 4, "~4~é"),
        ("🙂" * 5, "~5~🙂"),
        ("é~", "é~~"),
    ],
)
def test_encode_examples(plain, expected):
    assert encode(plain) == expected


@pytest.mark.parametrize(
    "encoded, expected",
    [
        ("", ""),
        ("abc", "abc"),
        ("aaaa", "aaaa"),
        ("aaa", "aaa"),
        ("~4~a", "aaaa"),
        ("~5~a", "aaaaa"),
        ("~12~a", "a" * 12),
        ("~10~1", "1" * 10),
        ("~4~1", "1111"),
        ("~4~a1", "aaaa1"),
        ("~4~a~4~a", "a" * 8),
        ("~4~a~5~a", "a" * 9),
        ("~~", "~"),
        ("a~~b", "a~b"),
        ("~4~~", "~~~~"),
        ("~4~~~~", "~" * 5),
        ("~4~~~~~~", "~" * 6),
        ("~5~~", "~~~~~"),
        ("x~~4~~", "x~4~"),
        ("~4~é", "é" * 4),
        ("~5~🙂", "🙂" * 5),
        ("~4~a~4~b", "aaaabbbb"),
    ],
)
def test_decode_examples(encoded, expected):
    assert decode(encoded) == expected


@pytest.mark.parametrize(
    "encoded",
    [
        "~",            # tilde at end of text
        "a~",           # tilde at end after text
        "~x",           # tilde followed by a letter
        "~ ",           # tilde followed by a space
        "~-1~a",        # tilde followed by a sign
        "~a",
        "~1~a",         # count below 4
        "~3~a",         # count below 4
        "~0~a",         # leading zero (zero count)
        "~00~a",        # leading zero
        "~04~a",        # leading zero
        "~05~a",        # leading zero
        "~4a",          # count not followed by tilde
        "~12",          # count not followed by tilde, at end
        "~4",           # count at end of text
        "~10a~",        # count followed by a non-tilde character
        "~4~",          # missing run character
        "~12~",         # missing run character
    ],
)
def test_decode_rejects_malformed(encoded):
    with pytest.raises(ValueError):
        decode(encoded)


def test_decode_accepts_adjacent_runs_of_same_character():
    assert decode("~4~a~4~a") == "a" * 8


def test_decode_accepts_plain_run_not_produced_by_encode():
    assert decode("aaaa") == "aaaa"


def test_encode_is_maximal_for_long_runs():
    assert encode("a" * 13) == "~13~a"
    assert encode("a" * 4 + "b" * 4) == "~4~a~4~b"


def test_encode_empty_and_single_characters():
    assert encode("") == ""
    assert decode("") == ""
    assert encode("~") == "~~"
    assert decode("~~") == "~"


def test_round_trip_examples():
    samples = [
        "",
        "~",
        "~~~~",
        "~~~~~~~~~~~~",
        "aaaa~~~~bbbb",
        "12345",
        "1111111111111",
        "a~4~b",
        "é🙂🙂🙂🙂x",
    ]
    for s in samples:
        assert decode(encode(s)) == s


@pytest.mark.parametrize("seed", range(200))
def test_round_trip_random(seed):
    rng = random.Random(seed)
    alphabet = "ab~0123456789é🙂 "
    length = rng.randint(0, 60)
    s = "".join(rng.choice(alphabet) for _ in range(length))
    # Make some runs long enough to trigger the encoded form.
    if rng.random() < 0.5 and s:
        ch = rng.choice(alphabet)
        s += ch * rng.randint(0, 20)
    assert decode(encode(s)) == s


@pytest.mark.parametrize("seed", range(50))
def test_encode_output_is_accepted_and_inverts(seed):
    rng = random.Random(1000 + seed)
    s = "".join(rng.choice("~a1") for _ in range(rng.randint(0, 80)))
    encoded = encode(s)
    assert decode(encoded) == s
    assert encode(decode(encoded)) == encoded
