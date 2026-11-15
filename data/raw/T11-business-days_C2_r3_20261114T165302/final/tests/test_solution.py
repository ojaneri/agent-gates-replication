from datetime import date, datetime

import pytest

from solution import add_business_days

# 2024-01-01 is a Monday.
MON = date(2024, 1, 8)
TUE = date(2024, 1, 9)
WED = date(2024, 1, 10)
THU = date(2024, 1, 11)
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)
SUN = date(2024, 1, 7)


def test_forward_from_friday_skips_weekend():
    assert add_business_days(FRI, 1) == MON


def test_forward_from_weekday():
    assert add_business_days(MON, 1) == TUE


def test_forward_five_days_from_monday():
    assert add_business_days(MON, 5) == date(2024, 1, 15)


def test_forward_ten_days_spans_two_weekends():
    assert add_business_days(MON, 10) == date(2024, 1, 22)


def test_forward_from_saturday_start_not_counted():
    assert add_business_days(SAT, 1) == MON


def test_forward_from_sunday_start_not_counted():
    assert add_business_days(SUN, 1) == MON
    assert add_business_days(SUN, 2) == TUE


def test_forward_start_on_business_day_not_counted():
    assert add_business_days(WED, 1) == THU
    assert add_business_days(WED, 2) == date(2024, 1, 12)


def test_backward_from_monday_one():
    assert add_business_days(MON, -1) == FRI


def test_backward_five_days_from_monday():
    assert add_business_days(MON, -5) == date(2024, 1, 1)


def test_backward_from_saturday():
    assert add_business_days(SAT, -1) == FRI


def test_backward_start_not_counted():
    assert add_business_days(WED, -1) == TUE
    assert add_business_days(WED, -2) == MON


def test_zero_on_business_day_returns_start():
    assert add_business_days(WED, 0) == WED


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(SAT, 0) == MON


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(SUN, 0) == MON


def test_zero_on_friday_returns_friday():
    assert add_business_days(FRI, 0) == FRI


def test_holiday_pushes_forward_result():
    assert add_business_days(FRI, 1, holidays=[MON]) == TUE


def test_holiday_on_start_not_counted_forward():
    assert add_business_days(WED, 1, holidays=[WED]) == THU


def test_holiday_on_weekend_changes_nothing():
    assert add_business_days(FRI, 1, holidays=[SAT]) == MON
    assert add_business_days(FRI, 1, holidays=[SUN]) == MON


def test_holiday_backward():
    assert add_business_days(TUE, -1, holidays=[MON]) == FRI
    assert add_business_days(TUE, -2, holidays=[MON]) == date(2024, 1, 4)


def test_holiday_on_day_with_zero_n_moves_to_next():
    assert add_business_days(WED, 0, holidays=[WED]) == THU


def test_zero_on_weekend_skips_holiday_monday():
    assert add_business_days(SAT, 0, holidays=[MON]) == TUE


def test_holidays_as_set_tuple_and_generator():
    expected = TUE
    assert add_business_days(FRI, 1, holidays={MON}) == expected
    assert add_business_days(FRI, 1, holidays=(MON,)) == expected
    assert add_business_days(FRI, 1, holidays=(d for d in [MON])) == expected


def test_duplicate_holidays_are_harmless():
    assert add_business_days(FRI, 1, holidays=[MON, MON]) == TUE


def test_default_holidays_empty():
    assert add_business_days(FRI, 1) == MON


def test_returns_date_type():
    result = add_business_days(MON, 3)
    assert isinstance(result, date)
    assert not isinstance(result, datetime)


def test_start_datetime_raises():
    with pytest.raises(TypeError):
        add_business_days(datetime(2024, 1, 8, 12, 0), 1)


def test_start_string_raises():
    with pytest.raises(TypeError):
        add_business_days("2024-01-08", 1)


def test_n_bool_raises():
    with pytest.raises(TypeError):
        add_business_days(MON, True)
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
        add_business_days(FRI, 1, holidays=[datetime(2024, 1, 8)])


def test_holiday_string_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1, holidays=["2024-01-08"])


def test_holiday_none_raises():
    with pytest.raises(TypeError):
        add_business_days(FRI, 1, holidays=[None])
