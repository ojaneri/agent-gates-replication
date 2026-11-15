from datetime import date, datetime, timedelta


def _is_pure_date(d) -> bool:
    return isinstance(d, date) and not isinstance(d, datetime)


def _validate_holidays(holidays) -> set:
    result = set()
    for h in holidays:
        if not _is_pure_date(h):
            raise TypeError("holidays must contain datetime.date values")
        result.add(h)
    return result


def _validate(start, n) -> None:
    if not _is_pure_date(start):
        raise TypeError("start must be a datetime.date")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    _validate(start, n)
    hol = _validate_holidays(holidays)

    def is_business(d: date) -> bool:
        return d.weekday() < 5 and d not in hol

    step = timedelta(days=1 if n >= 0 else -1)
    current = start
    if n == 0:
        while not is_business(current):
            current += step
        return current
    remaining = abs(n)
    while remaining:
        current += step
        if is_business(current):
            remaining -= 1
    return current
