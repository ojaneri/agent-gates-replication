from datetime import date, datetime, timedelta

ONE_DAY = timedelta(days=1)
FRIDAY = 4


def _is_date(x) -> bool:
    return isinstance(x, date) and not isinstance(x, datetime)


def _is_business(d: date, holidays: set) -> bool:
    return d.weekday() <= FRIDAY and d not in holidays


def add_business_days(start: date, n: int, holidays=()) -> date:
    if not _is_date(start):
        raise TypeError("start must be a date")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")
    hol = set()
    for h in holidays:
        if not _is_date(h):
            raise TypeError("holidays must be dates")
        hol.add(h)
    d = start
    if n == 0:
        while not _is_business(d, hol):
            d += ONE_DAY
        return d
    remaining = n
    if n >= 1:
        while remaining > 0:
            d = d + ONE_DAY
            if _is_business(d, hol):
                remaining -= 1
    else:
        while remaining < 0:
            d = d - ONE_DAY
            if _is_business(d, hol):
                remaining += 1
    return d
