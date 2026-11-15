import pytest

from solution import compare_versions


# --- basic core comparison -------------------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("0.0.0", "0.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.0.0", 1),
        ("1.2.0", "1.10.0", -1),   # numeric, not string, comparison
        ("1.10.0", "1.9.0", 1),
        ("1.0.10", "1.0.9", 1),
        ("0.0.1", "0.1.0", -1),
        ("10.0.0", "9.99.99", 1),
    ],
)
def test_core_comparison(a, b, expected):
    assert compare_versions(a, b) == expected


def test_result_is_antisymmetric():
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("1.0.1", "1.0.0") == 1


# --- prerelease vs release -------------------------------------------------

def test_release_higher_than_prerelease_same_core():
    assert compare_versions("1.0.0-alpha", "1.0.0") == -1
    assert compare_versions("1.0.0", "1.0.0-alpha") == 1


def test_prerelease_lower_than_higher_core():
    assert compare_versions("1.0.0-alpha", "1.0.1") == -1
    assert compare_versions("2.0.0-rc.1", "1.9.9") == 1


# --- prerelease identifier precedence --------------------------------------

def test_numeric_identifiers_compare_numerically():
    assert compare_versions("1.0.0-2", "1.0.0-10") == -1
    assert compare_versions("1.0.0-10", "1.0.0-2") == 1


def test_numeric_lower_than_non_numeric():
    assert compare_versions("1.0.0-1", "1.0.0-alpha") == -1
    assert compare_versions("1.0.0-alpha", "1.0.0-1") == 1


def test_non_numeric_compare_as_ascii_strings():
    assert compare_versions("1.0.0-alpha", "1.0.0-beta") == -1
    assert compare_versions("1.0.0-beta", "1.0.0-alpha") == 1
    # ASCII ordering: uppercase sorts before lowercase.
    assert compare_versions("1.0.0-Z", "1.0.0-a") == -1
    # Hyphen is an ordinary identifier character.
    assert compare_versions("1.0.0-a-b", "1.0.0-a") == 1


def test_fewer_identifiers_lower_when_prefix_equal():
    assert compare_versions("1.0.0-alpha", "1.0.0-alpha.1") == -1
    assert compare_versions("1.0.0-alpha.1", "1.0.0-alpha") == 1


def test_spec_example_ordering():
    ordered = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    for lower, higher in zip(ordered, ordered[1:]):
        assert compare_versions(lower, higher) == -1
        assert compare_versions(higher, lower) == 1
    assert compare_versions(ordered[3], ordered[3]) == 0


def test_identical_prerelease_equal():
    assert compare_versions("1.0.0-rc.1.x", "1.0.0-rc.1.x") == 0


def test_large_numeric_identifiers_compare_by_value():
    big = "9" * 30
    bigger = "1" + "0" * 30
    assert compare_versions(f"1.0.0-{big}", f"1.0.0-{bigger}") == -1


def test_zero_prerelease_identifier_is_valid():
    assert compare_versions("1.0.0-0", "1.0.0-0") == 0
    assert compare_versions("1.0.0-0", "1.0.0-1") == -1


# --- build metadata ---------------------------------------------------------

def test_build_metadata_ignored():
    assert compare_versions("1.0.0+a", "1.0.0+b") == 0
    assert compare_versions("1.0.0+build.1", "1.0.0") == 0
    assert compare_versions("1.0.0-alpha+001", "1.0.0-alpha") == 0


def test_build_metadata_does_not_affect_prerelease_order():
    assert compare_versions("1.0.0-alpha+zzz", "1.0.0-beta+aaa") == -1


def test_build_allows_leading_zeros_and_hyphens():
    assert compare_versions("1.0.0+001", "1.0.0+exp-sha.5114f85") == 0
    assert compare_versions("1.0.0+00", "1.0.0") == 0


def test_prerelease_with_hyphen_and_build_with_hyphen():
    assert compare_versions("1.0.0-x-y+b-c", "1.0.0-x-y") == 0


# --- invalid input ----------------------------------------------------------

@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "01.0.0",
        "1.00.0",
        "1.0.00",
        "1.0.0-01",
        "1.0.0-alpha.07",
        "1.0.0-",
        "1.0.0-alpha.",
        "1.0.0-.alpha",
        "1.0.0-alpha..1",
        "1.0.0+",
        "1.0.0+build.",
        "1.0.0+.build",
        "1.0.0+a..b",
        "1.0.0 ",
        " 1.0.0",
        "1.0.0-al pha",
        "1.0.0+b c",
        "1.0.0-alpha_1",
        "1.0.0-alpha+b+c",
        "-1.0.0",
        "1.-0.0",
        "a.b.c",
        "1.0.0\n",
        "1.0.0-alpha\n",
        "1.0.0-é",
        "١.0.0",  # Arabic-Indic digit one: not ASCII
        "1.0.0-١",
    ],
)
def test_invalid_versions_raise_value_error(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_non_string_raises_type_error():
    with pytest.raises(TypeError):
        compare_versions(1, "1.0.0")
    with pytest.raises(TypeError):
        compare_versions("1.0.0", None)


def test_valid_zero_components():
    assert compare_versions("0.0.0", "0.0.1") == -1
    assert compare_versions("0.0.0-0", "0.0.0") == -1
