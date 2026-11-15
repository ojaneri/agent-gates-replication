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
        ("1.0.0", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0", -1),
        ("2.0.0-alpha", "1.9.9", 1),
    ],
)
def test_core_and_release_precedence(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0-alpha", 0),
        ("1.0.0-alpha", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-1", "1.0.0-alpha", -1),
        ("1.0.0-alpha", "1.0.0-1", 1),
        ("1.0.0-2", "1.0.0-10", -1),
        ("1.0.0-0", "1.0.0-0.0", -1),
        ("1.0.0-x-y", "1.0.0-x-z", -1),
        ("1.0.0-A", "1.0.0-a", -1),
        ("1.0.0-a1", "1.0.0-a10", -1),
        ("1.0.0-1a", "1.0.0-1", 1),
    ],
)
def test_prerelease_precedence(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b",
    [
        ("1.0.0+a", "1.0.0+b"),
        ("1.0.0+20130313144700", "1.0.0"),
        ("1.0.0-alpha+001", "1.0.0-alpha"),
        ("1.0.0-alpha+a.b", "1.0.0-alpha+c"),
        ("1.0.0+build-1.007", "1.0.0+x"),
    ],
)
def test_build_metadata_is_ignored(a, b):
    assert compare_versions(a, b) == 0
    assert compare_versions(b, a) == 0


def test_result_is_antisymmetric():
    pairs = [("1.0.0-alpha", "1.0.0"), ("1.2.3", "1.2.4"), ("2.0.0-1", "2.0.0-a")]
    for a, b in pairs:
        assert compare_versions(a, b) == -compare_versions(b, a)


@pytest.mark.parametrize("valid", ["0.0.0", "10.20.30", "1.0.0-0", "1.0.0+01"])
def test_valid_versions_are_accepted(valid):
    assert compare_versions(valid, valid) == 0


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.2",
        "1.2.3.4",
        "1..3",
        "1.2.",
        ".1.2",
        "01.2.3",
        "1.02.3",
        "1.2.03",
        "1.2.-3",
        "1.2.3 ",
        " 1.2.3",
        "1.2.3-",
        "1.2.3-alpha.",
        "1.2.3-alpha..1",
        "1.2.3-01",
        "1.2.3-alpha.01",
        "1.2.3-a_b",
        "1.2.3-é",
        "1.2.3+",
        "1.2.3+a..b",
        "1.2.3+a+b",
        "1.2.3+a_b",
        "1.2.3-a+",
        "v1.2.3",
        "1.2.a",
        "+1.2.3",
    ],
)
def test_invalid_versions_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_leading_zero_build_identifier_is_valid():
    assert compare_versions("1.0.0+001.02", "1.0.0") == 0


def test_numeric_prerelease_identifier_zero_is_valid():
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1


def test_prerelease_with_hyphens_is_valid():
    assert compare_versions("1.0.0-a-b-c", "1.0.0-a-b-c") == 0
