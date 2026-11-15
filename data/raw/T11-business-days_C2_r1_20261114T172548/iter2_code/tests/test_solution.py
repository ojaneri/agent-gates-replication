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
    assert add_business_days(SAT, 1) == date(2024, 1, 8)
    assert add_business_days(FRI, 6) == date(2024, 1, 15)


def test_backward():
    assert add_business_days(date(2024, 1, 8), -1) == FRI
    assert add_business_days(SUN, -1) == FRI
    assert add_business_days(FRI, -1) == date(2024, 1, 4)
    assert add_business_days(date(2024, 1, 8), -5) == date(2024, 1, 1)
    assert add_business_days(date(2024, 1, 8), -6) == date(2023, 12, 29)


def test_zero():
    assert add_business_days(MON, 0) == MON
    assert add_business_days(SAT, 0) == date(2024, 1, 8)
    assert add_business_days(SUN, 0) == date(2024, 1, 8)
    assert add_business_days(MON, 0, [MON]) == date(2024, 1, 2)


def test_holidays():
    assert add_business_days(MON, 1, [date(2024, 1, 2)]) == date(2024, 1, 3)
    assert add_business_days(MON, 1, {SAT}) == date(2024, 1, 2)
    assert add_business_days(FRI, -1, (date(2024, 1, 4),)) == date(2024, 1, 3)
    gen = (d for d in [date(2024, 1, 2)])
    assert add_business_days(MON, 1, gen) == date(2024, 1, 3)


def test_start_not_counted_if_holiday():
    assert add_business_days(MON, 1, [MON]) == date(2024, 1, 2)


def test_type_errors():
    with pytest.raises(TypeError):
        add_business_days(datetime(2024, 1, 1), 1)
    with pytest.raises(TypeError):
        add_business_days("2024-01-01", 1)
    with pytest.raises(TypeError):
        add_business_days(MON, True)
    with pytest.raises(TypeError):
        add_business_days(MON, 1.0)
    with pytest.raises(TypeError):
        add_business_days(MON, 1, ["x"])
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [datetime(2024, 1, 2)])
