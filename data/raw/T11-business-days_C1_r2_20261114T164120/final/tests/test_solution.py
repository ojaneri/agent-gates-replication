import datetime as dt

import pytest

from solution import add_business_days

D = dt.date


# 2026-11-14 is a Saturday. 2026-11-16 is a Monday.


def test_weekday_checks():
    assert D(2026, 11, 16).weekday() == 0
    assert D(2026, 11, 14).weekday() == 5


def test_forward_from_monday_one_day():
    assert add_business_days(D(2026, 11, 16), 1) == D(2026, 11, 17)


def test_forward_across_weekend():
    # Friday + 1 business day = Monday
    assert add_business_days(D(2026, 11, 13), 1) == D(2026, 11, 16)


def test_forward_from_saturday_counts_from_next_day():
    # Saturday start: Mon is the 1st business day after start
    assert add_business_days(D(2026, 11, 14), 1) == D(2026, 11, 16)
    assert add_business_days(D(2026, 11, 14), 5) == D(2026, 11, 20)


def test_forward_five_from_friday_is_next_friday():
    assert add_business_days(D(2026, 11, 13), 5) == D(2026, 11, 20)


def test_forward_ten_days():
    assert add_business_days(D(2026, 11, 16), 10) == D(2026, 11, 30)


def test_backward_from_monday():
    # 1 business day before Monday is Friday
    assert add_business_days(D(2026, 11, 16), -1) == D(2026, 11, 13)


def test_backward_from_saturday():
    assert add_business_days(D(2026, 11, 14), -1) == D(2026, 11, 13)
    assert add_business_days(D(2026, 11, 14), -5) == D(2026, 11, 9)


def test_backward_across_weekend_multiple():
    assert add_business_days(D(2026, 11, 16), -6) == D(2026, 11, 6)


def test_zero_on_business_day_returns_start():
    assert add_business_days(D(2026, 11, 16), 0) == D(2026, 11, 16)


def test_zero_on_saturday_returns_monday():
    assert add_business_days(D(2026, 11, 14), 0) == D(2026, 11, 16)


def test_zero_on_sunday_returns_monday():
    assert add_business_days(D(2026, 11, 15), 0) == D(2026, 11, 16)


def test_holiday_skipped_forward():
    # Monday 16th is a holiday; from Friday 13th +1 -> Tuesday 17th
    assert add_business_days(D(2026, 11, 13), 1, [D(2026, 11, 16)]) == D(2026, 11, 17)


def test_holiday_skipped_backward():
    assert add_business_days(D(2026, 11, 17), -1, [D(2026, 11, 16)]) == D(2026, 11, 13)


def test_holiday_on_start_zero_moves_forward():
    assert add_business_days(D(2026, 11, 16), 0, [D(2026, 11, 16)]) == D(2026, 11, 17)


def test_holiday_zero_on_weekend_chain():
    holidays = [D(2026, 11, 16), D(2026, 11, 17)]
    assert add_business_days(D(2026, 11, 14), 0, holidays) == D(2026, 11, 18)


def test_weekend_holiday_changes_nothing():
    assert add_business_days(D(2026, 11, 13), 1, [D(2026, 11, 14)]) == D(2026, 11, 16)


def test_holidays_as_set_tuple_and_generator():
    h = [D(2026, 11, 16)]
    expected = D(2026, 11, 17)
    assert add_business_days(D(2026, 11, 13), 1, set(h)) == expected
    assert add_business_days(D(2026, 11, 13), 1, tuple(h)) == expected
    assert add_business_days(D(2026, 11, 13), 1, (x for x in h)) == expected


def test_default_holidays_is_empty():
    assert add_business_days(D(2026, 11, 13), 1) == D(2026, 11, 16)


def test_duplicate_holidays_are_fine():
    holidays = [D(2026, 11, 16), D(2026, 11, 16)]
    assert add_business_days(D(2026, 11, 13), 1, holidays) == D(2026, 11, 17)


def test_start_datetime_rejected():
    with pytest.raises(TypeError):
        add_business_days(dt.datetime(2026, 11, 16, 9, 0), 1)


def test_start_not_date_rejected():
    with pytest.raises(TypeError):
        add_business_days("2026-11-16", 1)


def test_n_bool_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), True)


def test_n_float_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1.0)


def test_n_string_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), "1")


def test_holiday_datetime_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1, [dt.datetime(2026, 11, 17, 0, 0)])


def test_holiday_non_date_rejected():
    with pytest.raises(TypeError):
        add_business_days(D(2026, 11, 16), 1, ["2026-11-17"])


def test_negative_zero_is_zero():
    assert add_business_days(D(2026, 11, 16), -0) == D(2026, 11, 16)
