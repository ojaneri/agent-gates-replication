import pytest

from solution import decode, encode


@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("abc", "abc"),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("a~b", "a~~b"),
        ("~", "~~"),
        ("~~~", "~~~~~~"),
        ("~~~~", "~4~~"),
        ("~~~~~", "~5~~"),
        ("aaa~~~~bb", "aaa~4~~bb"),
        ("éééé", "~4~é"),
        ("\U0001F600" * 5, "~5~\U0001F600"),
        ("ab1234", "ab1234"),
        ("aaaa5", "~4~a5"),
        ("aaaabbbb", "~4~a~4~b"),
    ],
)
def test_encode_and_decode_examples(plain, encoded):
    assert encode(plain) == encoded
    assert decode(encoded) == plain


@pytest.mark.parametrize(
    "encoded, plain",
    [
        ("aaaa", "aaaa"),
        ("~4~a~4~a", "aaaaaaaa"),
        ("~4~a~4~a", "aaaaaaaa"),
        ("~~", "~"),
        ("~4~~", "~~~~"),
        ("~10~x", "x" * 10),
        ("~1000~z", "z" * 1000),
        ("~4~a5", "aaaa5"),
    ],
)
def test_decode_accepts_non_canonical_text(encoded, plain):
    assert decode(encoded) == plain


@pytest.mark.parametrize(
    "bad",
    [
        "~",            # dangling escape
        "abc~",         # dangling escape at end
        "~x",           # neither '~' nor digit
        "~ ",           # space after escape
        "~0~a",         # leading zero
        "~05~a",        # leading zero
        "~00~a",        # leading zero
        "~3~a",         # count below 4
        "~1~a",         # count below 4
        "~4a",          # count not followed by '~'
        "~45",          # count not followed by '~' at end
        "~4~",          # missing character after second '~'
        "~12",          # digits then end of text
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


def test_decode_rejects_non_ascii_digit_as_count():
    with pytest.raises(ValueError):
        decode("~٤~a")


@pytest.mark.parametrize(
    "s",
    [
        "",
        "x",
        "~",
        "~~",
        "~~~~",
        "~~~~~~~~~~~~~~~",
        "a~~~~b~c~~d",
        "12345678901234567890",
        "\U0001F600\U0001F600\U0001F600\U0001F600",
        "aaaa~~~~" * 3,
    ],
)
def test_round_trip(s):
    assert decode(encode(s)) == s


def test_encode_produces_maximal_runs():
    assert encode("aaaaaaaa") == "~8~a"
    assert encode("aaaaaaaab") == "~8~ab"
