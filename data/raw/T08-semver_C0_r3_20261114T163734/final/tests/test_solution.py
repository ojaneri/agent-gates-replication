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
        ("1.0.0-alpha", "1.0.0-beta", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-1", "1.0.0-a", -1),
        ("1.0.0-a", "1.0.0-1", 1),
        ("1.0.0-alpha", "1.0.0-alpha.0", -1),
        ("1.0.0-A", "1.0.0-a", -1),  # ASCII ordering: uppercase before lowercase
        ("1.0.0-x-y", "1.0.0-x-z", -1),
        ("2.0.0-0", "1.9.9", 1),
    ],
)
def test_prerelease_precedence(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b",
    [
        ("1.0.0+a", "1.0.0+b"),
        ("1.0.0+build.1", "1.0.0"),
        ("1.0.0-alpha+001", "1.0.0-alpha+exp.sha.5114f85"),
        ("1.0.0+20130313144700", "1.0.0+1"),
    ],
)
def test_build_metadata_ignored(a, b):
    assert compare_versions(a, b) == 0
    assert compare_versions(b, a) == 0


def test_build_metadata_does_not_affect_order():
    assert compare_versions("1.0.0+zzz", "1.0.1+aaa") == -1


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "1.0.0-",
        "1.0.0+",
        "1.0.0-alpha..1",
        "1.0.0-.alpha",
        "1.0.0-alpha.",
        "1.0.0+build..1",
        "1.0.0+",
        "01.0.0",
        "1.00.0",
        "1.0.01",
        "1.0.0-01",
        "1.0.0-alpha.07",
        " 1.0.0",
        "1.0.0 ",
        "1.0. 0",
        "1.0.0-alpha beta",
        "1.0.0-alpha_beta",
        "1.0.0+build!",
        "-1.0.0",
        "1.-0.0",
        "a.b.c",
        "1.0.0-alpha+",
        "v1.0.0",
    ],
)
def test_invalid_versions_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_valid_zero_forms():
    assert compare_versions("0.0.0", "0.0.0") == 0
    assert compare_versions("1.0.0-0", "1.0.0-0") == 0
    assert compare_versions("1.0.0-0.3.7", "1.0.0-0.3.7+b01") == 0


def test_build_leading_zeros_allowed():
    assert compare_versions("1.0.0+01", "1.0.0+1") == 0
    assert compare_versions("1.0.0-alpha+007", "1.0.0-alpha") == 0


def test_antisymmetry():
    pairs = [
        ("1.0.0-alpha", "1.0.0"),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta"),
        ("2.0.0", "1.9.9"),
    ]
    for a, b in pairs:
        assert compare_versions(a, b) == -compare_versions(b, a)
