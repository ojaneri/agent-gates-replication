import pytest

from solution import compare_versions


# --- core version ordering -------------------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "2.0.0", -1),
        ("2.0.0", "1.0.0", 1),
        ("1.2.0", "1.10.0", -1),       # numeric, not string, comparison
        ("1.10.0", "1.9.0", 1),
        ("1.0.10", "1.0.9", 1),
        ("0.0.0", "0.0.1", -1),
        ("0.0.0", "0.0.0", 0),
        ("10.0.0", "9.99.99", 1),
    ],
)
def test_core_ordering(a, b, expected):
    assert compare_versions(a, b) == expected


def test_large_numbers_compare_numerically():
    big = "123456789012345678901234567890.0.0"
    assert compare_versions(big, "99999999999999999999.0.0") == 1


# --- prerelease precedence -------------------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0-alpha", 0),
        ("1.0.0-alpha", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-alpha", 1),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),  # fewer identifiers is lower
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),  # numeric < non-numeric
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta", "1.0.0-beta.2", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),  # numeric comparison
        ("1.0.0-beta.11", "1.0.0-rc.1", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-0", "1.0.0-a", -1),
        ("1.0.0-9", "1.0.0-10", -1),
        ("1.0.0-1a", "1.0.0-1", 1),  # "1a" is non-numeric, compared as string
        ("1.0.0-A", "1.0.0-a", -1),  # ASCII ordering: uppercase first
        ("1.0.0-a-b", "1.0.0-a-c", -1),  # hyphens inside identifiers
        ("1.0.0-x.7.z.92", "1.0.0-x.7.z.92", 0),
        ("1.0.0-x.7.z.92", "1.0.0-x.7.z.93", -1),
    ],
)
def test_prerelease_ordering(a, b, expected):
    assert compare_versions(a, b) == expected


def test_prerelease_spec_example_chain():
    # Ordering example from the semver specification, strictly increasing.
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


def test_core_difference_beats_prerelease():
    assert compare_versions("1.0.1-alpha", "1.0.0") == 1
    assert compare_versions("1.0.0", "1.0.1-alpha") == -1
    assert compare_versions("2.0.0-alpha", "1.9.9") == 1


# --- build metadata ----------------------------------------------------------

@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1.0.0+a", "1.0.0+b", 0),
        ("1.0.0+build.1", "1.0.0", 0),
        ("1.0.0-alpha+001", "1.0.0-alpha+exp.sha.5114f85", 0),
        ("1.0.0+001", "1.0.0+1", 0),  # leading zeros allowed in build
        ("1.0.0+20130313144700", "1.0.0-beta+exp.sha.5114f85", 1),
        ("1.0.0-beta", "1.0.0-beta+x", 0),
        ("1.0.0+z", "1.0.1", -1),
    ],
)
def test_build_metadata_ignored(a, b, expected):
    assert compare_versions(a, b) == expected


def test_build_with_hyphens_and_dots_is_valid():
    assert compare_versions("1.0.0+a-b.c-d", "1.0.0") == 0


# --- symmetry and antisymmetry ------------------------------------------------

@pytest.mark.parametrize(
    "a, b",
    [
        ("1.0.0-alpha", "1.0.0-alpha.1"),
        ("0.9.9", "1.0.0-rc.1"),
        ("3.2.1+x", "3.2.1-pre"),
    ],
)
def test_antisymmetry(a, b):
    assert compare_versions(a, b) == -compare_versions(b, a)


# --- invalid input -------------------------------------------------------------

@pytest.mark.parametrize(
    "bad",
    [
        "",
        "1",
        "1.0",
        "1.0.0.0",
        "1.0.0.",
        ".1.0.0",
        "1..0",
        "a.b.c",
        "1.0.x",
        " 1.0.0",
        "1.0.0 ",
        "1.0.0 -alpha",
        "1.0.0- alpha",
        "01.0.0",
        "1.00.0",
        "1.0.00",
        "-1.0.0",
        "+1.0.0",
        "1.0.0-",
        "1.0.0+",
        "1.0.0-alpha.",
        "1.0.0-.alpha",
        "1.0.0-alpha..1",
        "1.0.0-01",
        "1.0.0-alpha.007",
        "1.0.0-0.3.07",
        "1.0.0+",
        "1.0.0+build..1",
        "1.0.0+build_1",
        "1.0.0-alpha_beta",
        "1.0.0-alpha+",
        "1.0.0+a+b",
        "1.0.0-a-b+c+d",
        "1.0.0\n",
        "1.0.0-аlpha",  # Cyrillic letter, not ASCII
        "١.0.0",  # Arabic-Indic digit, not ASCII
        "1.0.0-alpha!",
    ],
)
def test_invalid_versions_raise_value_error(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0.0")
    with pytest.raises(ValueError):
        compare_versions("1.0.0", bad)


def test_invalid_second_argument_raises_even_when_first_valid():
    with pytest.raises(ValueError):
        compare_versions("1.0.0", "1.0")


def test_non_string_input_raises_type_error():
    with pytest.raises(TypeError):
        compare_versions(1, "1.0.0")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        compare_versions("1.0.0", None)  # type: ignore[arg-type]
