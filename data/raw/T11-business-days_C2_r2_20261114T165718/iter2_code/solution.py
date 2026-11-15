from datetime import date, datetime, timedelta


def _is_date(value) -> bool:
    return isinstance(value, date) and not isinstance(value, datetime)


def _holiday_set(holidays) -> set:
    hol = set()
    for h in holidays:
        if not _is_date(h):
            raise TypeError("holidays must contain dates")
        hol.add(h)
    return hol


def _validate(start, n) -> None:
    if not _is_date(start):
        raise TypeError("start must be a date")
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an int")


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _validate(start, n)
    hol = _holiday_set(holidays)

    def is_business(d):
        return d.weekday() < 5 and d not in hol

    if n == 0:
        current = start
        while not is_business(current):
            current += timedelta(days=1)
        return current

    step = timedelta(days=1 if n > 0 else -1)
    remaining = abs(n)
    current = start
    while remaining:
        current += step
        if is_business(current):
            remaining -= 1
    return current
