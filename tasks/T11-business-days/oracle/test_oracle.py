from datetime import date, datetime

import pytest

from solution import add_business_days

FRI = date(2026, 11, 13)
SAT = date(2026, 11, 14)
SUN = date(2026, 11, 15)
MON = date(2026, 11, 16)
TUE = date(2026, 11, 17)
WED = date(2026, 11, 18)
THU = date(2026, 11, 19)


def test_weekdays_as_expected():
    assert [d.weekday() for d in (FRI, SAT, SUN, MON, TUE, WED, THU)] == [4, 5, 6, 0, 1, 2, 3]


@pytest.mark.parametrize("start,n,hol,expected", [
    (FRI, 1, (), MON),
    (WED, 1, (), THU),
    (THU, 1, (), date(2026, 11, 20)),
    (MON, 5, (), date(2026, 11, 23)),
    (FRI, 1, (MON,), TUE),
    (SAT, 1, (), MON),
    (SUN, 1, (), MON),
    (SAT, 2, (), TUE),
    (date(2026, 12, 31), 2, (date(2027, 1, 1),), date(2027, 1, 5)),
    (MON, -1, (), FRI),
    (SAT, -1, (), FRI),
    (SUN, -1, (), FRI),
    (TUE, -1, (MON,), FRI),
    (date(2026, 11, 30), -10, (), MON),
    (TUE, -2, (), FRI),
    (SAT, 0, (), MON),
    (SUN, 0, (), MON),
    (SAT, 0, (MON,), TUE),
    (WED, 0, (), WED),
    (FRI, 0, (), FRI),
    (WED, 0, (WED,), THU),
    (FRI, 1, (SAT, SUN), MON),
    (FRI, 3, [MON, WED], date(2026, 11, 20)),
])
def test_add(start, n, hol, expected):
    assert add_business_days(start, n, hol) == expected


def test_default_holidays_and_generator():
    assert add_business_days(FRI, 1) == MON
    assert add_business_days(FRI, 1, (d for d in [MON])) == TUE
    assert add_business_days(FRI, 1, {MON, TUE}) == WED


def test_returns_date():
    r = add_business_days(FRI, 1)
    assert type(r) is date


@pytest.mark.parametrize("start,n,hol", [
    (datetime(2026, 11, 13, 9), 1, ()),
    ("2026-11-13", 1, ()),
    (FRI, True, ()),
    (FRI, 1.0, ()),
    (FRI, "1", ()),
    (FRI, 1, ("2026-11-16",)),
    (FRI, 1, (datetime(2026, 11, 16),)),
])
def test_type_errors(start, n, hol):
    with pytest.raises(TypeError):
        add_business_days(start, n, hol)
