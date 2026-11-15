from datetime import date, datetime

import pytest

from solution import add_business_days

MON = date(2024, 1, 1)  # Monday
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)
SUN = date(2024, 1, 7)


def test_forward_simple():
    assert add_business_days(MON, 1) == date(2024, 1, 2)
    assert add_business_days(MON, 5) == date(2024, 1, 8)


def test_forward_over_weekend():
    assert add_business_days(FRI, 1) == date(2024, 1, 8)


def test_start_weekend_not_counted():
    assert add_business_days(SAT, 1) == date(2024, 1, 8)
    assert add_business_days(SUN, -1) == FRI


def test_backward():
    assert add_business_days(MON, -1) == date(2023, 12, 29)
    assert add_business_days(date(2024, 1, 8), -5) == MON


def test_zero():
    assert add_business_days(MON, 0) == MON
    assert add_business_days(SAT, 0) == date(2024, 1, 8)
    assert add_business_days(MON, 0, [MON]) == date(2024, 1, 2)


def test_holidays():
    assert add_business_days(MON, 1, {date(2024, 1, 2)}) == date(2024, 1, 3)
    assert add_business_days(MON, -1, [date(2023, 12, 29)]) == date(2023, 12, 28)
    assert add_business_days(MON, 1, (d for d in [date(2024, 1, 2)])) == date(2024, 1, 3)


def test_weekend_holiday_no_effect():
    assert add_business_days(FRI, 1, [SAT, SUN]) == date(2024, 1, 8)


def test_start_holiday_not_counted():
    assert add_business_days(MON, 1, [MON]) == date(2024, 1, 2)


@pytest.mark.parametrize("start", [datetime(2024, 1, 1), "2024-01-01", None])
def test_bad_start(start):
    with pytest.raises(TypeError):
        add_business_days(start, 1)


@pytest.mark.parametrize("n", [True, 1.0, "1", None])
def test_bad_n(n):
    with pytest.raises(TypeError):
        add_business_days(MON, n)


@pytest.mark.parametrize("h", [[datetime(2024, 1, 2)], ["2024-01-02"], [None]])
def test_bad_holidays(h):
    with pytest.raises(TypeError):
        add_business_days(MON, 1, h)
