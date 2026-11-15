from datetime import date, datetime

import pytest

from solution import add_business_days as f

MON = date(2024, 1, 1)  # Monday
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)


def test_forward():
    assert f(MON, 1) == date(2024, 1, 2)
    assert f(FRI, 1) == date(2024, 1, 8)
    assert f(SAT, 1) == date(2024, 1, 8)
    assert f(MON, 5) == date(2024, 1, 8)


def test_backward():
    assert f(MON, -1) == date(2023, 12, 29)
    assert f(SAT, -1) == FRI


def test_zero():
    assert f(MON, 0) == MON
    assert f(SAT, 0) == date(2024, 1, 8)
    assert f(MON, 0, [MON]) == date(2024, 1, 2)


def test_holidays():
    assert f(MON, 1, [date(2024, 1, 2)]) == date(2024, 1, 3)
    assert f(MON, 1, (d for d in [date(2024, 1, 2)])) == date(2024, 1, 3)
    assert f(MON, 1, {SAT}) == date(2024, 1, 2)
    assert f(date(2024, 1, 3), -1, [date(2024, 1, 2)]) == MON


@pytest.mark.parametrize("start", [datetime(2024, 1, 1), "2024-01-01", None])
def test_bad_start(start):
    with pytest.raises(TypeError):
        f(start, 1)


@pytest.mark.parametrize("n", [True, 1.0, "1", None])
def test_bad_n(n):
    with pytest.raises(TypeError):
        f(MON, n)


@pytest.mark.parametrize("h", [datetime(2024, 1, 2), "x", 5])
def test_bad_holiday(h):
    with pytest.raises(TypeError):
        f(MON, 1, [h])
