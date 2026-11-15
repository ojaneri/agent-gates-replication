import random

import pytest

from solution import decode, encode


# --- encode: examples from the spec -----------------------------------------

@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("aaaaa", "~5~a"),
        ("~" * 5, "~5~~"),
        ("aaa", "aaa"),
        ("a~b", "a~~b"),
        ("a" * 12, "~12~a"),
        ("aaaa", "~4~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("abc", "abc"),
        ("~", "~~"),
        ("~~~", "~~~~~~"),
        ("~1111", "~~~4~1"),
        ("~5", "~~5"),
        ("aaaab", "~4~ab"),
        ("abbbbc", "a~4~bc"),
        ("aaaa~~~~", "~4~a~4~~"),
    ],
)
def test_encode_examples(plain, encoded):
    assert encode(plain) == encoded


def test_encode_runs_are_maximal_across_long_run():
    # A run of 12 must be one token, never split into shorter runs.
    assert encode("a" * 12) == "~12~a"
    assert "~4~a~8~a" not in encode("a" * 12)


def test_encode_unicode():
    assert encode("éééé") == "~4~é"
    assert encode("😀😀😀😀😀") == "~5~😀"
    assert encode("日本語") == "日本語"


# --- decode: examples and well-formed input the encoder would not produce ---

@pytest.mark.parametrize(
    "encoded, plain",
    [
        ("", ""),
        ("~5~a", "aaaaa"),
        ("~5~~", "~~~~~"),
        ("aaa", "aaa"),
        ("a~~b", "a~b"),
        ("~12~a", "a" * 12),
        ("aaaa", "aaaa"),          # plain run of 4, not produced by encode
        ("~4~a~4~a", "a" * 8),     # two runs of the same character in a row
        ("~4~~~4~~", "~" * 8),
        ("~~", "~"),
        ("~~5", "~5"),
        ("~4~1", "1111"),
        ("~4~a~~", "aaaa~"),
        ("~4~é", "éééé"),
    ],
)
def test_decode_examples(encoded, plain):
    assert decode(encoded) == plain


# --- decode: malformed input raises ValueError -------------------------------

@pytest.mark.parametrize(
    "bad",
    [
        "~",            # ~ at end of text
        "abc~",         # ~ at end of text after plain chars
        "~a",           # ~ followed by neither ~ nor digit
        "~x~a",         # ~ followed by a letter
        "~ ",           # ~ followed by a space
        "~04~a",        # leading zero
        "~00~a",        # leading zero
        "~0~a",         # count zero (also leading zero)
        "~3~a",         # count below 4
        "~1~a",         # count below 4
        "~5a",          # count not followed by ~
        "~5",           # count at end, no ~
        "~5~",          # missing character after second ~
        "~12",          # count not followed by ~
        "~4~a~",        # trailing ~ after a valid run
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


# --- round trip ---------------------------------------------------------------

@pytest.mark.parametrize(
    "s",
    [
        "",
        "a",
        "~",
        "~~",
        "~~~~",
        "~5",
        "~1111",
        "aaaa",
        "aaaaa",
        "a~b",
        "~" * 100,
        "a" * 1000,
        "ab" * 50,
        "aaaa~~~~bbbb",
        "1234567890" * 3,
        "é" * 7 + "x",
        "😀😀😀😀~~",
        "\n\n\n\n\t",
    ],
)
def test_round_trip_fixed(s):
    assert decode(encode(s)) == s


def test_round_trip_random():
    rng = random.Random(12345)
    alphabet = "ab~0123456789é😀 "
    for _ in range(2000):
        length = rng.randint(0, 60)
        s = "".join(rng.choice(alphabet) for _ in range(length))
        assert decode(encode(s)) == s, s


def test_round_trip_random_runs():
    rng = random.Random(54321)
    for _ in range(500):
        pieces = []
        for _ in range(rng.randint(0, 10)):
            c = rng.choice("ab~5é")
            pieces.append(c * rng.randint(1, 15))
        s = "".join(pieces)
        assert decode(encode(s)) == s, s


def test_encode_output_decodes_without_error_for_all_short_strings():
    alphabet = "a~1"
    for length in range(0, 7):
        def gen(prefix, remaining):
            if remaining == 0:
                yield prefix
                return
            for ch in alphabet:
                yield from gen(prefix + ch, remaining - 1)

        for s in gen("", length):
            assert decode(encode(s)) == s
