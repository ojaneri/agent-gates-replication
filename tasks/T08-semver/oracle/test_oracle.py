import pytest

from solution import compare_versions as cmp


@pytest.mark.parametrize("a,b,r", [
    ("1.0.0", "1.0.0", 0), ("1.0.0", "2.0.0", -1), ("2.0.0", "1.9.9", 1),
    ("1.10.0", "1.9.0", 1), ("1.0.10", "1.0.9", 1), ("0.0.1", "0.0.0", 1),
])
def test_core_numeric(a, b, r):
    assert cmp(a, b) == r


def test_prerelease_lower_than_release():
    assert cmp("1.0.0-alpha", "1.0.0") == -1
    assert cmp("1.0.0", "1.0.0-alpha") == 1


def test_prerelease_ordering_chain():
    chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2",
             "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"]
    for lo, hi in zip(chain, chain[1:]):
        assert cmp(lo, hi) == -1, (lo, hi)
        assert cmp(hi, lo) == 1, (hi, lo)


def test_numeric_identifiers_compare_numerically():
    assert cmp("1.0.0-2", "1.0.0-10") == -1


def test_numeric_lower_than_alphanumeric():
    assert cmp("1.0.0-999", "1.0.0-a") == -1
    assert cmp("1.0.0-a", "1.0.0-999") == 1


def test_alphanumeric_ascii_order():
    assert cmp("1.0.0-Beta", "1.0.0-alpha") == -1     # 'B' < 'a' in ASCII
    assert cmp("1.0.0-a-b", "1.0.0-a-c") == -1


def test_identifier_with_hyphen_and_digits_is_not_numeric():
    assert cmp("1.0.0-1a", "1.0.0-2") == 1


def test_fewer_identifiers_lower():
    assert cmp("1.0.0-a.b", "1.0.0-a.b.c") == -1
    assert cmp("1.0.0-a.b.c", "1.0.0-a.b") == 1


def test_equal_prereleases():
    assert cmp("1.0.0-rc.1", "1.0.0-rc.1") == 0


def test_build_ignored():
    assert cmp("1.0.0+a", "1.0.0+b") == 0
    assert cmp("1.0.0-rc.1+build.5", "1.0.0-rc.1") == 0
    assert cmp("1.0.0+001", "1.0.0") == 0


def test_prerelease_beats_core_only_when_core_equal():
    assert cmp("1.0.1-alpha", "1.0.0") == 1


@pytest.mark.parametrize("v", ["1.0", "1.0.0.0", "01.0.0", "1.01.0", "1.0.01", "1.0.0-", "1.0.0-a..b",
                               "1.0.0-07", "1.0.0+", "1.0.0+a..b", " 1.0.0", "1.0.0 ", "v1.0.0",
                               "1.0.0-a_b", "-1.0.0", "1.0.0+a+b", ""])
def test_invalid(v):
    with pytest.raises(ValueError):
        cmp(v, "1.0.0")
    with pytest.raises(ValueError):
        cmp("1.0.0", v)


def test_zero_identifier_allowed():
    assert cmp("1.0.0-0", "1.0.0-1") == -1
    assert cmp("0.0.0", "0.0.0") == 0


@pytest.mark.parametrize("v", ["1.0.0\n", "1.0.0-alpha\n", "1.0.0+b\n"])
def test_trailing_newline_is_invalid(v):
    # added after the extension run (deviations.md, fifth correction): "$" matched before a final newline
    with pytest.raises(ValueError):
        cmp(v, "1.0.0")
