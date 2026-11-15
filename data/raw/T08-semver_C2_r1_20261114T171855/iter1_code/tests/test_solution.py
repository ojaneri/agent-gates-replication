import pytest

from solution import compare_versions


# --- core numeric comparison -------------------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("0.0.0", "0.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.0.0", 1),
        ("1.2.0", "1.10.0", -1),
        ("1.10.0", "1.2.0", 1),
        ("1.0.2", "1.0.10", -1),
        ("1.0.10", "1.0.2", 1),
        ("0.0.1", "0.0.0", 1),
        ("0.1.0", "0.0.9", 1),
        ("10.0.0", "9.99.99", 1),
    ],
)
def test_numeric_core_ordering(a, b, expected):
    assert compare_versions(a, b) == expected


def test_result_is_int_in_range():
    for pair in [("1.0.0", "1.0.0"), ("1.0.0", "2.0.0"), ("2.0.0", "1.0.0")]:
        result = compare_versions(*pair)
        assert type(result) is int
        assert result in (-1, 0, 1)


def test_large_numbers_compare_numerically_not_lexically():
    assert compare_versions("1000000000000.0.0", "999999999999.0.0") == 1
    assert compare_versions("1.0.0", "1.0.1") == -1


def test_zero_is_valid_component():
    assert compare_versions("0.0.0", "0.0.1") == -1
    assert compare_versions("0.1.0", "0.0.0") == 1


def test_major_takes_precedence_over_minor_and_patch():
    assert compare_versions("1.99.99", "2.0.0") == -1


def test_minor_takes_precedence_over_patch():
    assert compare_versions("1.2.99", "1.3.0") == -1


# --- prerelease vs release ---------------------------------------------------

def test_prerelease_is_lower_than_release():
    assert compare_versions("1.0.0-alpha", "1.0.0") == -1
    assert compare_versions("1.0.0", "1.0.0-alpha") == 1


def test_release_with_same_core_is_equal_only_to_itself():
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_prerelease_with_higher_core_beats_lower_release():
    assert compare_versions("1.0.1-alpha", "1.0.0") == 1
    assert compare_versions("1.0.0", "1.0.1-alpha") == -1


def test_prerelease_with_lower_core_loses_to_higher_release():
    assert compare_versions("1.0.0-zzz", "1.0.1") == -1


def test_equal_prereleases_compare_equal():
    assert compare_versions("1.0.0-alpha.1", "1.0.0-alpha.1") == 0


# --- prerelease identifier precedence ---------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        # spec example chain
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        # numeric identifiers compare numerically
        ("1.0.0-2", "1.0.0-10", -1),
        ("1.0.0-10", "1.0.0-2", 1),
        ("1.0.0-9", "1.0.0-10", -1),
        # numeric lower than alphanumeric
        ("1.0.0-1", "1.0.0-alpha", -1),
        ("1.0.0-alpha", "1.0.0-1", 1),
        # alphanumeric compared as ASCII strings
        ("1.0.0-a", "1.0.0-b", -1),
        ("1.0.0-B", "1.0.0-a", -1),  # 'B' (0x42) < 'a' (0x61)
        ("1.0.0-abc", "1.0.0-abd", -1),
        ("1.0.0-ab", "1.0.0-abc", -1),
        ("1.0.0-a-b", "1.0.0-a-c", -1),
        ("1.0.0-x-y", "1.0.0-x-y", 0),
        # fewer identifiers is lower when prefix is equal
        ("1.0.0-alpha", "1.0.0-alpha.0", -1),
        ("1.0.0-alpha.0", "1.0.0-alpha", 1),
        # a numeric identifier with same value compares equal
        ("1.0.0-0", "1.0.0-0", 0),
    ],
)
def test_prerelease_precedence(a, b, expected):
    assert compare_versions(a, b) == expected


def test_numeric_identifier_zero_is_valid_and_lowest_numeric():
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1


def test_first_differing_identifier_decides():
    assert compare_versions("1.0.0-a.9", "1.0.0-b.1") == -1


def test_identifier_with_hyphen_is_non_numeric():
    assert compare_versions("1.0.0-1-2", "1.0.0-1") == 1


def test_hyphen_only_identifier_is_valid():
    assert compare_versions("1.0.0--", "1.0.0-a") == -1


# --- build metadata ----------------------------------------------------------

def test_build_metadata_is_ignored():
    assert compare_versions("1.0.0+a", "1.0.0+b") == 0


def test_build_metadata_ignored_against_no_build():
    assert compare_versions("1.0.0+build.1", "1.0.0") == 0


def test_build_metadata_ignored_in_prerelease_comparison():
    assert compare_versions("1.0.0-alpha+001", "1.0.0-alpha+zzz") == 0
    assert compare_versions("1.0.0-alpha+001", "1.0.0-beta") == -1


def test_build_leading_zeros_are_allowed():
    assert compare_versions("1.0.0+007", "1.0.0") == 0
    assert compare_versions("1.0.0+0.01.00", "1.0.0+1") == 0


def test_build_may_contain_hyphens_and_digits():
    assert compare_versions("1.0.0+exp-sha-5114f85", "1.0.0") == 0


def test_build_does_not_change_core_ordering():
    assert compare_versions("1.0.0+z", "1.0.1+a") == -1


def test_prerelease_with_hyphen_and_build_with_hyphen():
    assert compare_versions("1.0.0-a-b+c-d", "1.0.0-a-b") == 0


# --- invalid input -----------------------------------------------------------

@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "1..0",
        ".1.0",
        "1.0.",
        "1.0.0 ",
        " 1.0.0",
        "1. 0.0",
        "a.b.c",
        "1.0.x",
        "-1.0.0",
        "1.-0.0",
        "+1.0.0",
        "1.0.0+",
        "1.0.0-",
        "1.0.0-+a",
        "1.0.0-a.",
        "1.0.0-.a",
        "1.0.0-a..b",
        "1.0.0+a..b",
        "1.0.0+.a",
        "1.0.0+a.",
        "1.0.0+a b",
        "1.0.0-a b",
        "1.0.0+a+b",
        "1.0.0-a+b+c",
        "1.0.0-a_b",
        "1.0.0-a/b",
        "1.0.0-é",
        "1.0.0-١",
        "1.0.0\n",
        "1.0.0-01",
        "1.0.0-alpha.01",
        "1.0.0-00",
        "1.0.0-1.02",
        "01.0.0",
        "1.01.0",
        "1.0.00",
        "1.2.3.4-rc",
        "v1.0.0",
        "1.0.0-rc.1+",
        "1.0.0 -rc",
    ],
)
def test_invalid_versions_raise_value_error(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")


def test_invalid_second_argument_raises_value_error():
    with pytest.raises(ValueError):
        compare_versions("1.0.0", "1.0")


def test_non_string_raises_value_error():
    with pytest.raises(ValueError):
        compare_versions(1, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", None)


def test_invalid_input_raises_even_when_other_is_equal():
    with pytest.raises(ValueError):
        compare_versions("01.0.0", "01.0.0")


# --- valid edge cases that must NOT raise ------------------------------------

@pytest.mark.parametrize(
    "good",
    [
        "0.0.0",
        "10.20.30",
        "1.0.0-0",
        "1.0.0-0a",
        "1.0.0-a0",
        "1.0.0-0.3.7",
        "1.0.0-x.7.z.92",
        "1.0.0-x-y-z.--",
        "1.0.0+20130313144700",
        "1.0.0-beta+exp.sha.5114f85",
        "1.0.0+21AF26D3----117B344092BD",
        "1.0.0-ABC",
        "1.0.0-abcXYZ123",
    ],
)
def test_valid_versions_do_not_raise(good):
    assert compare_versions(good, good) == 0


# --- semver spec examples ----------------------------------------------------

def test_full_semver_precedence_chain_is_strictly_ascending():
    chain = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    for lower, higher in zip(chain, chain[1:]):
        assert compare_versions(lower, higher) == -1
        assert compare_versions(higher, lower) == 1
        assert compare_versions(lower, lower) == 0


def test_antisymmetry_and_transitivity_samples():
    versions = [
        "0.9.9",
        "1.0.0-0",
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0",
        "1.0.0+x",
        "1.0.1-a",
        "1.0.1",
        "2.0.0-rc.1",
        "2.0.0",
    ]
    for a in versions:
        for b in versions:
            assert compare_versions(a, b) == -compare_versions(b, a)
    for a in versions:
        for b in versions:
            for c in versions:
                if compare_versions(a, b) <= 0 and compare_versions(b, c) <= 0:
                    assert compare_versions(a, c) <= 0
