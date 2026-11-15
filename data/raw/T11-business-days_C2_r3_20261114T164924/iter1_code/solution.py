from datetime import date, datetime, timedelta


def _validate_holidays(holidays) -> set:
    result = set()
    for h in holidays:
        if not isinstance(h, date) or isinstance(h, datetime):
            raise TypeError("holidays must contain datetime.date values")
        result.add(h)
    return result


def add_business_days(start: date, n: int, holidays=()) -> date:
    """Return the date n business days from start. See spec.md."""
    if not isinstance(start, date) or isinstance(start, datetime):
        raise TypeError("start must be a datetime.date")
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
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
