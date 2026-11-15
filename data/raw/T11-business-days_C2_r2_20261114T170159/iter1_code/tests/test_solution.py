import datetime as dt

import pytest

from solution import add_business_days

# 2024-01-01 is a Monday.
MON = dt.date(2024, 1, 1)
TUE = dt.date(2024, 1, 2)
WED = dt.date(2024, 1, 3)
FRI = dt.date(2024, 1, 5)
SAT = dt.date(2024, 1, 6)
SUN = dt.date(2024, 1, 7)
NEXT_MON = dt.date(2024, 1, 8)


# ---- forward movement -------------------------------------------------

def test_one_day_forward_from_monday():
    assert add_business_days(MON, 1) == TUE


def test_one_day_forward_from_friday_skips_weekend():
    assert add_business_days(FRI, 1) == NEXT_MON


def test_five_forward_from_monday_is_next_monday():
    assert add_business_days(MON, 5) == NEXT_MON


def test_start_is_not_counted_when_start_is_weekend():
    assert add_business_days(SAT, 1) == NEXT_MON


def test_forward_from_saturday_two_days():
    assert add_business_days(SAT, 2) == dt.date(2024, 1, 9)


def test_forward_from_sunday_one_day_is_monday():
    assert add_business_days(SUN, 1) == NEXT_MON


def test_large_forward_crosses_year_of_weeks():
    # 260 business days = 52 weeks, from Mon 2024-01-01 to Mon 2024-12-30.
    assert add_business_days(MON, 260) == dt.date(2024, 12, 30)


def test_forward_two_days_from_monday_is_wednesday():
    assert add_business_days(MON, 2) == WED


# ---- backward movement ------------------------------------------------

def test_one_day_back_from_monday_is_friday():
    assert add_business_days(NEXT_MON, -1) == FRI


def test_one_day_back_from_saturday_is_friday():
    assert add_business_days(SAT, -1) == FRI


def test_five_back_from_next_monday_is_monday():
    assert add_business_days(NEXT_MON, -5) == MON


def test_back_from_sunday_one_is_friday():
    assert add_business_days(SUN, -1) == FRI


def test_start_not_counted_backward_on_weekday():
    assert add_business_days(WED, -1) == TUE


def test_large_backward():
    assert add_business_days(dt.date(2024, 12, 30), -260) == MON


# ---- n == 0 -----------------------------------------------------------

def test_zero_on_business_day_returns_start():
    assert add_business_days(WED, 0) == WED


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(SAT, 0) == NEXT_MON


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(SUN, 0) == NEXT_MON


def test_zero_on_friday_returns_friday():
    assert add_business_days(FRI, 0) == FRI


def test_zero_on_weekend_with_monday_holiday_skips_to_tuesday():
    assert add_business_days(SAT, 0, [NEXT_MON]) == dt.date(2024, 1, 9)


def test_zero_on_holiday_returns_next_business_day():
    assert add_business_days(TUE, 0, [TUE]) == WED


# ---- holidays ---------------------------------------------------------

def test_holiday_skipped_forward():
    assert add_business_days(MON, 1, [TUE]) == WED


def test_holiday_skipped_backward():
    assert add_business_days(WED, -1, [TUE]) == MON


def test_holiday_on_weekend_changes_nothing():
    assert add_business_days(MON, 5, [SAT, SUN]) == NEXT_MON


def test_holiday_on_weekend_backward_changes_nothing():
    assert add_business_days(NEXT_MON, -1, [SUN]) == FRI


def test_holiday_equal_to_start_is_not_counted_forward():
    # start is never counted, so a holiday on start has no effect on n>0.
    assert add_business_days(TUE, 1, [TUE]) == WED


def test_multiple_holidays_consecutive():
    assert add_business_days(MON, 1, [TUE, WED]) == dt.date(2024, 1, 4)


def test_holiday_on_friday_pushes_past_weekend():
    assert add_business_days(FRI - dt.timedelta(days=1), 1, [FRI]) == NEXT_MON


def test_holiday_on_start_friday_n_zero_no_effect_when_weekday():
    assert add_business_days(FRI, 0, [FRI]) == NEXT_MON


def test_holiday_before_start_does_not_affect_forward():
    assert add_business_days(WED, 1, [MON]) == dt.date(2024, 1, 4)


def test_holiday_in_backward_path_beyond_result_is_not_reached():
    # Backward from Mon 2024-01-08 by 2: Fri 01-05, Thu 01-04. Holiday on 01-01 is not reached.
    assert add_business_days(NEXT_MON, -2, [MON]) == dt.date(2024, 1, 4)


def test_holiday_in_backward_path_is_skipped():
    # Backward from Mon 2024-01-08 by 2 with Fri 01-05 a holiday: Thu 01-04, Wed 01-03.
    assert add_business_days(NEXT_MON, -2, [FRI]) == WED


def test_duplicate_holidays_counted_once():
    assert add_business_days(MON, 1, [TUE, TUE]) == WED


def test_holidays_as_set():
    assert add_business_days(MON, 1, {TUE}) == WED


def test_holidays_as_tuple():
    assert add_business_days(MON, 1, (TUE,)) == WED


def test_holidays_as_generator():
    assert add_business_days(MON, 1, (d for d in [TUE])) == WED


def test_default_holidays_is_empty():
    assert add_business_days(MON, 1) == TUE


def test_empty_holidays_list():
    assert add_business_days(MON, 1, []) == TUE


def test_holidays_not_consumed_across_calls_for_generator_semantics():
    hol = [TUE]
    assert add_business_days(MON, 1, hol) == WED
    assert add_business_days(MON, 1, hol) == WED


# ---- return type -----------------------------------------------------

def test_returns_date_not_datetime():
    result = add_business_days(MON, 3)
    assert isinstance(result, dt.date)
    assert not isinstance(result, dt.datetime)


def test_returns_date_for_zero():
    assert isinstance(add_business_days(MON, 0), dt.date)


# ---- input validation -------------------------------------------------

def test_start_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(dt.datetime(2024, 1, 1), 1)


def test_start_string_raises():
    with pytest.raises(TypeError):
        add_business_days("2024-01-01", 1)


def test_start_none_raises():
    with pytest.raises(TypeError):
        add_business_days(None, 1)


def test_n_bool_true_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, True)


def test_n_bool_false_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, False)


def test_n_float_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1.0)


def test_n_string_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, "1")


def test_holiday_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [dt.datetime(2024, 1, 2)])


def test_holiday_string_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, ["2024-01-02"])


def test_holiday_none_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [None])


def test_holiday_int_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [20240102])


def test_holidays_not_iterable_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, 1, 5)
