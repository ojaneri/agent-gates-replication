import pytest

from solution import compare_versions


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.0.0", 1),
        ("1.2.0", "1.10.0", -1),
        ("1.0.9", "1.0.10", -1),
        ("0.0.0", "0.0.1", -1),
        ("10.0.0", "9.99.99", 1),
    ],
)
def test_core_comparison(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0-alpha", 0),
        ("2.0.0-alpha", "1.9.9", 1),
        ("1.0.0-alpha", "1.0.1-alpha", -1),
    ],
)
def test_prerelease_vs_release(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        # spec examples ordering: 1.0.0-alpha < alpha.1 < alpha.beta < beta < beta.2 < beta.11 < rc.1 < 1.0.0
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
    ],
)
def test_prerelease_ordering_chain(a, b, expected):
    assert compare_versions(a, b) == expected
    assert compare_versions(b, a) == -expected


def test_numeric_identifiers_compare_numerically():
    assert compare_versions("1.0.0-2", "1.0.0-10") == -1
    assert compare_versions("1.0.0-10", "1.0.0-2") == 1


def test_numeric_lower_than_alphanumeric():
    assert compare_versions("1.0.0-1", "1.0.0-a") == -1
    assert compare_versions("1.0.0-a", "1.0.0-1") == 1


def test_ascii_string_comparison_is_case_sensitive():
    # 'Z' (0x5A) < 'a' (0x61) in ASCII
    assert compare_versions("1.0.0-Z", "1.0.0-a") == -1
    assert compare_versions("1.0.0-alpha", "1.0.0-Alpha") == 1


def test_hyphen_inside_identifier_is_non_numeric():
    assert compare_versions("1.0.0-a-b", "1.0.0-a") == 1
    assert compare_versions("1.0.0-x-1", "1.0.0-x-2") == -1


def test_zero_prerelease_identifier_is_numeric():
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1


def test_build_metadata_ignored():
    assert compare_versions("1.0.0+a", "1.0.0+b") == 0
    assert compare_versions("1.0.0+001", "1.0.0") == 0
    assert compare_versions("1.0.0-alpha+build.1", "1.0.0-alpha") == 0
    assert compare_versions("1.0.0+20130313144700", "1.0.0-rc.1") == 1


def test_build_identifiers_allow_leading_zeros():
    assert compare_versions("1.0.0+007", "1.0.0+7") == 0
    assert compare_versions("1.0.0+exp.sha.5114f85", "1.0.0") == 0


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "01.0.0",
        "1.00.0",
        "1.0.01",
        "1.0.0-",
        "1.0.0-alpha..1",
        "1.0.0-.alpha",
        "1.0.0-alpha.",
        "1.0.0-07",
        "1.0.0-01",
        "1.0.0+",
        "1.0.0+a..b",
        "1.0.0+a.",
        "1.0.0 ",
        " 1.0.0",
        "1.0.0-al pha",
        "1.0.0-alpha_1",
        "1.0.0+a b",
        "a.b.c",
        "-1.0.0",
        "1.-0.0",
        "1.0.0\n",
        "1.0.0-é",
        "1.0.0+١",
        "1.0.0-١",
        "1.0.0+a.+b",
        "1.0.0-alpha+",
    ],
)
def test_invalid_versions_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_invalid_non_string_raises():
    with pytest.raises(ValueError):
        compare_versions(None, "1.0.0")  # type: ignore[arg-type]


def test_large_numbers():
    assert compare_versions("123456789012345678901234567890.0.0", "99.0.0") == 1
