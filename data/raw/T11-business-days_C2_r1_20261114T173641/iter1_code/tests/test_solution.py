import datetime as dt

import pytest

from solution import add_business_days

# 2024-01-01 is a Monday.
MON = dt.date(2024, 1, 1)
TUE = dt.date(2024, 1, 2)
FRI = dt.date(2024, 1, 5)
SAT = dt.date(2024, 1, 6)
SUN = dt.date(2024, 1, 7)
NEXT_MON = dt.date(2024, 1, 8)


# --- forward movement -------------------------------------------------------

def test_forward_one_from_friday_skips_weekend():
    assert add_business_days(FRI, 1) == NEXT_MON


def test_forward_one_from_monday():
    assert add_business_days(NEXT_MON, 1) == dt.date(2024, 1, 9)


def test_forward_one_from_saturday():
    assert add_business_days(SAT, 1) == NEXT_MON


def test_forward_five_from_monday_is_next_monday():
    assert add_business_days(NEXT_MON, 5) == dt.date(2024, 1, 15)


def test_forward_two_from_thursday_crosses_weekend():
    assert add_business_days(dt.date(2024, 1, 4), 2) == NEXT_MON


def test_start_is_not_counted_on_business_day():
    assert add_business_days(MON, 1) == TUE


def test_start_is_not_counted_on_weekend():
    assert add_business_days(SUN, 1) == NEXT_MON


def test_forward_across_year_boundary():
    assert add_business_days(dt.date(2023, 12, 29), 2) == dt.date(2024, 1, 2)


def test_forward_large_n():
    # 20 business days = 4 full weeks from a Monday.
    assert add_business_days(MON, 20) == dt.date(2024, 1, 29)


# --- backward movement ------------------------------------------------------

def test_backward_one_from_monday_is_friday():
    assert add_business_days(NEXT_MON, -1) == FRI


def test_backward_one_from_saturday_is_friday():
    assert add_business_days(SAT, -1) == FRI


def test_backward_five_from_next_monday():
    assert add_business_days(NEXT_MON, -5) == MON


def test_backward_start_not_counted_on_business_day():
    assert add_business_days(TUE, -1) == MON


def test_backward_across_year_boundary():
    assert add_business_days(dt.date(2024, 1, 2), -2) == dt.date(2023, 12, 29)


# --- n == 0 -----------------------------------------------------------------

def test_zero_on_business_day_returns_start():
    assert add_business_days(TUE, 0) == TUE


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(SAT, 0) == NEXT_MON


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(SUN, 0) == NEXT_MON


def test_zero_on_holiday_returns_next_business_day():
    assert add_business_days(TUE, 0, holidays=[TUE]) == dt.date(2024, 1, 3)


def test_zero_on_friday_holiday_skips_weekend():
    assert add_business_days(FRI, 0, holidays=[FRI]) == NEXT_MON


def test_zero_on_business_day_not_holiday_returns_start():
    assert add_business_days(TUE, 0, holidays=[MON]) == TUE


# --- holidays ---------------------------------------------------------------

def test_holiday_is_skipped_forward():
    assert add_business_days(FRI, 1, holidays=[NEXT_MON]) == dt.date(2024, 1, 9)


def test_holiday_is_skipped_backward():
    assert add_business_days(NEXT_MON, -1, holidays=[FRI]) == dt.date(2024, 1, 4)


def test_multiple_consecutive_holidays():
    holidays = {dt.date(2024, 1, 2), dt.date(2024, 1, 3)}
    assert add_business_days(MON, 1, holidays=holidays) == dt.date(2024, 1, 4)


def test_holiday_on_weekend_changes_nothing():
    assert add_business_days(FRI, 1, holidays=[SAT, SUN]) == NEXT_MON


def test_holiday_on_weekend_backward_changes_nothing():
    assert add_business_days(NEXT_MON, -1, holidays=[SAT, SUN]) == FRI


def test_start_being_a_holiday_is_not_counted_specially():
    # start is a holiday and a business day: moving forward still starts from it.
    assert add_business_days(TUE, 1, holidays=[TUE]) == dt.date(2024, 1, 3)


def test_holiday_outside_range_has_no_effect():
    assert add_business_days(MON, 1, holidays=[dt.date(2030, 5, 5)]) == TUE


def test_holidays_as_generator():
    gen = (d for d in [NEXT_MON])
    assert add_business_days(FRI, 1, holidays=gen) == dt.date(2024, 1, 9)


def test_holidays_as_tuple_and_duplicates():
    assert add_business_days(FRI, 1, holidays=(NEXT_MON, NEXT_MON)) == dt.date(2024, 1, 9)


def test_holidays_default_is_empty():
    assert add_business_days(FRI, 1) == NEXT_MON


def test_holidays_as_set_of_dates():
    assert add_business_days(FRI, 2, holidays={NEXT_MON}) == dt.date(2024, 1, 10)


def test_returns_date_type():
    result = add_business_days(FRI, 1)
    assert type(result) is dt.date


# --- input validation -------------------------------------------------------

def test_start_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(dt.datetime(2024, 1, 5, 12, 0), 1)


def test_start_string_raises():
    with pytest.raises(TypeError):
        add_business_days("2024-01-05", 1)


def test_n_bool_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, True)


def test_n_float_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1.0)


def test_n_string_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, "1")


def test_holiday_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1, holidays=[dt.datetime(2024, 1, 8)])


def test_holiday_string_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1, holidays=["2024-01-08"])


def test_holiday_none_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1, holidays=[None])
