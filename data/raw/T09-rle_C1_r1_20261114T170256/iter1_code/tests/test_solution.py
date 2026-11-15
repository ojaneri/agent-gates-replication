import pytest

from solution import decode, encode


# ---------- encode ----------

@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("a", "a"),
        ("aaa", "aaa"),
        ("aaaa", "~4~a"),
        ("aaaaa", "~5~a"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("a~b", "a~~b"),
        ("~", "~~"),
        ("~~", "~~~~"),
        ("~~~", "~~~~~~"),
        ("~~~~~", "~5~~"),
        ("abc", "abc"),
        ("aaaabbbcc", "~4~abbbcc"),
        ("ééééé", "~5~é"),
        ("日日日日", "~4~日"),
        ("a\nb", "a\nb"),
    ],
)
def test_encode_examples(plain, encoded):
    assert encode(plain) == encoded


def test_encode_run_split_by_other_chars_is_maximal():
    assert encode("aaaaxaaaa") == "~4~ax~4~a"


def test_encode_runs_of_exactly_three_are_not_compressed():
    assert encode("aaabbbccc") == "aaabbbccc"


def test_encode_tilde_run_of_four_is_compressed():
    assert encode("~~~~") == "~4~~"


# ---------- decode ----------

@pytest.mark.parametrize(
    "encoded, plain",
    [
        ("", ""),
        ("a", "a"),
        ("aaa", "aaa"),
        ("aaaa", "aaaa"),
        ("~4~a", "aaaa"),
        ("~5~a", "aaaaa"),
        ("~12~a", "a" * 12),
        ("a~~b", "a~b"),
        ("~~", "~"),
        ("~~~~", "~~"),
        ("~5~~", "~~~~~"),
        ("~4~abbbcc", "aaaabbbcc"),
        ("~4~a~4~a", "aaaaaaaa"),
        ("~4~a~~", "aaaa~"),
        ("~10~x", "x" * 10),
        ("~1000~z", "z" * 1000),
        ("~4~é", "éééé"),
        ("~4~日", "日日日日"),
        ("~4~ ", "    "),
    ],
)
def test_decode_examples(encoded, plain):
    assert decode(encoded) == plain


@pytest.mark.parametrize(
    "bad",
    [
        "~",            # dangling tilde at end
        "a~",           # dangling tilde after text
        "~x",           # tilde followed by a non-digit, non-tilde
        "~ ",           # tilde followed by space
        "~04~a",        # leading zero
        "~00~a",        # leading zero
        "~0~a",         # zero (leading zero and below minimum)
        "~3~a",         # count below 4
        "~1~a",         # count below 4
        "~4a",          # count not followed by tilde
        "~4",           # count at end, no tilde
        "~45",          # count not followed by tilde
        "~4~",          # missing character after marker
        "~12",          # count not followed by tilde
        "~12~",         # missing character after marker
    ],
)
def test_decode_rejects_malformed(bad):
    with pytest.raises(ValueError):
        decode(bad)


def test_decode_rejects_non_ascii_digit_count():
    # Only ASCII 0-9 are counts; the Arabic-Indic digit is not.
    with pytest.raises(ValueError):
        decode("~٤~a")


# ---------- round trip ----------

@pytest.mark.parametrize(
    "s",
    [
        "",
        "a",
        "aaaa",
        "aaaaaaaaaaaa",
        "~",
        "~~~~~",
        "a~b~~c~~~d",
        "xx~~~~yyyy~zzzzz",
        "mixed  \t\n  spaces",
        "日本語日本語日本語日本語",
        "é" * 7 + "e" * 3,
        "\U0001F600" * 6,
        "~5~a",
        "~~a~~",
    ],
)
def test_round_trip(s):
    assert decode(encode(s)) == s


def test_round_trip_all_small_strings():
    import itertools

    alphabet = "a~1"
    for length in range(0, 7):
        for tup in itertools.product(alphabet, repeat=length):
            s = "".join(tup)
            assert decode(encode(s)) == s


def test_round_trip_long_runs():
    for n in range(1, 60):
        for c in ("a", "~", "9"):
            s = c * n
            assert decode(encode(s)) == s
