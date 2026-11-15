from datetime import date, datetime

import pytest

from solution import add_business_days


# 2024-01-01 is a Monday.
MON = date(2024, 1, 1)
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)
SUN = date(2024, 1, 7)


def test_forward_from_monday():
    assert add_business_days(MON, 1) == date(2024, 1, 2)
    assert add_business_days(MON, 4) == FRI
    assert add_business_days(MON, 5) == date(2024, 1, 8)


def test_start_not_counted_when_business_day():
    assert add_business_days(MON, 0) == MON


def test_forward_from_friday_skips_weekend():
    assert add_business_days(FRI, 1) == date(2024, 1, 8)


def test_forward_from_saturday_start_not_counted():
    # Saturday start: first business day after it is Monday (n=1).
    assert add_business_days(SAT, 1) == date(2024, 1, 8)


def test_backward_from_monday():
    assert add_business_days(MON, -1) == date(2023, 12, 29)  # Friday


def test_backward_five_from_monday_is_previous_monday():
    # Business days before Mon 2024-01-01: Fri 12-29, Thu 28, Wed 27, Tue 26, Mon 25.
    assert add_business_days(MON, -5) == date(2023, 12, 25)


def test_backward_from_saturday():
    assert add_business_days(SAT, -1) == FRI


def test_backward_from_sunday_n_minus_two():
    assert add_business_days(SUN, -2) == date(2024, 1, 4)


def test_zero_on_weekend_gives_next_business_day():
    assert add_business_days(SAT, 0) == date(2024, 1, 8)
    assert add_business_days(SUN, 0) == date(2024, 1, 8)


def test_zero_on_business_day_returns_start():
    assert add_business_days(FRI, 0) == FRI


def test_holidays_are_skipped_forward():
    hol = [date(2024, 1, 2)]
    assert add_business_days(MON, 1, hol) == date(2024, 1, 3)


def test_holidays_are_skipped_backward():
    hol = [date(2023, 12, 29)]
    assert add_business_days(MON, -1, hol) == date(2023, 12, 28)


def test_holiday_on_start_not_counted_forward():
    assert add_business_days(MON, 1, {MON}) == date(2024, 1, 2)


def test_holiday_on_start_zero_moves_to_next():
    assert add_business_days(MON, 0, {MON}) == date(2024, 1, 2)


def test_weekend_holiday_changes_nothing():
    assert add_business_days(FRI, 1, [SAT, SUN]) == date(2024, 1, 8)


def test_holidays_accept_generator_tuple_and_set():
    gen = (d for d in [date(2024, 1, 2)])
    assert add_business_days(MON, 1, gen) == date(2024, 1, 3)
    assert add_business_days(MON, 1, (date(2024, 1, 2),)) == date(2024, 1, 3)
    assert add_business_days(MON, 1, {date(2024, 1, 2)}) == date(2024, 1, 3)


def test_default_holidays_empty():
    assert add_business_days(MON, 2) == date(2024, 1, 3)


def test_consecutive_holidays():
    hol = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert add_business_days(MON, 1, hol) == FRI


@pytest.mark.parametrize("bad", [datetime(2024, 1, 1, 9, 0), "2024-01-01", None, 20240101])
def test_start_must_be_date(bad):
    with pytest.raises(TypeError):
        add_business_days(bad, 1)


@pytest.mark.parametrize("bad", [True, False, 1.0, 2.5, "3", None])
def test_n_must_be_int(bad):
    with pytest.raises(TypeError):
        add_business_days(MON, bad)


@pytest.mark.parametrize("bad", [datetime(2024, 1, 2), "2024-01-02", 5])
def test_holiday_elements_must_be_date(bad):
    with pytest.raises(TypeError):
        add_business_days(MON, 1, [bad])


def test_returns_date_type():
    result = add_business_days(MON, 3)
    assert isinstance(result, date)
    assert not isinstance(result, datetime)
