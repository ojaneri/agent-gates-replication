import pytest
from solution import compare_versions as c


@pytest.mark.parametrize("a,b,r", [
    ("1.0.0", "1.0.0", 0),
    ("1.0.0", "2.0.0", -1),
    ("1.10.0", "1.2.0", 1),
    ("1.0.10", "1.0.9", 1),
    ("1.0.0-alpha", "1.0.0", -1),
    ("1.0.0", "1.0.0-alpha", 1),
    ("1.0.0-alpha", "1.0.0-alpha.1", -1),
    ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
    ("1.0.0-beta.2", "1.0.0-beta.11", -1),
    ("1.0.0-beta", "1.0.0-alpha", 1),
    ("1.0.0-rc.1", "1.0.0-rc.1", 0),
    ("1.0.0-1", "1.0.0-a", -1),
    ("1.0.0-A", "1.0.0-a", -1),
    ("1.0.0+a", "1.0.0+b", 0),
    ("1.0.0-x-y+001", "1.0.0-x-y", 0),
])
def test_compare(a, b, r):
    assert c(a, b) == r
    assert c(b, a) == -r


@pytest.mark.parametrize("v", [
    "", "1", "1.0", "1.0.0.0", "01.0.0", "1.0.0-", "1.0.0-01", "1.0.0-a..b",
    "1.0.0+", "1.0.0+a..b", " 1.0.0", "1.0.0 ", "1.0.0-a_b", "1.0.0\n", "a.b.c",
    "1.0.0-a+b+c", "-1.0.0", "1.0.0-é",
])
def test_invalid(v):
    with pytest.raises(ValueError):
        c(v, "1.0.0")
    with pytest.raises(ValueError):
        c("1.0.0", v)


def test_valid_edge():
    assert c("0.0.0", "0.0.0-0") == 1
    assert c("1.0.0+001.002", "1.0.0") == 0
