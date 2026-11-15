import pytest
from solution import compare_versions as c


def test_core():
    assert c("1.0.0", "2.0.0") == -1
    assert c("1.10.0", "1.2.0") == 1
    assert c("1.2.3", "1.2.3") == 0
    assert c("1.2.10", "1.2.9") == 1


def test_prerelease():
    assert c("1.0.0-alpha", "1.0.0") == -1
    assert c("1.0.0", "1.0.0-alpha") == 1
    assert c("1.0.0-alpha", "1.0.0-alpha.1") == -1
    assert c("1.0.0-alpha.1", "1.0.0-alpha.beta") == -1
    assert c("1.0.0-beta.2", "1.0.0-beta.11") == -1
    assert c("1.0.0-beta", "1.0.0-alpha") == 1
    assert c("1.0.0-rc.1", "1.0.0") == -1
    assert c("1.0.0-a-b", "1.0.0-a-b") == 0
    assert c("1.0.0-B", "1.0.0-a") == -1


def test_build():
    assert c("1.0.0+a", "1.0.0+b") == 0
    assert c("1.0.0+001", "1.0.0") == 0
    assert c("1.0.0-x+a", "1.0.0-x") == 0


@pytest.mark.parametrize("v", [
    "", "1", "1.0", "1.0.0.0", "01.0.0", "1.00.0", "1.0.01", "1.0.0-", "1.0.0+",
    "1.0.0-01", "1.0.0-a..b", "1.0.0 ", " 1.0.0", "1.0.0-a_b", "1.0.0+a..b",
    "-1.0.0", "a.b.c", "1.0.0-é", "1.0.0\n", "1.0.0+a+b",
])
def test_invalid(v):
    with pytest.raises(ValueError):
        c(v, "1.0.0")
    with pytest.raises(ValueError):
        c("1.0.0", v)
