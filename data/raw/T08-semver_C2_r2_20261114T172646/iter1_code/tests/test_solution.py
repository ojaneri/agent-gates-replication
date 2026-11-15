import pytest

from solution import compare_versions as cv


@pytest.mark.parametrize("a,b,r", [
    ("1.0.0", "1.0.0", 0),
    ("1.0.0", "2.0.0", -1),
    ("2.0.0", "1.9.9", 1),
    ("1.2.0", "1.10.0", -1),
    ("1.1.0", "1.0.9", 1),
    ("1.0.2", "1.0.10", -1),
    ("1.0.1", "1.0.0", 1),
    ("1.0.0-alpha", "1.0.0", -1),
    ("1.0.0", "1.0.0-alpha", 1),
    ("1.0.0-alpha", "1.0.0-alpha", 0),
    ("1.0.0-alpha", "1.0.0-alpha.1", -1),
    ("1.0.0-alpha.1", "1.0.0-alpha", 1),
    ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
    ("1.0.0-alpha.beta", "1.0.0-alpha.1", 1),
    ("1.0.0-beta", "1.0.0-alpha", 1),
    ("1.0.0-alpha", "1.0.0-beta", -1),
    ("1.0.0-beta.2", "1.0.0-beta.11", -1),
    ("1.0.0-beta.11", "1.0.0-beta.2", 1),
    ("1.0.0-rc.1", "1.0.0", -1),
    ("1.0.0-0", "1.0.0-0", 0),
    ("1.0.0-a-b", "1.0.0-a-c", -1),
    ("1.0.0+a", "1.0.0+b", 0),
    ("1.0.0+001", "1.0.0", 0),
    ("1.0.0-alpha+x", "1.0.0-alpha", 0),
    ("0.0.0", "0.0.0", 0),
    ("1.0.0-Z", "1.0.0-a", -1),
])
def test_compare(a, b, r):
    assert cv(a, b) == r


@pytest.mark.parametrize("bad", [
    "", "1", "1.0", "1.0.0.0", "01.0.0", "1.00.0", "1.0.01", "1.0.0-",
    "1.0.0+", "1.0.0-a..b", "1.0.0-01", "1.0.0-a.", "1.0.0 ", " 1.0.0",
    "1.0.0+a..b", "1.0.0+a.", "1.0.0-a_b", "1.0.0+é", "a.b.c", "-1.0.0",
    "1.0.0\n", "1.0.0-+a", "1.0.0-a+", "1.0.0+a+b", "1.0.0-.a",
])
def test_invalid(bad):
    with pytest.raises(ValueError):
        cv(bad, "1.0.0")
    with pytest.raises(ValueError):
        cv("1.0.0", bad)


def test_non_string():
    with pytest.raises(ValueError):
        cv(None, "1.0.0")


def test_valid_edge_idents():
    assert cv("1.0.0-0.0a-1.a0", "1.0.0-0.0a-1.a0+007.01") == 0
    assert cv("1.0.0-a.0", "1.0.0-a.00x") == -1
