from datetime import date, datetime

import pytest

from solution import add_business_days as f

MON = date(2024, 1, 1)
FRI = date(2024, 1, 5)
SAT = date(2024, 1, 6)


def test_forward():
    assert f(MON, 1) == date(2024, 1, 2)
    assert f(FRI, 1) == date(2024, 1, 8)
    assert f(SAT, 1) == date(2024, 1, 8)
    assert f(MON, 10) == date(2024, 1, 15)


def test_backward():
    assert f(MON, -1) == date(2023, 12, 29)
    assert f(SAT, -1) == FRI


def test_zero():
    assert f(MON, 0) == MON
    assert f(SAT, 0) == date(2024, 1, 8)
    assert f(MON, 0, [MON]) == date(2024, 1, 2)


def test_holidays():
    assert f(MON, 1, [date(2024, 1, 2)]) == date(2024, 1, 3)
    assert f(MON, 1, (d for d in [date(2024, 1, 2)])) == date(2024, 1, 3)
    assert f(MON, 1, {SAT}) == date(2024, 1, 2)


def test_type_errors():
    with pytest.raises(TypeError):
        f(datetime(2024, 1, 1), 1)
    with pytest.raises(TypeError):
        f("2024-01-01", 1)
    with pytest.raises(TypeError):
        f(MON, True)
    with pytest.raises(TypeError):
        f(MON, 1.0)
    with pytest.raises(TypeError):
        f(MON, 1, [datetime(2024, 1, 2)])
    with pytest.raises(TypeError):
        f(MON, 1, ["x"])
