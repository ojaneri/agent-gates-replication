import os
import sys
from datetime import date, datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution import add_business_days  # noqa: E402

# 2024-01-01 is a Monday.
MON = date(2024, 1, 1)
MON2 = date(2024, 1, 8)
TUE2 = date(2024, 1, 9)
WED2 = date(2024, 1, 10)
THU1 = date(2024, 1, 4)
FRI1 = date(2024, 1, 5)
SAT1 = date(2024, 1, 6)
SUN1 = date(2024, 1, 7)
FRI2 = date(2024, 1, 12)
MON3 = date(2024, 1, 15)


# ---- forward movement ----

def test_forward_one_from_friday_skips_weekend():
    assert add_business_days(FRI1, 1) == MON2


def test_forward_one_from_monday():
    assert add_business_days(MON2, 1) == TUE2


def test_forward_five_from_friday():
    assert add_business_days(FRI1, 5) == FRI2


def test_forward_five_from_monday():
    assert add_business_days(MON, 5) == MON2


def test_forward_from_saturday_start_not_counted():
    assert add_business_days(SAT1, 1) == MON2


def test_forward_from_sunday_start_not_counted():
    assert add_business_days(SUN1, 1) == MON2


def test_forward_across_year_boundary_and_leap_day():
    assert add_business_days(date(2024, 2, 29), 1) == date(2024, 3, 1)


# ---- backward movement ----

def test_backward_one_from_monday_skips_weekend():
    assert add_business_days(MON2, -1) == FRI1


def test_backward_one_from_saturday():
    assert add_business_days(SAT1, -1) == FRI1


def test_backward_two_from_monday():
    assert add_business_days(MON2, -2) == THU1


def test_backward_five_from_monday():
    assert add_business_days(MON2, -5) == MON


# ---- n == 0 ----

def test_zero_on_business_day_returns_start():
    assert add_business_days(FRI1, 0) == FRI1


def test_zero_on_saturday_moves_to_monday():
    assert add_business_days(SAT1, 0) == MON2


def test_zero_on_sunday_moves_to_monday():
    assert add_business_days(SUN1, 0) == MON2


def test_zero_on_holiday_moves_to_next_business_day():
    assert add_business_days(MON2, 0, holidays=[MON2]) == TUE2


def test_zero_on_weekend_with_holiday_on_next_business_day():
    assert add_business_days(SAT1, 0, holidays=[MON2]) == TUE2


# ---- holidays ----

def test_holiday_is_skipped_forward():
    assert add_business_days(FRI1, 1, holidays=[MON2]) == TUE2


def test_holiday_is_skipped_backward():
    assert add_business_days(MON2, -1, holidays=[FRI1]) == THU1


def test_holiday_on_weekend_changes_nothing():
    assert add_business_days(FRI1, 1, holidays=[SAT1]) == MON2


def test_start_on_holiday_is_not_counted_specially():
    assert add_business_days(TUE2, 1, holidays=[TUE2]) == WED2


def test_holiday_on_start_with_zero_moves_forward():
    assert add_business_days(TUE2, 0, holidays=(TUE2,)) == WED2


def test_holidays_accepts_generator():
    gen = (d for d in [MON2])
    assert add_business_days(FRI1, 1, holidays=gen) == TUE2


def test_holidays_accepts_set_and_tuple():
    assert add_business_days(FRI1, 1, holidays={MON2}) == TUE2
    assert add_business_days(FRI1, 1, holidays=(MON2,)) == TUE2


def test_holidays_default_is_empty():
    assert add_business_days(FRI1, 1) == MON2


def test_duplicate_holidays_are_harmless():
    assert add_business_days(FRI1, 1, holidays=[MON2, MON2]) == TUE2


def test_holidays_with_zero_n_all_weekend_untouched():
    assert add_business_days(FRI1, 0, holidays=[SAT1, SUN1]) == FRI1


# ---- input validation ----

def test_start_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(datetime(2024, 1, 5), 1)


def test_start_string_raises():
    with pytest.raises(TypeError):
        add_business_days("2024-01-05", 1)


def test_n_bool_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, True)


def test_n_float_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, 1.0)


def test_n_string_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, "1")


def test_holiday_string_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, 1, holidays=["2024-01-08"])


def test_holiday_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, 1, holidays=[datetime(2024, 1, 8)])


def test_holiday_int_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI1, 1, holidays=[20240108])
