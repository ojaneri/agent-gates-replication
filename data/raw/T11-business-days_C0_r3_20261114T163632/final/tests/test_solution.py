from datetime import date, datetime

import pytest

from solution import add_business_days

# Reference calendar (2024): Mon 01 Jan ... Fri 05 Jan, Sat 06, Sun 07, Mon 08 Jan.


def test_forward_from_monday():
    assert add_business_days(date(2024, 1, 1), 1) == date(2024, 1, 2)


def test_forward_from_friday_skips_weekend():
    assert add_business_days(date(2024, 1, 5), 1) == date(2024, 1, 8)


def test_forward_five_days_across_week():
    assert add_business_days(date(2024, 1, 1), 5) == date(2024, 1, 8)


def test_forward_from_saturday_start_not_counted():
    assert add_business_days(date(2024, 1, 6), 1) == date(2024, 1, 8)


def test_zero_on_business_day_returns_start():
    assert add_business_days(date(2024, 1, 8), 0) == date(2024, 1, 8)


def test_zero_on_saturday_returns_next_monday():
    assert add_business_days(date(2024, 1, 6), 0) == date(2024, 1, 8)


def test_zero_on_sunday_returns_next_monday():
    assert add_business_days(date(2024, 1, 7), 0) == date(2024, 1, 8)


def test_backward_from_monday():
    assert add_business_days(date(2024, 1, 8), -1) == date(2024, 1, 5)


def test_backward_from_saturday():
    assert add_business_days(date(2024, 1, 6), -1) == date(2024, 1, 5)


def test_backward_five_days_across_week():
    assert add_business_days(date(2024, 1, 8), -5) == date(2024, 1, 1)


def test_forward_skips_holiday():
    assert add_business_days(date(2024, 1, 1), 1, [date(2024, 1, 2)]) == date(2024, 1, 3)


def test_backward_skips_holiday():
    assert add_business_days(date(2024, 1, 3), -1, {date(2024, 1, 2)}) == date(2024, 1, 1)


def test_weekend_holiday_changes_nothing():
    assert add_business_days(date(2024, 1, 5), 1, [date(2024, 1, 6)]) == date(2024, 1, 8)


def test_zero_on_holiday_moves_to_next_business_day():
    assert add_business_days(date(2024, 1, 2), 0, (date(2024, 1, 2),)) == date(2024, 1, 3)


def test_holidays_accepts_generator():
    gen = (d for d in [date(2024, 1, 2), date(2024, 1, 3)])
    assert add_business_days(date(2024, 1, 1), 1, gen) == date(2024, 1, 4)


def test_holiday_consecutive_run_is_skipped():
    holidays = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert add_business_days(date(2024, 1, 1), 1, holidays) == date(2024, 1, 5)


def test_start_datetime_raises_type_error():
    with pytest.raises(TypeError):
        add_business_days(datetime(2024, 1, 1), 1)


def test_start_string_raises_type_error():
    with pytest.raises(TypeError):
        add_business_days("2024-01-01", 1)


@pytest.mark.parametrize("bad_n", [True, False, 1.0, 2.5, "1"])
def test_non_int_n_raises_type_error(bad_n):
    with pytest.raises(TypeError):
        add_business_days(date(2024, 1, 1), bad_n)


def test_holiday_datetime_raises_type_error():
    with pytest.raises(TypeError):
        add_business_days(date(2024, 1, 1), 1, [datetime(2024, 1, 2)])


def test_holiday_non_date_raises_type_error():
    with pytest.raises(TypeError):
        add_business_days(date(2024, 1, 1), 1, ["2024-01-02"])
