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
        ("1.0.0-alpha", "2.0.0-alpha", -1),
        ("2.0.0-alpha", "1.9.9", 1),
    ],
)
def test_prerelease_vs_release(a, b, expected):
    assert compare_versions(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-2", "1.0.0-10", -1),
        ("1.0.0-1", "1.0.0-a", -1),
        ("1.0.0-a", "1.0.0-a", 0),
        ("1.0.0-a.b.c", "1.0.0-a.b", 1),
        ("1.0.0-0", "1.0.0-0a", -1),
        ("1.0.0-A", "1.0.0-a", -1),
        ("1.0.0-a-b", "1.0.0-a-c", -1),
    ],
)
def test_prerelease_identifier_ordering(a, b, expected):
    assert compare_versions(a, b) == expected
    assert compare_versions(b, a) == -expected


@pytest.mark.parametrize(
    "a, b",
    [
        ("1.0.0+a", "1.0.0+b"),
        ("1.0.0+build.1", "1.0.0"),
        ("1.0.0-alpha+001", "1.0.0-alpha+exp.sha.5114f85"),
        ("1.0.0+01", "1.0.0+1"),
    ],
)
def test_build_metadata_ignored(a, b):
    assert compare_versions(a, b) == 0


def test_antisymmetry_and_reflexivity_over_samples():
    samples = [
        "0.0.1", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0", "1.0.0+x",
        "2.0.0-rc.1", "2.0.0", "10.1.0-0.3",
    ]
    for a in samples:
        assert compare_versions(a, a) == 0
        for b in samples:
            assert compare_versions(a, b) == -compare_versions(b, a)


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
        "1.0.0-alpha+",
        "1.0.0 ",
        " 1.0.0",
        "1.0.0\n",
        "1.0.0-al pha",
        "1.0.0+bu_ild",
        "1.0.0-alpha_1",
        "1.0.0+a+b",
        "-1.0.0",
        "1.-1.0",
        "a.b.c",
        "1.0.0-é",
        "v1.0.0",
    ],
)
def test_invalid_versions_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


@pytest.mark.parametrize("bad", [None, 1, 1.0, ["1.0.0"]])
def test_non_string_raises(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_zero_identifiers_are_valid_numeric():
    assert compare_versions("1.0.0-0", "1.0.0-0") == 0
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1
