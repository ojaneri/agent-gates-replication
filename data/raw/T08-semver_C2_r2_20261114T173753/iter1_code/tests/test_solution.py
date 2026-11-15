import pytest

from solution import compare_versions


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.0.0", 1),
        ("1.2.0", "1.10.0", -1),
        ("1.0.10", "1.0.9", 1),
        ("0.0.0", "0.0.1", -1),
        ("10.0.0", "9.9.9", 1),
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0-alpha", 0),
        ("1.0.0-alpha", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-alpha", 1),
        ("1.0.0-1", "1.0.0-2", -1),
        ("1.0.0-2", "1.0.0-10", -1),
        ("1.0.0-10", "1.0.0-2", 1),
        ("1.0.0-1", "1.0.0-alpha", -1),
        ("1.0.0-alpha", "1.0.0-1", 1),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-a-b", "1.0.0-a-c", -1),
        ("1.0.0-A", "1.0.0-a", -1),
        ("1.0.0-0", "1.0.0-0", 0),
        ("1.0.0-x.7.z.92", "1.0.0-x.7.z.92", 0),
        ("1.0.0+a", "1.0.0+b", 0),
        ("1.0.0+build.1", "1.0.0", 0),
        ("1.0.0-alpha+001", "1.0.0-alpha+exp.sha.5114f85", 0),
        ("1.0.0-alpha+001", "1.0.0-beta", -1),
        ("1.0.0+01", "1.0.0+1", 0),
        ("1.0.0-rc-1+build-2.x", "1.0.0-rc-1", 0),
        ("0.0.0", "0.0.0", 0),
    ],
)
def test_comparison_results(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0-beta", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("2.1.1", "2.1.0", 1),
    ],
)
def test_comparison_is_antisymmetric(a, b, expected):
    assert compare_versions(a, b) == expected
    assert compare_versions(b, a) == -expected


@pytest.mark.parametrize(
    "version",
    [
        "1.0.0",
        "0.0.0",
        "1.0.0-alpha",
        "1.0.0-0.3.7",
        "1.0.0+build",
        "1.0.0-alpha.1+build.5",
    ],
)
def test_valid_versions_are_accepted(version):
    assert compare_versions(version, version) == 0


@pytest.mark.parametrize(
    "version",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "1.0.0-",
        "1.0.0+",
        "1.0.0 ",
        " 1.0.0",
        "1. 0.0",
        "1..0",
        ".1.0",
        "1.0.",
        "01.0.0",
        "1.02.0",
        "1.0.00",
        "-1.0.0",
        "1.-0.0",
        "1.0.0-01",
        "1.0.0-alpha.01",
        "1.0.0-alpha..1",
        "1.0.0-alpha.",
        "1.0.0-.alpha",
        "1.0.0-al pha",
        "1.0.0-alpha_beta",
        "1.0.0+build..1",
        "1.0.0+build.",
        "1.0.0+bu ild",
        "1.0.0+a_b",
        "1.0.0-alpha+",
        "1.0.0+1+2",
        "1.0.0-a+b-c+d",
        "1.0.0١",
        "a.b.c",
        "1.0.x",
        "v1.0.0",
        "1.0.0-é",
    ],
)
def test_invalid_versions_raise(version):
    with pytest.raises(ValueError):
        compare_versions(version, "1.0.0")


def test_invalid_second_argument_raises():
    with pytest.raises(ValueError):
        compare_versions("1.0.0", "1.0.0-01")


def test_non_string_raises():
    with pytest.raises(ValueError):
        compare_versions(None, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", 1)


def test_build_with_leading_zeros_is_valid():
    assert compare_versions("1.0.0+007", "1.0.0+7") == 0


def test_numeric_identifier_zero_is_valid():
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1
