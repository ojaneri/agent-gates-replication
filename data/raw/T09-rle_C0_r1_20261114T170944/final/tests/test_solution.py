import pytest

from solution import decode, encode


@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("a~b", "a~~b"),
        ("~", "~~"),
        ("~~~", "~~~~~~"),
        ("~~~~~", "~5~~"),
        ("abc", "abc"),
        ("aaaabbbbcc", "~4~a~4~bcc"),
        ("héllo", "héllo"),
        ("😀😀😀😀", "~4~😀"),
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
        ("~5~a", "aaaaa"),
        ("~12~a", "a" * 12),
        ("a~~b", "a~b"),
        ("~~", "~"),
        ("~5~~", "~" * 5),
        ("~4~a~4~a", "a" * 8),
        ("~4~a~4~bcc", "aaaabbbbcc"),
    ],
)
def test_decode_examples(encoded, plain):
    assert decode(encoded) == plain


@pytest.mark.parametrize(
    "s",
    [
        "",
        "a",
        "~",
        "~~",
        "~~~~",
        "a~b~~c~~~d",
        "aaaa~~~~bbbbb",
        "~4~a",
        "x" * 100 + "~" * 7 + "y",
        "é😀😀😀😀~",
        "1234567890",
        "~9~",
    ],
)
def test_round_trip(s):
    assert decode(encode(s)) == s


def test_encode_runs_are_maximal():
    assert encode("a" * 4 + "a" * 4) == "~8~a"


@pytest.mark.parametrize(
    "bad",
    [
        "~",            # dangling ~
        "abc~",         # dangling ~ at end
        "~x",           # ~ followed by a non-digit, non-~
        "~ a",          # space after ~
        "~05~a",        # leading zero
        "~00~a",        # leading zero
        "~3~a",         # count below 4
        "~0~a",         # count below 4 (zero)
        "~5a",          # count not followed by ~
        "~5",           # count not followed by ~ (end of text)
        "~5~",          # missing character after second ~
        "~12",          # count not followed by ~
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)
