import datetime as dt

import pytest

from solution import add_business_days

# 2024-01-01 is a Monday.
MON = dt.date(2024, 1, 1)
TUE = dt.date(2024, 1, 2)
THU = dt.date(2024, 1, 4)
FRI = dt.date(2024, 1, 5)
SAT = dt.date(2024, 1, 6)
SUN = dt.date(2024, 1, 7)
MON2 = dt.date(2024, 1, 8)
TUE2 = dt.date(2024, 1, 9)


def test_forward_from_friday_skips_weekend():
    assert add_business_days(FRI, 1) == MON2


def test_forward_from_saturday_does_not_count_start():
    assert add_business_days(SAT, 1) == MON2


def test_forward_from_weekday_does_not_count_start():
    assert add_business_days(MON, 1) == TUE


def test_forward_ten_days():
    assert add_business_days(MON, 10) == dt.date(2024, 1, 15)


def test_backward_from_monday():
    assert add_business_days(MON2, -1) == FRI


def test_backward_from_sunday():
    assert add_business_days(SUN, -1) == FRI


def test_backward_from_saturday_two_days():
    assert add_business_days(SAT, -2) == dt.date(2024, 1, 4)


def test_zero_on_business_day_returns_start():
    assert add_business_days(TUE, 0) == TUE


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(SAT, 0) == MON2


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(SUN, 0) == MON2


def test_holiday_is_skipped_forward():
    assert add_business_days(THU, 2, holidays=[FRI]) == TUE2


def test_holiday_is_skipped_backward():
    assert add_business_days(MON2, -1, holidays=[FRI]) == THU


def test_zero_on_holiday_returns_next_business_day():
    assert add_business_days(MON2, 0, holidays={MON2}) == TUE2


def test_weekend_holiday_changes_nothing():
    assert add_business_days(THU, 1, holidays=[SAT, SUN]) == FRI
    assert add_business_days(FRI, 1, holidays=(SAT,)) == MON2


def test_holidays_accepts_generator():
    gen = (d for d in [FRI])
    assert add_business_days(THU, 2, holidays=gen) == TUE2


def test_holidays_accepts_set_and_tuple():
    assert add_business_days(THU, 2, holidays={FRI}) == TUE2
    assert add_business_days(THU, 2, holidays=(FRI,)) == TUE2


def test_default_holidays_empty():
    assert add_business_days(THU, 2) == MON2


def test_returns_date_type():
    result = add_business_days(MON, 3)
    assert type(result) is dt.date


def test_start_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(dt.datetime(2024, 1, 1, 9, 0), 1)


def test_start_not_date_raises():
    with pytest.raises(TypeError):
        add_business_days("2024-01-01", 1)


@pytest.mark.parametrize("bad", [1.0, True, False, "1"])
def test_n_must_be_int(bad):
    with pytest.raises(TypeError):
        add_business_days(MON, bad)


def test_holiday_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, holidays=[dt.datetime(2024, 1, 5)])


def test_holiday_non_date_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, holidays=["2024-01-05"])
