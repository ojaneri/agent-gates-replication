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
        ("10.0.0", "9.9.9", 1),
    ],
)
def test_core_ordering(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0", "1.0.0-alpha", 1),
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
        ("1.0.0-1", "1.0.0-a", -1),
        ("1.0.0-a", "1.0.0-1", 1),
        ("1.0.0-2", "1.0.0-10", -1),
        ("1.0.0-0", "1.0.0-0.0", -1),
        ("1.0.0-a-b", "1.0.0-a-c", -1),
        ("2.0.0-0", "1.9.9", 1),
    ],
)
def test_prerelease_precedence(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b",
    [
        ("1.0.0+a", "1.0.0+b"),
        ("1.0.0+001", "1.0.0+20130313144700"),
        ("1.0.0-alpha+a", "1.0.0-alpha+b"),
        ("1.0.0+a", "1.0.0"),
    ],
)
def test_build_metadata_ignored(a, b):
    assert compare_versions(a, b) == 0


def test_build_metadata_ignored_with_prerelease_difference():
    assert compare_versions("1.0.0-alpha+zzz", "1.0.0-beta+aaa") == -1


def test_antisymmetry():
    pairs = [
        ("1.0.0-alpha", "1.0.0"),
        ("1.0.0-1", "1.0.0-a"),
        ("1.2.3", "1.10.0"),
        ("1.0.0+x", "1.0.0"),
    ]
    for a, b in pairs:
        assert compare_versions(a, b) == -compare_versions(b, a)


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
        "a.b.c",
        "1.0.0-",
        "1.0.0-alpha..1",
        "1.0.0-.alpha",
        "1.0.0-alpha.",
        "1.0.0-01",
        "1.0.0-alpha_1",
        "1.0.0+",
        "1.0.0+a..b",
        "1.0.0+a_b",
        " 1.0.0",
        "1.0.0 ",
        "1.0.0-al pha",
        "1.0.0+",
        "-1.0.0",
        "1.0.0+a+b",
    ],
)
def test_invalid_versions_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_leading_zero_build_identifier_is_valid():
    assert compare_versions("1.0.0+007", "1.0.0") == 0


def test_zero_components_are_valid():
    assert compare_versions("0.0.0", "0.0.0") == 0
    assert compare_versions("0.0.0-0", "0.0.0") == -1
