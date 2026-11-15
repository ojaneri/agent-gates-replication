import random
import string

import pytest

from solution import decode, encode


# ---------- encode: examples from the spec ----------

@pytest.mark.parametrize(
    "plain, encoded",
    [
        ("", ""),
        ("aaaaa", "~5~a"),
        ("~~~~~", "~5~~"),
        ("aaa", "aaa"),
        ("a~b", "a~~b"),
        ("aaaaaaaaaaaa", "~12~a"),
        ("aaaa", "~4~a"),
        ("a", "a"),
        ("ab", "ab"),
        ("~", "~~"),
        ("~~", "~~~~"),
        ("~~~", "~~~~~~"),
    ],
)
def test_encode_examples(plain, encoded):
    assert encode(plain) == encoded


def test_encode_run_of_exactly_three_is_literal():
    assert encode("bbb") == "bbb"


def test_encode_run_of_exactly_four_is_compressed():
    assert encode("cccc") == "~4~c"


def test_encode_short_tilde_run_is_escaped_each():
    assert encode("~~~") == "~~~~~~"


def test_encode_long_tilde_run_is_compressed():
    assert encode("~~~~") == "~4~~"


def test_encode_mixed_runs_are_maximal_and_split_correctly():
    assert encode("aaaabbbcccccd") == "~4~abbb~5~cd"


def test_encode_digits_and_letters_are_literal():
    assert encode("12345") == "12345"


def test_encode_unicode_run():
    assert encode("éééééé") == "~6~é"


def test_encode_unicode_mixed():
    assert encode("ñ日日日日") == "ñ~4~日"


def test_encode_run_of_length_ten_has_two_digits():
    assert encode("x" * 10) == "~10~x"


def test_encode_run_of_length_hundred():
    assert encode("z" * 100) == "~100~z"


def test_encode_whitespace_and_newlines_are_literal_short_runs():
    assert encode(" \n\t") == " \n\t"


def test_encode_whitespace_run_compressed():
    assert encode("    ") == "~4~ "


# ---------- decode: examples and valid forms ----------

@pytest.mark.parametrize(
    "encoded, plain",
    [
        ("", ""),
        ("~5~a", "aaaaa"),
        ("~5~~", "~~~~~"),
        ("aaa", "aaa"),
        ("a~~b", "a~b"),
        ("~12~a", "a" * 12),
        ("~4~a", "aaaa"),
        ("aaaa", "aaaa"),
        ("~4~a~4~a", "aaaaaaaa"),
        ("~~", "~"),
        ("~~~~", "~~"),
        ("~~~~~~", "~~~"),
        ("~4~~", "~~~~"),
    ],
)
def test_decode_examples(encoded, plain):
    assert decode(encoded) == plain


def test_decode_plain_text_passes_through():
    assert decode("hello world") == "hello world"


def test_decode_escape_at_start_and_end_of_escaped_pairs():
    assert decode("~~a~~") == "~a~"


def test_decode_every_digit_as_count():
    for d in range(4, 10):
        assert decode(f"~{d}~q") == "q" * d


def test_decode_two_digit_count_zero_tail():
    assert decode("~20~z") == "z" * 20


def test_decode_count_nine_boundary():
    assert decode("~9~a") == "aaaaaaaaa"


def test_decode_count_four_boundary():
    assert decode("~4~a") == "aaaa"


def test_decode_count_three_is_rejected():
    with pytest.raises(ValueError, match="below 4"):
        decode("~3~a")


def test_decode_count_one_is_rejected():
    with pytest.raises(ValueError, match="below 4"):
        decode("~1~a")


def test_decode_count_zero_is_rejected_as_leading_zero():
    with pytest.raises(ValueError, match="leading zero"):
        decode("~0~a")


def test_decode_count_with_leading_zero_is_rejected():
    with pytest.raises(ValueError, match="leading zero"):
        decode("~05~a")


def test_decode_count_with_double_leading_zero_is_rejected():
    with pytest.raises(ValueError, match="leading zero"):
        decode("~004~a")


def test_decode_run_of_tildes_with_escape_character_inside_count_position():
    assert decode("~4~~") == "~~~~"


def test_decode_run_of_tilde_followed_by_text():
    assert decode("~4~~xy") == "~~~~xy"


def test_decode_two_runs_same_character_in_a_row():
    assert decode("~4~a~5~a") == "a" * 9


def test_decode_run_then_plain_chars():
    assert decode("~5~ab") == "aaaaab"


def test_decode_unicode_run():
    assert decode("~6~é") == "é" * 6


def test_decode_unicode_plain():
    assert decode("日本語") == "日本語"


# ---------- decode: error cases ----------

def test_decode_trailing_tilde_raises():
    with pytest.raises(ValueError, match="ends with"):
        decode("abc~")


def test_decode_lone_tilde_raises():
    with pytest.raises(ValueError, match="ends with"):
        decode("~")


def test_decode_tilde_followed_by_letter_raises():
    with pytest.raises(ValueError, match="expected a count"):
        decode("~a")


def test_decode_tilde_followed_by_symbol_raises():
    with pytest.raises(ValueError, match="expected a count"):
        decode("~!4~a")


def test_decode_tilde_followed_by_space_raises():
    with pytest.raises(ValueError, match="expected a count"):
        decode("~ 4~a")


def test_decode_count_without_following_tilde_at_end_raises():
    with pytest.raises(ValueError, match="not followed by"):
        decode("~5")


def test_decode_count_followed_by_other_char_raises():
    with pytest.raises(ValueError, match="not followed by"):
        decode("~5x")


def test_decode_count_followed_by_letter_then_tilde_raises():
    with pytest.raises(ValueError, match="not followed by"):
        decode("~5x~a")


def test_decode_missing_character_after_run_marker_raises():
    with pytest.raises(ValueError, match="missing character"):
        decode("~5~")


def test_decode_missing_character_after_multi_digit_count_raises():
    with pytest.raises(ValueError, match="missing character"):
        decode("~12~")


def test_decode_run_error_after_valid_prefix_raises():
    with pytest.raises(ValueError):
        decode("abc~2~x")


def test_decode_error_inside_longer_text_raises():
    with pytest.raises(ValueError):
        decode("aaaa~5x")


# ---------- round trip ----------

@pytest.mark.parametrize(
    "s",
    [
        "",
        "a",
        "aaa",
        "aaaa",
        "aaaaa",
        "~",
        "~~",
        "~~~",
        "~~~~",
        "~~~~~",
        "a~b~~c~~~d",
        "~4~a",
        "~4~~4~a",
        "0123456789",
        "aaaaaaaaaaaa",
        "é" * 5 + "ü",
        "日日日日日日",
        "\n\n\n\n",
        "a" * 1000 + "~" * 999 + "b",
    ],
)
def test_round_trip_examples(s):
    assert decode(encode(s)) == s


def test_round_trip_all_lengths_of_runs_for_each_char():
    for ch in ["a", "~", "9", "é"]:
        for n in range(0, 30):
            s = "b" + ch * n + "c"
            assert decode(encode(s)) == s


def test_round_trip_random_strings_seeded():
    rng = random.Random(12345)
    alphabet = string.ascii_letters + string.digits + "~~~~ é日\n"
    for _ in range(500):
        length = rng.randint(0, 60)
        s = "".join(rng.choice(alphabet) for _ in range(length))
        assert decode(encode(s)) == s


def test_round_trip_random_runs_seeded():
    rng = random.Random(777)
    for _ in range(300):
        parts = []
        for _ in range(rng.randint(0, 8)):
            ch = rng.choice("ab~z9")
            parts.append(ch * rng.randint(1, 15))
        s = "".join(parts)
        assert decode(encode(s)) == s


def test_encoded_output_never_contains_invalid_structure_for_round_trip():
    s = "~~~~~~~~~~~~~~~~~~~~"
    encoded = encode(s)
    assert encoded == "~20~~"
    assert decode(encoded) == s
