from datetime import date, datetime

import pytest

from solution import add_business_days

MON = date(2024, 1, 1)
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)
SUN = date(2024, 1, 7)


def test_forward_simple():
    assert add_business_days(MON, 1) == date(2024, 1, 2)
    assert add_business_days(MON, 4) == FRI


def test_forward_over_weekend():
    assert add_business_days(FRI, 1) == date(2024, 1, 8)
    assert add_business_days(FRI, 6) == date(2024, 1, 15)


def test_start_weekend_not_counted():
    assert add_business_days(SAT, 1) == date(2024, 1, 8)
    assert add_business_days(SUN, 1) == date(2024, 1, 8)


def test_backward():
    assert add_business_days(date(2024, 1, 8), -1) == FRI
    assert add_business_days(MON, -1) == date(2023, 12, 29)
    assert add_business_days(SUN, -1) == FRI


def test_backward_multiple():
    assert add_business_days(date(2024, 1, 15), -6) == date(2024, 1, 5)
    assert add_business_days(date(2024, 1, 8), -5) == MON


def test_zero():
    assert add_business_days(MON, 0) == MON
    assert add_business_days(SAT, 0) == date(2024, 1, 8)
    assert add_business_days(SUN, 0) == date(2024, 1, 8)


def test_zero_with_holiday():
    assert add_business_days(MON, 0, [MON]) == date(2024, 1, 2)
    assert add_business_days(SAT, 0, {date(2024, 1, 8)}) == date(2024, 1, 9)


def test_holidays_skipped():
    assert add_business_days(MON, 1, [date(2024, 1, 2)]) == date(2024, 1, 3)
    assert add_business_days(date(2024, 1, 3), -1, [date(2024, 1, 2)]) == MON


def test_holiday_on_weekend_no_effect():
    assert add_business_days(FRI, 1, [SAT, SUN]) == date(2024, 1, 8)


def test_start_holiday_not_counted():
    assert add_business_days(MON, 1, [MON]) == date(2024, 1, 2)


def test_generator_holidays():
    assert add_business_days(MON, 1, (d for d in [date(2024, 1, 2)])) == date(2024, 1, 3)


def test_bad_start():
    with pytest.raises(TypeError):
        add_business_days(datetime(2024, 1, 1), 1)
    with pytest.raises(TypeError):
        add_business_days("2024-01-01", 1)


def test_bad_n():
    for bad in (True, 1.0, "1", None):
        with pytest.raises(TypeError):
            add_business_days(MON, bad)


def test_bad_holidays():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, ["2024-01-02"])
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [datetime(2024, 1, 2)])
