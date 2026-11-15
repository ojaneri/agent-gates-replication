import random

import pytest

from solution import decode, encode


@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("a", "a"),
        ("aa", "aa"),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("~", "~~"),
        ("~~", "~~~~"),
        ("~~~", "~~~~~~"),
        ("~~~~", "~4~~"),
        ("~~~~~", "~5~~"),
        ("a~b", "a~~b"),
        ("abc", "abc"),
        ("aaabbbb", "aaa~4~b"),
        ("xxxxyyyyzzz", "~4~x~4~yzzz"),
        ("é" * 5, "~5~é"),
        ("\U0001F389" * 4, "~4~\U0001F389"),
        ("aaaa~~~~", "~4~a~4~~"),
        ("aaaabaaaa", "~4~ab~4~a"),
        ("a" * 1000, "~1000~a"),
    ],
)
def test_encode_examples(plain, encoded):
    assert encode(plain) == encoded


@pytest.mark.parametrize(
    "encoded, plain",
    [
        ("", ""),
        ("aaa", "aaa"),
        ("aaaa", "aaaa"),
        ("~4~a", "aaaa"),
        ("~5~a", "aaaaa"),
        ("~12~a", "a" * 12),
        ("~10~b", "b" * 10),
        ("~1000~a", "a" * 1000),
        ("~~", "~"),
        ("~~~~", "~~"),
        ("a~~b", "a~b"),
        ("~4~~", "~~~~"),
        ("~5~~", "~~~~~"),
        ("~4~a~4~a", "a" * 8),
        ("~4~a~4~b", "a" * 4 + "b" * 4),
        ("~4~ab", "aaaab"),
        ("~4~a~4~~", "aaaa~~~~"),
    ],
)
def test_decode_examples(encoded, plain):
    assert decode(encoded) == plain


@pytest.mark.parametrize(
    "bad",
    [
        "~",            # tilde at end
        "a~",           # tilde at end after text
        "~a",           # tilde followed by a letter
        "~ ~a",         # tilde followed by a space
        "~-4~a",        # sign is not a digit
        "~٤~a",    # non-ASCII digit
        "~0~a",         # zero count
        "~04~a",        # leading zero
        "~00~a",        # leading zeros
        "~3~a",         # count below 4
        "~1~a",         # count of one
        "~4a",          # count not followed by tilde
        "~4",           # count at end, no tilde
        "~4~",          # missing character after tilde
        "~12",          # count at end
        "~9x",          # count followed by a non-tilde
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


def test_decode_accepts_adjacent_runs_of_same_char():
    assert decode("~4~a~5~a") == "a" * 9


def test_decode_is_left_to_right_with_plain_text_between_runs():
    assert decode("x~4~yz~~w") == "x" + "y" * 4 + "z~w"


def test_round_trip_random_strings():
    rng = random.Random(12345)
    alphabet = "ab~é\U0001F389"
    for _ in range(500):
        length = rng.randint(0, 60)
        s = "".join(rng.choice(alphabet) for _ in range(length))
        assert decode(encode(s)) == s


def test_round_trip_long_runs_of_each_character():
    for c in "~aé\U0001F389":
        for n in range(0, 12):
            s = "x" + c * n + "y"
            assert decode(encode(s)) == s


def test_encode_threshold_three_and_four():
    assert encode("aaa") == "aaa"
    assert encode("aaaa") == "~4~a"
    assert encode("~~~") == "~~~~~~"
    assert encode("~~~~") == "~4~~"


def test_encode_output_uses_maximal_runs():
    assert encode("aaaaaaaa") == "~8~a"
    assert "~" not in encode("abc")
