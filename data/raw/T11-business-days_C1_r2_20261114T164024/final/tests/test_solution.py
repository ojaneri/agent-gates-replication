from datetime import date, datetime

import pytest

from solution import add_business_days

MON = date(2024, 1, 1)  # Monday
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)


def test_forward():
    assert add_business_days(MON, 1) == date(2024, 1, 2)
    assert add_business_days(FRI, 1) == date(2024, 1, 8)
    assert add_business_days(SAT, 1) == date(2024, 1, 8)


def test_backward():
    assert add_business_days(MON, -1) == date(2023, 12, 29)
    assert add_business_days(SAT, -1) == FRI


def test_zero():
    assert add_business_days(MON, 0) == MON
    assert add_business_days(SAT, 0) == date(2024, 1, 8)
    assert add_business_days(MON, 0, [MON]) == date(2024, 1, 2)


def test_holidays():
    assert add_business_days(MON, 1, {date(2024, 1, 2)}) == date(2024, 1, 3)
    assert add_business_days(FRI, 1, (d for d in [SAT])) == date(2024, 1, 8)
    assert add_business_days(MON, -1, [date(2023, 12, 29)]) == date(2023, 12, 28)


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
        add_business_days(MON, 1, [datetime(2024, 1, 2)])
    with pytest.raises(TypeError):
        add_business_days(MON, 1, ["x"])
