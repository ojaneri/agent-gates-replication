import datetime as dt

import pytest

from solution import add_business_days

D = dt.date


# 2026-11-14 is a Saturday; 2026-11-16 is a Monday.


def test_weekday_identities():
    assert D(2026, 11, 16).weekday() == 0
    assert D(2026, 11, 14).weekday() == 5


# n > 0

def test_forward_one_from_friday_skips_weekend():
    assert add_business_days(D(2026, 11, 13), 1) == D(2026, 11, 16)


def test_forward_from_weekday_within_week():
    assert add_business_days(D(2026, 11, 16), 3) == D(2026, 11, 19)


def test_forward_from_saturday_start_not_counted():
    # Saturday start: first business day after is Monday 16th.
    assert add_business_days(D(2026, 11, 14), 1) == D(2026, 11, 16)
    assert add_business_days(D(2026, 11, 14), 5) == D(2026, 11, 20)


def test_forward_across_multiple_weeks():
    assert add_business_days(D(2026, 11, 13), 10) == D(2026, 11, 27)


def test_forward_start_never_counted_on_business_day():
    # Monday start, n=1 -> Tuesday, not Monday.
    assert add_business_days(D(2026, 11, 16), 1) == D(2026, 11, 17)


def test_forward_with_holiday_skipped():
    assert add_business_days(D(2026, 11, 16), 1, holidays=[D(2026, 11, 17)]) == D(2026, 11, 18)


def test_forward_holiday_on_weekend_changes_nothing():
    assert add_business_days(D(2026, 11, 13), 1, holidays={D(2026, 11, 14)}) == D(2026, 11, 16)


def test_forward_holiday_is_start_not_counted_again():
    assert add_business_days(D(2026, 11, 16), 1, holidays=(D(2026, 11, 16),)) == D(2026, 11, 17)


def test_forward_multiple_holidays_consecutive():
    hol = [D(2026, 11, 17), D(2026, 11, 18)]
    assert add_business_days(D(2026, 11, 16), 1, holidays=hol) == D(2026, 11, 19)


# n < 0

def test_backward_one_from_monday_skips_weekend():
    assert add_business_days(D(2026, 11, 16), -1) == D(2026, 11, 13)


def test_backward_from_weekday():
    assert add_business_days(D(2026, 11, 18), -2) == D(2026, 11, 16)


def test_backward_from_saturday():
    assert add_business_days(D(2026, 11, 14), -1) == D(2026, 11, 13)


def test_backward_across_weeks():
    assert add_business_days(D(2026, 11, 27), -10) == D(2026, 11, 13)


def test_backward_with_holiday_skipped():
    assert add_business_days(D(2026, 11, 18), -1, holidays=[D(2026, 11, 17)]) == D(2026, 11, 16)


def test_backward_start_never_counted():
    assert add_business_days(D(2026, 11, 13), -1) == D(2026, 11, 12)


def test_backward_holiday_on_weekend_changes_nothing():
    assert add_business_days(D(2026, 11, 16), -1, holidays=[D(2026, 11, 15)]) == D(2026, 11, 13)


# n == 0

def test_zero_on_business_day_returns_start():
    assert add_business_days(D(2026, 11, 18), 0) == D(2026, 11, 18)


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(D(2026, 11, 14), 0) == D(2026, 11, 16)


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(D(2026, 11, 15), 0) == D(2026, 11, 16)


def test_zero_on_holiday_returns_next_business_day():
    assert add_business_days(D(2026, 11, 18), 0, holidays=[D(2026, 11, 18)]) == D(2026, 11, 19)


def test_zero_weekend_with_holiday_monday_moves_further():
    hol = [D(2026, 11, 16)]
    assert add_business_days(D(2026, 11, 14), 0, holidays=hol) == D(2026, 11, 17)


# holidays input forms

def test_holidays_generator_accepted():
    gen = (d for d in [D(2026, 11, 17)])
    assert add_business_days(D(2026, 11, 16), 1, holidays=gen) == D(2026, 11, 18)


def test_holidays_default_empty():
    assert add_business_days(D(2026, 11, 16), 1) == D(2026, 11, 17)


def test_holidays_tuple_and_set_equivalent():
    h = D(2026, 11, 17)
    assert add_business_days(D(2026, 11, 16), 2, (h,)) == add_business_days(D(2026, 11, 16), 2, {h})


# Type validation

def test_start_datetime_rejected():
    with pytest.raises(TypeError):
        add_business_days(dt.datetime(2026, 11, 16, 9, 0), 1)


def test_start_string_rejected():
    with pytest.raises(TypeError):
        add_business_days("2026-11-16", 1)


@pytest.mark.parametrize("bad", [1.0, True, False, "3", None])
def test_n_must_be_int(bad):
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), bad)


def test_holiday_datetime_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1, holidays=[dt.datetime(2026, 11, 17, 0, 0)])


def test_holiday_non_date_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1, holidays=["2026-11-17"])


def test_holiday_non_date_in_generator_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1, holidays=(x for x in [D(2026, 11, 17), 5]))
